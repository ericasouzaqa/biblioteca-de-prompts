import json
import tempfile
from pathlib import Path
from app import Storage, hash_password, verify_password

with tempfile.TemporaryDirectory() as tmp:
    storage = Storage(tmp)
    assert storage.db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert storage.db.execute("SELECT COUNT(*) FROM tips").fetchone()[0] >= 1
    stored = hash_password("senha-segura")
    assert verify_password("senha-segura", stored)
    assert not verify_password("senha-incorreta", stored)
    storage.set_setting("username", "erica")
    storage.set_setting("email", "erica@example.test")
    token = storage.issue_reset_token("erica@example.test")
    assert token and storage.reset_password(token, "nova-senha")
    assert verify_password("nova-senha", storage.setting("password_hash"))
    assert not storage.reset_password(token, "outra-senha")
    storage.db.execute("INSERT INTO projects(name,status,created_at,updated_at) VALUES(?,?,?,?)", ("Projeto Teste", "Ativo", "2025-01-01 00:00:00", "2025-01-01 00:00:00"))
    project_id = storage.db.execute("SELECT last_insert_rowid()").fetchone()[0]
    storage.db.execute("INSERT INTO prompts(name,content,project_id,created_at,updated_at) VALUES(?,?,?,?,?)", ("Prompt Teste", "Conteúdo", project_id, "2025-01-01 00:00:00", "2025-01-01 00:00:00"))
    storage.db.commit()
    assert storage.db.execute("SELECT COUNT(*) FROM prompts WHERE project_id=?", (project_id,)).fetchone()[0] == 1
    storage.close()
print("STORAGE_TESTS_OK")
