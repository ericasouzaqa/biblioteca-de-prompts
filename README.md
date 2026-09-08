# Biblioteca de Prompts

## Visão Geral

Aplicação desktop local para organizar prompts, projetos, dicas, códigos e arquivos técnicos. Funciona offline, mantém os dados em SQLite no dispositivo e não depende de IA, servidor externo ou GitHub durante o uso.

## Funcionalidades

- Login local com senha derivada por `scrypt`.
- Dashboard com métricas, favoritos e pesquisa global.
- CRUD de projetos, prompts, governança, códigos e arquivos.
- Repositório local com upload, download e hash SHA-256.
- Backup JSON com transação e remapeamento de relações.
- Identidade visual oficial com fundo e avatar Erica QA.

## Instalação

### Windows

Baixe [`BibliotecaDePrompts-Windows.zip`](https://github.com/ericasouzaqa/biblioteca-de-prompts/releases/latest), extraia e execute `BibliotecaDePrompts.exe`. Não é necessário instalar Python. O banco é criado em `%USERPROFILE%\.central-de-prompts`.

### macOS

O workflow [`macos-build.yml`](.github/workflows/macos-build.yml) gera `BibliotecaDePrompts-macOS.zip` em um runner macOS. O artefato deve ser extraído e o aplicativo `.app` aberto pelo Finder. A compilação macOS não é executada neste ambiente Linux.

## Execução Local

Requer Python 3.10+ e Tkinter:

```bash
python3 app.py
```

No Ubuntu/Debian, instale `python3-tk` quando necessário.

## Build

Windows, no GitHub Actions:

```bash
python -m pip install pyinstaller pillow
pyinstaller --clean --noconfirm --onefile --windowed --name BibliotecaDePrompts --icon=favicon.ico --add-data "assets/Fundo_Login_EricaQA_2912x2160.png;assets" --add-data "assets/Foto_Perfil_EricaQA_800x800.png;assets" app.py
```

A versão Windows é publicada em tags `v*`. A versão macOS usa o workflow próprio e empacota o `.app` em ZIP.

## Deploy

A landing page está em [GitHub Pages](https://ericasouzaqa.github.io/biblioteca-de-prompts/). Ela é uma página pública de apresentação; os dados da biblioteca permanecem locais.

## Download

- [Release mais recente](https://github.com/ericasouzaqa/biblioteca-de-prompts/releases/latest)
- [Executável Windows](https://github.com/ericasouzaqa/biblioteca-de-prompts/releases/latest)
- [GitHub Pages](https://ericasouzaqa.github.io/biblioteca-de-prompts/)

## Estrutura Básica

| Caminho | Responsabilidade |
|---|---|
| `app.py` | Interface Tkinter, persistência, autenticação e funcionalidades locais |
| `assets/` | Logo, favicon, fundo e avatar oficiais |
| `docs/` | Landing page e assets do GitHub Pages |
| `.github/workflows/` | Builds Windows, macOS e deploy do Pages |
| `test_storage.py` | Testes de SQLite, hash e recuperação de senha |
| `test_gui.py` | Smoke test da interface |
