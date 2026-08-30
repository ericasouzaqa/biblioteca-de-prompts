import base64
import hashlib
import hmac
import json
import os
import secrets
import shutil
import sqlite3
import stat
import sys
import tempfile
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

APP_NAME = "Central de Prompts"
APP_DIR = Path.home() / ".central-de-prompts"
DB_PATH = APP_DIR / "central.db"

STATUSES = ["Em testes", "Ativo", "Em construção", "Congelado"]
PROMPT_TOOLS = ["ChatGPT", "Manus", "Copilot", "Claude", "Gemini", "Outra"]
TIP_CATEGORIES = [
    "Analisar arquitetura", "Retomar projeto", "Continuar implementação",
    "Revisar código", "Refatorar com segurança", "Investigar erro",
    "Preparar publicação", "Melhorar testes", "Criar documentação",
    "Avaliar impacto de alteração"
]


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def hash_password(password, salt=None):
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1)
    return base64.b64encode(salt + digest).decode("ascii")


def verify_password(password, stored):
    try:
        raw = base64.b64decode(stored.encode("ascii"))
        salt, expected = raw[:16], raw[16:]
        actual = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1)
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False


class Storage:
    def __init__(self):
        APP_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.db = sqlite3.connect(DB_PATH)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys = ON")
        self.db.execute("PRAGMA secure_delete = ON")
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, objective TEXT,
            github_repo TEXT, repo_link TEXT, tool TEXT, status TEXT NOT NULL,
            last_prompt TEXT, last_interaction TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, category TEXT,
            project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL, tool TEXT,
            objective TEXT, trigger TEXT, when_to_use TEXT, content TEXT NOT NULL,
            expected_result TEXT, notes TEXT, tags TEXT, favorite INTEGER DEFAULT 0,
            created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS tips (
            id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, category TEXT,
            when_to_use TEXT, explanation TEXT, content TEXT NOT NULL,
            created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, language TEXT,
            project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL, purpose TEXT,
            content TEXT NOT NULL, tags TEXT, notes TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        """)
        self.db.commit()
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_prompts_search ON prompts(name, category, tool, tags)")
        self.db.commit()

    def setting(self, key, default=None):
        row = self.db.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row["value"] if row else default

    def set_setting(self, key, value):
        self.db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)", (key, value))
        self.db.commit()

    def rows(self, table, where="", params=()):
        return self.db.execute(f"SELECT * FROM {table} {where}", params).fetchall()

    def close(self):
        self.db.close()


class LoginFrame(ttk.Frame):
    def __init__(self, master, on_login):
        super().__init__(master, padding=40)
        self.on_login = on_login
        self.storage = master.storage
        self.has_user = bool(self.storage.setting("username"))
        self.columnconfigure(0, weight=1)
        ttk.Label(self, text="Central de Prompts", style="Title.TLabel").grid(row=0, column=0, pady=(20, 8))
        ttk.Label(self, text="Sua biblioteca pessoal, privada e offline", style="Subtitle.TLabel").grid(row=1, column=0, pady=(0, 28))
        box = ttk.LabelFrame(self, text="Acesso privado", padding=20)
        box.grid(row=2, column=0, sticky="ew")
        box.columnconfigure(1, weight=1)
        ttk.Label(box, text="Usuário").grid(row=0, column=0, sticky="w", padx=(0, 12), pady=6)
        self.user = ttk.Entry(box, width=32)
        self.user.grid(row=0, column=1, sticky="ew", pady=6)
        ttk.Label(box, text="Senha").grid(row=1, column=0, sticky="w", padx=(0, 12), pady=6)
        self.password = ttk.Entry(box, show="•", width=32)
        self.password.grid(row=1, column=1, sticky="ew", pady=6)
        self.password.bind("<Return>", lambda e: self.submit())
        ttk.Button(box, text="Entrar", command=self.submit).grid(row=2, column=1, sticky="e", pady=(16, 0))
        if not self.has_user:
            ttk.Label(self, text="Primeiro acesso: informe um usuário e crie sua senha local.", foreground="#52606d").grid(row=3, column=0, pady=18)

    def submit(self):
        user, password = self.user.get().strip(), self.password.get()
        if not user or len(password) < 6:
            messagebox.showwarning(APP_NAME, "Informe o usuário e uma senha com pelo menos 6 caracteres.")
            return
        stored_user = self.storage.setting("username")
        if not stored_user:
            self.storage.set_setting("username", user)
            self.storage.set_setting("password_hash", hash_password(password))
            messagebox.showinfo(APP_NAME, "Acesso local criado com sucesso.")
            self.on_login(user)
        elif hmac.compare_digest(stored_user, user) and verify_password(password, self.storage.setting("password_hash", "")):
            self.on_login(user)
        else:
            messagebox.showerror(APP_NAME, "Usuário ou senha inválidos.")


class MainApp(ttk.Frame):
    def __init__(self, master, username, logout):
        super().__init__(master, padding=14)
        self.master = master
        self.storage = master.storage
        self.username = username
        self.logout = logout
        self.project_map = {}
        self.build()

    def build(self):
        self.columnconfigure(0, weight=1); self.rowconfigure(2, weight=1)
        header = ttk.Frame(self)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10)); header.columnconfigure(1, weight=1)
        ttk.Label(header, text="Central de Prompts", style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(header, text=f"Sessão local: {self.username}", style="Subtitle.TLabel").grid(row=0, column=1, sticky="w", padx=20)
        ttk.Button(header, text="Sair", command=self.logout).grid(row=0, column=2)
        search = ttk.Frame(self); search.grid(row=1, column=0, sticky="ew", pady=(0, 10)); search.columnconfigure(1, weight=1)
        ttk.Label(search, text="⌕ Pesquisa global").grid(row=0, column=0, padx=(0, 10))
        self.search_var = tk.StringVar(); entry = ttk.Entry(search, textvariable=self.search_var)
        entry.grid(row=0, column=1, sticky="ew"); entry.bind("<KeyRelease>", lambda e: self.refresh_all())
        ttk.Button(search, text="Limpar", command=lambda: self.search_var.set("")).grid(row=0, column=2, padx=(8, 0))
        self.tabs = ttk.Notebook(self); self.tabs.grid(row=2, column=0, sticky="nsew")
        self.project_tab = self.make_projects_tab(); self.prompt_tab = self.make_prompts_tab(); self.tip_tab = self.make_tips_tab(); self.code_tab = self.make_codes_tab(); self.settings_tab = self.make_settings_tab()
        self.refresh_all()

    def make_tree(self, parent, columns, headings):
        frame = ttk.Frame(parent); frame.columnconfigure(0, weight=1); frame.rowconfigure(0, weight=1)
        tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse")
        for col, head in zip(columns, headings): tree.heading(col, text=head); tree.column(col, width=150, anchor="w")
        tree.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview); scroll.grid(row=0, column=1, sticky="ns"); tree.configure(yscrollcommand=scroll.set)
        return frame, tree

    def tab_header(self, parent, title, command):
        top = ttk.Frame(parent); top.pack(fill="x", pady=(0, 8)); ttk.Label(top, text=title, style="Section.TLabel").pack(side="left"); ttk.Button(top, text="＋ Novo", command=command).pack(side="right")

    def make_projects_tab(self):
        tab = ttk.Frame(self.tabs, padding=12); self.tabs.add(tab, text="Projetos"); self.tab_header(tab, "Projetos", lambda: self.edit_project())
        frame, self.project_tree = self.make_tree(tab, ("name", "status", "tool", "github", "updated"), ("Projeto", "Status", "Ferramenta", "Repositório", "Atualizado")); frame.pack(fill="both", expand=True)
        self.project_tree.bind("<Double-1>", lambda e: self.edit_project())
        self.project_tree.bind("<<TreeviewSelect>>", lambda e: self.show_project_detail())
        self.project_detail = tk.Text(tab, height=7, wrap="word", state="disabled", bg="#f7f9fb", relief="flat"); self.project_detail.pack(fill="x", pady=(8, 0)); return tab

    def make_prompts_tab(self):
        tab = ttk.Frame(self.tabs, padding=12); self.tabs.add(tab, text="Biblioteca de Prompts"); self.tab_header(tab, "Prompts reutilizáveis", lambda: self.edit_prompt())
        frame, self.prompt_tree = self.make_tree(tab, ("favorite", "name", "category", "project", "tool", "tags"), ("★", "Nome", "Categoria", "Projeto", "Ferramenta", "Tags")); frame.pack(fill="both", expand=True); self.prompt_tree.bind("<Double-1>", lambda e: self.edit_prompt()); return tab

    def make_tips_tab(self):
        tab = ttk.Frame(self.tabs, padding=12); self.tabs.add(tab, text="Dicas de Prompt"); self.tab_header(tab, "Dicas prontas", lambda: self.edit_tip())
        frame, self.tip_tree = self.make_tree(tab, ("title", "category", "when"), ("Título", "Categoria", "Quando usar")); frame.pack(fill="both", expand=True); self.tip_tree.bind("<Double-1>", lambda e: self.edit_tip()); return tab

    def make_codes_tab(self):
        tab = ttk.Frame(self.tabs, padding=12); self.tabs.add(tab, text="Biblioteca de Códigos"); self.tab_header(tab, "Códigos técnicos úteis", lambda: self.edit_code())
        frame, self.code_tree = self.make_tree(tab, ("name", "language", "project", "tags"), ("Nome", "Linguagem", "Projeto", "Tags")); frame.pack(fill="both", expand=True); self.code_tree.bind("<Double-1>", lambda e: self.edit_code()); return tab

    def make_settings_tab(self):
        tab = ttk.Frame(self.tabs, padding=18); self.tabs.add(tab, text="Configurações")
        ttk.Label(tab, text="Configurações e proteção local", style="Section.TLabel").pack(anchor="w")
        ttk.Label(tab, text="Os dados ficam em ~/.central-de-prompts e não são enviados para serviços externos.", wraplength=600).pack(anchor="w", pady=(8, 20))
        ttk.Button(tab, text="Exportar backup JSON", command=self.export_backup).pack(anchor="w", pady=4)
        ttk.Button(tab, text="Importar backup JSON", command=self.import_backup).pack(anchor="w", pady=4)
        ttk.Button(tab, text="Alterar senha", command=self.change_password).pack(anchor="w", pady=4)
        ttk.Button(tab, text="Abrir pasta de dados", command=lambda: messagebox.showinfo(APP_NAME, str(APP_DIR))).pack(anchor="w", pady=4)
        ttk.Separator(tab).pack(fill="x", pady=20)
        ttk.Label(tab, text="A exclusão de registros ocorre somente quando solicitada pelo usuário.", foreground="#52606d").pack(anchor="w")
        return tab

    def query_filter(self, table, extra="", params=()):
        q = self.search_var.get().strip().lower(); where = extra; values = list(params)
        if q:
            fields = {"projects": "name || ' ' || objective || ' ' || github_repo || ' ' || tool || ' ' || status", "prompts": "name || ' ' || category || ' ' || objective || ' ' || trigger || ' ' || content || ' ' || tags", "tips": "title || ' ' || category || ' ' || when_to_use || ' ' || explanation || ' ' || content", "codes": "name || ' ' || language || ' ' || purpose || ' ' || content || ' ' || tags"}[table]
            where = (where + " AND " if where else "WHERE ") + f"LOWER({fields}) LIKE ?"; values.append(f"%{q}%")
        return self.storage.rows(table, where, values)

    def refresh_all(self):
        self.project_map = {r["id"]: r["name"] for r in self.storage.rows("projects", "ORDER BY name")}
        for tree in (self.project_tree, self.prompt_tree, self.tip_tree, self.code_tree): tree.delete(*tree.get_children())
        for r in self.query_filter("projects", "ORDER BY updated_at DESC"):
            self.project_tree.insert("", "end", iid=str(r["id"]), values=(r["name"], r["status"], r["tool"] or "", r["github_repo"] or "", r["updated_at"]))
        for r in self.query_filter("prompts", "ORDER BY favorite DESC, updated_at DESC"):
            self.prompt_tree.insert("", "end", iid=str(r["id"]), values=("★" if r["favorite"] else "", r["name"], r["category"] or "", self.project_map.get(r["project_id"], ""), r["tool"] or "", r["tags"] or ""))
        for r in self.query_filter("tips", "ORDER BY updated_at DESC"): self.tip_tree.insert("", "end", iid=str(r["id"]), values=(r["title"], r["category"] or "", r["when_to_use"] or ""))
        for r in self.query_filter("codes", "ORDER BY updated_at DESC"): self.code_tree.insert("", "end", iid=str(r["id"]), values=(r["name"], r["language"] or "", self.project_map.get(r["project_id"], ""), r["tags"] or ""))

    def show_project_detail(self):
        sel = self.project_tree.selection()
        if not sel: return
        r = self.storage.db.execute("SELECT * FROM projects WHERE id=?", (int(sel[0]),)).fetchone()
        prompts = self.storage.db.execute("SELECT name FROM prompts WHERE project_id=? ORDER BY updated_at DESC", (r["id"],)).fetchall()
        text = f"{r['name']} — {r['status']}\nObjetivo: {r['objective'] or '—'}\nFerramenta: {r['tool'] or '—'}\nRepositório: {r['github_repo'] or r['repo_link'] or '—'}\nÚltimo prompt: {r['last_prompt'] or '—'} | Última interação: {r['last_interaction'] or '—'}\nPrompts relacionados: {', '.join(x['name'] for x in prompts) or '—'}"
        self.project_detail.configure(state="normal"); self.project_detail.delete("1.0", "end"); self.project_detail.insert("1.0", text); self.project_detail.configure(state="disabled")

    def form(self, title, fields, values=None):
        win = tk.Toplevel(self); win.title(title); win.transient(self); win.grab_set(); win.geometry("620x560")
        body = ttk.Frame(win, padding=16); body.pack(fill="both", expand=True); body.columnconfigure(1, weight=1); body.rowconfigure(len(fields)-1, weight=1)
        widgets = {}
        for i, (key, label, kind, options) in enumerate(fields):
            ttk.Label(body, text=label).grid(row=i, column=0, sticky="nw", padx=(0, 12), pady=6)
            if kind == "combo": w = ttk.Combobox(body, values=options, state="readonly")
            elif kind == "text": w = tk.Text(body, height=5, wrap="word")
            else: w = ttk.Entry(body)
            w.grid(row=i, column=1, sticky="nsew" if kind == "text" else "ew", pady=6); widgets[key] = w
            if values and values.get(key) is not None:
                val = str(values[key]); w.insert("1.0", val) if kind == "text" else w.set(val) if kind == "combo" else w.insert(0, val)
        result = {}
        def save():
            for key, w in widgets.items(): result[key] = w.get("1.0", "end-1c") if isinstance(w, tk.Text) else w.get()
            if any(not str(result.get(k, "")).strip() for k, _, _, _ in fields[:1]): messagebox.showwarning(APP_NAME, "Preencha o nome ou título.", parent=win); return
            win.destroy()
        ttk.Button(body, text="Salvar", command=save).grid(row=len(fields), column=1, sticky="e", pady=12)
        self.wait_window(win); return result or None

    def selected(self, tree):
        sel = tree.selection(); return int(sel[0]) if sel else None

    def edit_project(self):
        rid = self.selected(self.project_tree); old = self.storage.db.execute("SELECT * FROM projects WHERE id=?", (rid,)).fetchone() if rid else None
        fields = [("name", "Nome", "entry", None), ("objective", "Objetivo", "text", None), ("github_repo", "Repositório GitHub", "entry", None), ("repo_link", "Link do repositório", "entry", None), ("tool", "Ferramenta", "entry", None), ("status", "Status", "combo", STATUSES), ("last_prompt", "Último prompt usado", "entry", None), ("last_interaction", "Data da última interação", "entry", None)]
        data = self.form("Projeto", fields, old)
        if data:
            t = now()
            if rid: self.storage.db.execute("UPDATE projects SET name=?, objective=?, github_repo=?, repo_link=?, tool=?, status=?, last_prompt=?, last_interaction=?, updated_at=? WHERE id=?", (*[data[x] for x, *_ in fields], t, rid))
            else: self.storage.db.execute("INSERT INTO projects(name,objective,github_repo,repo_link,tool,status,last_prompt,last_interaction,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?)", (*[data[x] for x, *_ in fields], t, t))
            self.storage.db.commit(); self.refresh_all()
            if rid: self.project_tree.selection_set(str(rid))

    def edit_prompt(self):
        rid = self.selected(self.prompt_tree); old = self.storage.db.execute("SELECT * FROM prompts WHERE id=?", (rid,)).fetchone() if rid else None
        project_values = ["(Sem projeto)"] + list(self.project_map.values()); fields = [("name", "Nome", "entry", None), ("category", "Categoria", "entry", None), ("project_name", "Projeto relacionado", "combo", project_values), ("tool", "Ferramenta", "combo", PROMPT_TOOLS), ("objective", "Objetivo", "entry", None), ("trigger", "Gatilho", "entry", None), ("when_to_use", "Quando usar", "text", None), ("content", "Prompt completo", "text", None), ("expected_result", "Resultado esperado", "text", None), ("notes", "Observações", "text", None), ("tags", "Tags", "entry", None)]
        vals = dict(old) if old else {}; vals["project_name"] = self.project_map.get(vals.get("project_id"), "(Sem projeto)")
        data = self.form("Prompt", fields, vals)
        if data:
            pid = next((k for k,v in self.project_map.items() if v == data["project_name"]), None); t=now(); args=[data[x] for x, *_ in fields if x != "project_name"]
            if rid: self.storage.db.execute("UPDATE prompts SET name=?,category=?,project_id=?,tool=?,objective=?,trigger=?,when_to_use=?,content=?,expected_result=?,notes=?,tags=?,updated_at=? WHERE id=?", (data["name"],data["category"],pid,data["tool"],data["objective"],data["trigger"],data["when_to_use"],data["content"],data["expected_result"],data["notes"],data["tags"],t,rid))
            else: self.storage.db.execute("INSERT INTO prompts(name,category,project_id,tool,objective,trigger,when_to_use,content,expected_result,notes,tags,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)", (data["name"],data["category"],pid,data["tool"],data["objective"],data["trigger"],data["when_to_use"],data["content"],data["expected_result"],data["notes"],data["tags"],t,t))
            self.storage.db.commit(); self.refresh_all()

    def edit_tip(self):
        rid=self.selected(self.tip_tree); old=self.storage.db.execute("SELECT * FROM tips WHERE id=?",(rid,)).fetchone() if rid else None; fields=[("title","Título","entry",None),("category","Categoria","combo",TIP_CATEGORIES),("when_to_use","Quando usar","text",None),("explanation","Explicação curta","text",None),("content","Prompt copiável","text",None)]; data=self.form("Dica de Prompt",fields,old)
        if data:
            t=now(); vals=[data[x] for x,*_ in fields]
            if rid:self.storage.db.execute("UPDATE tips SET title=?,category=?,when_to_use=?,explanation=?,content=?,updated_at=? WHERE id=?",(*vals,t,rid))
            else:self.storage.db.execute("INSERT INTO tips(title,category,when_to_use,explanation,content,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",(*vals,t,t))
            self.storage.db.commit();self.refresh_all()

    def edit_code(self):
        rid=self.selected(self.code_tree); old=self.storage.db.execute("SELECT * FROM codes WHERE id=?",(rid,)).fetchone() if rid else None; fields=[("name","Nome","entry",None),("language","Linguagem","entry",None),("project_name","Projeto relacionado","combo",["(Sem projeto)"]+list(self.project_map.values())),("purpose","Finalidade","text",None),("content","Código","text",None),("tags","Tags","entry",None),("notes","Observações","text",None)]; vals=dict(old) if old else {}; vals["project_name"]=self.project_map.get(vals.get("project_id"),"(Sem projeto)"); data=self.form("Código técnico",fields,vals)
        if data:
            pid=next((k for k,v in self.project_map.items() if v==data["project_name"]),None);t=now();args=(data["name"],data["language"],pid,data["purpose"],data["content"],data["tags"],data["notes"])
            if rid:self.storage.db.execute("UPDATE codes SET name=?,language=?,project_id=?,purpose=?,content=?,tags=?,notes=?,updated_at=? WHERE id=?",(*args,t,rid))
            else:self.storage.db.execute("INSERT INTO codes(name,language,project_id,purpose,content,tags,notes,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)",(*args,t,t))
            self.storage.db.commit();self.refresh_all()

    def export_backup(self):
        path=filedialog.asksaveasfilename(defaultextension=".json",filetypes=[("Backup JSON","*.json")]);
        if not path:return
        data={};
        for table in ("settings","projects","prompts","tips","codes"):data[table]=[dict(x) for x in self.storage.rows(table)]
        Path(path).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8"); messagebox.showinfo(APP_NAME,"Backup exportado com sucesso.")

    def import_backup(self):
        path=filedialog.askopenfilename(filetypes=[("Backup JSON","*.json")]);
        if not path:return
        try:
            data=json.loads(Path(path).read_text(encoding="utf-8"));
            if not messagebox.askyesno(APP_NAME,"Importar este backup adicionará registros aos dados atuais. Continuar?"):return
            for table in ("projects","prompts","tips","codes"):
                cols=[k for k in (data.get(table) or [{}])[0].keys() if k != "id"] if data.get(table) else []
                for row in data.get(table,[]):
                    if cols:self.storage.db.execute(f"INSERT INTO {table}({','.join(cols)}) VALUES({','.join('?' for _ in cols)})",[row.get(c) for c in cols])
            self.storage.db.commit();self.refresh_all();messagebox.showinfo(APP_NAME,"Backup importado.")
        except Exception as exc:messagebox.showerror(APP_NAME,f"Não foi possível importar: {exc}")

    def change_password(self):
        current=simpledialog.askstring(APP_NAME,"Senha atual:",show="•",parent=self); 
        if not current or not verify_password(current,self.storage.setting("password_hash","")):messagebox.showerror(APP_NAME,"Senha atual inválida.");return
        new=simpledialog.askstring(APP_NAME,"Nova senha (mínimo 6 caracteres):",show="•",parent=self)
        if new and len(new)>=6:self.storage.set_setting("password_hash",hash_password(new));messagebox.showinfo(APP_NAME,"Senha alterada.")


class App(tk.Tk):
    def __init__(self):
        super().__init__(); self.storage=Storage(); self.title(APP_NAME); self.geometry("1120x720"); self.minsize(900,600)
        style=ttk.Style(self); style.theme_use("clam"); style.configure("Title.TLabel",font=("Segoe UI",20,"bold"),foreground="#17324d"); style.configure("Subtitle.TLabel",font=("Segoe UI",10),foreground="#52606d"); style.configure("Section.TLabel",font=("Segoe UI",15,"bold"),foreground="#17324d")
        self.protocol("WM_DELETE_WINDOW",self.quit_app); self.show_login()
    def clear(self):
        for w in self.winfo_children():w.destroy()
    def show_login(self):self.clear(); LoginFrame(self,self.login).pack(fill="both",expand=True)
    def login(self,user):self.clear();MainApp(self,user,self.show_login).pack(fill="both",expand=True)
    def quit_app(self):self.storage.close();self.destroy()

if __name__ == "__main__":
    App().mainloop()
