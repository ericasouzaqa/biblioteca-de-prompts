# Biblioteca de Prompts

## Visão Geral

Aplicação desktop local para organizar prompts, projetos, governança, códigos e arquivos técnicos. Funciona offline, usa SQLite no dispositivo e não depende de IA, servidor externo ou GitHub durante o uso.

## Funcionalidades

- Login local com senha derivada por `scrypt`.
- Dashboard, favoritos e pesquisa global.
- Projetos, prompts, governança, códigos e arquivos.
- Upload, download e hash SHA-256 para arquivos locais.
- Backup e restauração JSON transacional.
- Identidade visual Erica QA no desktop e GitHub Pages.

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

A landing page é publicada em [GitHub Pages](https://ericasouzaqa.github.io/biblioteca-de-prompts/). Ela apresenta o projeto e usa os assets em `docs/assets/`; os dados da biblioteca permanecem locais.
