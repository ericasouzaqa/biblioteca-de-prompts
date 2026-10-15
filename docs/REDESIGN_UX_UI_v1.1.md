# Redesign UX/UI — Biblioteca de Prompts v1.1

## 1. Direção do produto

A Biblioteca de Prompts foi reposicionada como um espaço local de trabalho para profissionais que usam IA diariamente. A interface prioriza retomada, busca e organização; não depende de IA, APIs, chaves, internet ou serviços externos durante a execução.

A experiência adota uma linguagem visual premium de produto desktop moderno: dark mode nativo, superfícies discretas, tipografia clara, destaque índigo e hierarquia baseada em espaço e peso tipográfico — não em bordas excessivas.

## 2. Wireframe da nova estrutura

```text
┌──────────────────────┬──────────────────────────────────────────────────────┐
│ ✦ Biblioteca         │ Biblioteca de Prompts                 [+ Novo Prompt] │
│                      │ Organize seu contexto. Retome seu trabalho.         │
│ ✎ Prompts           │                                                      │
│ ▣ Projetos          │  ⌕  Pesquisar prompts, projetos ou categorias...  •••│
│ ★ Favoritos         │                                                      │
│ ◷ Recentes          │  ┌────────────── Prompts ────────────────┐           │
│ ↗ Repositórios      │  │  Card                    Card          │           │
│                      │  │  Nome                    Nome          │           │
│ ─────────────────── │  │  Categoria • Ferramenta  Tags          │           │
│ ⚙ Configurações    │  │  Uso • Atualização       ☆ Abrir        │           │
│                      │  └───────────────────────────────────────┘           │
│ OFFLINE • LOCAL     │                                                      │
└──────────────────────┴──────────────────────────────────────────────────────┘
```

## 3. Mockup implementado

O mockup funcional está implementado diretamente no aplicativo Tkinter e pode ser visualizado em:

- [Mockup da Home redesenhada](../screenshots_redesign_home.png)
- [Mockup com cards preenchidos](../screenshots_redesign_cards.png)

A tela implementada contém sidebar persistente, cabeçalho com ação primária, busca com ícone interno, menu de recursos secundários e biblioteca em cards com rolagem.

## 4. Paleta de cores

| Token | Hex | Aplicação |
|---|---|---|
| Background | `#0F1117` | Área principal |
| Sidebar | `#161A23` | Navegação lateral |
| Surface | `#1D2330` | Toolbars e superfícies |
| Surface raised | `#222A39` | Cards e menus |
| Border | `#2A3344` | Divisores discretos |
| Texto primário | `#FFFFFF` | Títulos e conteúdo |
| Texto secundário | `#A8B3C7` | Metadados e navegação |
| Accent | `#6366F1` | Ações primárias e foco |
| Hover | `#818CF8` | Estados ativos |
| Sucesso | `#22C55E` | Confirmações |
| Erro | `#EF4444` | Exclusões e falhas |

## 5. Sistema de componentes

**Sidebar.** Marca do produto, cinco destinos operacionais, separador e Configurações. O rodapé comunica o modo offline/local.

**Header.** Título, subtítulo orientado à retomada e uma única ação primária: Novo Prompt.

**Campo de busca.** Ícone interno, fundo sutil, foco índigo, texto legível e menu de filtros avançados separado da digitação.

**Prompt card.** Nome, categoria, ferramenta, tags, uso, atualização, favorito e ação Abrir. O card é a unidade principal de leitura e seleção.

**Toolbar.** Novo, Editar e Excluir permanecem disponíveis; operações menos frequentes ficam em ⋯ Mais ações.

**Menus.** Recursos secundários continuam acessíveis sem ocupar permanentemente a área de trabalho: Governança, Wiki, Templates, Coleções, Códigos, Diagnóstico, Relatórios, Lixeira, filtros e histórico.

**Tabela legada.** Continua montada internamente para compatibilidade com CRUDs, seleção, edição, exclusão, favoritos e testes, mas não é exibida na visualização principal de Prompts.

## 6. Fluxo de navegação

1. O aplicativo abre diretamente na biblioteca de Prompts.
2. O usuário pode pesquisar imediatamente ou selecionar Novo Prompt.
3. Cards exibem o contexto essencial sem exigir abertura de uma tabela.
4. Abrir leva ao formulário existente, preservando edição e histórico.
5. Favoritos e Recentes continuam acessíveis pela sidebar.
6. Projetos e Repositórios continuam como áreas independentes.
7. Configurações fica na sidebar; recursos de menor frequência ficam em Mais.
8. Backup, restore, diagnóstico, relatórios e lixeira continuam locais e acessíveis.

## 7. Justificativa UX

**Sidebar persistente:** reduz custo de navegação e cria um mapa mental estável.

**Cards em vez de tabela:** melhora escaneabilidade e permite que cada prompt seja lido como uma unidade de trabalho, mantendo os metadados essenciais visíveis.

**Uma ação primária:** Novo Prompt recebe destaque; Editar e Excluir permanecem contextuais para reduzir competição visual.

**Busca separada dos filtros:** a digitação fica direta e os recursos avançados não desaparecem — apenas deixam de dominar a primeira leitura.

**Tipografia e espaçamento:** hierarquia visual substitui contornos pesados, melhorando leitura e sensação de produto premium.

**Compatibilidade:** o armazenamento SQLite, o schema legado, os CRUDs, o histórico, os favoritos, os backups e o restore não foram descartados. A camada de cards usa a mesma fonte de dados local.

## 8. Independência operacional

O redesenho não introduz dependência de IA em tempo de execução. Não há chamadas a modelos, APIs, tokens, internet, geração remota ou serviços externos. O funcionamento permanece previsível, local e offline-first.

## 9. Validação

A suíte aprovada para esta revisão contém compilação, armazenamento, GUI, regressão, modo produção, navegação da sidebar, menus, cards, formulários e verificação de whitespace:

```text
STORAGE_TESTS_OK
GUI_SMOKE_OK
REGRESSION_TESTS_OK
PRODUCTION_MODE_TESTS_OK
UX_REVIEW_TESTS_OK
git diff --check
```


## 10. Propostas de identidade visual

Foram consideradas quatro direções para substituir o ícone anterior:

1. **Sparkles minimalistas:** duas estrelas sobre uma superfície índigo, comunicando velocidade e inteligência.
2. **Biblioteca inteligente:** livro aberto com páginas organizadas e um brilho no topo.
3. **IA + Organização:** páginas estruturadas com um ponto de conexão, sugerindo conhecimento aplicado.
4. **Prompt Hub:** cartão central com faísca, representando um ponto de entrada para prompts reutilizáveis.

A proposta selecionada para a implementação é **Spark Library**: um livro digital em índigo com linhas organizadas, uma faísca branca e um ponto verde de status. O ativo está versionado em `assets/logo_spark_library.svg`, acompanhado por PNG, favicon e ICO Windows.
