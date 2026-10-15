import tempfile
from pathlib import Path
import app

with tempfile.TemporaryDirectory() as tmp:
    app.APP_DIR = Path(tmp)
    window = app.App()
    main = next(child for child in window.winfo_children() if isinstance(child, app.MainApp))
    assert not any(child.__class__.__name__ == "LoginFrame" for child in window.winfo_children())
    window.update_idletasks()
    assert str(main.tabs.select()) == str(main.prompts)
    assert main.search.winfo_exists()
    assert main.home_favorites.winfo_exists()
    assert main.home_recent.winfo_exists()
    main.search_var.set("projeto")
    assert main.query("projects") == []
    main.favorite_filter.set(True)
    assert main.query("prompts") == []
    window.quit_app()
print("REGRESSION_TESTS_OK")
