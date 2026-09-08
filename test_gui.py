import tempfile
from pathlib import Path
import app

with tempfile.TemporaryDirectory() as tmp:
    app.APP_DIR = Path(tmp)
    window = app.App()
    assert window.title() == app.APP_NAME
    assert window.storage.db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    window.quit_app()
print("GUI_SMOKE_OK")
