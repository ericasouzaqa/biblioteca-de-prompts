import tempfile
from pathlib import Path
import app

with tempfile.TemporaryDirectory() as tmp:
    storage = app.Storage(tmp)
    storage.db.execute("INSERT INTO projects(name,status,created_at,updated_at) VALUES(?,?,?,?)", ("Projeto", "Ativo", app.now(), app.now()))
    storage.db.commit()
    storage.close()

with tempfile.TemporaryDirectory() as tmp:
    app.APP_DIR = Path(tmp)
    window = app.App()
    window.login("tester")
    main = next(child for child in window.winfo_children() if isinstance(child, app.MainApp))
    main.search_var.set("projeto")
    assert main.query("projects") == []
    main.search_var.set("teste")
    main.destroy()
    window.quit_app()
print("REGRESSION_TESTS_OK")
