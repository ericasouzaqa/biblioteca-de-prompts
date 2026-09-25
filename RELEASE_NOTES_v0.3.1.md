# v0.3.1 — Simplificação Radical da Experiência

## Resumo

A versão 0.3.1 transforma a Biblioteca de Prompts em uma experiência mais direta para o trabalho diário. A navegação principal passa a destacar Projetos, Prompts, Repositórios, Favoritos e Recentes, enquanto recursos de baixa frequência ficam organizados no menu Mais.

A Home deixa de priorizar indicadores administrativos e passa a responder às perguntas mais importantes para a retomada: onde estou, onde parei e qual é o próximo passo. A busca global recebe destaque para localizar rapidamente projetos, prompts e repositórios.

## Destaques

| Área | Resultado |
|---|---|
| Navegação | Projetos, Prompts, Repositórios, Favoritos, Recentes e Mais ficam no primeiro nível. |
| Home | Foco em continuidade do trabalho, contexto atual e próximo passo. |
| Busca | Campo global destacado com o placeholder “Pesquisar projetos, prompts ou repositórios...”. |
| Interface | Hierarquia visual, espaçamento, foco, hover e superfícies refinados. |
| Áreas avançadas | Governança, Wiki, Templates, Coleções, Códigos, Configurações, Diagnóstico, Relatórios e Lixeira ficam em Mais. |

## Compatibilidade e migração

Não é necessária nenhuma migração para a v0.3.1. Não houve alteração de banco de dados, schema ou persistência. A versão é compatível com os dados existentes e com os backups existentes.

Os fluxos de backup e restore permanecem preservados. Recursos avançados continuam disponíveis; a mudança principal é a organização da navegação e a prioridade visual da experiência.

## Validação

A candidata foi validada com compilação Python, testes de armazenamento, testes de regressão, smoke test de GUI, navegação direcionada, foco da busca, favoritos, recentes e abertura de telas principais. Todas as validações executadas passaram.

## Status de publicação

Este documento acompanha a publicação da v0.3.1.
