# Biblioteca de Prompts Erica QA

Aplicação desktop local para preservar contexto entre projetos e ferramentas de IA. Organiza prompts, projetos, dicas, códigos técnicos e materiais relacionados em um banco SQLite persistente, com autenticação local e funcionamento sem internet em tempo de execução.

> Os dados pessoais e o banco local não pertencem ao repositório. Eles ficam em `~/.central-de-prompts/` e são excluídos do versionamento pelo `.gitignore`.

## Download para Windows

A versão Windows é distribuída como executável portátil em [Releases](https://github.com/ericasouzaqa/biblioteca-de-prompts/releases/latest). Baixe o ZIP, extraia e abra `BibliotecaDePrompts.exe` com duplo clique. O pacote já contém Python, SQLite, Tkinter e as DLLs necessárias; não é preciso instalar terminal, Python ou bibliotecas.

## Funcionalidades

A aplicação possui um dashboard com métricas de prompts, favoritos, categorias e arquivos, além de atalhos para criação, favoritos, repositório e configurações. A biblioteca mantém projetos, prompts, dicas e códigos com criação, edição, exclusão, favoritos, cópia, tags, categorias e busca global.

O módulo **Repositório** permite importar, pesquisar, filtrar por categoria e baixar arquivos PDF, DOCX, XLSX, PPTX, TXT, ZIP, PNG, JPG e JPEG. Os arquivos são armazenados localmente com nome interno aleatório e hash SHA-256 para verificação de integridade.

A autenticação local mantém o hash da senha com `scrypt`. O fluxo **Esqueci minha senha** usa um token temporário, de uso único e com validade de 20 minutos. No modo offline, o token é exibido localmente. Uma integração real de e-mail pode ser adicionada posteriormente sem alterar o banco existente.

## Recuperação e preservação de dados

As atualizações criam uma cópia `central.db.before-update` antes de alterações estruturais. A importação de backup valida o formato, preserva os registros existentes, remapeia IDs de projetos relacionados e executa a operação em transação com rollback em caso de falha. A exportação inclui configurações, projetos, prompts, dicas, códigos e metadados do repositório.

## Execução a partir do código-fonte

Requer Python 3.10 ou superior e Tkinter. No Ubuntu/Debian, se necessário, instale `python3-tk` pelo gerenciador de pacotes. Depois execute:

```bash
python3 app.py
```

Para validar a implementação:

```bash
python3 -m py_compile app.py
python3 test_storage.py
xvfb-run -a python3 test_gui.py
```

## Estrutura

| Caminho | Responsabilidade |
|---|---|
| `app.py` | Interface Tkinter, autenticação, persistência, dashboard, biblioteca e repositório |
| `test_storage.py` | Testes isolados de SQLite, hash e recuperação de senha |
| `test_gui.py` | Smoke test de inicialização da interface em display virtual |
| `docs/index.html` | Página pública responsiva do projeto para GitHub Pages |
| `.github/workflows/windows-build.yml` | Build portátil Windows via PyInstaller e publicação de release |
| `AUDIT_FINDINGS.md` | Auditoria arquitetural, riscos e estratégia de atualização |

## Links de distribuição

- **GitHub Pages:** https://ericasouzaqa.github.io/biblioteca-de-prompts/
- **Release mais recente:** https://github.com/ericasouzaqa/biblioteca-de-prompts/releases/latest
- **Executável Windows:** disponível como `BibliotecaDePrompts-Windows.zip` na Release mais recente

## GitHub Pages

A aplicação principal é desktop e depende de SQLite local, portanto não pode ser executada diretamente em GitHub Pages sem perder privacidade e persistência. Como alternativa compatível, `docs/index.html` fornece uma página pública responsiva de apresentação e download. O aplicativo continua sendo a fonte de dados e de funcionalidades completas.

## Desenvolvimento e publicação

O workflow `Build Windows` é executado em tags `v*`. Ele gera `BibliotecaDePrompts.exe`, cria `BibliotecaDePrompts-Windows.zip`, publica os artefatos e mantém o executável independente de serviços externos durante o uso.

## Identidade visual

A interface utiliza a direção visual futurista solicitada: fundo escuro em tons `#070317`, `#0B0820` e `#120B2E`, acentos rosa neon `#FF4FD8`, roxo `#9B4DFF`, ciano `#00E5FF`, cards arredondados, foco visível e contraste reforçado. As imagens de referência citadas na especificação não estavam presentes no repositório no momento da auditoria; por isso a implementação usa a paleta e o sistema visual sem inventar arquivos pessoais.

## Limites conhecidos

A recuperação de senha offline não envia e-mails por não haver provedor configurado. O GitHub Pages é uma landing page, não uma réplica da biblioteca privada. A sincronização entre dispositivos e o envio de e-mail exigiriam um serviço externo opcional, ausente por decisão de independência operacional.

## Instalação no Windows

1. Baixe `BibliotecaDePrompts-Windows.zip` na [Release mais recente](https://github.com/ericasouzaqa/biblioteca-de-prompts/releases/latest).
2. Extraia o ZIP para uma pasta de sua preferência.
3. Execute `BibliotecaDePrompts.exe`. O banco local será criado em `%USERPROFILE%\.central-de-prompts`.

O executável é portátil: não exige Python instalado nem conexão com a internet durante o uso.
