import tempfile
from app import Storage

with tempfile.TemporaryDirectory() as tmp:
    storage = Storage(tmp)
    assert storage.db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert storage.db.execute("SELECT COUNT(*) FROM tips").fetchone()[0] >= 1
    tables = {row["name"] for row in storage.db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"projects", "prompts", "files", "trash", "prompt_versions", "activity_log"}.issubset(tables)
    # Registros legados de autenticação não são apagados durante a atualização.
    storage.set_setting("username", "legado")
    storage.set_setting("password_hash", "legado-preservado")
    assert storage.setting("username") == "legado"
    assert storage.setting("password_hash") == "legado-preservado"
    storage.db.execute("INSERT INTO projects(name,status,created_at,updated_at) VALUES(?,?,?,?)", ("Projeto Teste", "Ativo", "2025-01-01 00:00:00", "2025-01-01 00:00:00"))
    project_id = storage.db.execute("SELECT last_insert_rowid()").fetchone()[0]
    storage.db.execute("INSERT INTO prompts(name,content,project_id,favorite,created_at,updated_at) VALUES(?,?,?,?,?,?)", ("Prompt Teste", "Conteúdo", project_id, 1, "2025-01-01 00:00:00", "2025-01-01 00:00:00"))
    storage.db.commit()
    assert storage.db.execute("SELECT COUNT(*) FROM prompts WHERE project_id=? AND favorite=1", (project_id,)).fetchone()[0] == 1
    storage.close()
print("STORAGE_TESTS_OK")
