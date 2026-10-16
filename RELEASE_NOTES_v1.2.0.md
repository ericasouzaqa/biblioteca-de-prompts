# Biblioteca de Prompts v1.2.0 — Variáveis e produtividade local

A Spark Library v1.2.0 adiciona uma camada completa de preparação e reutilização de prompts sem abandonar o funcionamento offline-first.

## Principais melhorias

A aplicação agora reconhece variáveis no formato `{{NOME_VARIAVEL}}`. O Preview identifica os campos, permite informar valores e mostra o prompt final renderizado antes da cópia. Variáveis não preenchidas continuam visíveis, evitando perda silenciosa de contexto.

O Prompt Playground oferece um ambiente local para escrever, testar variáveis e copiar resultados sem persistir automaticamente e sem chamar IA.

O novo Dashboard apresenta total de prompts, favoritos, uso acumulado, uso nos últimos 30 dias, prompts mais utilizados, categorias mais utilizadas e uso diário por período. As métricas são derivadas do SQLite e do histórico local de cópias.

Os filtros avançados agora cobrem categoria, ferramenta, tags, favoritos, status, templates e intervalo de datas. O intercâmbio de prompts suporta exportação e importação em JSON, Markdown e ZIP. Pacotes ZIP contêm uma versão estruturada JSON e uma versão legível Markdown.

## Compatibilidade

SQLite, backups, restore, histórico, favoritos e repositórios foram preservados. A importação nunca sobrescreve registros existentes: cria cópias com novos IDs e a marca `(importado)`. Não houve migration destrutiva e não foram adicionadas APIs, IA, tokens ou serviços externos.

## Validação

```text
STORAGE_TESTS_OK
GUI_SMOKE_OK
REGRESSION_TESTS_OK
PRODUCTION_MODE_TESTS_OK
UX_REVIEW_TESTS_OK
V120_TESTS_OK
git diff --check
```

## Documentação

- [Plano técnico](docs/PLANO_TECNICO_v1.2.0.md)
- [Wireframes Mermaid](docs/wireframes_v1.2.0.mmd)
- [Relatório final](RELATORIO_IMPLEMENTACAO_FINAL.md)
