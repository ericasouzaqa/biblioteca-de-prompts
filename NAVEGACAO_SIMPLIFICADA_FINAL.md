# Navegação simplificada final

**Estado:** candidato interno, não publicado
**Data:** 2026-09-24

## Navegação principal visível

A barra principal agora exibe exatamente:

- Projetos
- Prompts
- Repositórios
- Favoritos
- Recentes
- Mais

Evidência visual: [navigation-final.png](</home/ubuntu/biblioteca-de-prompts/screenshots/navigation-final.png>).

## Menu Mais

O menu **Mais** contém os acessos secundários:

- Governança
- Wiki
- Templates
- Coleções
- Códigos
- Configurações
- Diagnóstico
- Relatórios
- Lixeira

As telas internas continuam existentes no notebook da aplicação e podem ser selecionadas pelos comandos existentes. Apenas a composição visível da navegação foi alterada.

## Preservação

Não foram alterados:

- estilos visuais;
- cores;
- tipografia;
- cards;
- Home;
- busca;
- banco de dados;
- persistência;
- backup;
- restore;
- histórico;
- regras de negócio;
- funcionalidades existentes.

A única mudança desta etapa foi a composição da navegação principal e o ajuste de expansão do conteúdo para acomodar a barra simplificada.

## Validação

| Verificação | Resultado |
|---|---|
| Inicialização | `GUI_SMOKE_OK` |
| Persistência / SQLite | `STORAGE_TESTS_OK` |
| Regressões | `REGRESSION_TESTS_OK` |
| Sintaxe | `py_compile` passou |
| Navegação pelas telas internas preservadas | 10 tabs confirmadas |
| Projetos | Seleção e renderização confirmadas |
| Prompts | Seleção e renderização confirmadas |
| Repositórios | Seleção e renderização confirmadas |
| Favoritos | Comando e filtro confirmados |
| Recentes | Retorno à Home confirmado |
| Busca | Campo focado e placeholder preservado |
| Integridade do diff | `git diff --check` passou |

Não houve commit, release, deploy ou publicação.
