import base64
import hashlib
import hmac
import json
import os
import platform
import secrets
import shutil
import sys
import sqlite3
import tkinter as tk
from datetime import datetime, timedelta
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

APP_NAME = "Biblioteca de Prompts"
APP_VERSION = "1.0.0"
BUILD_DATE = "2026-09-12"
BRAND_TAGLINE = "Conhecimento organizado para criar melhor com IA"
PALETTE = {
    "bg": "#0B0A16", "surface": "#141322", "surface_raised": "#1D1A31",
    "border": "#332D4F", "border_soft": "#25213B", "text": "#F8F7FF", "muted": "#A9A5BF",
    "pink": "#F08BCE", "magenta": "#D96BB8", "purple": "#A78BFA",
    "violet": "#7C5CFC", "cyan": "#8ED8E5", "input": "#211D35",
    "focus": "#A78BFA", "selection": "#51419B", "success": "#55C58A",
    "danger": "#E97883", "warning": "#F0B86E",
}
def application_dir():
    return Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent


def default_data_dir():
    app_dir = application_dir()
    portable = os.environ.get("BIBLIOTECA_PORTABLE", "").strip().lower() in {"1", "true", "sim", "yes"} or (app_dir / "portable.flag").exists()
    if portable:
        return app_dir / "data"
    legacy = Path.home() / ".central-de-prompts"
    if os.name == "nt":
        appdata = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA")
        if appdata:
            target = Path(appdata) / "BibliotecaDePrompts"
            return legacy if (legacy / "central.db").exists() and not (target / "central.db").exists() else target
    return legacy


APP_DIR = default_data_dir()
STATUSES = ["Em testes", "Ativo", "Em construção", "Congelado"]
CONTENT_STATUSES = ["Rascunho", "Em Revisão", "Aprovado", "Arquivado"]
TEMPLATE_CATEGORIES = ["QA", "Casos de Teste", "BDD", "Requisitos", "User Stories", "Defeitos", "Automação", "Documentação", "Engenharia de Prompt"]
COLLECTION_CATALOGS = ["QA", "Automação", "BDD", "Documentação", "Manus", "GitHub", "Estudos", "Geral"]
ENTITY_LABELS = {"projects": "Projeto", "prompts": "Prompt", "tips": "Governança", "codes": "Código", "files": "Arquivo", "knowledge": "Conhecimento"}
ENTITY_NAME_FIELDS = {"projects": "name", "prompts": "name", "tips": "title", "codes": "name", "files": "name", "knowledge": "title"}
CONTENT_TABLES = tuple(ENTITY_LABELS)
PROMPT_TOOLS = ["ChatGPT", "Manus", "Copilot", "Claude", "Gemini", "Outra"]
TIP_CATEGORIES = ["Analisar arquitetura", "Retomar projeto", "Continuar implementação", "Revisar código", "Refatorar com segurança", "Investigar erro", "Preparar publicação", "Melhorar testes", "Criar documentação", "Avaliar impacto de alteração"]
FILE_CATEGORIES = ["Templates", "Documentações", "Referências", "Arquivos Gerais"]
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".pptx", ".txt", ".zip", ".png", ".jpg", ".jpeg"}


