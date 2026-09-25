# Changelog

## [0.3.1] — Simplificação Radical da Experiência

### Alterado

- Nova navegação principal reduzida a Projetos, Prompts, Repositórios, Favoritos, Recentes e Mais.
- Áreas avançadas reorganizadas no menu Mais: Governança, Wiki, Templates, Coleções, Códigos, Configurações, Diagnóstico, Relatórios e Lixeira.
- Home orientada à continuidade do trabalho, com contexto do projeto, ponto de parada, próximo passo, prompt utilizado e repositório relacionado.
- Busca global destacada para localizar projetos, prompts e repositórios.
- Interface refinada com melhor hierarquia visual, superfícies elevadas, espaçamento, foco, hover e menor densidade de informação.
- Listas de Projetos, Prompts e Repositórios com leitura mais limpa, preservando as ações existentes.

### Preservado

- SQLite, schema e persistência existentes.
- Dados existentes e compatibilidade com backups existentes.
- Backup e restore.
- Histórico, lixeira, governança, Wiki, templates, coleções, códigos, relatórios e diagnóstico.
- Atalhos de teclado, regras de negócio e fluxos existentes.

### Migração

- Nenhuma migração necessária.
- Nenhuma alteração de banco de dados.
- Nenhuma alteração no formato de backup.
- Compatível com dados existentes.
- Compatível com backups existentes.

### Validação

- `python3 -m py_compile app.py` — passou.
- `python3 test_storage.py` — `STORAGE_TESTS_OK`.
- `python3 test_regressions.py` — `REGRESSION_TESTS_OK`.
- `xvfb-run -a python3 test_gui.py` — `GUI_SMOKE_OK`.
- Validação direcionada de navegação — `NAVIGATION_ONLY_OK`.
- `git diff --check` — passou.
