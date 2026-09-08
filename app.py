import base64
import hashlib
import hmac
import json
import secrets
import shutil
import sys
import sqlite3
import tkinter as tk
from datetime import datetime, timedelta
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

APP_NAME = "Biblioteca de Prompts"
BRAND_TAGLINE = "Conhecimento organizado para criar melhor com IA"
PALETTE = {
    "bg": "#070317", "surface": "#100A26", "surface_raised": "#181039",
    "border": "#3A2866", "text": "#FFFFFF", "muted": "#CBD5E1",
    "pink": "#FF4FD8", "magenta": "#E535C7", "purple": "#9B4DFF",
    "violet": "#7C3AED", "cyan": "#00E5FF", "success": "#6EE7B7",
}
APP_DIR = Path.home() / ".central-de-prompts"
DB_PATH = APP_DIR / "central.db"
FILE_DIR = APP_DIR / "files"
STATUSES = ["Em testes", "Ativo", "Em construção", "Congelado"]
PROMPT_TOOLS = ["ChatGPT", "Manus", "Copilot", "Claude", "Gemini", "Outra"]
TIP_CATEGORIES = ["Analisar arquitetura", "Retomar projeto", "Continuar implementação", "Revisar código", "Refatorar com segurança", "Investigar erro", "Preparar publicação", "Melhorar testes", "Criar documentação", "Avaliar impacto de alteração"]
FILE_CATEGORIES = ["Templates", "Documentações", "Referências", "Arquivos Gerais"]
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".pptx", ".txt", ".zip", ".png", ".jpg", ".jpeg"}
ASSET_DIR = Path(__file__).resolve().parent / "assets"

def resource_path(name):
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / "assets" / name


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def hash_password(password, salt=None):
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return base64.b64encode(salt + digest).decode()


def verify_password(password, stored):
    try:
        raw = base64.b64decode(stored.encode())
        actual = hashlib.scrypt(password.encode(), salt=raw[:16], n=2**14, r=8, p=1)
        return hmac.compare_digest(actual, raw[16:])
    except Exception:
        return False


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


