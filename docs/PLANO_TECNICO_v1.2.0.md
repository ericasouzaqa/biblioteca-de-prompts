# Plano técnico — Spark Library v1.2.0

## Objetivo

Evoluir a Biblioteca de Prompts para uma estação local de trabalho com renderização de variáveis, Preview, Playground, métricas e intercâmbio de prompts, sem alterar o contrato do SQLite ou introduzir serviços externos.

## Arquitetura preservada

A aplicação continua monolítica desktop em Python/Tkinter com `Storage` como camada SQLite local e `MainApp` como camada de interface. A v1.2.0 usa somente consultas SQL locais, widgets Tkinter e a biblioteca padrão do Python.

Não serão criadas APIs, chamadas a modelos, tokens, dependências de rede ou serviços de IA em runtime.

## Entregas técnicas

### 1. Variáveis e Preview

- Sintaxe reconhecida: `{{NOME_VARIAVEL}}`.
- Regex local identifica nomes em caixa alta, números e underscore.
- Preview extrai variáveis únicas, cria campos de entrada e renderiza o texto em tempo real.
- Variáveis não preenchidas continuam visíveis como `{{NOME}}` para evitar perda silenciosa de contexto.
- Copiar o resultado renderizado incrementa `usage_count` e mantém o histórico de uso existente.

### 2. Prompt Playground

- Janela local independente para experimentar um texto sem salvá-lo.
- Editor à esquerda, variáveis no centro e resultado renderizado à direita.
- Copiar resultado disponível sem depender de prompt persistido.
- O Playground não grava automaticamente no SQLite.

### 3. Dashboard

- Nova aba local com total de prompts, favoritos, uso total e uso nos últimos 30 dias.
- Ranking dos prompts mais utilizados.
- Ranking das categorias mais utilizadas por soma de `usage_count`.
- Série diária de uso baseada em `activity_log` e nos eventos locais de cópia.
- Métricas recalculadas a cada refresh; nenhuma tabela destrutiva ou migration necessária.

### 4. Filtros avançados

- Categoria via `category_id`.
- Ferramenta via `tool`.
- Tags via correspondência local normalizada.
- Favoritos via `favorite=1`.
- Período via `date(created_at)`.
- Filtros continuam disponíveis no menu secundário e refletem no resumo da busca.

### 5. Importação e exportação

- Pacote de prompts em JSON, Markdown e ZIP.
- ZIP contém JSON estruturado e Markdown legível.
- Importação cria cópias com sufixo `(importado)` e IDs novos.
- O backup completo existente continua separado e preserva restauração transacional.
- Nenhum arquivo ou registro existente é sobrescrito.

## Migração e compatibilidade

A v1.2.0 não exige nova coluna. A coluna `usage_count` criada na v1.1.0 continua sendo usada. O schema legado, backups, históricos, favoritos e repositórios permanecem intactos. Qualquer extensão futura de schema deverá seguir `ALTER TABLE` aditivo e backup preventivo existente.

## Critérios de aceite

- Prompt com duas variáveis gera dois campos e renderiza o resultado.
- Variável ausente não desaparece silenciosamente.
- Playground funciona sem rede e sem persistência automática.
- Dashboard mostra métricas coerentes após cópia local.
- Filtros combinados retornam apenas os registros esperados.
- JSON, Markdown e ZIP exportam e importam prompts sem sobrescrever dados.
- Suíte anterior permanece aprovada e novos testes cobrem a v1.2.0.