def normalize_tags(value):
    seen = set()
    result = []
    for tag in str(value or "").replace(";", ",").split(","):
        clean = " ".join(tag.strip().split())
        key = clean.casefold()
        if clean and key not in seen:
            seen.add(key); result.append(clean)
    return ", ".join(result)


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
        (self.base_dir / "trash-files").mkdir(mode=0o700, exist_ok=True)
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
        CREATE TABLE IF NOT EXISTS trash (id INTEGER PRIMARY KEY AUTOINCREMENT, entity_type TEXT NOT NULL, original_id INTEGER NOT NULL, payload TEXT NOT NULL, deleted_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS prompt_versions (id INTEGER PRIMARY KEY AUTOINCREMENT, prompt_id INTEGER NOT NULL, version INTEGER NOT NULL, snapshot TEXT NOT NULL, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS categories (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, parent_id INTEGER REFERENCES categories(id) ON DELETE SET NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS favorite_folders (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS knowledge (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, content TEXT NOT NULL, category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL, tags TEXT, favorite INTEGER DEFAULT 0, is_template INTEGER DEFAULT 0, favorite_folder_id INTEGER REFERENCES favorite_folders(id) ON DELETE SET NULL, pinned INTEGER DEFAULT 0, status TEXT DEFAULT 'Rascunho', created_at TEXT NOT NULL, updated_at TEXT NOT NULL, last_viewed_at TEXT, edit_count INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS relationships (id INTEGER PRIMARY KEY AUTOINCREMENT, source_type TEXT NOT NULL, source_id INTEGER NOT NULL, target_type TEXT NOT NULL, target_id INTEGER NOT NULL, relation_type TEXT DEFAULT 'Relacionado', created_at TEXT NOT NULL, UNIQUE(source_type,source_id,target_type,target_id));
        CREATE TABLE IF NOT EXISTS activity_log (id INTEGER PRIMARY KEY AUTOINCREMENT, action TEXT NOT NULL, entity_type TEXT, entity_id INTEGER, details TEXT, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS collections (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, catalog TEXT DEFAULT 'Geral', description TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS collection_items (id INTEGER PRIMARY KEY AUTOINCREMENT, collection_id INTEGER NOT NULL REFERENCES collections(id) ON DELETE CASCADE, entity_type TEXT NOT NULL, entity_id INTEGER NOT NULL, created_at TEXT NOT NULL, UNIQUE(collection_id,entity_type,entity_id));
        CREATE TABLE IF NOT EXISTS search_history (id INTEGER PRIMARY KEY AUTOINCREMENT, query TEXT, filters TEXT, searched_at TEXT NOT NULL);
        CREATE INDEX IF NOT EXISTS idx_prompts_search ON prompts(name, category, tool, tags);
        CREATE INDEX IF NOT EXISTS idx_files_search ON files(name, category, extension);
        CREATE INDEX IF NOT EXISTS idx_trash_type ON trash(entity_type, deleted_at);
        CREATE INDEX IF NOT EXISTS idx_prompt_versions_prompt ON prompt_versions(prompt_id, version);
        CREATE INDEX IF NOT EXISTS idx_categories_parent ON categories(parent_id,name);
        CREATE INDEX IF NOT EXISTS idx_relationships_source ON relationships(source_type,source_id);
        CREATE INDEX IF NOT EXISTS idx_relationships_target ON relationships(target_type,target_id);
        CREATE INDEX IF NOT EXISTS idx_activity_created ON activity_log(created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_collection_items_collection ON collection_items(collection_id);
        """)
        additions = {
            "projects": {"tags": "TEXT", "category_id": "INTEGER", "is_template": "INTEGER DEFAULT 0", "favorite": "INTEGER DEFAULT 0", "favorite_folder_id": "INTEGER", "pinned": "INTEGER DEFAULT 0", "last_viewed_at": "TEXT", "edit_count": "INTEGER DEFAULT 0"},
            "prompts": {"category_id": "INTEGER", "is_template": "INTEGER DEFAULT 0", "favorite_folder_id": "INTEGER", "pinned": "INTEGER DEFAULT 0", "last_viewed_at": "TEXT", "edit_count": "INTEGER DEFAULT 0", "status": "TEXT DEFAULT 'Rascunho'"},
            "tips": {"tags": "TEXT", "category_id": "INTEGER", "is_template": "INTEGER DEFAULT 0", "favorite": "INTEGER DEFAULT 0", "favorite_folder_id": "INTEGER", "pinned": "INTEGER DEFAULT 0", "last_viewed_at": "TEXT", "edit_count": "INTEGER DEFAULT 0", "status": "TEXT DEFAULT 'Rascunho'"},
            "codes": {"category_id": "INTEGER", "is_template": "INTEGER DEFAULT 0", "favorite": "INTEGER DEFAULT 0", "favorite_folder_id": "INTEGER", "pinned": "INTEGER DEFAULT 0", "last_viewed_at": "TEXT", "edit_count": "INTEGER DEFAULT 0"},
            "files": {"category_id": "INTEGER", "favorite": "INTEGER DEFAULT 0", "favorite_folder_id": "INTEGER", "pinned": "INTEGER DEFAULT 0", "last_viewed_at": "TEXT", "edit_count": "INTEGER DEFAULT 0"},
        }
        for table, columns in additions.items():
            existing = {row["name"] for row in self.db.execute(f"PRAGMA table_info({table})")}
            for column, definition in columns.items():
                if column not in existing:
                    self.db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
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
        if table not in set(CONTENT_TABLES) | {"categories", "collections", "favorite_folders"}:
            raise ValueError("Tabela não permitida")
        return self.db.execute(f"SELECT * FROM {table} {where}", params).fetchall()

    def counts(self):
        return {k: self.db.execute(f"SELECT COUNT(*) n FROM {k}").fetchone()["n"] for k in ("prompts", "projects", "tips", "codes", "files", "knowledge")}

    @staticmethod
    def human_size_bytes(size):
        value = float(size)
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if value < 1024 or unit == "TB":
                return f"{value:.1f} {unit}" if unit != "B" else f"{value:.0f} {unit}"
            value /= 1024

    def health_metrics(self):
        file_size = sum(path.stat().st_size for path in self.file_dir.rglob("*") if path.is_file()) if self.file_dir.exists() else 0
        counts = {
            "prompts": self.db.execute("SELECT COUNT(*) n FROM prompts").fetchone()["n"],
            "projects": self.db.execute("SELECT COUNT(*) n FROM projects").fetchone()["n"],
            "tips": self.db.execute("SELECT COUNT(*) n FROM tips").fetchone()["n"],
            "codes": self.db.execute("SELECT COUNT(*) n FROM codes").fetchone()["n"],
            "files": self.db.execute("SELECT COUNT(*) n FROM files").fetchone()["n"],
            "trash": self.db.execute("SELECT COUNT(*) n FROM trash").fetchone()["n"],
            "versions": self.db.execute("SELECT COUNT(*) n FROM prompt_versions").fetchone()["n"],
            "knowledge": self.db.execute("SELECT COUNT(*) n FROM knowledge").fetchone()["n"],
            "templates": sum(self.db.execute(f"SELECT COUNT(*) n FROM {table} WHERE is_template=1").fetchone()["n"] for table in ("prompts", "projects", "tips", "codes", "knowledge")),
            "collections": self.db.execute("SELECT COUNT(*) n FROM collections").fetchone()["n"],
        }
        counts["db_size"] = self.db_path.stat().st_size if self.db_path.exists() else 0
        counts["files_size"] = file_size
        counts["last_backup"] = self.setting("last_backup_at", "Nunca")
        return counts

    def verify_library(self):
        result = {"database": False, "database_accessible": False, "database_integrity": False, "files_dir": self.file_dir.exists(), "trash_files_dir": (self.base_dir / "trash-files").exists(), "referenced_files": [], "missing_files": [], "orphan_files": [], "orphan_records": [], "invalid_hashes": []}
        try:
            result["database_accessible"] = self.db.execute("SELECT 1").fetchone()[0] == 1
            result["database_integrity"] = self.db.execute("PRAGMA quick_check").fetchone()[0] == "ok"
            result["database"] = result["database_integrity"]
        except sqlite3.Error as exc:
            result["database_accessible"] = False
            result["orphan_records"].append(f"Banco: {exc}")
        referenced = set()
        for row in self.db.execute("SELECT id,stored_name,sha256 FROM files"):
            referenced.add(row["stored_name"])
            path = self.file_dir / row["stored_name"]
            result["referenced_files"].append(row["stored_name"])
            if not path.is_file():
                result["missing_files"].append(f"files:{row['id']}:{row['stored_name']}")
            elif row["sha256"] and sha256_file(path) != row["sha256"]:
                result["invalid_hashes"].append(f"files:{row['id']}:{row['stored_name']}")
        if self.file_dir.exists():
            result["orphan_files"] = [str(path.relative_to(self.file_dir)) for path in self.file_dir.rglob("*") if path.is_file() and path.name not in referenced and not path.name.startswith(".restore-")]
        for table, column in (("prompts", "project_id"), ("codes", "project_id")):
            result["orphan_records"].extend(f"{table}:{row['id']}" for row in self.db.execute(f"SELECT id FROM {table} WHERE {column} IS NOT NULL AND {column} NOT IN (SELECT id FROM projects)"))
        result["orphan_records"].extend(f"prompt_versions:{row['id']}" for row in self.db.execute("SELECT id FROM prompt_versions WHERE prompt_id NOT IN (SELECT id FROM prompts)"))
        for table in ("projects", "prompts", "tips", "codes", "files", "knowledge"):
            result["orphan_records"].extend(f"{table}:category:{row['id']}" for row in self.db.execute(f"SELECT id FROM {table} WHERE category_id IS NOT NULL AND category_id NOT IN (SELECT id FROM categories)"))
        for row in self.db.execute("SELECT id,source_type,source_id,target_type,target_id FROM relationships"):
            if not self.entity_exists(row["source_type"], row["source_id"]) or not self.entity_exists(row["target_type"], row["target_id"]):
                result["orphan_records"].append(f"relationships:{row['id']}")
        for row in self.db.execute("SELECT id,entity_type,entity_id FROM collection_items"):
            if not self.entity_exists(row["entity_type"], row["entity_id"]): result["orphan_records"].append(f"collection_items:{row['id']}")
        return result

    def trash_row(self, table, rid):
        if table not in set(CONTENT_TABLES):
            raise ValueError("Tabela não permitida")
        row = self.db.execute(f"SELECT * FROM {table} WHERE id=?", (rid,)).fetchone()
        if not row:
            return False
        payload = dict(row)
        if table == "projects":
            payload["_prompt_ids"] = [r["id"] for r in self.db.execute("SELECT id FROM prompts WHERE project_id=?", (rid,))]
            payload["_code_ids"] = [r["id"] for r in self.db.execute("SELECT id FROM codes WHERE project_id=?", (rid,))]
        payload["_relationships"] = [dict(r) for r in self.db.execute("SELECT * FROM relationships WHERE (source_type=? AND source_id=?) OR (target_type=? AND target_id=?)", (table, rid, table, rid))]
        if table == "files":
            trash_dir = self.base_dir / "trash-files"
            trash_dir.mkdir(mode=0o700, exist_ok=True)
            source = self.file_dir / row["stored_name"]
            if source.is_file():
                moved_name = f"{secrets.token_hex(12)}{source.suffix}"
                shutil.move(str(source), str(trash_dir / moved_name))
                payload["_trash_file"] = moved_name
        self.db.execute("INSERT INTO trash(entity_type,original_id,payload,deleted_at) VALUES(?,?,?,?)", (table, rid, json.dumps(payload, ensure_ascii=False), now()))
        self.db.execute("DELETE FROM relationships WHERE (source_type=? AND source_id=?) OR (target_type=? AND target_id=?)", (table, rid, table, rid))
        self.db.execute("DELETE FROM collection_items WHERE entity_type=? AND entity_id=?", (table, rid))
        self.db.execute(f"DELETE FROM {table} WHERE id=?", (rid,))
        self.log_activity("exclusão", table, rid, payload.get(ENTITY_NAME_FIELDS.get(table, "name"), ""), commit=False)
        self.db.commit()
        return True

    def trash_rows(self):
        return self.db.execute("SELECT * FROM trash ORDER BY deleted_at DESC, id DESC").fetchall()

    def restore_trash(self, trash_id):
        row = self.db.execute("SELECT * FROM trash WHERE id=?", (trash_id,)).fetchone()
        if not row:
            return False
        table, payload = row["entity_type"], json.loads(row["payload"])
        if table not in set(CONTENT_TABLES):
            raise ValueError("Tipo de lixeira inválido")
        columns = [r["name"] for r in self.db.execute(f"PRAGMA table_info({table})") if r["name"] != "id"]
        values = {key: payload.get(key) for key in columns}
        original_id = int(row["original_id"])
        use_original_id = not self.db.execute(f"SELECT 1 FROM {table} WHERE id=?", (original_id,)).fetchone()
        physical_source = None
        restored_name = values.get("stored_name")
        if table == "files" and payload.get("_trash_file"):
            physical_source = self.base_dir / "trash-files" / Path(payload["_trash_file"]).name
            if not physical_source.is_file():
                physical_source = None
            target = self.file_dir / restored_name
            if target.exists():
                restored_name = f"{secrets.token_hex(12)}{Path(restored_name).suffix}"
                values["stored_name"] = restored_name
        target = self.file_dir / restored_name if table == "files" and physical_source else None
        if physical_source and target:
            shutil.copy2(physical_source, target)
            if values.get("sha256") and sha256_file(target) != values["sha256"]:
                target.unlink(missing_ok=True)
                raise ValueError("SHA-256 inválido durante a restauração")
        try:
            insert_columns = [key for key in columns if key in values]
            placeholders = ",".join("?" for _ in insert_columns)
            if use_original_id:
                insert_columns = ["id"] + insert_columns
                values_to_insert = [original_id] + [values[key] for key in insert_columns[1:]]
            else:
                values_to_insert = [values[key] for key in insert_columns]
            self.db.execute(f"INSERT INTO {table}({','.join(insert_columns)}) VALUES({placeholders if not use_original_id else ','.join('?' for _ in insert_columns)})", values_to_insert)
            if table == "projects":
                for dependent_table, key in (("prompts", "_prompt_ids"), ("codes", "_code_ids")):
                    for dependent_id in payload.get(key, []):
                        self.db.execute(f"UPDATE {dependent_table} SET project_id=? WHERE id=? AND project_id IS NULL", (original_id, dependent_id))
            restored_id = original_id if use_original_id else self.db.execute("SELECT last_insert_rowid()").fetchone()[0]
            for relation in payload.get("_relationships", []):
                source_id = restored_id if relation.get("source_type") == table and relation.get("source_id") == original_id else relation.get("source_id")
                target_id = restored_id if relation.get("target_type") == table and relation.get("target_id") == original_id else relation.get("target_id")
                if self.entity_exists(relation.get("source_type"), source_id) and self.entity_exists(relation.get("target_type"), target_id):
                    self.db.execute("INSERT OR IGNORE INTO relationships(source_type,source_id,target_type,target_id,relation_type,created_at) VALUES(?,?,?,?,?,?)", (relation.get("source_type"),source_id,relation.get("target_type"),target_id,relation.get("relation_type","Relacionado"),relation.get("created_at",now())))
            self.db.execute("DELETE FROM trash WHERE id=?", (trash_id,))
            self.log_activity("restauração", table, restored_id, values.get(ENTITY_NAME_FIELDS.get(table, "name"), ""), commit=False)
            self.db.commit()
            if physical_source:
                physical_source.unlink(missing_ok=True)
            return True
        except Exception:
            self.db.rollback()
            if target:
                target.unlink(missing_ok=True)
            raise

    def add_prompt_version(self, prompt_id, snapshot):
        version = self.db.execute("SELECT COALESCE(MAX(version),0)+1 n FROM prompt_versions WHERE prompt_id=?", (prompt_id,)).fetchone()["n"]
        self.db.execute("INSERT INTO prompt_versions(prompt_id,version,snapshot,created_at) VALUES(?,?,?,?)", (prompt_id, version, json.dumps(dict(snapshot), ensure_ascii=False), now()))
        self.db.commit()

    def prompt_versions(self, prompt_id):
        return self.db.execute("SELECT * FROM prompt_versions WHERE prompt_id=? ORDER BY version DESC", (prompt_id,)).fetchall()

    def entity_exists(self, entity_type, entity_id):
        if entity_type not in CONTENT_TABLES or entity_id is None:
            return False
        return self.db.execute(f"SELECT 1 FROM {entity_type} WHERE id=?", (entity_id,)).fetchone() is not None

    def entity_row(self, entity_type, entity_id):
        if entity_type not in CONTENT_TABLES:
            raise ValueError("Tipo de conteúdo inválido")
        return self.db.execute(f"SELECT * FROM {entity_type} WHERE id=?", (entity_id,)).fetchone()

    def entity_label(self, entity_type, entity_id):
        row = self.entity_row(entity_type, entity_id)
        return row[ENTITY_NAME_FIELDS[entity_type]] if row else "Item removido"

    def log_activity(self, action, entity_type=None, entity_id=None, details="", commit=True):
        if entity_type is not None and entity_type not in set(CONTENT_TABLES) | {"collections", "categories", "backup", "relatório", "instalação"}:
            entity_type = "outro"
        self.db.execute("INSERT INTO activity_log(action,entity_type,entity_id,details,created_at) VALUES(?,?,?,?,?)", (action, entity_type, entity_id, str(details or ""), now()))
        if commit: self.db.commit()

    def record_access(self, entity_type, entity_id):
        if not self.entity_exists(entity_type, entity_id): return
        column = "accessed_at" if entity_type == "files" else "last_viewed_at"
        self.db.execute(f"UPDATE {entity_type} SET {column}=? WHERE id=?", (now(), entity_id))
        self.log_activity("visualização", entity_type, entity_id, self.entity_label(entity_type, entity_id), commit=False)
        self.db.commit()

    def category_paths(self):
        rows = {row["id"]: row for row in self.db.execute("SELECT * FROM categories ORDER BY name COLLATE NOCASE")}
        cache = {}
        def resolve(cid, trail=()):
            if cid in cache: return cache[cid]
            row = rows.get(cid)
            if not row: return ""
            if cid in trail: return row["name"]
            parent = resolve(row["parent_id"], trail + (cid,)) if row["parent_id"] else ""
            cache[cid] = f"{parent} / {row['name']}" if parent else row["name"]
            return cache[cid]
        return {cid: resolve(cid) for cid in rows}

    def category_id_for(self, value):
        wanted = str(value or "").strip().casefold()
        if not wanted: return None
        return next((cid for cid, path in self.category_paths().items() if path.casefold() == wanted or path.rsplit(" / ", 1)[-1].casefold() == wanted), None)

    def save_category(self, name, parent_id=None, category_id=None):
        name = " ".join(str(name).split())
        if not name: raise ValueError("Nome da categoria é obrigatório")
        if parent_id is not None and not self.db.execute("SELECT 1 FROM categories WHERE id=?", (parent_id,)).fetchone(): raise ValueError("Categoria pai inválida")
        if category_id is not None:
            descendants = {category_id}; changed = True
            while changed:
                before = len(descendants); descendants.update(r["id"] for r in self.db.execute("SELECT id,parent_id FROM categories") if r["parent_id"] in descendants); changed = len(descendants) != before
            if parent_id in descendants: raise ValueError("Uma categoria não pode ser filha de si própria")
            self.db.execute("UPDATE categories SET name=?,parent_id=?,updated_at=? WHERE id=?", (name,parent_id,now(),category_id)); cid = category_id; action = "edição"
        else:
            cur = self.db.execute("INSERT INTO categories(name,parent_id,created_at,updated_at) VALUES(?,?,?,?)", (name,parent_id,now(),now())); cid = cur.lastrowid; action = "criação"
        self.log_activity(action, "categories", cid, name, commit=False); self.db.commit(); return cid

    def delete_category(self, category_id):
        row = self.db.execute("SELECT * FROM categories WHERE id=?", (category_id,)).fetchone()
        if not row: return False
        parent_id = row["parent_id"]
        self.db.execute("UPDATE categories SET parent_id=? WHERE parent_id=?", (parent_id, category_id))
        for table in CONTENT_TABLES: self.db.execute(f"UPDATE {table} SET category_id=NULL WHERE category_id=?", (category_id,))
        self.db.execute("DELETE FROM categories WHERE id=?", (category_id,))
        self.log_activity("exclusão", "categories", category_id, row["name"], commit=False); self.db.commit(); return True

    def save_relationship(self, source_type, source_id, target_type, target_id, relation_type="Relacionado"):
        if source_type == target_type and int(source_id) == int(target_id): raise ValueError("Não é possível relacionar um item a ele mesmo")
        if not self.entity_exists(source_type, source_id) or not self.entity_exists(target_type, target_id): raise ValueError("Conteúdo relacionado inválido")
        self.db.execute("INSERT OR REPLACE INTO relationships(source_type,source_id,target_type,target_id,relation_type,created_at) VALUES(?,?,?,?,?,?)", (source_type,source_id,target_type,target_id,relation_type.strip() or "Relacionado",now()))
        self.log_activity("relacionamento", source_type, source_id, f"{relation_type}: {target_type}:{target_id}", commit=False); self.db.commit()

    def related_items(self, entity_type, entity_id):
        result = []
        for row in self.db.execute("SELECT * FROM relationships WHERE (source_type=? AND source_id=?) OR (target_type=? AND target_id=?) ORDER BY created_at DESC", (entity_type,entity_id,entity_type,entity_id)):
            other_type, other_id = (row["target_type"],row["target_id"]) if row["source_type"] == entity_type and row["source_id"] == entity_id else (row["source_type"],row["source_id"])
            if self.entity_exists(other_type, other_id): result.append((row, other_type, other_id, self.entity_label(other_type, other_id)))
        return result

    def duplicate_item(self, entity_type, entity_id, as_template=False):
        row = self.entity_row(entity_type, entity_id)
        if not row: raise ValueError("Item não encontrado")
        data = dict(row); data.pop("id", None)
        name_field = ENTITY_NAME_FIELDS[entity_type]; data[name_field] = f"{data[name_field]} (cópia)"
        if "created_at" in data: data["created_at"] = now()
        if "updated_at" in data: data["updated_at"] = now()
        if "last_viewed_at" in data: data["last_viewed_at"] = None
        if "accessed_at" in data: data["accessed_at"] = None
        if "edit_count" in data: data["edit_count"] = 0
        if "is_template" in data: data["is_template"] = 1 if as_template else int(data.get("is_template") or 0)
        if entity_type == "files":
            source = self.file_dir / data["stored_name"]
            stored = f"{secrets.token_hex(12)}{Path(data['stored_name']).suffix}"
            if source.is_file(): shutil.copy2(source, self.file_dir / stored)
            data["stored_name"] = stored
        columns = list(data); cur = self.db.execute(f"INSERT INTO {entity_type}({','.join(columns)}) VALUES({','.join('?' for _ in columns)})", [data[c] for c in columns]); new_id = cur.lastrowid
        for relation in self.db.execute("SELECT * FROM relationships WHERE source_type=? AND source_id=?", (entity_type, entity_id)):
            self.db.execute("INSERT OR IGNORE INTO relationships(source_type,source_id,target_type,target_id,relation_type,created_at) VALUES(?,?,?,?,?,?)", (entity_type,new_id,relation["target_type"],relation["target_id"],relation["relation_type"],now()))
        self.log_activity("duplicação", entity_type, new_id, data[name_field], commit=False); self.db.commit(); return new_id

    def create_from_template(self, source_type, source_id, target_type):
        source = self.entity_row(source_type, source_id)
        if not source or target_type not in {"prompts", "projects", "tips", "knowledge"}: raise ValueError("Template ou destino inválido")
        title = source[ENTITY_NAME_FIELDS[source_type]]
        content = source["content"] if "content" in source.keys() else source["objective"] if "objective" in source.keys() else ""
        tags = normalize_tags(source["tags"] if "tags" in source.keys() else "")
        category_id = source["category_id"] if "category_id" in source.keys() else None
        t = now()
        if target_type == "prompts": cur = self.db.execute("INSERT INTO prompts(name,content,tags,category_id,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?)", (title,content,tags,category_id,"Rascunho",t,t))
        elif target_type == "projects": cur = self.db.execute("INSERT INTO projects(name,objective,status,tags,category_id,created_at,updated_at) VALUES(?,?,?,?,?,?,?)", (title,content,"Em construção",tags,category_id,t,t))
        elif target_type == "tips": cur = self.db.execute("INSERT INTO tips(title,content,tags,category_id,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?)", (title,content,tags,category_id,"Rascunho",t,t))
        else: cur = self.db.execute("INSERT INTO knowledge(title,content,tags,category_id,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?)", (title,content,tags,category_id,"Rascunho",t,t))
        self.log_activity("criação por template", target_type, cur.lastrowid, title, commit=False); self.db.commit(); return cur.lastrowid

    def record_search(self, query, filters=None):
        query = str(query or "").strip(); encoded = json.dumps(filters or {}, ensure_ascii=False, sort_keys=True)
        if not query and encoded == "{}": return
        last = self.db.execute("SELECT query,filters FROM search_history ORDER BY id DESC LIMIT 1").fetchone()
        if last and last["query"] == query and last["filters"] == encoded: return
        self.db.execute("INSERT INTO search_history(query,filters,searched_at) VALUES(?,?,?)", (query,encoded,now()))
        self.db.execute("DELETE FROM search_history WHERE id NOT IN (SELECT id FROM search_history ORDER BY id DESC LIMIT 100)")
        self.db.commit()

    def recent_items(self, limit=10):
        rows = []
        for table in CONTENT_TABLES:
            viewed = "accessed_at" if table == "files" else "last_viewed_at"
            for row in self.db.execute(f"SELECT id,{ENTITY_NAME_FIELDS[table]} label,{viewed} viewed FROM {table} WHERE {viewed} IS NOT NULL ORDER BY {viewed} DESC LIMIT ?", (limit,)):
                rows.append((row["viewed"], table, row["id"], row["label"]))
        return sorted(rows, reverse=True)[:limit]

    def productivity_metrics(self):
        cutoff = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
        created = sum(self.db.execute(f"SELECT COUNT(*) n FROM {table} WHERE created_at>=?", (cutoff,)).fetchone()["n"] for table in ("prompts","projects","tips","codes","knowledge"))
        edited = self.db.execute("SELECT COUNT(*) n FROM activity_log WHERE action='edição' AND created_at>=?", (cutoff,)).fetchone()["n"]
        restored = self.db.execute("SELECT COUNT(*) n FROM activity_log WHERE action='restauração' AND created_at>=?", (cutoff,)).fetchone()["n"]
        active = self.db.execute("SELECT COUNT(*) n FROM projects WHERE status='Ativo'").fetchone()["n"]
        review = sum(self.db.execute(f"SELECT COUNT(*) n FROM {table} WHERE status='Em Revisão'").fetchone()["n"] for table in ("prompts","tips","knowledge"))
        archived = sum(self.db.execute(f"SELECT COUNT(*) n FROM {table} WHERE status='Arquivado'").fetchone()["n"] for table in ("prompts","tips","knowledge"))
        return {"created_30":created,"edited_30":edited,"restored_30":restored,"active_projects":active,"review":review,"archived":archived}

    def diagnosis(self):
        integrity = self.verify_library(); checks = {
            "SQLite acessível": integrity["database_accessible"], "SQLite íntegro": integrity["database_integrity"],
            "Diretório de dados": self.base_dir.is_dir(), "Diretório de arquivos": self.file_dir.is_dir(),
            "Diretório de lixeira": (self.base_dir / "trash-files").is_dir(), "Dados graváveis": os.access(self.base_dir, os.W_OK),
            "Banco gravável": os.access(self.db_path, os.W_OK) if self.db_path.exists() else os.access(self.base_dir, os.W_OK),
            "app.py/Executável": Path(sys.executable if getattr(sys, "frozen", False) else __file__).exists(),
        }
        return checks, integrity

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
        ttk.Button(box, text="Entrar  →", style="Primary.TButton", command=self.submit).grid(row=5, column=0, sticky="ew", pady=(18, 4)); self.user.bind("<Return>", lambda _: self.submit()); self.password.bind("<Return>", lambda _: self.submit())
        ttk.Button(shell, text="Esqueci minha senha", style="Link.TButton", command=self.recover).grid(row=4, column=0, pady=(14, 4))
        self.after_idle((self.password if self.storage.setting("username") else self.user).focus_set)
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
        super().__init__(master, padding=12)
        self.master = master; self.storage = master.storage; self.username = username; self.logout = logout
        self.project_map = {}; self.category_map = {}; self.search_var = tk.StringVar(); self.type_filter = tk.StringVar(value="Todos")
        self.tag_filter = tk.StringVar(); self.category_filter = tk.StringVar(value="Todas"); self.favorite_filter = tk.BooleanVar(value=False)
        self.template_filter = tk.BooleanVar(value=False); self.status_filter = tk.StringVar(value="Todos"); self.date_from_filter = tk.StringVar(); self.date_to_filter = tk.StringVar()
        self.refresh_job = None; self.build()
        shortcuts = {"<Control-k>": self.focus_search, "<Control-n>": self.shortcut_new, "<Control-f>": self.show_favorites,
                     "<Control-s>": self.shortcut_save, "<Control-d>": self.shortcut_duplicate, "<Control-e>": self.shortcut_export}
        for sequence, command in shortcuts.items(): self.bind_all(sequence, command)

    def build(self):
        self.columnconfigure(0, weight=1); self.rowconfigure(4, weight=1)
        header = ttk.Frame(self); header.grid(row=0, column=0, sticky="ew", pady=(0, 8)); header.columnconfigure(2, weight=1)
        self.header_profile = None
        try:
            self.header_profile = tk.PhotoImage(file=str(resource_path("Foto_Perfil_EricaQA_800x800.png")))
            avatar = tk.Label(header, image=self.header_profile, borderwidth=0, highlightthickness=0, bg=PALETTE["surface"]); avatar.grid(row=0, column=0, sticky="w", padx=(0, 10)); avatar.configure(width=42, height=42)
        except tk.TclError: ttk.Label(header, text="▰", style="BrandMark.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 10))
        ttk.Label(header, text="Biblioteca de Prompts", style="Title.TLabel").grid(row=0, column=1, sticky="w")
        ttk.Label(header, text=f"Olá, {self.username}", style="Subtitle.TLabel").grid(row=0, column=2, sticky="w", padx=16)
        ttk.Button(header, text="Sair", command=self.logout).grid(row=0, column=3)
        search = ttk.Frame(self); search.grid(row=1, column=0, sticky="ew", pady=(0, 10)); search.columnconfigure(1, weight=1)
        ttk.Label(search, text="Pesquisar projetos, prompts ou repositórios...", style="SearchHint.TLabel").grid(row=0, column=0, padx=(0, 10)); self.search = ttk.Entry(search, textvariable=self.search_var, style="Search.TEntry"); self.search.grid(row=0, column=1, sticky="ew"); self.search.bind("<KeyRelease>", self.schedule_refresh)
        ttk.Combobox(search, textvariable=self.type_filter, values=["Todos", "Projetos", "Prompts", "Governança", "Códigos", "Arquivos", "Conhecimento"], state="readonly", width=15).grid(row=0, column=2, padx=5)
        ttk.Button(search, text="Filtros", command=self.open_filters).grid(row=0, column=3, padx=5); ttk.Button(search, text="Histórico", command=self.show_search_history).grid(row=0, column=4, padx=5); ttk.Button(search, text="Limpar", command=self.clear_search).grid(row=0, column=5)
        for var in (self.type_filter, self.category_filter, self.favorite_filter, self.template_filter, self.status_filter): var.trace_add("write", lambda *_: self.schedule_refresh())
        self.filter_summary = ttk.Label(self, text="", style="Muted.TLabel"); self.filter_summary.grid(row=2, column=0, sticky="w", pady=(0, 4))
        navigation = ttk.Frame(self, style="Toolbar.TFrame"); navigation.grid(row=3, column=0, sticky="ew", pady=(0, 10)); navigation.columnconfigure(6, weight=1)
        for index, (label, command) in enumerate((("Projetos", lambda: self.tabs.select(self.projects)), ("Prompts", lambda: self.tabs.select(self.prompts)), ("Repositórios", lambda: self.tabs.select(self.repository)), ("Favoritos", self.show_favorites), ("Recentes", self.show_recent))):
            ttk.Button(navigation, text=label, style="Quiet.TButton", command=command).grid(row=0, column=index, padx=(0, 6))
        self.advanced_menu = ttk.Menubutton(navigation, text="Mais", style="Quiet.TButton"); menu = tk.Menu(self.advanced_menu, tearoff=False, bg=PALETTE["surface_raised"], fg=PALETTE["text"], activebackground=PALETTE["violet"], activeforeground=PALETTE["text"]); self.advanced_menu.configure(menu=menu)
        self.tabs = ttk.Notebook(self, style="Hidden.TNotebook"); self.tabs.grid(row=4, column=0, sticky="nsew")
        self.dashboard_tab(); self.project_tab(); self.prompt_tab(); self.tip_tab(); self.code_tab(); self.knowledge_tab(); self.template_tab(); self.collection_tab(); self.repository_tab(); self.settings_tab(); self.refresh_all()
        for label, frame in (("Governança", self.tips), ("Wiki", self.knowledge), ("Templates", self.templates), ("Coleções", self.collections_tab_frame), ("Códigos", self.codes), ("Configurações", self.settings)):
            menu.add_command(label=label, command=lambda target=frame: self.tabs.select(target))
        menu.add_separator(); menu.add_command(label="Diagnóstico", command=self.diagnose_installation); menu.add_command(label="Relatórios", command=self.export_general_report); menu.add_command(label="Lixeira", command=self.open_trash)
        self.advanced_menu.grid(row=0, column=6, sticky="e")

    def dashboard_tab(self):
        tab = ttk.Frame(self.tabs, padding=(42, 34)); self.dashboard = tab; self.tabs.add(tab, text="Dashboard"); tab.columnconfigure(0, weight=1); tab.rowconfigure(3, weight=1)
        ttk.Label(tab, text="CONTINUAR TRABALHANDO", style="Kicker.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(tab, text="Retome seu contexto sem procurar de novo.", style="Hero.TLabel").grid(row=1, column=0, sticky="w", pady=(5, 4))
        ttk.Label(tab, text="Seu espaço de trabalho pessoal, focado no próximo passo.", style="Muted.TLabel").grid(row=2, column=0, sticky="w", pady=(0, 24))
        self.resume_shell, self.resume_card = self.rounded_card(tab, padding=(26, 24), height=292); self.resume_shell.grid(row=3, column=0, sticky="ew"); self.resume_card.columnconfigure(1, weight=1)
        self.home_fields = {}
        for row, label in enumerate(("Projeto atual", "Onde parei", "Próximo passo", "Último prompt utilizado", "Repositório relacionado", "Última atualização")):
            ttk.Label(self.resume_card, text=label.upper(), style="CardLabel.TLabel").grid(row=row, column=0, sticky="nw", padx=(0, 28), pady=8); self.home_fields[label] = ttk.Label(self.resume_card, text="—", style="CardBody.TLabel"); self.home_fields[label].grid(row=row, column=1, sticky="w", pady=8)
        ttk.Button(self.resume_card, text="Continuar  →", style="Primary.TButton", command=self.continue_work).grid(row=6, column=1, sticky="w", pady=(18, 4))
        lower = ttk.Frame(tab); lower.grid(row=4, column=0, sticky="ew", pady=(30, 0)); lower.columnconfigure((0, 1), weight=1)
        fav_shell, fav_card = self.rounded_card(lower, padding=(18, 16)); fav_shell.grid(row=0, column=0, sticky="ew", padx=(0, 12)); recent_shell, recent_card = self.rounded_card(lower, padding=(18, 16)); recent_shell.grid(row=0, column=1, sticky="ew", padx=(12, 0))
        self.home_favorites = ttk.Label(fav_card, text="Favoritos\n—", style="CardBody.TLabel"); self.home_favorites.pack(anchor="w"); self.home_recent = ttk.Label(recent_card, text="Recentes\n—", style="CardBody.TLabel"); self.home_recent.pack(anchor="w")

    def bind_card_hover(self, card):
        def set_state(style):
            card.configure(style=style)
            for child in card.winfo_children():
                if isinstance(child, ttk.Frame): child.configure(style=style)
        card.bind("<Enter>", lambda _event: set_state("CardHover.TFrame"))
        card.bind("<Leave>", lambda _event: set_state("Card.TFrame"))
        for child in card.winfo_children():
            child.bind("<Enter>", lambda _event: set_state("CardHover.TFrame"))
            child.bind("<Leave>", lambda _event: set_state("Card.TFrame"))

    def rounded_card(self, parent, padding=(16, 14), height=98):
        shell = tk.Canvas(parent, bg=PALETTE["surface"], highlightthickness=0, borderwidth=0, height=height)
        card = ttk.Frame(shell, style="Card.TFrame", padding=padding)
        window_id = shell.create_window((10, 10), window=card, anchor="nw")
        def redraw(event):
            shell.delete("rounded-bg")
            width, height, radius = max(event.width - 2, 2), max(event.height - 2, 2), 16
            points = [(radius, 1), (width - radius, 1), (width - 1, radius), (width - 1, height - radius), (width - radius, height - 1), (radius, height - 1), (1, height - radius), (1, radius)]
            shadow = [(x + 2, y + 3) for x, y in points]
            shell.create_polygon(shadow, fill="#080710", outline="", smooth=True, tags="rounded-bg")
            shell.create_polygon(points, fill=PALETTE["surface_raised"], outline="", smooth=True, tags="rounded-bg")
            shell.tag_lower("rounded-bg")
            shell.itemconfigure(window_id, width=max(width - 20, 1))
        shell.bind("<Configure>", redraw)
        return shell, card

    def tree(self, parent, cols, heads):
        frame = ttk.Frame(parent); frame.columnconfigure(0, weight=1); frame.rowconfigure(0, weight=1); tree = ttk.Treeview(frame, columns=cols, show="headings");
        for c, h in zip(cols, heads): tree.heading(c, text=h); tree.column(c, width=150, minwidth=90, anchor="w", stretch=True)
        tree.grid(row=0, column=0, sticky="nsew"); vertical = ttk.Scrollbar(frame, orient="vertical", command=tree.yview); vertical.grid(row=0, column=1, sticky="ns"); horizontal = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview); horizontal.grid(row=1, column=0, sticky="ew"); tree.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set); return frame, tree

    def toolbar(self, parent, title, new, edit, delete, extras=()):
        bar = ttk.Frame(parent, style="Toolbar.TFrame"); bar.pack(fill="x", pady=(0, 12)); bar.columnconfigure(0, weight=1); ttk.Label(bar, text=title, style="Section.TLabel").grid(row=0, column=0, sticky="w"); actions = ttk.Frame(bar, style="Toolbar.TFrame"); actions.grid(row=0, column=1, sticky="e")
        for label, fn in extras: ttk.Button(actions, text=label, style="Quiet.TButton", command=fn).pack(side="left", padx=(5, 0))
        ttk.Button(actions, text="Excluir", style="Danger.TButton", command=delete).pack(side="left", padx=(5, 0)); ttk.Button(actions, text="Editar", style="Quiet.TButton", command=edit).pack(side="left", padx=(5, 0)); ttk.Button(actions, text="＋ Novo", style="Primary.TButton", command=new).pack(side="left")

    def project_tab(self):
        self.projects = ttk.Frame(self.tabs, padding=12); self.tabs.add(self.projects, text="Projetos")
        self.toolbar(self.projects, "Projetos", self.new_project, self.edit_project, lambda: self.delete(self.project_tree, "projects"), [("Relações", lambda: self.manage_relationships("projects", self.project_tree)), ("Duplicar", lambda: self.duplicate_selected("projects", self.project_tree)), ("Exportar coleção", lambda: self.export_collection("projects", self.project_tree))])
        frame, self.project_tree = self.tree(self.projects, ("pin","fav","template","name","status","category","tags"), ("📌","★","T","Projeto","Status","Categoria","Tags")); frame.pack(fill="both", expand=True); self.project_tree.bind("<Double-1>", lambda _: self.edit_project())

    def prompt_tab(self):
        self.prompts = ttk.Frame(self.tabs, padding=12); self.tabs.add(self.prompts, text="Prompts")
        self.toolbar(self.prompts, "Biblioteca de Prompts", self.new_prompt, self.edit_prompt, lambda: self.delete(self.prompt_tree, "prompts"), [("Relações", lambda: self.manage_relationships("prompts", self.prompt_tree)), ("Duplicar", lambda: self.duplicate_selected("prompts", self.prompt_tree)), ("Exportar coleção", lambda: self.export_collection("prompts", self.prompt_tree)), ("Histórico", self.show_prompt_history), ("Copiar", self.copy_prompt), ("★", lambda: self.toggle_flag("prompts", self.prompt_tree, "favorite")), ("📌", lambda: self.toggle_flag("prompts", self.prompt_tree, "pinned"))])
        frame, self.prompt_tree = self.tree(self.prompts, ("pin","fav","template","name","status","category","project","tool","tags"), ("📌","★","T","Nome","Status","Categoria","Projeto","Ferramenta","Tags")); frame.pack(fill="both", expand=True); self.prompt_tree.bind("<Double-1>", lambda _: self.edit_prompt())

    def tip_tab(self):
        self.tips = ttk.Frame(self.tabs, padding=12); self.tabs.add(self.tips, text="Governança")
        self.toolbar(self.tips, "Governança de Projetos", self.new_tip, self.edit_tip, lambda: self.delete(self.tip_tree, "tips"), [("Relações", lambda: self.manage_relationships("tips", self.tip_tree)), ("Duplicar", lambda: self.duplicate_selected("tips", self.tip_tree)), ("Exportar coleção", lambda: self.export_collection("tips", self.tip_tree)), ("Copiar", self.copy_tip)])
        frame, self.tip_tree = self.tree(self.tips, ("pin","fav","template","title","status","category","tags"), ("📌","★","T","Título","Status","Categoria","Tags")); frame.pack(fill="both", expand=True); self.tip_tree.bind("<Double-1>", lambda _: self.edit_tip())

    def code_tab(self):
        self.codes = ttk.Frame(self.tabs, padding=12); self.tabs.add(self.codes, text="Códigos")
        self.toolbar(self.codes, "Biblioteca de Códigos", self.new_code, self.edit_code, lambda: self.delete(self.code_tree, "codes"), [("Relações", lambda: self.manage_relationships("codes", self.code_tree)), ("Duplicar", lambda: self.duplicate_selected("codes", self.code_tree)), ("Exportar coleção", lambda: self.export_collection("codes", self.code_tree)), ("Copiar", self.copy_code)])
        frame, self.code_tree = self.tree(self.codes, ("pin","fav","template","name","language","project","category","tags"), ("📌","★","T","Nome","Linguagem","Projeto","Categoria","Tags")); frame.pack(fill="both", expand=True); self.code_tree.bind("<Double-1>", lambda _: self.edit_code())

    def knowledge_tab(self):
        self.knowledge = ttk.Frame(self.tabs, padding=12); self.tabs.add(self.knowledge, text="Wiki")
        self.toolbar(self.knowledge, "Base de Conhecimento Local", self.new_knowledge, self.edit_knowledge, lambda: self.delete(self.knowledge_tree, "knowledge"), [("Relações", lambda: self.manage_relationships("knowledge", self.knowledge_tree)), ("Duplicar", lambda: self.duplicate_selected("knowledge", self.knowledge_tree)), ("Exportar coleção", lambda: self.export_collection("knowledge", self.knowledge_tree)), ("Visualizar", self.view_knowledge)])
        frame, self.knowledge_tree = self.tree(self.knowledge, ("pin","fav","template","title","status","category","tags","updated"), ("📌","★","T","Título","Status","Categoria","Tags","Atualizado")); frame.pack(fill="both", expand=True); self.knowledge_tree.bind("<Double-1>", lambda _: self.view_knowledge())

    def template_tab(self):
        self.templates = ttk.Frame(self.tabs, padding=12); self.tabs.add(self.templates, text="Templates")
        self.toolbar(self.templates, "Galeria de Templates", self.new_prompt, self.edit_template, self.unmark_template, [("Criar a partir", self.create_from_selected_template), ("Duplicar", self.duplicate_template)])
        frame, self.template_tree = self.tree(self.templates, ("type","title","category","tags","updated"), ("Tipo","Título","Categoria","Tags","Atualizado")); frame.pack(fill="both", expand=True); self.template_tree.bind("<Double-1>", lambda _: self.create_from_selected_template())

    def collection_tab(self):
        self.collections_tab_frame = ttk.Frame(self.tabs, padding=12); self.tabs.add(self.collections_tab_frame, text="Coleções")
        self.toolbar(self.collections_tab_frame, "Coleções e Catálogos", self.new_collection, self.edit_collection, self.delete_collection, [("Importar pacote", self.import_collection), ("Exportar pacote", self.export_selected_package), ("Gerenciar itens", self.manage_collection_items)])
        frame, self.collection_tree = self.tree(self.collections_tab_frame, ("name","catalog","description","items","updated"), ("Coleção","Catálogo","Descrição","Itens","Atualizada")); frame.pack(fill="both", expand=True); self.collection_tree.bind("<Double-1>", lambda _: self.manage_collection_items())

    def repository_tab(self):
        self.repository = ttk.Frame(self.tabs, padding=12); self.tabs.add(self.repository, text="📁 Repositório")
        self.toolbar(self.repository, "Arquivos relacionados", self.upload_file, self.file_info, lambda: self.delete_file(), [("Relações", lambda: self.manage_relationships("files", self.file_tree)), ("Exportar", lambda: self.export_selected(self.file_tree, "files")), ("Baixar", self.download_file)])
        frame, self.file_tree = self.tree(self.repository, ("pin","fav","name","category","extension","size","created"), ("📌","★","Arquivo","Categoria","Tipo","Tamanho","Adicionado")); frame.pack(fill="both", expand=True); self.file_tree.bind("<Double-1>", lambda _: self.file_info())

    def settings_tab(self):
        self.settings = ttk.Frame(self.tabs, padding=18); self.tabs.add(self.settings, text="Configurações")
        ttk.Label(self.settings, text="Configurações e proteção", style="Section.TLabel").pack(anchor="w")
        ttk.Label(self.settings, text="Dados locais, sem envio automático para serviços externos.", style="Muted.TLabel").pack(anchor="w", pady=(4, 18))
        groups = [("ORGANIZAÇÃO", [("Gerenciar categorias", self.manage_categories), ("Pastas de favoritos", self.manage_favorite_folders)]), ("DADOS E SEGURANÇA", [("Exportar backup seguro", self.export_backup), ("Importar backup seguro", self.import_backup), ("Abrir lixeira", self.open_trash), ("Abrir pasta de dados", lambda: messagebox.showinfo(APP_NAME, str(self.storage.base_dir)))]), ("DIAGNÓSTICO E RELATÓRIOS", [("Relatório geral", self.export_general_report), ("Log de atividades", self.show_activity_log), ("Diagnosticar instalação", self.diagnose_installation), ("Analisar Espaço Utilizado", self.analyze_space), ("Exportar relatório de saúde", self.export_health_report)]), ("CONTA E APLICAÇÃO", [("Alterar senha", self.change_password), ("Configurar e-mail de recuperação", self.configure_email), ("Sobre a aplicação", self.about)])]
        for title, actions in groups:
            section = ttk.Frame(self.settings, style="Card.TFrame", padding=(14, 12)); section.pack(fill="x", pady=(0, 10)); ttk.Label(section, text=title, style="Kicker.TLabel").pack(anchor="w", pady=(0, 8)); row = ttk.Frame(section, style="Card.TFrame"); row.pack(fill="x")
            for label, fn in actions: ttk.Button(row, text=label, style="Quiet.TButton", command=fn).pack(side="left", padx=(0, 7))
        ttk.Label(self.settings, text="Modo portátil: crie portable.flag ao lado do executável/app.py ou defina BIBLIOTECA_PORTABLE=1. Os dados serão mantidos em ./data.", wraplength=760, style="Muted.TLabel").pack(anchor="w", pady=(4, 0))

    def focus_search(self, _event=None):
        if self.search.winfo_exists():
            self.search.focus_set()
        return "break"

    def clear_search(self):
        self.search_var.set(""); self.schedule_refresh()

    def shortcut_new(self, _event=None): self.new_prompt(); return "break"
    def shortcut_save(self, _event=None):
        widget = self.master.focus_get()
        if widget: widget.event_generate("<Return>")
        return "break"
    def shortcut_duplicate(self, _event=None):
        table, tree = self.current_entity_context()
        if table: self.duplicate_selected(table, tree)
        return "break"
    def shortcut_export(self, _event=None):
        table, tree = self.current_entity_context()
        if table: self.export_collection(table, tree)
        return "break"

    def current_entity_context(self):
        mapping = {str(self.projects):("projects",self.project_tree), str(self.prompts):("prompts",self.prompt_tree), str(self.tips):("tips",self.tip_tree), str(self.codes):("codes",self.code_tree), str(self.knowledge):("knowledge",self.knowledge_tree), str(self.repository):("files",self.file_tree)}
        return mapping.get(self.tabs.select(), (None,None))

    def open_filters(self):
        win = tk.Toplevel(self); win.title("Filtros combinados"); win.transient(self); win.grab_set(); win.configure(bg=PALETTE["bg"]); self.center_window(win, 520, 430); box = ttk.Frame(win, padding=20, style="Modal.TFrame"); box.pack(fill="both", expand=True); box.columnconfigure(1, weight=1)
        fields = [("Tags (todas, separadas por vírgula)",self.tag_filter),("Categoria",self.category_filter),("Status",self.status_filter),("Criado desde (AAAA-MM-DD)",self.date_from_filter),("Criado até (AAAA-MM-DD)",self.date_to_filter)]
        for i,(label,var) in enumerate(fields):
            ttk.Label(box,text=label).grid(row=i,column=0,sticky="w",padx=(0,8),pady=6)
            values = ["Todas"] + list(self.category_map.values()) if var is self.category_filter else ["Todos"] + CONTENT_STATUSES if var is self.status_filter else None
            widget = ttk.Combobox(box,textvariable=var,values=values,state="readonly") if values else ttk.Entry(box,textvariable=var); widget.grid(row=i,column=1,sticky="ew",pady=6)
        ttk.Checkbutton(box,text="Somente favoritos",variable=self.favorite_filter).grid(row=5,column=1,sticky="w",pady=6); ttk.Checkbutton(box,text="Somente templates",variable=self.template_filter).grid(row=6,column=1,sticky="w",pady=6)
        def clear():
            self.tag_filter.set(""); self.category_filter.set("Todas"); self.status_filter.set("Todos"); self.date_from_filter.set(""); self.date_to_filter.set(""); self.favorite_filter.set(False); self.template_filter.set(False)
        actions=ttk.Frame(box, style="Modal.TFrame"); actions.grid(row=7,column=0,columnspan=2,sticky="e",pady=14); ttk.Button(actions,text="Limpar",style="Quiet.TButton",command=clear).pack(side="left",padx=5); ttk.Button(actions,text="Aplicar filtros",style="Primary.TButton",command=lambda:(win.destroy(),self.refresh_all())).pack(side="left")

    def show_search_history(self):
        win=tk.Toplevel(self); win.title("Histórico de pesquisas"); win.transient(self); win.geometry("720x420"); frame,tree=self.tree(win,("query","filters","date"),("Pesquisa","Filtros","Data")); frame.pack(fill="both",expand=True,padx=12,pady=12)
        for row in self.storage.db.execute("SELECT * FROM search_history ORDER BY id DESC LIMIT 100"): tree.insert("","end",iid=str(row["id"]),values=(row["query"],row["filters"],row["searched_at"]))
        def reuse():
            if not tree.selection(): return
            row=self.storage.db.execute("SELECT * FROM search_history WHERE id=?",(int(tree.selection()[0]),)).fetchone(); self.search_var.set(row["query"]); win.destroy(); self.refresh_all()
        ttk.Button(win,text="Reutilizar",command=reuse).pack(anchor="e",padx=12,pady=(0,12))

    def verify_library(self):
        result = self.storage.verify_library()
        database = "OK" if result["database_accessible"] else "FALHA"
        integrity = "OK" if result["database_integrity"] else "FALHA"
        files_dir = "OK" if result["files_dir"] else "AUSENTE"
        trash_dir = "OK" if result["trash_files_dir"] else "AUSENTE"
        messagebox.showinfo(APP_NAME, f"Banco acessível: {database}\nBanco íntegro: {integrity}\nPasta files: {files_dir}\nPasta trash-files: {trash_dir}\nArquivos referenciados: {len(result['referenced_files'])}\nArquivos ausentes: {len(result['missing_files'])}\nArquivos órfãos: {len(result['orphan_files'])}\nRegistros órfãos: {len(result['orphan_records'])}\nHashes inválidos: {len(result['invalid_hashes'])}")

    def health_report_text(self, markdown=False):
        metrics = self.storage.health_metrics(); result = self.storage.verify_library(); analyzed_at = now()
        lines = [f"# Relatório de Saúde — {analyzed_at}" if markdown else f"RELATÓRIO DE SAÚDE — {analyzed_at}", ""]
        stats = [("Prompts", metrics["prompts"]), ("Projetos", metrics["projects"]), ("Governanças", metrics["tips"]), ("Códigos", metrics["codes"]), ("Arquivos", metrics["files"]), ("Lixeira", metrics["trash"]), ("Versões", metrics["versions"]), ("Banco SQLite", self.storage.human_size_bytes(metrics["db_size"])), ("Pasta de arquivos", self.storage.human_size_bytes(metrics["files_size"])), ("Último backup", metrics["last_backup"])]
        lines.append("## Estatísticas" if markdown else "ESTATÍSTICAS")
        lines.extend(f"- **{key}**: {value}" if markdown else f"{key}: {value}" for key, value in stats)
        checks = [("Banco acessível", result["database_accessible"]), ("Banco íntegro", result["database_integrity"]), ("Pasta files existente", result["files_dir"]), ("Pasta trash-files existente", result["trash_files_dir"]), ("Arquivos ausentes", result["missing_files"]), ("Arquivos órfãos", result["orphan_files"]), ("Registros órfãos", result["orphan_records"]), ("Hashes inválidos", result["invalid_hashes"])]
        lines.extend(["", "## Verificações" if markdown else "", "VERIFICAÇÕES" if not markdown else ""])
        for key, value in checks:
            display = value if isinstance(value, bool) else len(value)
            lines.append(f"- **{key}**: {display}" if markdown else f"{key}: {display}")
        return "\n".join(lines) + "\n"

    def export_health_report(self):
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Texto", "*.txt"), ("Markdown", "*.md")])
        if not path or not self.confirm_export("O relatório de saúde"):
            return
        markdown = Path(path).suffix.lower() == ".md"
        Path(path).write_text(self.health_report_text(markdown), encoding="utf-8")
        messagebox.showinfo(APP_NAME, "Relatório de saúde exportado.")

    def analyze_space(self):
        result = self.storage.verify_library(); win = tk.Toplevel(self); win.title("Analisar Espaço Utilizado"); win.transient(self); win.geometry("820x500")
        frame, tree = self.tree(win, ("kind", "item"), ("Tipo", "Item")); frame.pack(fill="both", expand=True, padx=14, pady=14)
        issues = [("Arquivo órfão", item) for item in result["orphan_files"]] + [("Registro órfão", item) for item in result["orphan_records"]]
        for index, (kind, item) in enumerate(issues): tree.insert("", "end", iid=str(index), values=(kind, item))
        def remove_selected():
            selected = tree.selection()
            if not selected or not messagebox.askyesno(APP_NAME, "Remover permanentemente o item selecionado? Esta ação não poderá ser desfeita.", parent=win):
                return
            kind, item = tree.item(selected[0], "values")
            if kind == "Arquivo órfão":
                candidate = (self.storage.file_dir / item).resolve()
                if self.storage.file_dir.resolve() in candidate.parents and candidate.is_file(): candidate.unlink()
            elif ":" in item:
                table, raw_id = item.split(":", 1)
                if table in {"prompts", "codes", "prompt_versions"} and raw_id.isdigit(): self.storage.db.execute(f"DELETE FROM {table} WHERE id=?", (int(raw_id),)); self.storage.db.commit()
            win.destroy(); self.analyze_space(); self.refresh_all()
        ttk.Button(win, text="Remover selecionado", command=remove_selected).pack(anchor="e", padx=14, pady=(0, 14))

    def schedule_refresh(self, _event=None):
        if self.refresh_job:
            self.after_cancel(self.refresh_job)
        self.refresh_job = self.after(150, self.refresh_all)

    def query(self, table, order="updated_at DESC", extra="", params=()):
        q = self.search_var.get().strip().lower(); values = list(params); clauses = []
        if extra:
            clean = extra.strip(); clean = clean[5:].strip() if clean.upper().startswith("WHERE") else clean
            if clean: clauses.append(f"({clean})")
        fields = {"projects":("name","objective","github_repo","tool","status","tags"),"prompts":("name","category","objective","trigger","content","tags","status"),"tips":("title","category","when_to_use","explanation","content","tags","status"),"codes":("name","language","purpose","content","tags"),"files":("name","category","extension","notes"),"knowledge":("title","content","tags","status")}[table]
        if q:
            searchable = " || ' ' || ".join(f"COALESCE({field}, '')" for field in fields); clauses.append(f"LOWER({searchable}) LIKE ?"); values.append(f"%{q}%")
        for tag in [x.strip().lower() for x in self.tag_filter.get().replace(";",",").split(",") if x.strip()]: clauses.append("LOWER(COALESCE(tags,'')) LIKE ?"); values.append(f"%{tag}%")
        category = self.category_filter.get()
        if category and category != "Todas": clauses.append("category_id=?"); values.append(self.storage.category_id_for(category) or -1)
        if self.favorite_filter.get(): clauses.append("favorite=1")
        if self.template_filter.get() and table != "files": clauses.append("is_template=1")
        status = self.status_filter.get()
        if status and status != "Todos" and table in {"prompts","tips","knowledge"}: clauses.append("status=?"); values.append(status)
        if self.date_from_filter.get().strip(): clauses.append("date(created_at)>=date(?)"); values.append(self.date_from_filter.get().strip())
        if self.date_to_filter.get().strip(): clauses.append("date(created_at)<=date(?)"); values.append(self.date_to_filter.get().strip())
        where = "WHERE " + " AND ".join(clauses) if clauses else ""
        return self.storage.rows(table, where + (" ORDER BY " + order if order else ""), values)

    def refresh_all(self):
        self.project_map = {r["id"]:r["name"] for r in self.storage.rows("projects","ORDER BY name")}; self.category_map = self.storage.category_paths()
        trees=(self.project_tree,self.prompt_tree,self.tip_tree,self.code_tree,self.knowledge_tree,self.template_tree,self.collection_tree,self.file_tree)
        for tree in trees: tree.delete(*tree.get_children())
        enabled = self.type_filter.get(); allowed={"Todos":set(CONTENT_TABLES),"Projetos":{"projects"},"Prompts":{"prompts"},"Governança":{"tips"},"Códigos":{"codes"},"Arquivos":{"files"},"Conhecimento":{"knowledge"}}.get(enabled,set(CONTENT_TABLES))
        if "projects" in allowed:
            for r in self.query("projects"): self.project_tree.insert("","end",iid=str(r["id"]),values=("📌" if r["pinned"] else "","★" if r["favorite"] else "","T" if r["is_template"] else "",r["name"],r["status"],self.category_map.get(r["category_id"],""),r["tags"] or ""))
        if "prompts" in allowed:
            for r in self.query("prompts","pinned DESC, favorite DESC, updated_at DESC"): self.prompt_tree.insert("","end",iid=str(r["id"]),values=("📌" if r["pinned"] else "","★" if r["favorite"] else "","T" if r["is_template"] else "",r["name"],r["status"] or "Rascunho",self.category_map.get(r["category_id"],r["category"] or ""),self.project_map.get(r["project_id"],""),r["tool"] or "",r["tags"] or ""))
        if "tips" in allowed:
            for r in self.query("tips"): self.tip_tree.insert("","end",iid=str(r["id"]),values=("📌" if r["pinned"] else "","★" if r["favorite"] else "","T" if r["is_template"] else "",r["title"],r["status"] or "Rascunho",self.category_map.get(r["category_id"],r["category"] or ""),r["tags"] or ""))
        if "codes" in allowed:
            for r in self.query("codes"): self.code_tree.insert("","end",iid=str(r["id"]),values=("📌" if r["pinned"] else "","★" if r["favorite"] else "","T" if r["is_template"] else "",r["name"],r["language"] or "",self.project_map.get(r["project_id"],""),self.category_map.get(r["category_id"],""),r["tags"] or ""))
        if "knowledge" in allowed:
            for r in self.query("knowledge"): self.knowledge_tree.insert("","end",iid=str(r["id"]),values=("📌" if r["pinned"] else "","★" if r["favorite"] else "","T" if r["is_template"] else "",r["title"],r["status"] or "Rascunho",self.category_map.get(r["category_id"],""),r["tags"] or "",r["updated_at"]))
        if "files" in allowed:
            for r in self.query("files","created_at DESC"): self.file_tree.insert("","end",iid=str(r["id"]),values=("📌" if r["pinned"] else "","★" if r["favorite"] else "",r["name"],self.category_map.get(r["category_id"],r["category"]),r["extension"],self.human_size(r["size"]),r["created_at"]))
        for table in ("prompts","projects","tips","codes","knowledge"):
            for r in self.storage.db.execute(f"SELECT * FROM {table} WHERE is_template=1 ORDER BY updated_at DESC"): self.template_tree.insert("","end",iid=f"{table}:{r['id']}",values=(ENTITY_LABELS[table],r[ENTITY_NAME_FIELDS[table]],self.category_map.get(r["category_id"],r["category"] if "category" in r.keys() else ""),r["tags"] or "",r["updated_at"]))
        for r in self.storage.db.execute("SELECT c.*,COUNT(ci.id) items FROM collections c LEFT JOIN collection_items ci ON ci.collection_id=c.id GROUP BY c.id ORDER BY c.updated_at DESC"): self.collection_tree.insert("","end",iid=str(r["id"]),values=(r["name"],r["catalog"],r["description"] or "",r["items"],r["updated_at"]))
        self.refresh_home_context()
        filters=[]
        if self.tag_filter.get(): filters.append("tags: "+self.tag_filter.get())
        if self.category_filter.get()!="Todas": filters.append("categoria: "+self.category_filter.get())
        if self.favorite_filter.get(): filters.append("favoritos")
        if self.template_filter.get(): filters.append("templates")
        self.filter_summary.configure(text="Filtros: "+(" • ".join(filters) if filters else "nenhum")); self.refresh_job=None
        if self.search_var.get().strip(): self.storage.record_search(self.search_var.get(), {"tipo":self.type_filter.get(),"tags":self.tag_filter.get(),"categoria":self.category_filter.get(),"favorito":self.favorite_filter.get(),"template":self.template_filter.get(),"status":self.status_filter.get()})

    def destroy(self):
        if self.refresh_job:
            self.after_cancel(self.refresh_job)
        for sequence in ("<Control-k>","<Control-n>","<Control-f>","<Control-s>","<Control-d>","<Control-e>"): self.unbind_all(sequence)
        super().destroy()

    @staticmethod
    def human_size(size):
        for unit in ("B", "KB", "MB", "GB"):
            if size < 1024: return f"{size:.0f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def center_window(self, win, width, height):
        self.update_idletasks()
        x = self.winfo_rootx() + max((self.winfo_width() - width) // 2, 0)
        y = self.winfo_rooty() + max((self.winfo_height() - height) // 2, 0)
        win.geometry(f"{width}x{height}+{x}+{y}")

    def selected(self, tree): return int(tree.selection()[0]) if tree.selection() else None
    def refresh_home_context(self):
        project = self.storage.db.execute("SELECT * FROM projects ORDER BY updated_at DESC LIMIT 1").fetchone()
        prompt = self.storage.db.execute("SELECT p.*, pr.name project_name FROM prompts p LEFT JOIN projects pr ON pr.id=p.project_id ORDER BY p.updated_at DESC LIMIT 1").fetchone()
        values = {"Projeto atual": project["name"] if project else "Nenhum projeto recente", "Onde parei": (project["last_prompt"] if project and project["last_prompt"] else "Abra um projeto para registrar seu ponto de parada"), "Próximo passo": (project["objective"] if project and project["objective"] else "Defina o próximo passo no projeto"), "Último prompt utilizado": prompt["name"] if prompt else "Nenhum prompt recente", "Repositório relacionado": (project["github_repo"] or project["repo_link"] if project else "Nenhum repositório relacionado"), "Última atualização": (project["updated_at"] if project else "—")}
        for key, value in values.items(): self.home_fields[key].configure(text=value)
        favorites = self.storage.db.execute("SELECT name FROM prompts WHERE favorite=1 ORDER BY updated_at DESC LIMIT 3").fetchall(); recent = self.storage.recent_items(3)
        self.home_favorites.configure(text="Favoritos\n" + ("\n".join(f"• {r['name']}" for r in favorites) if favorites else "—")); self.home_recent.configure(text="Recentes\n" + ("\n".join(f"• {label}" for _, _, _, label in recent) if recent else "—"))
    def continue_work(self):
        project = self.storage.db.execute("SELECT id FROM projects ORDER BY updated_at DESC LIMIT 1").fetchone()
        if project: self.tabs.select(self.projects); self.project_tree.selection_set(str(project["id"])); self.project_tree.focus(str(project["id"]))
        else: self.tabs.select(self.projects)
    def delete(self, tree, table):
        rid = self.selected(tree)
        if rid and messagebox.askyesno(APP_NAME, "Mover o item selecionado para a lixeira?"):
            self.storage.trash_row(table, rid); self.refresh_all()
    def copy_row(self, tree, table, field):
        rid = self.selected(tree)
        if rid:
            row = self.storage.db.execute(f"SELECT {field} FROM {table} WHERE id=?", (rid,)).fetchone(); self.master.clipboard_clear(); self.master.clipboard_append(row[field]); messagebox.showinfo(APP_NAME, "Conteúdo copiado.")
    def copy_prompt(self): self.copy_row(self.prompt_tree, "prompts", "content")
    def copy_tip(self): self.copy_row(self.tip_tree, "tips", "content")
    def copy_code(self): self.copy_row(self.code_tree, "codes", "content")

    def confirm_export(self, description):
        return messagebox.askyesno(APP_NAME, f"{description} será gravado no local escolhido por você.\n\nO arquivo pode conter dados da sua biblioteca. Continuar?", parent=self)

    def export_selected(self, tree, table):
        rid = self.selected(tree)
        if not rid:
            return
        row = self.storage.db.execute(f"SELECT * FROM {table} WHERE id=?", (rid,)).fetchone()
        if not row:
            return
        name = row["name"] if "name" in row.keys() else row["title"]
        path = filedialog.asksaveasfilename(defaultextension=".json", initialfile=name, filetypes=[("JSON", "*.json"), ("Texto", "*.txt"), ("Markdown", "*.md")])
        if not path or not self.confirm_export(f"A exportação de {name}"):
            return
        data = dict(row)
        if table == "files":
            data["arquivo_local"] = str(self.storage.file_dir / row["stored_name"])
        suffix = Path(path).suffix.lower()
        if suffix == ".txt":
            content = "\n".join(f"{key}: {value if value is not None else ''}" for key, value in data.items())
        elif suffix in {".md", ".markdown"}:
            content = f"# {name}\n\n" + "\n".join(f"- **{key}**: {value if value is not None else ''}" for key, value in data.items())
        else:
            content = json.dumps(data, ensure_ascii=False, indent=2)
        Path(path).write_text(content, encoding="utf-8")
        messagebox.showinfo(APP_NAME, "Item exportado.")

    def show_prompt_history(self):
        rid = self.selected(self.prompt_tree)
        if not rid:
            return
        win = tk.Toplevel(self); win.title("Histórico do prompt"); win.transient(self); win.geometry("760x520")
        frame, tree = self.tree(win, ("version", "created"), ("Versão", "Criada em")); frame.pack(fill="x", padx=14, pady=14)
        text = tk.Text(win, height=15, wrap="word", font=("Segoe UI", 14), bg=PALETTE["input"], fg=PALETTE["text"], insertbackground=PALETTE["text"], relief="flat", padx=10, pady=8); text.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        versions = self.storage.prompt_versions(rid)
        for version in versions: tree.insert("", "end", iid=str(version["id"]), values=(version["version"], version["created_at"]))
        def show(_=None):
            selected = tree.selection()
            if selected:
                snapshot = json.loads(self.storage.db.execute("SELECT snapshot FROM prompt_versions WHERE id=?", (int(selected[0]),)).fetchone()["snapshot"])
                text.delete("1.0", "end"); text.insert("1.0", snapshot.get("content", ""))
        tree.bind("<<TreeviewSelect>>", show)
        if versions: tree.selection_set(str(versions[0]["id"])); show()

    def open_trash(self):
        win = tk.Toplevel(self); win.title("Lixeira"); win.transient(self); win.geometry("760x460")
        frame, tree = self.tree(win, ("type", "item", "deleted"), ("Tipo", "Item", "Excluído em")); frame.pack(fill="both", expand=True, padx=14, pady=14)
        rows = self.storage.trash_rows()
        for row in rows:
            payload = json.loads(row["payload"]); label = payload.get("name") or payload.get("title") or "Item"
            tree.insert("", "end", iid=str(row["id"]), values=(row["entity_type"], label, row["deleted_at"]))
        actions = ttk.Frame(win); actions.pack(fill="x", padx=14, pady=(0, 14))
        def restore():
            selected = tree.selection()
            if selected:
                self.storage.restore_trash(int(selected[0])); win.destroy(); self.refresh_all()
        def remove():
            selected = tree.selection()
            if selected and messagebox.askyesno(APP_NAME, "Excluir permanentemente o item da lixeira?"):
                self.storage.db.execute("DELETE FROM trash WHERE id=?", (int(selected[0]),)); self.storage.db.commit(); win.destroy(); self.open_trash()
        ttk.Button(actions, text="Restaurar", style="Success.TButton", command=restore).pack(side="right", padx=4); ttk.Button(actions, text="Excluir permanentemente", style="Danger.TButton", command=remove).pack(side="right", padx=4)

    def form(self, title, fields, values=None):
        if values is not None and not isinstance(values, dict): values = dict(values)
        win = tk.Toplevel(self); win.title(title); win.transient(self); win.grab_set(); win.minsize(560, 420); win.geometry("720x620"); win.configure(bg=PALETTE["bg"])
        outer = ttk.Frame(win, style="Modal.TFrame"); outer.pack(fill="both", expand=True); canvas = tk.Canvas(outer, highlightthickness=0, bg=PALETTE["surface"]); scroll = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview); inner = ttk.Frame(canvas, padding=(24, 20), style="Modal.TFrame"); inner.columnconfigure(1, weight=1); canvas.create_window((0, 0), window=inner, anchor="nw"); canvas.configure(yscrollcommand=scroll.set); canvas.pack(side="left", fill="both", expand=True); scroll.pack(side="right", fill="y"); inner.bind("<Configure>", lambda _: canvas.configure(scrollregion=canvas.bbox("all")))
        ttk.Label(inner, text=title.upper(), style="Kicker.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 4)); ttk.Label(inner, text="Preencha o essencial agora — você poderá complementar depois.", style="FormHint.TLabel").grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 14))
        widgets = {}
        for i, (key, label, kind, options) in enumerate(fields):
            ttk.Label(inner, text=label, style="FieldLabel.TLabel").grid(row=i + 2, column=0, sticky="nw", padx=(0, 14), pady=7)
            w = ttk.Combobox(inner, values=options, state="readonly") if kind == "combo" else tk.Text(inner, height=5, wrap="word", font=("Segoe UI", 14), bg=PALETTE["input"], fg=PALETTE["text"], insertbackground=PALETTE["text"], selectbackground=PALETTE["selection"], selectforeground=PALETTE["text"], relief="flat", highlightthickness=2, highlightbackground=PALETTE["border"], highlightcolor=PALETTE["focus"], padx=10, pady=8) if kind == "text" else ttk.Entry(inner)
            w.grid(row=i + 2, column=1, sticky="ew", pady=7); widgets[key] = w
            if values and values.get(key) is not None:
                val = str(values[key]); w.insert("1.0", val) if kind == "text" else w.set(val) if kind == "combo" else w.insert(0, val)
        result = {}
        def save():
            for key, w in widgets.items(): result[key] = w.get("1.0", "end-1c") if isinstance(w, tk.Text) else w.get()
            if not result.get(fields[0][0], "").strip(): messagebox.showwarning(APP_NAME, "Preencha o campo principal.", parent=win); return
            win.destroy()
        actions = ttk.Frame(inner, style="Modal.TFrame"); actions.grid(row=len(fields) + 2, column=0, columnspan=2, sticky="e", pady=(18, 0)); ttk.Button(actions, text="Cancelar", style="Quiet.TButton", command=win.destroy).pack(side="left", padx=(0, 8)); ttk.Button(actions, text="Salvar alterações", style="Primary.TButton", command=save).pack(side="left"); win.bind("<Escape>", lambda _: win.destroy()); self.wait_window(win); return result or None

    def category_values(self): return ["(Sem categoria)"] + list(self.category_map.values())
    def category_from_data(self, data): return self.storage.category_id_for(data.get("category_path"))
    @staticmethod
    def bool_value(value): return 1 if str(value or "").strip().lower() in {"1","sim","s","true","yes","x"} else 0

    def project_fields(self): return [("name","Nome","entry",None),("objective","Objetivo","text",None),("github_repo","Repositório GitHub","entry",None),("repo_link","Link","entry",None),("tool","Ferramenta","entry",None),("status","Status","combo",STATUSES),("last_prompt","Último prompt","entry",None),("last_interaction","Última interação","entry",None),("category_path","Categoria hierárquica","combo",self.category_values()),("tags","Tags (vírgula)","entry",None),("is_template","Template? (Sim/Não)","combo",["Não","Sim"])]
    def edit_project(self):
        rid=self.selected(self.project_tree); old=self.storage.entity_row("projects",rid) if rid else None; vals=dict(old) if old else {}; vals["category_path"]=self.category_map.get(vals.get("category_id"),"(Sem categoria)"); vals["is_template"]="Sim" if vals.get("is_template") else "Não"; data=self.form("Projeto",self.project_fields(),vals)
        if not data:return
        t=now(); args=(data["name"],data["objective"],data["github_repo"],data["repo_link"],data["tool"],data["status"],data["last_prompt"],data["last_interaction"],self.category_from_data(data),normalize_tags(data["tags"]),self.bool_value(data["is_template"]))
        if rid:self.storage.db.execute("UPDATE projects SET name=?,objective=?,github_repo=?,repo_link=?,tool=?,status=?,last_prompt=?,last_interaction=?,category_id=?,tags=?,is_template=?,edit_count=edit_count+1,updated_at=? WHERE id=?",(*args,t,rid)); action="edição"; item_id=rid
        else:item_id=self.storage.db.execute("INSERT INTO projects(name,objective,github_repo,repo_link,tool,status,last_prompt,last_interaction,category_id,tags,is_template,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",(*args,t,t)).lastrowid; action="criação"
        self.storage.log_activity(action,"projects",item_id,data["name"],commit=False); self.storage.db.commit(); self.refresh_all()
    def new_project(self): self.project_tree.selection_remove(self.project_tree.selection()); self.edit_project()

    def prompt_fields(self): return [("name","Nome","entry",None),("category_path","Categoria hierárquica","combo",self.category_values()),("project_name","Projeto","combo",["(Sem projeto)"]+list(self.project_map.values())),("tool","Ferramenta","combo",PROMPT_TOOLS),("status","Status","combo",CONTENT_STATUSES),("objective","Objetivo","entry",None),("trigger","Gatilho","entry",None),("when_to_use","Quando usar","text",None),("content","Prompt completo","text",None),("expected_result","Resultado esperado","text",None),("notes","Observações","text",None),("tags","Tags (vírgula)","entry",None),("is_template","Template? (Sim/Não)","combo",["Não","Sim"])]
    def edit_prompt(self):
        rid=self.selected(self.prompt_tree); old=self.storage.entity_row("prompts",rid) if rid else None; vals=dict(old) if old else {}; vals["project_name"]=self.project_map.get(vals.get("project_id"),"(Sem projeto)"); vals["category_path"]=self.category_map.get(vals.get("category_id"),vals.get("category") or "(Sem categoria)"); vals["is_template"]="Sim" if vals.get("is_template") else "Não"; vals["status"]=vals.get("status") or "Rascunho"; data=self.form("Prompt",self.prompt_fields(),vals)
        if not data:return
        pid=next((k for k,v in self.project_map.items() if v==data["project_name"]),None); cid=self.category_from_data(data); category=self.category_map.get(cid,data["category_path"] if data["category_path"]!="(Sem categoria)" else ""); t=now(); args=(data["name"],category,cid,pid,data["tool"],data["status"],data["objective"],data["trigger"],data["when_to_use"],data["content"],data["expected_result"],data["notes"],normalize_tags(data["tags"]),self.bool_value(data["is_template"]))
        if rid:self.storage.add_prompt_version(rid,old); self.storage.db.execute("UPDATE prompts SET name=?,category=?,category_id=?,project_id=?,tool=?,status=?,objective=?,trigger=?,when_to_use=?,content=?,expected_result=?,notes=?,tags=?,is_template=?,edit_count=edit_count+1,updated_at=? WHERE id=?",(*args,t,rid)); action="edição"; item_id=rid
        else:item_id=self.storage.db.execute("INSERT INTO prompts(name,category,category_id,project_id,tool,status,objective,trigger,when_to_use,content,expected_result,notes,tags,is_template,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(*args,t,t)).lastrowid; action="criação"
        self.storage.log_activity(action,"prompts",item_id,data["name"],commit=False); self.storage.db.commit(); self.refresh_all()
    def new_prompt(self): self.prompt_tree.selection_remove(self.prompt_tree.selection()); self.edit_prompt()

    def tip_fields(self): return [("title","Título","entry",None),("category_path","Categoria hierárquica","combo",self.category_values()),("status","Status","combo",CONTENT_STATUSES),("when_to_use","Quando usar","text",None),("explanation","Explicação","text",None),("content","Prompt copiável","text",None),("tags","Tags (vírgula)","entry",None),("is_template","Template? (Sim/Não)","combo",["Não","Sim"])]
    def edit_tip(self):
        rid=self.selected(self.tip_tree); old=self.storage.entity_row("tips",rid) if rid else None; vals=dict(old) if old else {}; vals["category_path"]=self.category_map.get(vals.get("category_id"),vals.get("category") or "(Sem categoria)"); vals["is_template"]="Sim" if vals.get("is_template") else "Não"; vals["status"]=vals.get("status") or "Rascunho"; data=self.form("Governança",self.tip_fields(),vals)
        if not data:return
        cid=self.category_from_data(data); category=self.category_map.get(cid,data["category_path"] if data["category_path"]!="(Sem categoria)" else ""); t=now(); args=(data["title"],category,cid,data["status"],data["when_to_use"],data["explanation"],data["content"],normalize_tags(data["tags"]),self.bool_value(data["is_template"]))
        if rid:self.storage.db.execute("UPDATE tips SET title=?,category=?,category_id=?,status=?,when_to_use=?,explanation=?,content=?,tags=?,is_template=?,edit_count=edit_count+1,updated_at=? WHERE id=?",(*args,t,rid)); action="edição"; item_id=rid
        else:item_id=self.storage.db.execute("INSERT INTO tips(title,category,category_id,status,when_to_use,explanation,content,tags,is_template,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",(*args,t,t)).lastrowid; action="criação"
        self.storage.log_activity(action,"tips",item_id,data["title"],commit=False); self.storage.db.commit(); self.refresh_all()
    def new_tip(self): self.tip_tree.selection_remove(self.tip_tree.selection()); self.edit_tip()

    def code_fields(self): return [("name","Nome","entry",None),("language","Linguagem","entry",None),("project_name","Projeto","combo",["(Sem projeto)"]+list(self.project_map.values())),("category_path","Categoria hierárquica","combo",self.category_values()),("purpose","Finalidade","text",None),("content","Código","text",None),("tags","Tags (vírgula)","entry",None),("notes","Observações","text",None),("is_template","Template? (Sim/Não)","combo",["Não","Sim"])]
    def edit_code(self):
        rid=self.selected(self.code_tree); old=self.storage.entity_row("codes",rid) if rid else None; vals=dict(old) if old else {}; vals["project_name"]=self.project_map.get(vals.get("project_id"),"(Sem projeto)"); vals["category_path"]=self.category_map.get(vals.get("category_id"),"(Sem categoria)"); vals["is_template"]="Sim" if vals.get("is_template") else "Não"; data=self.form("Código",self.code_fields(),vals)
        if not data:return
        pid=next((k for k,v in self.project_map.items() if v==data["project_name"]),None); t=now(); args=(data["name"],data["language"],pid,self.category_from_data(data),data["purpose"],data["content"],normalize_tags(data["tags"]),data["notes"],self.bool_value(data["is_template"]))
        if rid:self.storage.db.execute("UPDATE codes SET name=?,language=?,project_id=?,category_id=?,purpose=?,content=?,tags=?,notes=?,is_template=?,edit_count=edit_count+1,updated_at=? WHERE id=?",(*args,t,rid)); action="edição"; item_id=rid
        else:item_id=self.storage.db.execute("INSERT INTO codes(name,language,project_id,category_id,purpose,content,tags,notes,is_template,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",(*args,t,t)).lastrowid; action="criação"
        self.storage.log_activity(action,"codes",item_id,data["name"],commit=False); self.storage.db.commit(); self.refresh_all()
    def new_code(self): self.code_tree.selection_remove(self.code_tree.selection()); self.edit_code()

    def knowledge_fields(self): return [("title","Título","entry",None),("category_path","Categoria hierárquica","combo",self.category_values()),("status","Status","combo",CONTENT_STATUSES),("content","Conteúdo","text",None),("tags","Tags (vírgula)","entry",None),("is_template","Template? (Sim/Não)","combo",["Não","Sim"])]
    def edit_knowledge(self):
        rid=self.selected(self.knowledge_tree); old=self.storage.entity_row("knowledge",rid) if rid else None; vals=dict(old) if old else {}; vals["category_path"]=self.category_map.get(vals.get("category_id"),"(Sem categoria)"); vals["is_template"]="Sim" if vals.get("is_template") else "Não"; vals["status"]=vals.get("status") or "Rascunho"; data=self.form("Conhecimento",self.knowledge_fields(),vals)
        if not data:return
        t=now(); args=(data["title"],data["content"],self.category_from_data(data),normalize_tags(data["tags"]),self.bool_value(data["is_template"]),data["status"])
        if rid:self.storage.db.execute("UPDATE knowledge SET title=?,content=?,category_id=?,tags=?,is_template=?,status=?,edit_count=edit_count+1,updated_at=? WHERE id=?",(*args,t,rid)); action="edição"; item_id=rid
        else:item_id=self.storage.db.execute("INSERT INTO knowledge(title,content,category_id,tags,is_template,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)",(*args,t,t)).lastrowid; action="criação"
        self.storage.log_activity(action,"knowledge",item_id,data["title"],commit=False); self.storage.db.commit(); self.refresh_all()
    def new_knowledge(self): self.knowledge_tree.selection_remove(self.knowledge_tree.selection()); self.edit_knowledge()
    def view_knowledge(self):
        rid=self.selected(self.knowledge_tree)
        if not rid:return
        row=self.storage.entity_row("knowledge",rid); self.storage.record_access("knowledge",rid); related=self.storage.related_items("knowledge",rid); links="\n".join(f"- {ENTITY_LABELS[t]}: {label} ({rel['relation_type']})" for rel,t,oid,label in related) or "Nenhum"
        messagebox.showinfo(row["title"],f"{row['content']}\n\nConteúdo relacionado:\n{links}\n\nCriado: {row['created_at']}\nAtualizado: {row['updated_at']}\nEdições: {row['edit_count']}")

    def toggle_flag(self,table,tree,column):
        rid=self.selected(tree)
        if rid:self.storage.db.execute(f"UPDATE {table} SET {column}=1-{column},updated_at=? WHERE id=?",(now(),rid)); self.storage.log_activity(column,table,rid,self.storage.entity_label(table,rid),commit=False); self.storage.db.commit(); self.refresh_all()
    def favorite(self): self.toggle_flag("prompts",self.prompt_tree,"favorite")
    def duplicate_selected(self,table,tree):
        rid=self.selected(tree)
        if rid:self.storage.duplicate_item(table,rid); self.refresh_all()

    def selected_template(self):
        selected=self.template_tree.selection()
        if not selected:return None,None
        table,rid=selected[0].split(":",1); return table,int(rid)
    def duplicate_template(self):
        table,rid=self.selected_template()
        if table:self.storage.duplicate_item(table,rid,as_template=True);self.refresh_all()
    def unmark_template(self):
        table,rid=self.selected_template()
        if table:self.storage.db.execute(f"UPDATE {table} SET is_template=0,updated_at=? WHERE id=?",(now(),rid));self.storage.db.commit();self.refresh_all()
    def edit_template(self):
        table,rid=self.selected_template()
        if not table:return
        mapping={"prompts":(self.prompts,self.prompt_tree,self.edit_prompt),"projects":(self.projects,self.project_tree,self.edit_project),"tips":(self.tips,self.tip_tree,self.edit_tip),"codes":(self.codes,self.code_tree,self.edit_code),"knowledge":(self.knowledge,self.knowledge_tree,self.edit_knowledge)}; tab,tree,fn=mapping[table]; self.tabs.select(tab); tree.selection_set(str(rid)); fn()
    def create_from_selected_template(self):
        table,rid=self.selected_template()
        if not table:return
        target=simpledialog.askstring(APP_NAME,"Criar a partir do template (prompts, projects, tips ou knowledge):",initialvalue=table if table in {"prompts","projects","tips","knowledge"} else "prompts",parent=self)
        if target:
            aliases={"prompt":"prompts","projeto":"projects","governança":"tips","governanca":"tips","wiki":"knowledge","conhecimento":"knowledge"}; target=aliases.get(target.strip().lower(),target.strip().lower())
            try:self.storage.create_from_template(table,rid,target);self.refresh_all()
            except ValueError as exc:messagebox.showerror(APP_NAME,str(exc))

    def manage_categories(self):
        win=tk.Toplevel(self);win.title("Categorias hierárquicas");win.transient(self);win.geometry("650x460");frame,tree=self.tree(win,("path",),("Categoria",));frame.pack(fill="both",expand=True,padx=12,pady=12)
        def reload():
            tree.delete(*tree.get_children());self.category_map=self.storage.category_paths()
            for cid,label in sorted(self.category_map.items(),key=lambda x:x[1].casefold()):tree.insert("","end",iid=str(cid),values=(label,))
        def add():
            name=simpledialog.askstring(APP_NAME,"Nome da categoria:",parent=win)
            if not name:return
            parent_id=int(tree.selection()[0]) if tree.selection() else None
            try:self.storage.save_category(name,parent_id);reload();self.refresh_all()
            except ValueError as exc:messagebox.showerror(APP_NAME,str(exc),parent=win)
        def edit():
            if not tree.selection():return
            cid=int(tree.selection()[0]);row=self.storage.db.execute("SELECT * FROM categories WHERE id=?",(cid,)).fetchone();name=simpledialog.askstring(APP_NAME,"Novo nome:",initialvalue=row["name"],parent=win)
            if name:self.storage.save_category(name,row["parent_id"],cid);reload();self.refresh_all()
        def remove():
            if tree.selection() and messagebox.askyesno(APP_NAME,"Remover categoria? Subcategorias serão promovidas e conteúdos preservados.",parent=win):self.storage.delete_category(int(tree.selection()[0]));reload();self.refresh_all()
        actions=ttk.Frame(win);actions.pack(fill="x",padx=12,pady=(0,12));ttk.Button(actions,text="Nova raiz/filha",command=add).pack(side="left");ttk.Button(actions,text="Editar",command=edit).pack(side="left",padx=5);ttk.Button(actions,text="Remover",command=remove).pack(side="left");reload()

    def manage_relationships(self,table,tree):
        rid=self.selected(tree)
        if not rid:return
        self.storage.record_access(table,rid);win=tk.Toplevel(self);win.title("Conteúdo Relacionado");win.transient(self);win.geometry("760x480");frame,rel_tree=self.tree(win,("type","title","relation"),("Tipo","Conteúdo","Relação"));frame.pack(fill="both",expand=True,padx=12,pady=12)
        def reload():
            rel_tree.delete(*rel_tree.get_children())
            for rel,t,oid,label in self.storage.related_items(table,rid):rel_tree.insert("","end",iid=str(rel["id"]),values=(ENTITY_LABELS[t],label,rel["relation_type"]))
        def add():
            target_type=simpledialog.askstring(APP_NAME,"Tipo: projects, prompts, tips, codes, files ou knowledge",initialvalue="projects",parent=win)
            if not target_type or target_type not in CONTENT_TABLES:return
            choices=list(self.storage.db.execute(f"SELECT id,{ENTITY_NAME_FIELDS[target_type]} label FROM {target_type} ORDER BY label"))
            prompt="ID do item:\n"+"\n".join(f"{r['id']} — {r['label']}" for r in choices[:40]);target_id=simpledialog.askinteger(APP_NAME,prompt,parent=win)
            if not target_id:return
            relation=simpledialog.askstring(APP_NAME,"Tipo da relação:",initialvalue="Relacionado",parent=win) or "Relacionado"
            try:self.storage.save_relationship(table,rid,target_type,target_id,relation);reload()
            except ValueError as exc:messagebox.showerror(APP_NAME,str(exc),parent=win)
        def remove():
            if rel_tree.selection():self.storage.db.execute("DELETE FROM relationships WHERE id=?",(int(rel_tree.selection()[0]),));self.storage.db.commit();reload()
        actions=ttk.Frame(win);actions.pack(fill="x",padx=12,pady=(0,12));ttk.Button(actions,text="Adicionar vínculo",command=add).pack(side="left");ttk.Button(actions,text="Remover vínculo",command=remove).pack(side="left",padx=5);reload()

    def manage_favorite_folders(self):
        win=tk.Toplevel(self);win.title("Pastas de favoritos");win.transient(self);win.geometry("620x430");frame,tree=self.tree(win,("name","items"),("Pasta","Itens"));frame.pack(fill="both",expand=True,padx=12,pady=12)
        def reload():
            tree.delete(*tree.get_children())
            for row in self.storage.db.execute("SELECT * FROM favorite_folders ORDER BY name COLLATE NOCASE"):
                count=sum(self.storage.db.execute(f"SELECT COUNT(*) n FROM {table} WHERE favorite_folder_id=?",(row["id"],)).fetchone()["n"] for table in CONTENT_TABLES);tree.insert("","end",iid=str(row["id"]),values=(row["name"],count))
        def add():
            name=simpledialog.askstring(APP_NAME,"Nome da pasta:",parent=win)
            if name:self.storage.db.execute("INSERT OR IGNORE INTO favorite_folders(name,created_at) VALUES(?,?)",(name.strip(),now()));self.storage.db.commit();reload()
        def assign():
            table,entity_tree=self.current_entity_context()
            if not tree.selection() or not table or not entity_tree.selection():messagebox.showwarning(APP_NAME,"Selecione uma pasta e um item na aba de conteúdo.",parent=win);return
            rid=int(entity_tree.selection()[0]);folder=int(tree.selection()[0]);self.storage.db.execute(f"UPDATE {table} SET favorite=1,favorite_folder_id=? WHERE id=?",(folder,rid));self.storage.db.commit();self.refresh_all();reload()
        def remove():
            if tree.selection():self.storage.db.execute("DELETE FROM favorite_folders WHERE id=?",(int(tree.selection()[0]),));self.storage.db.commit();reload()
        actions=ttk.Frame(win);actions.pack(fill="x",padx=12,pady=(0,12));ttk.Button(actions,text="Nova pasta",command=add).pack(side="left");ttk.Button(actions,text="Atribuir item selecionado",command=assign).pack(side="left",padx=5);ttk.Button(actions,text="Remover",command=remove).pack(side="left");reload()

    def show_favorites(self,_event=None):self.favorite_filter.set(True);self.template_filter.set(False);self.tabs.select(self.prompts);self.refresh_all();return "break"
    def show_pinned(self):
        lines=[]
        for table in CONTENT_TABLES:
            for row in self.storage.db.execute(f"SELECT id,{ENTITY_NAME_FIELDS[table]} label FROM {table} WHERE pinned=1 ORDER BY updated_at DESC"):lines.append(f"{ENTITY_LABELS[table]} — {row['label']}")
        messagebox.showinfo(APP_NAME,"Itens fixados:\n\n"+("\n".join(lines) if lines else "Nenhum item fixado."))
    def show_recent(self):
        self.tabs.select(self.dashboard); self.refresh_home_context()

    def new_collection(self):
        data=self.form("Coleção",[("name","Nome","entry",None),("catalog","Catálogo","combo",COLLECTION_CATALOGS),("description","Descrição","text",None)],{"catalog":"Geral"})
        if data:self.storage.db.execute("INSERT INTO collections(name,catalog,description,created_at,updated_at) VALUES(?,?,?,?,?)",(data["name"],data["catalog"],data["description"],now(),now()));self.storage.log_activity("criação","collections",self.storage.db.execute("SELECT last_insert_rowid()").fetchone()[0],data["name"],commit=False);self.storage.db.commit();self.refresh_all()
    def edit_collection(self):
        rid=self.selected(self.collection_tree);row=self.storage.db.execute("SELECT * FROM collections WHERE id=?",(rid,)).fetchone() if rid else None
        if not row:return
        data=self.form("Coleção",[("name","Nome","entry",None),("catalog","Catálogo","combo",COLLECTION_CATALOGS),("description","Descrição","text",None)],row)
        if data:self.storage.db.execute("UPDATE collections SET name=?,catalog=?,description=?,updated_at=? WHERE id=?",(data["name"],data["catalog"],data["description"],now(),rid));self.storage.db.commit();self.refresh_all()
    def delete_collection(self):
        rid=self.selected(self.collection_tree)
        if rid and messagebox.askyesno(APP_NAME,"Excluir coleção? Os conteúdos serão preservados."):self.storage.db.execute("DELETE FROM collections WHERE id=?",(rid,));self.storage.db.commit();self.refresh_all()
    def manage_collection_items(self):
        cid=self.selected(self.collection_tree)
        if not cid:return
        win=tk.Toplevel(self);win.title("Itens da coleção");win.transient(self);win.geometry("720x470");frame,tree=self.tree(win,("type","title"),("Tipo","Conteúdo"));frame.pack(fill="both",expand=True,padx=12,pady=12)
        def reload():
            tree.delete(*tree.get_children())
            for row in self.storage.db.execute("SELECT * FROM collection_items WHERE collection_id=? ORDER BY id",(cid,)):
                if self.storage.entity_exists(row["entity_type"],row["entity_id"]):tree.insert("","end",iid=str(row["id"]),values=(ENTITY_LABELS[row["entity_type"]],self.storage.entity_label(row["entity_type"],row["entity_id"])))
        def add():
            table=simpledialog.askstring(APP_NAME,"Tipo: prompts, projects, knowledge ou codes",initialvalue="prompts",parent=win)
            if table not in {"prompts","projects","knowledge","codes"}:return
            choices=self.storage.db.execute(f"SELECT id,{ENTITY_NAME_FIELDS[table]} label FROM {table} ORDER BY label").fetchall();rid=simpledialog.askinteger(APP_NAME,"ID do item:\n"+"\n".join(f"{r['id']} — {r['label']}" for r in choices[:40]),parent=win)
            if rid and self.storage.entity_exists(table,rid):self.storage.db.execute("INSERT OR IGNORE INTO collection_items(collection_id,entity_type,entity_id,created_at) VALUES(?,?,?,?)",(cid,table,rid,now()));self.storage.db.execute("UPDATE collections SET updated_at=? WHERE id=?",(now(),cid));self.storage.db.commit();reload();self.refresh_all()
        def remove():
            if tree.selection():self.storage.db.execute("DELETE FROM collection_items WHERE id=?",(int(tree.selection()[0]),));self.storage.db.commit();reload();self.refresh_all()
        actions=ttk.Frame(win);actions.pack(fill="x",padx=12,pady=(0,12));ttk.Button(actions,text="Adicionar",command=add).pack(side="left");ttk.Button(actions,text="Remover",command=remove).pack(side="left",padx=5);reload()

    def collection_payload(self,items,metadata=None):
        data=[];keys=set(items)
        for table,rid in items:
            row=self.storage.entity_row(table,rid)
            if row:data.append({"type":table,"data":dict(row)})
        relations=[dict(r) for r in self.storage.db.execute("SELECT * FROM relationships") if (r["source_type"],r["source_id"]) in keys and (r["target_type"],r["target_id"]) in keys]
        return {"format":"biblioteca-de-prompts-collection","version":1,"exported_at":now(),"metadata":metadata or {},"items":data,"relationships":relations}
    def export_collection(self,table,tree):
        selected=tree.selection() or tree.get_children();items=[(table,int(i)) for i in selected];self.save_collection_payload(self.collection_payload(items))
    def export_selected_package(self):
        cid=self.selected(self.collection_tree)
        if not cid:return
        collection=dict(self.storage.db.execute("SELECT * FROM collections WHERE id=?",(cid,)).fetchone());items=[(r["entity_type"],r["entity_id"]) for r in self.storage.db.execute("SELECT entity_type,entity_id FROM collection_items WHERE collection_id=?",(cid,))];self.save_collection_payload(self.collection_payload(items,collection))
    def save_collection_payload(self,payload):
        path=filedialog.asksaveasfilename(defaultextension=".json",filetypes=[("JSON","*.json"),("Markdown","*.md")])
        if not path or not self.confirm_export("A coleção"):return
        if Path(path).suffix.lower()==".md":
            lines=[f"# {payload.get('metadata',{}).get('name','Coleção')}",""]
            for item in payload["items"]:row=item["data"];lines.extend([f"## {ENTITY_LABELS[item['type']]} — {row.get(ENTITY_NAME_FIELDS[item['type']],'')}","",str(row.get("content") or row.get("objective") or row.get("purpose") or ""),""])
            content="\n".join(lines)
        else:content=json.dumps(payload,ensure_ascii=False,indent=2)
        Path(path).write_text(content,encoding="utf-8");self.storage.log_activity("exportação","collections",None,Path(path).name);messagebox.showinfo(APP_NAME,"Coleção exportada.")
    def import_collection(self):
        path=filedialog.askopenfilename(filetypes=[("Coleção JSON","*.json")])
        if not path:return
        try:
            payload=json.loads(Path(path).read_text(encoding="utf-8"))
            if payload.get("format")!="biblioteca-de-prompts-collection":raise ValueError("Formato de coleção incompatível")
            self.storage.db.execute("BEGIN");mapping={}
            for item in payload.get("items",[]):
                table=item.get("type");row=dict(item.get("data") or {});old_id=row.pop("id",None)
                if table not in {"prompts","projects","tips","codes","knowledge"}:continue
                columns={r["name"] for r in self.storage.db.execute(f"PRAGMA table_info({table})")};row={k:v for k,v in row.items() if k in columns};row[ENTITY_NAME_FIELDS[table]]=f"{row.get(ENTITY_NAME_FIELDS[table],'Item')} (importado)";row["created_at"]=row.get("created_at") or now();row["updated_at"]=now()
                cols=list(row);cur=self.storage.db.execute(f"INSERT INTO {table}({','.join(cols)}) VALUES({','.join('?' for _ in cols)})",[row[c] for c in cols]);mapping[(table,old_id)]=cur.lastrowid
            for rel in payload.get("relationships",[]):
                source=mapping.get((rel.get("source_type"),rel.get("source_id")));target=mapping.get((rel.get("target_type"),rel.get("target_id")))
                if source and target:self.storage.db.execute("INSERT OR IGNORE INTO relationships(source_type,source_id,target_type,target_id,relation_type,created_at) VALUES(?,?,?,?,?,?)",(rel["source_type"],source,rel["target_type"],target,rel.get("relation_type","Relacionado"),now()))
            meta=payload.get("metadata") or {};cur=self.storage.db.execute("INSERT INTO collections(name,catalog,description,created_at,updated_at) VALUES(?,?,?,?,?)",(f"{meta.get('name','Coleção')} (importada)",meta.get("catalog","Geral"),meta.get("description",""),now(),now()));cid=cur.lastrowid
            for (table,_),rid in mapping.items():self.storage.db.execute("INSERT INTO collection_items(collection_id,entity_type,entity_id,created_at) VALUES(?,?,?,?)",(cid,table,rid,now()))
            self.storage.log_activity("importação","collections",cid,Path(path).name,commit=False);self.storage.db.commit();self.refresh_all();messagebox.showinfo(APP_NAME,"Coleção importada.")
        except Exception as exc:self.storage.db.rollback();messagebox.showerror(APP_NAME,f"Importação cancelada: {exc}")

    def general_report_text(self,markdown=False):
        m=self.storage.health_metrics();p=self.storage.productivity_metrics();title=f"Relatório Geral — {now()}";lines=[f"# {title}" if markdown else title,""]
        stats=[("Prompts",m["prompts"]),("Projetos",m["projects"]),("Governanças",m["tips"]),("Códigos",m["codes"]),("Arquivos",m["files"]),("Conhecimentos",m["knowledge"]),("Templates",m["templates"]),("Versões",m["versions"]),("Lixeira",m["trash"]),("Coleções",m["collections"]),("Criados em 30 dias",p["created_30"]),("Editados em 30 dias",p["edited_30"]),("Restaurados em 30 dias",p["restored_30"]),("Projetos ativos",p["active_projects"]),("Em revisão",p["review"]),("Arquivados",p["archived"])]
        lines.extend(f"- **{k}**: {v}" if markdown else f"{k}: {v}" for k,v in stats);lines.extend(["","Atividades recentes:" if not markdown else "## Atividades recentes"])
        for r in self.storage.db.execute("SELECT * FROM activity_log ORDER BY id DESC LIMIT 25"):lines.append(f"- {r['created_at']} — {r['action']} — {r['entity_type'] or ''} — {r['details'] or ''}")
        return "\n".join(lines)+"\n"
    def export_general_report(self):
        path=filedialog.asksaveasfilename(defaultextension=".txt",filetypes=[("Texto","*.txt"),("Markdown","*.md")])
        if path and self.confirm_export("O relatório geral"):Path(path).write_text(self.general_report_text(Path(path).suffix.lower()==".md"),encoding="utf-8");self.storage.log_activity("exportação","relatório",None,Path(path).name);messagebox.showinfo(APP_NAME,"Relatório geral exportado.")
    def show_activity_log(self):
        win=tk.Toplevel(self);win.title("Log de atividades");win.transient(self);win.geometry("880x520");frame,tree=self.tree(win,("date","action","type","item","details"),("Data","Ação","Tipo","ID","Detalhes"));frame.pack(fill="both",expand=True,padx=12,pady=12)
        for r in self.storage.db.execute("SELECT * FROM activity_log ORDER BY id DESC LIMIT 500"):tree.insert("","end",values=(r["created_at"],r["action"],r["entity_type"] or "",r["entity_id"] or "",r["details"] or ""))
    def diagnose_installation(self):
        checks,integrity=self.storage.diagnosis();lines=[f"Biblioteca de Prompts {APP_VERSION}",f"Build: {BUILD_DATE}",f"Sistema: {platform.platform()}",f"Python: {platform.python_version()}",f"Executável/app: {sys.executable if getattr(sys,'frozen',False) else Path(__file__).resolve()}",f"Dados: {self.storage.base_dir}",f"Modo portátil: {'Sim' if self.storage.base_dir==application_dir()/'data' else 'Não'}",""]+[f"{name}: {'OK' if value else 'FALHA'}" for name,value in checks.items()]+[f"Arquivos ausentes: {len(integrity['missing_files'])}",f"Arquivos órfãos: {len(integrity['orphan_files'])}",f"Registros órfãos: {len(integrity['orphan_records'])}"]
        win=tk.Toplevel(self);win.title("Diagnóstico de instalação");win.transient(self);win.geometry("760x560");box=tk.Text(win,wrap="word",font=("Segoe UI",12),bg=PALETTE["input"],fg=PALETTE["text"]);box.pack(fill="both",expand=True,padx=12,pady=12);box.insert("1.0","\n".join(lines));box.configure(state="disabled")
        def export():
            target=filedialog.asksaveasfilename(defaultextension=".txt",filetypes=[("Texto","*.txt"),("Markdown","*.md")])
            if target and self.confirm_export("O diagnóstico da instalação"):Path(target).write_text("\n".join(lines)+"\n",encoding="utf-8");self.storage.log_activity("exportação","instalação",None,Path(target).name)
        ttk.Button(win,text="Exportar TXT/Markdown",command=export).pack(anchor="e",padx=12,pady=(0,12))

    def upload_file(self):
        source=filedialog.askopenfilename(filetypes=[("Arquivos aceitos", "*.pdf *.docx *.xlsx *.pptx *.txt *.zip *.png *.jpg *.jpeg")]);
        if not source: return
        src=Path(source); ext=src.suffix.lower()
        if ext not in ALLOWED_EXTENSIONS: messagebox.showerror(APP_NAME,"Tipo de arquivo não permitido."); return
        category=simpledialog.askstring(APP_NAME,"Categoria (Templates, Documentações, Referências ou Arquivos Gerais):",initialvalue="Arquivos Gerais") or "Arquivos Gerais"
        if category not in FILE_CATEGORIES: category="Arquivos Gerais"
        stored=f"{secrets.token_hex(12)}{ext}"; target=self.storage.file_dir/stored; shutil.copy2(src,target); cur=self.storage.db.execute("INSERT INTO files(name,stored_name,extension,category,size,sha256,created_at) VALUES(?,?,?,?,?,?,?)",(src.name,stored,ext,category,target.stat().st_size,sha256_file(target),now())); self.storage.log_activity("criação","files",cur.lastrowid,src.name,commit=False); self.storage.db.commit(); self.refresh_all()
    def file_info(self):
        rid=self.selected(self.file_tree)
        if rid:
            r=self.storage.db.execute("SELECT * FROM files WHERE id=?",(rid,)).fetchone(); self.storage.record_access("files",rid); messagebox.showinfo(APP_NAME,f"{r['name']}\nTipo: {r['extension']}\nCategoria: {r['category']}\nTamanho: {self.human_size(r['size'])}\nSHA-256: {r['sha256']}")
    def download_file(self):
        rid=self.selected(self.file_tree)
        if not rid:return
        r=self.storage.db.execute("SELECT * FROM files WHERE id=?",(rid,)).fetchone(); path=filedialog.asksaveasfilename(initialfile=r["name"]);
        if path and self.confirm_export(f"O arquivo {r['name']}"): shutil.copy2(self.storage.file_dir/r["stored_name"],path); self.storage.record_access("files",rid); self.storage.log_activity("exportação","files",rid,r["name"]);
    def delete_file(self):
        rid=self.selected(self.file_tree)
        if not rid or not messagebox.askyesno(APP_NAME,"Mover arquivo e registro para a lixeira?"):return
        self.storage.trash_row("files", rid); self.refresh_all()

    def configure_email(self):
        email=simpledialog.askstring(APP_NAME,"E-mail usado para recuperação local:",initialvalue=self.storage.setting("email", ""),parent=self)
        if email is not None:self.storage.set_setting("email",email.strip()); messagebox.showinfo(APP_NAME,"E-mail salvo localmente. Nenhuma mensagem é enviada sem configurar um provedor externo.")
    def change_password(self):
        current=simpledialog.askstring(APP_NAME,"Senha atual:",show="•",parent=self); new=simpledialog.askstring(APP_NAME,"Nova senha:",show="•",parent=self) if current and verify_password(current,self.storage.setting("password_hash","")) else None
        if new and len(new)>=6:self.storage.set_setting("password_hash",hash_password(new)); messagebox.showinfo(APP_NAME,"Senha alterada.")
        elif current: messagebox.showerror(APP_NAME,"Senha atual inválida ou nova senha muito curta.")
    def _backup_payload(self):
        files=[]
        for row in self.storage.rows("files"):
            item=dict(row);source=self.storage.file_dir/row["stored_name"]
            if source.is_file():item["content_base64"]=base64.b64encode(source.read_bytes()).decode("ascii")
            files.append(item)
        payload={"version":5,"exported_at":now(),"files":files}
        for table in ("settings","projects","prompts","tips","codes","trash","prompt_versions","categories","favorite_folders","knowledge","relationships","activity_log","collections","collection_items","search_history"):
            payload[table]=[dict(r) for r in self.storage.db.execute(f"SELECT * FROM {table}")]
        return payload
    def export_backup(self):
        path=filedialog.asksaveasfilename(defaultextension=".json",filetypes=[("Backup JSON","*.json")])
        if not path or not self.confirm_export("O backup local"):return
        payload=self._backup_payload();raw=json.dumps(payload,ensure_ascii=False,indent=2);envelope={"format":"biblioteca-de-prompts-backup","sha256":hashlib.sha256(raw.encode("utf-8")).hexdigest(),"payload":payload}
        Path(path).write_text(json.dumps(envelope,ensure_ascii=False,indent=2),encoding="utf-8");self.storage.set_setting("last_backup_at",now());self.storage.log_activity("exportação","backup",None,Path(path).name);messagebox.showinfo(APP_NAME,"Backup exportado com verificação de integridade.")
    def _stage_backup_files(self,payload):
        stage=self.storage.file_dir/f".restore-{secrets.token_hex(8)}";stage.mkdir(mode=0o700);staged=[]
        try:
            for row in payload.get("files",[]):
                raw_name=str(row.get("stored_name") or "");stored_name=Path(raw_name).name
                if not stored_name or stored_name!=raw_name or stored_name in {".",".."}:raise ValueError("Nome de arquivo restaurado inválido")
                source=self.storage.file_dir/stored_name;encoded=row.get("content_base64")
                if encoded is not None:
                    data=base64.b64decode(encoded,validate=True);candidate=stage/stored_name;candidate.write_bytes(data)
                    if row.get("size") is not None and candidate.stat().st_size!=int(row["size"]):raise ValueError(f"Tamanho inválido para {row.get('name',stored_name)}")
                    if row.get("sha256") and sha256_file(candidate)!=row["sha256"]:raise ValueError(f"SHA-256 inválido para {row.get('name',stored_name)}")
                    staged.append((candidate,stored_name))
                elif source.is_file() and (not row.get("sha256") or sha256_file(source)==row["sha256"]):candidate=stage/stored_name;shutil.copy2(source,candidate);staged.append((candidate,stored_name))
            return stage,staged
        except Exception:shutil.rmtree(stage,ignore_errors=True);raise
    def _insert_compatible(self,table,row,overrides=None):
        columns={r["name"] for r in self.storage.db.execute(f"PRAGMA table_info({table})")};data={k:v for k,v in dict(row).items() if k in columns and k!="id"};data.update(overrides or {})
        cols=list(data);cur=self.storage.db.execute(f"INSERT INTO {table}({','.join(cols)}) VALUES({','.join('?' for _ in cols)})",[data[c] for c in cols]);return cur.lastrowid
    def import_backup(self):
        path=filedialog.askopenfilename(filetypes=[("Backup JSON","*.json")])
        if not path:return
        stage=None;moved=[]
        try:
            loaded=json.loads(Path(path).read_text(encoding="utf-8"));payload=loaded.get("payload") if loaded.get("format")=="biblioteca-de-prompts-backup" else loaded
            if loaded.get("format")=="biblioteca-de-prompts-backup":
                raw=json.dumps(payload,ensure_ascii=False,indent=2);expected=loaded.get("sha256")
                if not expected or not hmac.compare_digest(expected,hashlib.sha256(raw.encode("utf-8")).hexdigest()):raise ValueError("Integridade do backup inválida")
            if not {"projects","prompts","tips","codes"}.issubset(payload):raise ValueError("Formato de backup incompatível")
            if not messagebox.askyesno(APP_NAME,"Os registros serão adicionados em uma transação segura. Continuar?"):return
            stage,staged=self._stage_backup_files(payload);self.storage.db.execute("BEGIN");maps={table:{} for table in CONTENT_TABLES};category_ids={};folder_ids={};collection_ids={}
            for row in payload.get("categories",[]):category_ids[row.get("id")]=self._insert_compatible("categories",row,{"parent_id":None})
            for row in payload.get("categories",[]):
                if row.get("parent_id") in category_ids:self.storage.db.execute("UPDATE categories SET parent_id=? WHERE id=?",(category_ids[row["parent_id"]],category_ids[row.get("id")]))
            for row in payload.get("favorite_folders",[]):
                existing=self.storage.db.execute("SELECT id FROM favorite_folders WHERE name=?",(row.get("name"),)).fetchone();folder_ids[row.get("id")]=existing["id"] if existing else self._insert_compatible("favorite_folders",row)
            for table in ("projects","prompts","tips","codes","knowledge"):
                for row in payload.get(table,[]):
                    overrides={"category_id":category_ids.get(row.get("category_id")),"favorite_folder_id":folder_ids.get(row.get("favorite_folder_id"))}
                    if table in {"prompts","codes"}:overrides["project_id"]=maps["projects"].get(row.get("project_id"))
                    maps[table][row.get("id")]=self._insert_compatible(table,row,overrides)
            for row in payload.get("files",[]):
                original=str(row.get("stored_name") or "")
                if not original:continue
                stored=original
                if self.storage.db.execute("SELECT 1 FROM files WHERE stored_name=?",(stored,)).fetchone() or (self.storage.file_dir/stored).exists():stored=f"{secrets.token_hex(12)}{row.get('extension') or Path(stored).suffix}"
                maps["files"][row.get("id")]=self._insert_compatible("files",row,{"stored_name":stored,"category_id":category_ids.get(row.get("category_id")),"favorite_folder_id":folder_ids.get(row.get("favorite_folder_id"))})
                for candidate,original_name in staged:
                    if original_name==original:target=self.storage.file_dir/stored;candidate.replace(target);moved.append(target);break
            for row in payload.get("prompt_versions",[]):
                pid=maps["prompts"].get(row.get("prompt_id"))
                if pid:self._insert_compatible("prompt_versions",row,{"prompt_id":pid})
            for row in payload.get("relationships",[]):
                source=maps.get(row.get("source_type"),{}).get(row.get("source_id"));target=maps.get(row.get("target_type"),{}).get(row.get("target_id"))
                if source and target:self._insert_compatible("relationships",row,{"source_id":source,"target_id":target})
            for row in payload.get("collections",[]):collection_ids[row.get("id")]=self._insert_compatible("collections",row)
            for row in payload.get("collection_items",[]):
                cid=collection_ids.get(row.get("collection_id"));eid=maps.get(row.get("entity_type"),{}).get(row.get("entity_id"))
                if cid and eid:self._insert_compatible("collection_items",row,{"collection_id":cid,"entity_id":eid})
            for row in payload.get("settings",[]):
                if row.get("key") is not None:self.storage.db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)",(str(row["key"]),str(row.get("value",""))))
            for row in payload.get("trash",[]):
                if row.get("entity_type") in CONTENT_TABLES and row.get("payload") is not None:self._insert_compatible("trash",row)
            for row in payload.get("activity_log",[]):self._insert_compatible("activity_log",row)
            for row in payload.get("search_history",[]):self._insert_compatible("search_history",row)
            self.storage.log_activity("importação","backup",None,Path(path).name,commit=False);self.storage.db.commit();self.refresh_all();messagebox.showinfo(APP_NAME,"Backup importado sem alterar os dados anteriores.")
        except Exception as exc:
            self.storage.db.rollback();messagebox.showerror(APP_NAME,f"Importação cancelada e revertida: {exc}")
            for target in moved:target.unlink(missing_ok=True)
        finally:
            if stage:shutil.rmtree(stage,ignore_errors=True)
    def about(self):
        mode="Portátil" if self.storage.base_dir==application_dir()/"data" else "Padrão"
        messagebox.showinfo(APP_NAME,f"Biblioteca de Prompts {APP_VERSION}\nBuild: {BUILD_DATE}\nModo: {mode}\nSistema: {platform.system()} {platform.release()}\nDados: {self.storage.base_dir}\n\nAplicação local e offline para gestão de conhecimento, sem IA, APIs ou cloud obrigatórias.")



class App(tk.Tk):
    def __init__(self):
        super().__init__(); self.storage=Storage(); self.title(APP_NAME); self.geometry("1200x780"); self.minsize(760,520); self.configure(bg=PALETTE["bg"]); style=ttk.Style(self); style.theme_use("clam")
        try: self.iconbitmap(str(Path(__file__).resolve().parent / "icon.ico"))
        except tk.TclError: pass
        style.configure(".", background=PALETTE["surface"], foreground=PALETTE["text"], font=("Segoe UI", 12)); style.configure("TFrame", background=PALETTE["surface"]); style.configure("LoginShell.TFrame", background=PALETTE["bg"]); style.configure("TLabel", background=PALETTE["surface"], foreground=PALETTE["text"], font=("Segoe UI", 12))
        style.configure("TButton", padding=(13, 8), foreground=PALETTE["text"], background=PALETTE["surface_raised"], bordercolor=PALETTE["border_soft"], font=("Segoe UI", 11)); style.map("TButton", background=[("active", PALETTE["border"]), ("pressed", PALETTE["purple"]), ("focus", PALETTE["border"])], foreground=[("disabled", "#6F6A82")], bordercolor=[("focus", PALETTE["focus"])])
        style.configure("Primary.TButton", background=PALETTE["violet"], foreground=PALETTE["text"], font=("Segoe UI", 11, "bold"), padding=(15, 9)); style.map("Primary.TButton", background=[("active", PALETTE["purple"]), ("pressed", PALETTE["selection"]), ("focus", PALETTE["purple"])])
        style.configure("Quiet.TButton", background=PALETTE["surface"], foreground=PALETTE["muted"], font=("Segoe UI", 10), borderwidth=0); style.map("Quiet.TButton", background=[("active", PALETTE["surface_raised"]), ("pressed", PALETTE["selection"]), ("focus", PALETTE["surface_raised"])], foreground=[("active", PALETTE["text"])])
        style.configure("Danger.TButton", background="#552630", foreground="#FFDADF", font=("Segoe UI", 10, "bold")); style.map("Danger.TButton", background=[("active", PALETTE["danger"]), ("pressed", "#A93F4E"), ("focus", PALETTE["danger"])], foreground=[("active", "#FFFFFF")])
        style.configure("Success.TButton", background="#214B3A", foreground="#B9F5D4", font=("Segoe UI", 10, "bold")); style.map("Success.TButton", background=[("active", PALETTE["success"]), ("pressed", "#2E8B5C")])
        style.configure("Title.TLabel", font=("Segoe UI", 22, "bold"), foreground=PALETTE["pink"]); style.configure("BrandMark.TLabel", font=("Segoe UI Symbol", 40), foreground=PALETTE["cyan"], background=PALETTE["bg"]); style.configure("Hero.TLabel", font=("Segoe UI", 25, "bold"), foreground=PALETTE["text"]); style.configure("Section.TLabel", font=("Segoe UI", 17, "bold"), foreground=PALETTE["text"]); style.configure("Kicker.TLabel", foreground=PALETTE["cyan"], font=("Segoe UI", 9, "bold")); style.configure("Subtitle.TLabel", foreground=PALETTE["muted"], font=("Segoe UI", 12)); style.configure("Muted.TLabel", foreground=PALETTE["muted"], wraplength=760, font=("Segoe UI", 11)); style.configure("CardBody.TLabel", foreground=PALETTE["text"], background=PALETTE["surface_raised"], wraplength=760, font=("Segoe UI", 11)); style.configure("Security.TLabel", font=("Segoe UI", 11, "bold"), foreground=PALETTE["cyan"], background=PALETTE["bg"]); style.configure("FieldLabel.TLabel", foreground=PALETTE["text"], font=("Segoe UI", 11, "bold")); style.configure("Metric.TLabel", font=("Segoe UI", 30, "bold"), foreground=PALETTE["pink"], background=PALETTE["surface_raised"]); style.configure("CardLabel.TLabel", foreground=PALETTE["muted"], background=PALETTE["surface_raised"], font=("Segoe UI", 8, "bold")); style.configure("Link.TButton", foreground=PALETTE["cyan"], background=PALETTE["bg"], borderwidth=0, font=("Segoe UI", 11, "underline")); style.map("Link.TButton", foreground=[("active", PALETTE["pink"]), ("focus", PALETTE["pink"])])
        style.configure("Card.TFrame", background=PALETTE["surface_raised"]); style.configure("CardHover.TFrame", background="#26213F"); style.configure("Inset.TFrame", background=PALETTE["input"]); style.configure("Hero.TFrame", background=PALETTE["surface"]); style.configure("Toolbar.TFrame", background=PALETTE["surface"]); style.configure("Modal.TFrame", background=PALETTE["surface"]); style.configure("FormHint.TLabel", background=PALETTE["surface"], foreground=PALETTE["muted"], font=("Segoe UI", 10)); style.configure("SearchHint.TLabel", background=PALETTE["surface"], foreground=PALETTE["muted"], font=("Segoe UI", 10)); style.configure("Search.TEntry", fieldbackground=PALETTE["input"], foreground=PALETTE["text"], insertcolor=PALETTE["text"], bordercolor=PALETTE["violet"], lightcolor=PALETTE["violet"], darkcolor=PALETTE["border"], padding=12, font=("Segoe UI", 13)); style.map("Search.TEntry", fieldbackground=[("focus", PALETTE["surface_raised"])], bordercolor=[("focus", PALETTE["pink"])], lightcolor=[("focus", PALETTE["pink"])])
        style.configure("LoginBox.TLabelframe", background=PALETTE["surface"], foreground=PALETTE["cyan"], bordercolor=PALETTE["border"]); style.configure("LoginBox.TLabelframe.Label", background=PALETTE["surface"], foreground=PALETTE["cyan"], font=("Segoe UI", 11, "bold")); style.configure("Auth.TEntry", fieldbackground=PALETTE["input"], foreground=PALETTE["text"], insertcolor=PALETTE["text"], bordercolor=PALETTE["border"], lightcolor=PALETTE["focus"], darkcolor=PALETTE["border"], padding=10, font=("Segoe UI", 12)); style.map("Auth.TEntry", fieldbackground=[("focus", PALETTE["input"])], bordercolor=[("focus", PALETTE["focus"])], lightcolor=[("focus", PALETTE["focus"])])
        style.configure("TEntry", fieldbackground=PALETTE["input"], foreground=PALETTE["text"], insertcolor=PALETTE["text"], bordercolor=PALETTE["border"], lightcolor=PALETTE["focus"], darkcolor=PALETTE["border"], padding=9, font=("Segoe UI", 11)); style.map("TEntry", fieldbackground=[("focus", PALETTE["input"])], bordercolor=[("focus", PALETTE["focus"])], lightcolor=[("focus", PALETTE["focus"])])
        style.configure("TCombobox", fieldbackground=PALETTE["input"], background=PALETTE["input"], foreground=PALETTE["text"], arrowcolor=PALETTE["cyan"], bordercolor=PALETTE["border"], lightcolor=PALETTE["focus"], darkcolor=PALETTE["border"], padding=9, font=("Segoe UI", 11)); style.map("TCombobox", fieldbackground=[("readonly", PALETTE["input"]), ("focus", PALETTE["input"])], foreground=[("readonly", PALETTE["text"])], bordercolor=[("focus", PALETTE["focus"])], lightcolor=[("focus", PALETTE["focus"])])
        style.layout("Hidden.TNotebook.Tab", []); style.configure("Hidden.TNotebook", background=PALETTE["bg"], borderwidth=0); style.configure("TNotebook", background=PALETTE["bg"], borderwidth=0, tabmargins=(0, 0, 0, 0)); style.configure("TNotebook.Tab", background=PALETTE["surface"], foreground=PALETTE["muted"], padding=(16, 10), borderwidth=0, lightcolor=PALETTE["surface"], darkcolor=PALETTE["surface"], font=("Segoe UI", 10, "bold")); style.map("TNotebook.Tab", background=[("selected", PALETTE["surface_raised"]), ("active", PALETTE["surface_raised"])], foreground=[("selected", PALETTE["pink"]), ("active", PALETTE["text"])], lightcolor=[("selected", PALETTE["surface_raised"])], darkcolor=[("selected", PALETTE["surface_raised"])])
        style.configure("Treeview", background=PALETTE["surface"], fieldbackground=PALETTE["surface"], foreground=PALETTE["text"], rowheight=40, font=("Segoe UI", 11), borderwidth=0, relief="flat"); style.configure("Treeview.Heading", background=PALETTE["surface"], foreground=PALETTE["muted"], font=("Segoe UI", 10, "bold"), padding=(10, 11), relief="flat", borderwidth=0); style.map("Treeview", background=[("selected", PALETTE["selection"]), ("focus", PALETTE["selection"])], foreground=[("selected", PALETTE["text"])])
        self.protocol("WM_DELETE_WINDOW",self.quit_app)
        if self.storage.setting("password_hash"):
            self.show_login()
        else:
            self.login(self.storage.setting("username", "Usuário local"))
    def clear(self):
        for w in self.winfo_children(): w.destroy()
    def show_login(self): self.clear(); LoginFrame(self,self.login).pack(fill="both",expand=True)
    def login(self,user): self.clear(); MainApp(self,user,self.show_login).pack(fill="both",expand=True)
    def quit_app(self): self.storage.close(); self.destroy()

if __name__ == "__main__": App().mainloop()