class Storage:
    def __init__(self, base_dir=None):
        self.base_dir = Path(base_dir) if base_dir else APP_DIR
        self.base_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.file_dir = self.base_dir / "files"
        self.file_dir.mkdir(mode=0o700, exist_ok=True)
        self.db_path = self.base_dir / "central.db"
        self._pre_migration_backup()
        self.db = sqlite3.connect(self.db_path)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("PRAGMA secure_delete=ON")
        self._schema()

    def _pre_migration_backup(self):
        if self.db_path.exists() and self.db_path.stat().st_size:
            backup = self.base_dir / "central.db.before-update"
            if not backup.exists():
                shutil.copy2(self.db_path, backup)

    def _schema(self):
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS projects (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, objective TEXT, github_repo TEXT, repo_link TEXT, tool TEXT, status TEXT NOT NULL, last_prompt TEXT, last_interaction TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS prompts (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, category TEXT, project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL, tool TEXT, objective TEXT, trigger TEXT, when_to_use TEXT, content TEXT NOT NULL, expected_result TEXT, notes TEXT, tags TEXT, favorite INTEGER DEFAULT 0, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS tips (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, category TEXT, when_to_use TEXT, explanation TEXT, content TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS codes (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, language TEXT, project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL, purpose TEXT, content TEXT NOT NULL, tags TEXT, notes TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS files (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, stored_name TEXT NOT NULL UNIQUE, extension TEXT NOT NULL, category TEXT NOT NULL, size INTEGER NOT NULL, sha256 TEXT NOT NULL, notes TEXT, created_at TEXT NOT NULL, accessed_at TEXT);
        CREATE TABLE IF NOT EXISTS password_reset_tokens (id INTEGER PRIMARY KEY AUTOINCREMENT, token_hash TEXT NOT NULL, expires_at TEXT NOT NULL, used_at TEXT, created_at TEXT NOT NULL);
        CREATE INDEX IF NOT EXISTS idx_prompts_search ON prompts(name, category, tool, tags);
        CREATE INDEX IF NOT EXISTS idx_files_search ON files(name, category, extension);
        """)
        self.db.commit()
        self.seed_defaults()

    def seed_defaults(self):
        existing = {row["title"] for row in self.db.execute("SELECT title FROM tips")}
        t = now()
        rows = [("Analisar arquitetura", "Analisar arquitetura", "Antes de alterar um projeto", "Entenda limites, dependências e riscos antes de editar.", "Analise a arquitetura atual deste projeto. Identifique componentes, fluxos, dependências, pontos frágeis e riscos. Não altere arquivos ainda; apresente um plano seguro."), ("Retomar projeto", "Retomar projeto", "Ao voltar após uma pausa", "Recupere rapidamente o contexto e o próximo passo.", "Retome este projeto a partir do estado atual. Resuma o que já existe, o que foi concluído, o que está pendente e indique o próximo passo mais seguro."), ("Investigar erro", "Investigar erro", "Quando surgir uma falha", "Organize a investigação antes de aplicar correções.", "Investigue este erro de forma sistemática. Explique a causa provável, evidências faltantes, reprodução e uma correção mínima com testes."), ("Continuidade de Projeto", "Governança de Projetos", "Ao retomar qualquer projeto", "Preserve contexto, decisões e próximos passos.", "Retome este projeto com segurança. Resuma o estado atual, decisões tomadas, riscos, pendências, arquivos relevantes e o próximo passo verificável. Seja aplicável a web, desktop, mobile, APIs e ferramentas internas."), ("Arquitetura Limpa", "Governança de Projetos", "Antes de uma alteração estrutural", "Mantenha responsabilidades claras e evolução simples.", "Revise a arquitetura deste projeto buscando responsabilidades bem definidas, baixo acoplamento, dependências justificadas e simplicidade. Proponha apenas mudanças necessárias e preserve compatibilidade."), ("Economia de Tokens", "Governança de Projetos", "Ao preparar contexto para IA", "Reduza contexto redundante sem perder informação essencial.", "Otimize este contexto para uma execução eficiente. Remova redundâncias, preserve requisitos, restrições, decisões e critérios de aceite, e organize o material por prioridade."), ("Limpeza de Repositório", "Governança de Projetos", "Antes de publicar ou entregar", "Remova resíduos sem apagar recursos usados.", "Faça uma limpeza controlada do repositório. Identifique temporários, logs, artefatos, imports, componentes e assets sem uso. Não remova recursos referenciados; mostre o plano antes de excluir."), ("README Inteligente", "Governança de Projetos", "Ao preparar documentação", "Explique o necessário para outra pessoa manter o projeto.", "Atualize o README com visão geral, funcionalidades, instalação, execução local, build, deploy, download e estrutura básica. Seja objetivo e não documente o que não existe."), ("QA Final", "Governança de Projetos", "Antes de concluir uma entrega", "Valide comportamento, acessibilidade e distribuição.", "Execute uma revisão final. Verifique fluxos principais, botões, formulários, uploads, downloads, links, assets, persistência, build, dependências e mensagens de erro. Registre evidências e pendências."), ("Deploy Seguro", "Governança de Projetos", "Antes de publicar", "Reduza riscos de uma publicação incompleta.", "Prepare um deploy seguro: valide testes, build de produção, variáveis, assets, links, rollback e artefatos. Não publique se houver falha crítica; informe exatamente o que bloqueia."), ("Independência de IA", "Governança de Projetos", "Ao revisar sustentabilidade", "Garanta que o projeto permaneça mantível sem a IA.", "Revise este projeto para confirmar que ele funciona sem a IA que auxiliou o desenvolvimento, sem servidor externo desnecessário e sem dependência oculta. Simplifique abstrações e documente decisões essenciais.")]
        rows = [row for row in rows if row[0] not in existing]
        if rows:
            self.db.executemany("INSERT INTO tips(title,category,when_to_use,explanation,content,created_at,updated_at) VALUES(?,?,?,?,?,?,?)", [r + (t, t) for r in rows])
            self.db.commit()

    def setting(self, key, default=None):
        row = self.db.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row["value"] if row else default

    def set_setting(self, key, value):
        self.db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)", (key, str(value))); self.db.commit()

    def rows(self, table, where="", params=()):
        if table not in {"projects", "prompts", "tips", "codes", "files"}:
            raise ValueError("Tabela não permitida")
        return self.db.execute(f"SELECT * FROM {table} {where}", params).fetchall()

    def counts(self):
        return {k: self.db.execute(f"SELECT COUNT(*) n FROM {k}").fetchone()["n"] for k in ("prompts", "projects", "files")}

    def close(self): self.db.close()

    def issue_reset_token(self, email):
        configured = self.setting("email", "")
        if not configured or not hmac.compare_digest(configured.lower(), email.strip().lower()):
            return None
        self.db.execute("UPDATE password_reset_tokens SET used_at=? WHERE used_at IS NULL AND expires_at < ?", (now(), now()))
        raw = secrets.token_urlsafe(32); digest = hashlib.sha256(raw.encode()).hexdigest(); expiry = (datetime.now() + timedelta(minutes=20)).strftime("%Y-%m-%d %H:%M:%S")
        self.db.execute("INSERT INTO password_reset_tokens(token_hash,expires_at,created_at) VALUES(?,?,?)", (digest, expiry, now())); self.db.commit(); return raw

    def reset_password(self, token, new_password):
        digest = hashlib.sha256(token.encode()).hexdigest(); row = self.db.execute("SELECT * FROM password_reset_tokens WHERE token_hash=? AND used_at IS NULL AND expires_at>=? ORDER BY id DESC LIMIT 1", (digest, now())).fetchone()
        if not row: return False
        self.set_setting("password_hash", hash_password(new_password)); self.db.execute("UPDATE password_reset_tokens SET used_at=? WHERE id=?", (now(), row["id"])); self.db.commit(); return True


class LoginFrame(ttk.Frame):
    def __init__(self, master, on_login):
        super().__init__(master, padding=(28, 22)); self.master = master; self.storage = master.storage; self.on_login = on_login; self.columnconfigure(0, weight=1); self.rowconfigure(0, weight=1)
        shell = ttk.Frame(self, style="LoginShell.TFrame", padding=(34, 30)); shell.grid(row=0, column=0, sticky="nsew", padx=14, pady=14); shell.columnconfigure(0, weight=1); shell.rowconfigure(0, weight=1)
        self.login_bg = None
        try:
            self.login_bg = tk.PhotoImage(file=str(resource_path("Fundo_Login_EricaQA_2912x2160.png")))
            bg = tk.Label(shell, image=self.login_bg, borderwidth=0, highlightthickness=0, bg=PALETTE["bg"]); bg.place(relx=0, rely=0, relwidth=1, relheight=1); bg.lower()
        except tk.TclError:
            pass
        overlay = tk.Frame(shell, bg="#070317", highlightthickness=0); overlay.place(relx=0, rely=0, relwidth=.48, relheight=1); overlay.lower()
        self.profile_image = None
        try:
            self.profile_image = tk.PhotoImage(file=str(resource_path("Foto_Perfil_EricaQA_800x800.png")))
            avatar = tk.Label(shell, image=self.profile_image, borderwidth=0, highlightthickness=0, bg=PALETTE["bg"]); avatar.grid(row=0, column=0, pady=(0, 8)); avatar.configure(width=112, height=112); avatar.pack_propagate(False)
        except tk.TclError:
            ttk.Label(shell, text="▰", style="BrandMark.TLabel").grid(row=0, column=0, pady=(0, 4))
        ttk.Label(shell, text="Biblioteca de Prompts", style="Title.TLabel").grid(row=1, column=0, pady=(0, 5))
        ttk.Label(shell, text=BRAND_TAGLINE, style="Subtitle.TLabel").grid(row=2, column=0, pady=(0, 24))
        box = ttk.LabelFrame(shell, text="  ACESSO PRIVADO  ", style="LoginBox.TLabelframe", padding=(22, 18)); box.grid(row=3, column=0, sticky="ew", padx=10); box.columnconfigure(0, weight=1)
        ttk.Label(box, text="Entre para acessar sua biblioteca local.", style="Muted.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 14))
        self.user = self.field(box, 1, "Usuário"); self.password = self.field(box, 3, "Senha", True)
        ttk.Button(box, text="Entrar  →", style="Primary.TButton", command=self.submit).grid(row=4, column=0, sticky="ew", pady=(18, 4)); self.password.bind("<Return>", lambda _: self.submit())
        ttk.Button(shell, text="Esqueci minha senha", style="Link.TButton", command=self.recover).grid(row=4, column=0, pady=(14, 4))
        if not self.storage.setting("username"): ttk.Label(shell, text="Primeiro acesso: crie um usuário e uma senha com pelo menos 6 caracteres.", style="Muted.TLabel").grid(row=5, column=0, pady=(8, 0))
        ttk.Label(shell, text="OFFLINE • SEUS DADOS FICAM NESTE DISPOSITIVO", style="Security.TLabel").grid(row=6, column=0, pady=(25, 0))

    def field(self, parent, row, label, secret=False):
        ttk.Label(parent, text=label, style="FieldLabel.TLabel").grid(row=row, column=0, sticky="w", pady=(0, 5)); entry = ttk.Entry(parent, show="•" if secret else "", style="Auth.TEntry"); entry.grid(row=row + 1, column=0, sticky="ew"); return entry

    def submit(self):
        user, password = self.user.get().strip(), self.password.get(); stored = self.storage.setting("username")
        if not user or len(password) < 6: messagebox.showwarning(APP_NAME, "Informe usuário e senha com pelo menos 6 caracteres."); return
        if not stored:
            self.storage.set_setting("username", user); self.storage.set_setting("password_hash", hash_password(password)); self.on_login(user)
        elif hmac.compare_digest(stored, user) and verify_password(password, self.storage.setting("password_hash", "")): self.on_login(user)
        else: messagebox.showerror(APP_NAME, "Usuário ou senha inválidos.")

    def recover(self):
        email = simpledialog.askstring(APP_NAME, "Informe o e-mail de recuperação configurado:", parent=self)
        if not email: return
        token = self.storage.issue_reset_token(email)
        if not token:
            messagebox.showerror(APP_NAME, "E-mail não reconhecido ou não configurado. Configure-o na aba Configurações após entrar."); return
        messagebox.showinfo(APP_NAME, "Modo offline: token temporário gerado. Anote este código e use-o para redefinir a senha:\n\n" + token)
        new = simpledialog.askstring(APP_NAME, "Cole o token temporário:", parent=self)
        password = simpledialog.askstring(APP_NAME, "Nova senha:", show="•", parent=self) if new else None
        if new and password and len(password) >= 6 and self.storage.reset_password(new, password): messagebox.showinfo(APP_NAME, "Senha redefinida. Faça login com a nova senha.")
        else: messagebox.showerror(APP_NAME, "Token inválido/expirado ou senha muito curta.")


class MainApp(ttk.Frame):
    def __init__(self, master, username, logout):
        super().__init__(master, padding=12); self.master = master; self.storage = master.storage; self.username = username; self.logout = logout; self.project_map = {}; self.search_var = tk.StringVar(); self.build(); self.bind_all("<Control-k>", lambda _: self.search.focus_set())

    def build(self):
        self.columnconfigure(0, weight=1); self.rowconfigure(2, weight=1)
        header = ttk.Frame(self); header.grid(row=0, column=0, sticky="ew", pady=(0, 8)); header.columnconfigure(2, weight=1)
        self.header_profile = None
        try:
            self.header_profile = tk.PhotoImage(file=str(resource_path("Foto_Perfil_EricaQA_800x800.png")))
            avatar = tk.Label(header, image=self.header_profile, borderwidth=0, highlightthickness=0, bg=PALETTE["surface"]); avatar.grid(row=0, column=0, sticky="w", padx=(0, 10)); avatar.configure(width=42, height=42)
        except tk.TclError:
            ttk.Label(header, text="▰", style="BrandMark.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 10))
        ttk.Label(header, text="Biblioteca de Prompts", style="Title.TLabel").grid(row=0, column=1, sticky="w"); ttk.Label(header, text=f"Olá, {self.username}", style="Subtitle.TLabel").grid(row=0, column=2, sticky="w", padx=16); ttk.Button(header, text="Sair", command=self.logout).grid(row=0, column=3)
        search = ttk.Frame(self); search.grid(row=1, column=0, sticky="ew", pady=(0, 8)); search.columnconfigure(1, weight=1); ttk.Label(search, text="Pesquisa global  (Ctrl+K)").grid(row=0, column=0, padx=(0, 8)); self.search = ttk.Entry(search, textvariable=self.search_var); self.search.grid(row=0, column=1, sticky="ew"); self.search.bind("<KeyRelease>", lambda _: self.refresh_all()); ttk.Button(search, text="Limpar", command=lambda: self.search_var.set("")).grid(row=0, column=2, padx=6)
        self.tabs = ttk.Notebook(self); self.tabs.grid(row=2, column=0, sticky="nsew"); self.dashboard_tab(); self.project_tab(); self.prompt_tab(); self.tip_tab(); self.code_tab(); self.repository_tab(); self.settings_tab(); self.refresh_all()

    def dashboard_tab(self):
        tab = ttk.Frame(self.tabs, padding=18); self.tabs.add(tab, text="Dashboard"); tab.columnconfigure((0, 1, 2, 3), weight=1); ttk.Label(tab, text="Visão geral", style="Section.TLabel").grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 14))
        self.metrics = {}
        for i, (key, label) in enumerate([("prompts", "Prompts"), ("favorites", "Favoritos"), ("categories", "Categorias"), ("files", "Arquivos")]):
            card = ttk.LabelFrame(tab, text=label, padding=16); card.grid(row=1, column=i, sticky="nsew", padx=4); self.metrics[key] = ttk.Label(card, text="0", style="Metric.TLabel"); self.metrics[key].pack()
        ttk.Label(tab, text="Atalhos rápidos", style="Section.TLabel").grid(row=2, column=0, columnspan=4, sticky="w", pady=(26, 8)); actions = ttk.Frame(tab); actions.grid(row=3, column=0, columnspan=4, sticky="w")
        for label, fn in [("Novo Prompt", self.new_prompt), ("Favoritos", lambda: self.show_favorites()), ("Repositório", lambda: self.tabs.select(self.repository)), ("Configurações", lambda: self.tabs.select(self.settings))]: ttk.Button(actions, text=label, command=fn).pack(side="left", padx=(0, 8))
        self.activity = ttk.Label(tab, text="", style="Muted.TLabel"); self.activity.grid(row=4, column=0, columnspan=4, sticky="w", pady=24)

    def tree(self, parent, cols, heads):
        frame = ttk.Frame(parent); frame.columnconfigure(0, weight=1); frame.rowconfigure(0, weight=1); tree = ttk.Treeview(frame, columns=cols, show="headings");
        for c, h in zip(cols, heads): tree.heading(c, text=h); tree.column(c, width=150, anchor="w")
        tree.grid(row=0, column=0, sticky="nsew"); scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview); scrollbar.grid(row=0, column=1, sticky="ns"); tree.configure(yscrollcommand=scrollbar.set); return frame, tree

    def toolbar(self, parent, title, new, edit, delete, extras=()):
        bar = ttk.Frame(parent); bar.pack(fill="x", pady=(0, 8)); ttk.Label(bar, text=title, style="Section.TLabel").pack(side="left");
        for label, fn in extras: ttk.Button(bar, text=label, command=fn).pack(side="right", padx=(5, 0))
        ttk.Button(bar, text="Excluir", command=delete).pack(side="right", padx=(5, 0)); ttk.Button(bar, text="Editar", command=edit).pack(side="right", padx=(5, 0)); ttk.Button(bar, text="＋ Novo", command=new).pack(side="right")

    def project_tab(self):
        self.projects = ttk.Frame(self.tabs, padding=12); self.tabs.add(self.projects, text="Projetos"); self.toolbar(self.projects, "Projetos", self.new_project, self.edit_project, lambda: self.delete(self.project_tree, "projects")); frame, self.project_tree = self.tree(self.projects, ("name", "status", "tool", "github"), ("Projeto", "Status", "Ferramenta", "Repositório")); frame.pack(fill="both", expand=True); self.project_tree.bind("<Double-1>", lambda _: self.edit_project())

    def prompt_tab(self):
        self.prompts = ttk.Frame(self.tabs, padding=12); self.tabs.add(self.prompts, text="Prompts"); self.toolbar(self.prompts, "Biblioteca de Prompts", self.new_prompt, self.edit_prompt, lambda: self.delete(self.prompt_tree, "prompts"), [("Copiar", self.copy_prompt), ("★ Favoritar", self.favorite)]); frame, self.prompt_tree = self.tree(self.prompts, ("fav", "name", "category", "project", "tool", "tags"), ("★", "Nome", "Categoria", "Projeto", "Ferramenta", "Tags")); frame.pack(fill="both", expand=True); self.prompt_tree.bind("<Double-1>", lambda _: self.edit_prompt())

    def tip_tab(self):
        self.tips = ttk.Frame(self.tabs, padding=12); self.tabs.add(self.tips, text="Governança"); self.toolbar(self.tips, "Governança de Projetos", self.new_tip, self.edit_tip, lambda: self.delete(self.tip_tree, "tips"), [("Copiar", self.copy_tip)]); frame, self.tip_tree = self.tree(self.tips, ("title", "category", "when"), ("Título", "Categoria", "Quando usar")); frame.pack(fill="both", expand=True)

    def code_tab(self):
        self.codes = ttk.Frame(self.tabs, padding=12); self.tabs.add(self.codes, text="Códigos"); self.toolbar(self.codes, "Biblioteca de Códigos", self.new_code, self.edit_code, lambda: self.delete(self.code_tree, "codes"), [("Copiar", self.copy_code)]); frame, self.code_tree = self.tree(self.codes, ("name", "language", "project", "tags"), ("Nome", "Linguagem", "Projeto", "Tags")); frame.pack(fill="both", expand=True)

    def repository_tab(self):
        self.repository = ttk.Frame(self.tabs, padding=12); self.tabs.add(self.repository, text="📁 Repositório"); self.toolbar(self.repository, "Arquivos relacionados", self.upload_file, self.file_info, lambda: self.delete_file(), [("Baixar", self.download_file)]); frame, self.file_tree = self.tree(self.repository, ("name", "category", "extension", "size", "created"), ("Arquivo", "Categoria", "Tipo", "Tamanho", "Adicionado")); frame.pack(fill="both", expand=True)

    def settings_tab(self):
        self.settings = ttk.Frame(self.tabs, padding=18); self.tabs.add(self.settings, text="Configurações"); ttk.Label(self.settings, text="Configurações e proteção", style="Section.TLabel").pack(anchor="w"); ttk.Label(self.settings, text="Dados locais, sem envio automático para serviços externos.", style="Muted.TLabel").pack(anchor="w", pady=(4, 16));
        for text, fn in [("Exportar backup seguro", self.export_backup), ("Importar backup seguro", self.import_backup), ("Alterar senha", self.change_password), ("Configurar e-mail de recuperação", self.configure_email), ("Abrir pasta de dados", lambda: messagebox.showinfo(APP_NAME, str(self.storage.base_dir))), ("Sobre a aplicação", self.about)]: ttk.Button(self.settings, text=text, command=fn).pack(anchor="w", pady=4)
        ttk.Separator(self.settings).pack(fill="x", pady=18); ttk.Label(self.settings, text="Recuperação por e-mail requer um serviço externo; no modo offline, um token temporário é exibido localmente e expira em 20 minutos.", wraplength=700, style="Muted.TLabel").pack(anchor="w")

    def query(self, table, order="updated_at DESC", extra="", params=()):
        q = self.search_var.get().strip().lower(); values = list(params); where = extra
        if q:
            fields = {"projects": "name || ' ' || objective || ' ' || github_repo || ' ' || tool || ' ' || status", "prompts": "name || ' ' || category || ' ' || objective || ' ' || trigger || ' ' || content || ' ' || tags", "tips": "title || ' ' || category || ' ' || when_to_use || ' ' || explanation || ' ' || content", "codes": "name || ' ' || language || ' ' || purpose || ' ' || content || ' ' || tags", "files": "name || ' ' || category || ' ' || extension || ' ' || notes"}[table]
            where = (where + " AND " if where else "WHERE ") + f"LOWER({fields}) LIKE ?"; values.append(f"%{q}%")
        return self.storage.rows(table, where + (" ORDER BY " + order if order else ""), values)

    def refresh_all(self):
        self.project_map = {r["id"]: r["name"] for r in self.storage.rows("projects", "ORDER BY name")}
        for tree in (self.project_tree, self.prompt_tree, self.tip_tree, self.code_tree, self.file_tree): tree.delete(*tree.get_children())
        for r in self.query("projects"): self.project_tree.insert("", "end", iid=str(r["id"]), values=(r["name"], r["status"], r["tool"] or "", r["github_repo"] or ""))
        for r in self.query("prompts", "favorite DESC, updated_at DESC"): self.prompt_tree.insert("", "end", iid=str(r["id"]), values=("★" if r["favorite"] else "", r["name"], r["category"] or "", self.project_map.get(r["project_id"], ""), r["tool"] or "", r["tags"] or ""))
        for r in self.query("tips"): self.tip_tree.insert("", "end", iid=str(r["id"]), values=(r["title"], r["category"] or "", r["when_to_use"] or ""))
        for r in self.query("codes"): self.code_tree.insert("", "end", iid=str(r["id"]), values=(r["name"], r["language"] or "", self.project_map.get(r["project_id"], ""), r["tags"] or ""))
        for r in self.query("files", "created_at DESC"): self.file_tree.insert("", "end", iid=str(r["id"]), values=(r["name"], r["category"], r["extension"], self.human_size(r["size"]), r["created_at"]))
        c = self.storage.counts(); self.metrics["prompts"].configure(text=str(c["prompts"])); self.metrics["files"].configure(text=str(c["files"])); self.metrics["favorites"].configure(text=str(self.storage.db.execute("SELECT COUNT(*) n FROM prompts WHERE favorite=1").fetchone()["n"])); self.metrics["categories"].configure(text=str(self.storage.db.execute("SELECT COUNT(DISTINCT category) n FROM prompts WHERE category IS NOT NULL AND category!=''").fetchone()["n"])); self.activity.configure(text=f"Última atualização: {now()}  •  {c['prompts']} prompts, {c['files']} arquivos")

    @staticmethod
    def human_size(size):
        for unit in ("B", "KB", "MB", "GB"):
            if size < 1024: return f"{size:.0f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def selected(self, tree): return int(tree.selection()[0]) if tree.selection() else None
    def delete(self, tree, table):
        rid = self.selected(tree)
        if rid and messagebox.askyesno(APP_NAME, "Excluir o item selecionado? Esta ação não pode ser desfeita."): self.storage.db.execute(f"DELETE FROM {table} WHERE id=?", (rid,)); self.storage.db.commit(); self.refresh_all()
    def favorite(self):
        rid = self.selected(self.prompt_tree)
        if rid: self.storage.db.execute("UPDATE prompts SET favorite=1-favorite,updated_at=? WHERE id=?", (now(), rid)); self.storage.db.commit(); self.refresh_all()
    def copy_row(self, tree, table, field):
        rid = self.selected(tree)
        if rid:
            row = self.storage.db.execute(f"SELECT {field} FROM {table} WHERE id=?", (rid,)).fetchone(); self.master.clipboard_clear(); self.master.clipboard_append(row[field]); messagebox.showinfo(APP_NAME, "Conteúdo copiado.")
    def copy_prompt(self): self.copy_row(self.prompt_tree, "prompts", "content")
    def copy_tip(self): self.copy_row(self.tip_tree, "tips", "content")
    def copy_code(self): self.copy_row(self.code_tree, "codes", "content")
    def show_favorites(self): self.tabs.select(self.prompts); self.search_var.set(""); self.refresh_all(); self.prompt_tree.focus_set()

    def form(self, title, fields, values=None):
        if values is not None and not isinstance(values, dict): values = dict(values)
        win = tk.Toplevel(self); win.title(title); win.transient(self); win.grab_set(); win.minsize(560, 420); win.geometry("720x620")
        outer = ttk.Frame(win); outer.pack(fill="both", expand=True); canvas = tk.Canvas(outer, highlightthickness=0); scroll = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview); inner = ttk.Frame(canvas, padding=18); inner.columnconfigure(1, weight=1); canvas.create_window((0, 0), window=inner, anchor="nw"); canvas.configure(yscrollcommand=scroll.set); canvas.pack(side="left", fill="both", expand=True); scroll.pack(side="right", fill="y"); inner.bind("<Configure>", lambda _: canvas.configure(scrollregion=canvas.bbox("all")))
        widgets = {}
        for i, (key, label, kind, options) in enumerate(fields):
            ttk.Label(inner, text=label).grid(row=i, column=0, sticky="nw", padx=(0, 14), pady=6)
            w = ttk.Combobox(inner, values=options, state="readonly") if kind == "combo" else tk.Text(inner, height=5, wrap="word") if kind == "text" else ttk.Entry(inner)
            w.grid(row=i, column=1, sticky="ew", pady=6); widgets[key] = w
            if values and values.get(key) is not None:
                val = str(values[key]); w.insert("1.0", val) if kind == "text" else w.set(val) if kind == "combo" else w.insert(0, val)
        result = {}
        def save():
            for key, w in widgets.items(): result[key] = w.get("1.0", "end-1c") if isinstance(w, tk.Text) else w.get()
            if not result.get(fields[0][0], "").strip(): messagebox.showwarning(APP_NAME, "Preencha o campo principal.", parent=win); return
            win.destroy()
        ttk.Button(inner, text="Salvar", command=save).grid(row=len(fields), column=1, sticky="e", pady=14); win.bind("<Escape>", lambda _: win.destroy()); self.wait_window(win); return result or None

    def project_fields(self): return [("name", "Nome", "entry", None), ("objective", "Objetivo", "text", None), ("github_repo", "Repositório GitHub", "entry", None), ("repo_link", "Link", "entry", None), ("tool", "Ferramenta", "entry", None), ("status", "Status", "combo", STATUSES), ("last_prompt", "Último prompt", "entry", None), ("last_interaction", "Última interação", "entry", None)]
    def edit_project(self):
        rid = self.selected(self.project_tree); old = self.storage.db.execute("SELECT * FROM projects WHERE id=?", (rid,)).fetchone() if rid else None; data = self.form("Projeto", self.project_fields(), old)
        if data:
            t=now(); vals=[data[k] for k,*_ in self.project_fields()]
            if rid: self.storage.db.execute("UPDATE projects SET name=?,objective=?,github_repo=?,repo_link=?,tool=?,status=?,last_prompt=?,last_interaction=?,updated_at=? WHERE id=?", (*vals,t,rid))
            else: self.storage.db.execute("INSERT INTO projects(name,objective,github_repo,repo_link,tool,status,last_prompt,last_interaction,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?)", (*vals,t,t))
            self.storage.db.commit(); self.refresh_all()
    def new_project(self): self.project_tree.selection_remove(self.project_tree.selection()); self.edit_project()
    def edit_prompt(self):
        rid=self.selected(self.prompt_tree); old=self.storage.db.execute("SELECT * FROM prompts WHERE id=?",(rid,)).fetchone() if rid else None; fields=[("name","Nome","entry",None),("category","Categoria","entry",None),("project_name","Projeto","combo",["(Sem projeto)"]+list(self.project_map.values())),("tool","Ferramenta","combo",PROMPT_TOOLS),("objective","Objetivo","entry",None),("trigger","Gatilho","entry",None),("when_to_use","Quando usar","text",None),("content","Prompt completo","text",None),("expected_result","Resultado esperado","text",None),("notes","Observações","text",None),("tags","Tags","entry",None)]; vals=dict(old) if old else {}; vals["project_name"]=self.project_map.get(vals.get("project_id"),"(Sem projeto)"); data=self.form("Prompt",fields,vals)
        if data:
            pid=next((k for k,v in self.project_map.items() if v==data["project_name"]),None); t=now(); args=(data["name"],data["category"],pid,data["tool"],data["objective"],data["trigger"],data["when_to_use"],data["content"],data["expected_result"],data["notes"],data["tags"])
            if rid:self.storage.db.execute("UPDATE prompts SET name=?,category=?,project_id=?,tool=?,objective=?,trigger=?,when_to_use=?,content=?,expected_result=?,notes=?,tags=?,updated_at=? WHERE id=?",(*args,t,rid))
            else:self.storage.db.execute("INSERT INTO prompts(name,category,project_id,tool,objective,trigger,when_to_use,content,expected_result,notes,tags,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",(*args,t,t))
            self.storage.db.commit();self.refresh_all()
    def new_prompt(self): self.prompt_tree.selection_remove(self.prompt_tree.selection()); self.edit_prompt()
    def edit_tip(self):
        rid=self.selected(self.tip_tree); old=self.storage.db.execute("SELECT * FROM tips WHERE id=?",(rid,)).fetchone() if rid else None; fields=[("title","Título","entry",None),("category","Categoria","combo",TIP_CATEGORIES),("when_to_use","Quando usar","text",None),("explanation","Explicação","text",None),("content","Prompt copiável","text",None)]; data=self.form("Dica",fields,old)
        if data:
            t=now(); vals=[data[k] for k,*_ in fields]
            if rid:self.storage.db.execute("UPDATE tips SET title=?,category=?,when_to_use=?,explanation=?,content=?,updated_at=? WHERE id=?",(*vals,t,rid))
            else:self.storage.db.execute("INSERT INTO tips(title,category,when_to_use,explanation,content,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",(*vals,t,t))
            self.storage.db.commit();self.refresh_all()
    def new_tip(self): self.tip_tree.selection_remove(self.tip_tree.selection()); self.edit_tip()
    def edit_code(self):
        rid=self.selected(self.code_tree); old=self.storage.db.execute("SELECT * FROM codes WHERE id=?",(rid,)).fetchone() if rid else None; fields=[("name","Nome","entry",None),("language","Linguagem","entry",None),("project_name","Projeto","combo",["(Sem projeto)"]+list(self.project_map.values())),("purpose","Finalidade","text",None),("content","Código","text",None),("tags","Tags","entry",None),("notes","Observações","text",None)]; vals=dict(old) if old else {}; vals["project_name"]=self.project_map.get(vals.get("project_id"),"(Sem projeto)"); data=self.form("Código",fields,vals)
        if data:
            pid=next((k for k,v in self.project_map.items() if v==data["project_name"]),None); t=now(); args=(data["name"],data["language"],pid,data["purpose"],data["content"],data["tags"],data["notes"])
            if rid:self.storage.db.execute("UPDATE codes SET name=?,language=?,project_id=?,purpose=?,content=?,tags=?,notes=?,updated_at=? WHERE id=?",(*args,t,rid))
            else:self.storage.db.execute("INSERT INTO codes(name,language,project_id,purpose,content,tags,notes,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)",(*args,t,t))
            self.storage.db.commit();self.refresh_all()
    def new_code(self): self.code_tree.selection_remove(self.code_tree.selection()); self.edit_code()

    def upload_file(self):
        source=filedialog.askopenfilename(filetypes=[("Arquivos aceitos", "*.pdf *.docx *.xlsx *.pptx *.txt *.zip *.png *.jpg *.jpeg")]);
        if not source: return
        src=Path(source); ext=src.suffix.lower()
        if ext not in ALLOWED_EXTENSIONS: messagebox.showerror(APP_NAME,"Tipo de arquivo não permitido."); return
        category=simpledialog.askstring(APP_NAME,"Categoria (Templates, Documentações, Referências ou Arquivos Gerais):",initialvalue="Arquivos Gerais") or "Arquivos Gerais"
        if category not in FILE_CATEGORIES: category="Arquivos Gerais"
        stored=f"{secrets.token_hex(12)}{ext}"; target=self.storage.file_dir/stored; shutil.copy2(src,target); self.storage.db.execute("INSERT INTO files(name,stored_name,extension,category,size,sha256,created_at) VALUES(?,?,?,?,?,?,?)",(src.name,stored,ext,category,target.stat().st_size,sha256_file(target),now())); self.storage.db.commit(); self.refresh_all()
    def file_info(self):
        rid=self.selected(self.file_tree)
        if rid:
            r=self.storage.db.execute("SELECT * FROM files WHERE id=?",(rid,)).fetchone(); messagebox.showinfo(APP_NAME,f"{r['name']}\nTipo: {r['extension']}\nCategoria: {r['category']}\nTamanho: {self.human_size(r['size'])}\nSHA-256: {r['sha256']}")
    def download_file(self):
        rid=self.selected(self.file_tree)
        if not rid:return
        r=self.storage.db.execute("SELECT * FROM files WHERE id=?",(rid,)).fetchone(); path=filedialog.asksaveasfilename(initialfile=r["name"]);
        if path: shutil.copy2(self.storage.file_dir/r["stored_name"],path); self.storage.db.execute("UPDATE files SET accessed_at=? WHERE id=?",(now(),rid)); self.storage.db.commit()
    def delete_file(self):
        rid=self.selected(self.file_tree)
        if not rid or not messagebox.askyesno(APP_NAME,"Excluir arquivo e registro? Esta ação não pode ser desfeita."):return
        r=self.storage.db.execute("SELECT stored_name FROM files WHERE id=?",(rid,)).fetchone(); (self.storage.file_dir/r["stored_name"]).unlink(missing_ok=True); self.storage.db.execute("DELETE FROM files WHERE id=?",(rid,)); self.storage.db.commit(); self.refresh_all()

    def configure_email(self):
        email=simpledialog.askstring(APP_NAME,"E-mail usado para recuperação local:",initialvalue=self.storage.setting("email", ""),parent=self)
        if email is not None:self.storage.set_setting("email",email.strip()); messagebox.showinfo(APP_NAME,"E-mail salvo localmente. Nenhuma mensagem é enviada sem configurar um provedor externo.")
    def change_password(self):
        current=simpledialog.askstring(APP_NAME,"Senha atual:",show="•",parent=self); new=simpledialog.askstring(APP_NAME,"Nova senha:",show="•",parent=self) if current and verify_password(current,self.storage.setting("password_hash","")) else None
        if new and len(new)>=6:self.storage.set_setting("password_hash",hash_password(new)); messagebox.showinfo(APP_NAME,"Senha alterada.")
        elif current: messagebox.showerror(APP_NAME,"Senha atual inválida ou nova senha muito curta.")
    def export_backup(self):
        path=filedialog.asksaveasfilename(defaultextension=".json",filetypes=[("Backup JSON","*.json")]);
        if not path:return
        payload={"version":2,"exported_at":now(),"settings":[dict(r) for r in self.storage.db.execute("SELECT * FROM settings")],"projects":[dict(r) for r in self.storage.rows("projects")],"prompts":[dict(r) for r in self.storage.rows("prompts")],"tips":[dict(r) for r in self.storage.rows("tips")],"codes":[dict(r) for r in self.storage.rows("codes")],"files":[dict(r) for r in self.storage.rows("files")]}; Path(path).write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8"); messagebox.showinfo(APP_NAME,"Backup exportado.")
    def import_backup(self):
        path=filedialog.askopenfilename(filetypes=[("Backup JSON","*.json")]);
        if not path:return
        try:
            payload=json.loads(Path(path).read_text(encoding="utf-8")); required={"projects","prompts","tips","codes"};
            if not required.issubset(payload):raise ValueError("Formato de backup incompatível")
            if not messagebox.askyesno(APP_NAME,"Os registros serão adicionados em uma transação segura. Continuar?"):return
            self.storage.db.execute("BEGIN")
            project_ids={}
            for row in payload.get("projects",[]):
                cur=self.storage.db.execute("INSERT INTO projects(name,objective,github_repo,repo_link,tool,status,last_prompt,last_interaction,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?)",tuple(row.get(k) or "" for k in ("name","objective","github_repo","repo_link","tool","status","last_prompt","last_interaction","created_at","updated_at"))); project_ids[row.get("id")]=cur.lastrowid
            for row in payload.get("prompts",[]):
                self.storage.db.execute("INSERT INTO prompts(name,category,project_id,tool,objective,trigger,when_to_use,content,expected_result,notes,tags,favorite,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(row.get("name",""),row.get("category",""),project_ids.get(row.get("project_id")),row.get("tool",""),row.get("objective",""),row.get("trigger",""),row.get("when_to_use",""),row.get("content",""),row.get("expected_result",""),row.get("notes",""),row.get("tags",""),int(row.get("favorite",0)),row.get("created_at",now()),row.get("updated_at",now())))
            for table, cols in (("tips",("title","category","when_to_use","explanation","content","created_at","updated_at")), ("codes",("name","language","project_id","purpose","content","tags","notes","created_at","updated_at"))):
                for row in payload.get(table,[]):
                    vals=[project_ids.get(row.get("project_id")) if c=="project_id" else row.get(c,"") for c in cols]; self.storage.db.execute(f"INSERT INTO {table}({','.join(cols)}) VALUES({','.join('?' for _ in cols)})",vals)
            self.storage.db.commit(); self.refresh_all(); messagebox.showinfo(APP_NAME,"Backup importado sem alterar os dados anteriores.")
        except Exception as exc:
            self.storage.db.rollback(); messagebox.showerror(APP_NAME,f"Importação cancelada e revertida: {exc}")
    def about(self): messagebox.showinfo(APP_NAME,"Biblioteca de Prompts\n\nAplicação local para preservar contexto, prompts, projetos e materiais técnicos. Dados mantidos no dispositivo, sem IA embutida nem dependência de internet em tempo de execução.")


class App(tk.Tk):
    def __init__(self):
        super().__init__(); self.storage=Storage(); self.title(APP_NAME); self.geometry("1200x780"); self.minsize(760,520); self.configure(bg=PALETTE["bg"]); style=ttk.Style(self); style.theme_use("clam")
        style.configure(".", background=PALETTE["surface"], foreground=PALETTE["text"], font=("Segoe UI", 10)); style.configure("TFrame", background=PALETTE["surface"]); style.configure("LoginShell.TFrame", background=PALETTE["bg"]); style.configure("TLabel", background=PALETTE["surface"], foreground=PALETTE["text"]); style.configure("TButton", padding=(12, 8), foreground=PALETTE["text"], background=PALETTE["surface_raised"], bordercolor=PALETTE["border"]); style.map("TButton", background=[("active", PALETTE["violet"]), ("pressed", PALETTE["purple"])], foreground=[("disabled", "#64748B")]); style.configure("Primary.TButton", background=PALETTE["magenta"], foreground=PALETTE["text"], font=("Segoe UI", 11, "bold")); style.map("Primary.TButton", background=[("active", PALETTE["pink"]), ("pressed", PALETTE["violet"])])
        style.configure("Title.TLabel", font=("Segoe UI",20,"bold"), foreground=PALETTE["pink"]); style.configure("BrandMark.TLabel", font=("Segoe UI Symbol", 44), foreground=PALETTE["cyan"], background=PALETTE["bg"]); style.configure("Section.TLabel", font=("Segoe UI",15,"bold"), foreground=PALETTE["cyan"]); style.configure("Subtitle.TLabel", foreground=PALETTE["muted"]); style.configure("Muted.TLabel", foreground=PALETTE["muted"], wraplength=760); style.configure("Security.TLabel", font=("Segoe UI", 8, "bold"), foreground=PALETTE["cyan"], background=PALETTE["bg"]); style.configure("FieldLabel.TLabel", foreground=PALETTE["text"], font=("Segoe UI", 10, "bold")); style.configure("Metric.TLabel", font=("Segoe UI",24,"bold"), foreground=PALETTE["pink"]); style.configure("Link.TButton", foreground=PALETTE["cyan"], background=PALETTE["bg"], borderwidth=0); style.configure("LoginBox.TLabelframe", background=PALETTE["surface"], foreground=PALETTE["cyan"], bordercolor=PALETTE["border"]); style.configure("LoginBox.TLabelframe.Label", background=PALETTE["surface"], foreground=PALETTE["cyan"], font=("Segoe UI", 9, "bold")); style.configure("Auth.TEntry", fieldbackground=PALETTE["surface_raised"], foreground=PALETTE["text"], insertcolor=PALETTE["text"], bordercolor=PALETTE["border"], lightcolor=PALETTE["cyan"], darkcolor=PALETTE["border"], padding=9); style.map("Auth.TEntry", fieldbackground=[("focus", "#24164D")], bordercolor=[("focus", PALETTE["cyan"])])
        style.configure("TNotebook", background=PALETTE["bg"], borderwidth=0); style.configure("TNotebook.Tab", background=PALETTE["surface_raised"], foreground=PALETTE["muted"], padding=(12, 7)); style.map("TNotebook.Tab", background=[("selected", PALETTE["violet"])], foreground=[("selected", PALETTE["text"])])
        style.configure("Treeview", background=PALETTE["surface"], fieldbackground=PALETTE["surface"], foreground=PALETTE["text"], rowheight=30); style.configure("Treeview.Heading", background=PALETTE["surface_raised"], foreground=PALETTE["cyan"], font=("Segoe UI", 9, "bold")); style.map("Treeview", background=[("selected", PALETTE["violet"])], foreground=[("selected", PALETTE["text"])])
        self.protocol("WM_DELETE_WINDOW",self.quit_app); self.show_login()
    def clear(self):
        for w in self.winfo_children(): w.destroy()
    def show_login(self): self.clear(); LoginFrame(self,self.login).pack(fill="both",expand=True)
    def login(self,user): self.clear(); MainApp(self,user,self.show_login).pack(fill="both",expand=True)
    def quit_app(self): self.storage.close(); self.destroy()

if __name__ == "__main__": App().mainloop()
