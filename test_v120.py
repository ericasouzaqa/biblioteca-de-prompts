import json
import tempfile
import zipfile
from pathlib import Path
import app

assert app.prompt_variables("Olá {{NOME}}, use {{NOME}} em {{PROJETO_1}}.") == ["NOME", "PROJETO_1"]
assert app.render_prompt("Olá {{NOME}} — {{AUSENTE}}", {"NOME": "Erica"}) == "Olá Erica — {{AUSENTE}}"

with tempfile.TemporaryDirectory() as tmp:
    app.APP_DIR = Path(tmp)
    storage = app.Storage(tmp)
    stamp = app.now()
    storage.db.execute("INSERT INTO prompts(name,category,tool,tags,favorite,usage_count,content,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)", ("Prompt Métrica", "QA", "ChatGPT", "teste, v120", 1, 5, "Olá {{NOME}}", stamp, stamp))
    storage.db.execute("INSERT INTO activity_log(action,entity_type,entity_id,details,created_at) VALUES(?,?,?,?,?)", ("cópia", "prompts", 1, "Olá Erica", stamp))
    storage.db.commit()
    metrics = storage.prompt_metrics()
    assert metrics["total"] == 1 and metrics["favorites"] == 1 and metrics["usage"] == 5
    assert metrics["top_prompts"][0]["name"] == "Prompt Métrica"
    storage.close()

with tempfile.TemporaryDirectory() as tmp:
    app.APP_DIR = Path(tmp)
    window = app.App()
    main = next(child for child in window.winfo_children() if isinstance(child, app.MainApp))
    assert main.metrics_dashboard.winfo_exists() and main.playground.winfo_exists()
    main.playground_editor.insert("1.0", "Olá {{NOME}}")
    main.refresh_playground()
    assert "NOME" in main.playground_values
    main.playground_values["NOME"].set("Erica")
    assert main.playground_result.get("1.0", "end-1c") == "Olá Erica"
    stamp = app.now()
    main.storage.db.execute("INSERT INTO prompts(name,category,tool,tags,content,created_at,updated_at) VALUES(?,?,?,?,?,?,?)", ("Prompt Métrica", "QA", "ChatGPT", "teste", "conteúdo", stamp, stamp))
    main.storage.db.commit(); main.refresh_all(); main.search_var.set("Métrica")
    main.tool_filter.set("ChatGPT")
    assert main.query("prompts")[0]["name"] == "Prompt Métrica"
    window.quit_app()

with tempfile.TemporaryDirectory() as tmp:
    app.APP_DIR = Path(tmp)
    window = app.App(); main = next(child for child in window.winfo_children() if isinstance(child, app.MainApp))
    stamp = app.now(); main.storage.db.execute("INSERT INTO prompts(name,content,created_at,updated_at) VALUES(?,?,?,?)", ("Exportável", "Texto {{VAR}}", stamp, stamp)); main.storage.db.commit(); main.refresh_all()
    main.prompt_tree.selection_set("1")
    output = Path(tmp) / "prompts.zip"
    app.filedialog.asksaveasfilename = lambda **kwargs: str(output)
    app.messagebox.askyesno = lambda *args, **kwargs: True
    app.messagebox.showinfo = lambda *args, **kwargs: None
    main.export_prompt_package()
    with zipfile.ZipFile(output) as bundle:
        payload = json.loads(bundle.read("prompts.json"))
        assert payload["prompts"]
        assert "Texto {{VAR}}" in bundle.read("prompts.md").decode()
    markdown_output = Path(tmp) / "prompts.md"
    app.filedialog.asksaveasfilename = lambda **kwargs: str(markdown_output)
    main.export_prompt_package()
    assert "Texto {{VAR}}" in markdown_output.read_text(encoding="utf-8")
    before = main.storage.db.execute("SELECT COUNT(*) FROM prompts").fetchone()[0]
    app.filedialog.askopenfilename = lambda **kwargs: str(markdown_output)
    main.import_prompt_package()
    assert main.storage.db.execute("SELECT COUNT(*) FROM prompts").fetchone()[0] == before + 1
    window.quit_app()

print("V120_TESTS_OK")
