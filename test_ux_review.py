import tempfile
from pathlib import Path
from tkinter import ttk
import app


def descendants(widget):
    yield widget
    for child in widget.winfo_children():
        yield from descendants(child)


with tempfile.TemporaryDirectory() as tmp:
    app.APP_DIR = Path(tmp)
    window = app.App()
    main = next(child for child in window.winfo_children() if isinstance(child, app.MainApp))
    window.update_idletasks()

    # A busca permanece simples: os controles avançados não competem com ela.
    search_frame = main.search.master
    assert not any(isinstance(child, ttk.Button) for child in search_frame.winfo_children())
    assert main.search.winfo_exists()
    stamp = app.now()
    main.storage.db.execute("INSERT INTO prompts(name,category,tool,tags,usage_count,content,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)", ("Card de validação", "QA", "GPT", "teste, ux", 7, "conteúdo", stamp, stamp))
    main.storage.db.commit(); main.refresh_all(); window.update_idletasks()
    assert any("text" in child.keys() and child.cget("text") == "Card de validação" for child in descendants(main.prompt_cards_frame))

    labels = {child.cget("text") for child in main.sidebar.winfo_children() if "text" in child.keys()}
    assert {"✎  Prompts", "▣  Projetos", "★  Favoritos", "◷  Recentes", "↗  Repositórios", "⚙  Configurações"}.issubset(labels)

    more = main.advanced_menu
    menu = window.nametowidget(more.cget("menu"))
    menu_labels = {menu.entrycget(i, "label") for i in range(menu.index("end") + 1) if menu.type(i) != "separator"}
    assert {"Governança", "Wiki", "Templates", "Coleções", "Códigos", "Configurações", "Diagnóstico", "Relatórios", "Lixeira", "Filtros de busca", "Histórico de buscas", "Limpar busca"}.issubset(menu_labels)

    # Ações secundárias foram movidas para o menu contextual da toolbar.
    project_toolbar = main.projects.pack_slaves()[0]
    toolbar_more = next(child for child in descendants(project_toolbar) if isinstance(child, ttk.Menubutton))
    toolbar_menu = window.nametowidget(toolbar_more.cget("menu"))
    toolbar_labels = {toolbar_menu.entrycget(i, "label") for i in range(toolbar_menu.index("end") + 1) if toolbar_menu.type(i) != "separator"}
    assert {"Relações", "Duplicar", "Exportar coleção"}.issubset(toolbar_labels)

    captured = []
    def inspect_form(win):
        captured.append({w.cget("text") for w in descendants(win) if isinstance(w, ttk.Button)})
        win.destroy()

    main.wait_window = inspect_form
    main.form("Projeto", [("name", "Nome", "entry", None)], None, "Salvar")
    main.form("Projeto", [("name", "Nome", "entry", None)], {"name": "Existente"}, "Alterar")
    assert {"Salvar", "Cancelar"}.issubset(captured[0])
    assert {"Alterar", "Cancelar"}.issubset(captured[1])

    main.set_type_filter("Prompts")
    assert main.type_filter.get() == "Prompts"
    window.quit_app()
print("UX_REVIEW_TESTS_OK")
