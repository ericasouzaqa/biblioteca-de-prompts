# Biblioteca de Prompts

## Visão Geral

Aplicação desktop local para organizar prompts, projetos, governança, códigos e arquivos técnicos. Funciona offline, usa SQLite no dispositivo e não depende de IA, servidor externo ou GitHub durante o uso.

**Versão em produção:** v1.1.0 — redesenho estrutural premium com sidebar, busca e cards, preservando os dados locais.

## Navegação principal

A versão atual prioriza o trabalho diário com seis entradas visíveis: **Projetos, Prompts, Repositórios, Favoritos, Recentes e Mais**. Governança, Wiki, Templates, Coleções, Códigos, Configurações, Diagnóstico, Relatórios e Lixeira permanecem disponíveis no menu Mais.

A Home é focada em continuidade do trabalho, mostrando o contexto atual, onde o usuário parou, o próximo passo, o último prompt utilizado e o repositório relacionado. A busca global usa o placeholder “Pesquisar projetos, prompts ou repositórios...” e permite localizar rapidamente o conteúdo da biblioteca.

## Funcionalidades

- Abertura direta da Home, sem tela de login ou autenticação.
- Navegação simplificada para Projetos, Prompts, Repositórios, Favoritos, Recentes e Mais.
- Home orientada à continuidade do trabalho.
- Busca global de projetos, prompts e repositórios.
- Governança, Wiki, templates, coleções, códigos, relatórios, diagnóstico e lixeira no menu avançado.
- Upload, download e hash SHA-256 para arquivos locais.
- Backup e restauração JSON transacional.
- Identidade visual Erica QA no desktop e GitHub Pages.

## Compatibilidade e migração

Não é necessária nenhuma migração destrutiva para a v1.1.0. A autenticação foi removida do fluxo de uso, as tabelas e configurações legadas permanecem intactas no SQLite e a nova coluna de uso é adicionada de forma compatível. O redesenho é compatível com dados existentes e backups existentes.

## Instalação

No Windows, baixe a [Release mais recente](https://github.com/ericasouzaqa/biblioteca-de-prompts/releases/latest), extraia `BibliotecaDePrompts-Windows.zip` e execute `BibliotecaDePrompts.exe`. Não é necessário instalar Python. O banco fica em `%USERPROFILE%\\.central-de-prompts`.

No macOS, o workflow [macos-build.yml](.github/workflows/macos-build.yml) gera `BibliotecaDePrompts-macOS.zip` em um runner macOS. Extraia e abra o aplicativo `.app` pelo Finder.

## Execução Local

Requer Python 3.10+ e Tkinter:

```bash
python3 app.py
```

No Ubuntu/Debian, instale `python3-tk` quando necessário.

## Build

O build Windows usa PyInstaller e o workflow é acionado por tags `v*`:

```bash
python -m pip install pyinstaller
pyinstaller --clean --noconfirm --onefile --windowed --name BibliotecaDePrompts --icon=favicon.ico --add-data "assets/Fundo_Login_EricaQA_2912x2160.png;assets" --add-data "assets/Foto_Perfil_EricaQA_800x800.png;assets" app.py
```

O build macOS usa o workflow próprio e empacota o aplicativo `.app` em ZIP. Os assets locais são incluídos nos dois builds.

## Deploy

A landing page está preparada em `docs/` e é publicada pelo workflow de GitHub Pages quando o recurso está habilitado no repositório. Como este repositório é privado e a conta/plano atual não expõe o site publicamente, a URL pode retornar 404; a distribuição oficial continua sendo a Release do GitHub. Os dados da biblioteca permanecem locais.
