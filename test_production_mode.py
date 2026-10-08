import json
import tempfile
from pathlib import Path
import app

with tempfile.TemporaryDirectory() as tmp:
    app.APP_DIR = Path(tmp)
    window = app.App()
    main = next(child for child in window.winfo_children() if isinstance(child, app.MainApp))
    assert isinstance(main, app.MainApp)
    window.update_idletasks()
    assert str(main.tabs.select()) == str(main.dashboard)

    created = app.now()
    main.storage.db.execute(
        "INSERT INTO prompts(name,content,favorite,created_at,updated_at) VALUES(?,?,?,?,?)",
        ("Prompt de Produção", "Conteúdo de validação", 1, created, created),
    )
    main.storage.db.commit()
    main.refresh_all()
    main.search_var.set("Produção")
    assert main.query("prompts")[0]["name"] == "Prompt de Produção"
    main.favorite_filter.set(True)
    assert main.query("prompts")[0]["favorite"] == 1

    backup = Path(tmp) / "backup.json"
    app.filedialog.asksaveasfilename = lambda **kwargs: str(backup)
    app.messagebox.askyesno = lambda *args, **kwargs: True
    app.messagebox.showinfo = lambda *args, **kwargs: None
    main.export_backup()
    envelope = json.loads(backup.read_text(encoding="utf-8"))
    assert envelope["format"] == "biblioteca-de-prompts-backup"
    assert envelope["payload"]["prompts"]

    main.storage.db.execute("DELETE FROM prompts WHERE name=?", ("Prompt de Produção",))
    main.storage.db.commit()
    app.filedialog.askopenfilename = lambda **kwargs: str(backup)
    main.import_backup()
    assert main.storage.db.execute("SELECT COUNT(*) FROM prompts WHERE name=?", ("Prompt de Produção",)).fetchone()[0] >= 1
    assert main.storage.db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    window.quit_app()
print("PRODUCTION_MODE_TESTS_OK")
