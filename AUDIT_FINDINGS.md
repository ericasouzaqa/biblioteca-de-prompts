# Auditoria inicial — Biblioteca de Prompts

## Arquitetura encontrada

O repositório é uma aplicação desktop Python/Tkinter de arquivo único (`app.py`), sem frontend web, sem backend HTTP, sem rotas, sem componentes separados e sem suíte de testes versionada. O armazenamento é SQLite local em `~/.central-de-prompts/central.db`, com as tabelas `settings`, `projects`, `prompts`, `tips` e `codes`. A autenticação é local, de usuário único, com senha derivada por `hashlib.scrypt`.

## Funcionalidades existentes

A aplicação possui login/logout, criação inicial de usuário, CRUD de projetos/prompts/dicas/códigos, pesquisa textual global, favoritos de prompts, cópia para clipboard, exportação/importação JSON, alteração de senha e build Windows via GitHub Actions/PyInstaller.

## Lacunas em relação à especificação

Não existem dashboard, filtros estruturados, recuperação de senha, módulo de arquivos, upload/download, visualização de metadados de arquivos, identidade visual solicitada, componentes responsivos para tablet/mobile, imagens de referência no repositório, testes automatizados ou frontend compatível com GitHub Pages. O campo `homepageUrl` aponta para GitHub Pages, mas o repositório não contém `index.html` ou uma aplicação web publicada.

## Riscos identificados

1. O importador de backup insere diretamente várias tabelas sem transação explícita; uma falha intermediária pode deixar o banco parcialmente importado.
2. O importador não preserva IDs e não remapeia relações entre projetos e prompts/códigos, podendo quebrar associações ao restaurar um backup.
3. O importador aceita chaves vindas do JSON sem uma lista estrita de colunas, aumentando o risco de erro ou incompatibilidade futura.
4. Não há cópia automática do banco antes de migrações ou importações.
5. A tabela de arquivos não existe; qualquer implementação ingênua poderia alterar tabelas existentes sem preservar dados.
6. A recuperação de senha por e-mail não pode funcionar offline sem serviço externo; ela deve ser implementada como recuperação local segura e opcionalmente documentar o adaptador de e-mail.
7. A interface usa janelas fixas, `Treeview` sem adaptação móvel e formulários de altura fixa, portanto não atende tablet/mobile nem todas as resoluções pequenas.

## Estratégia de atualização

A atualização deve ser incremental e compatível: manter as cinco tabelas atuais e adicionar apenas tabelas novas (`files`, `password_reset_tokens`, `categories` se necessário) com migrações idempotentes. Antes de qualquer alteração de esquema, criar backup automático do SQLite; executar migrações em transação; validar integridade com `PRAGMA integrity_check`; e manter exportação JSON compatível com o formato atual. O importador deve fazer pré-validação, preservar relações por mapeamento de IDs e usar rollback integral em caso de falha.

Não há banco local de usuário presente neste ambiente; portanto, nenhuma informação pessoal disponível na sandbox foi lida ou alterada. O `.gitignore` já exclui bancos locais e arquivos de ambiente.
