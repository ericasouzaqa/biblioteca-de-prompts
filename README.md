# Central de Prompts

Aplicativo desktop offline para organizar projetos, prompts reutilizáveis, dicas de continuidade e códigos técnicos úteis. A aplicação não possui IA embutida, não exige internet e não depende de APIs externas em tempo de execução.

## Requisitos

Python 3.10 ou superior com Tkinter instalado. Em distribuições Debian/Ubuntu, caso necessário, instale `python3-tk` pelo gerenciador de pacotes do sistema.

## Download para Windows

A versão Windows é um pacote **portátil** publicado em [Releases](https://github.com/ericasouzaqa/central-de-prompts/releases/latest). Você não precisa instalar Python, Tkinter, bibliotecas, DLLs, runtime ou qualquer outro programa.

Baixe `CentralDePrompts-Windows.zip`, extraia o arquivo em qualquer pasta e abra `CentralDePrompts.exe` com duplo clique. O executável já contém o runtime Python, o SQLite e os componentes gráficos necessários. Não é necessário abrir o terminal, executar comandos ou manter internet conectada.

O Windows pode exibir um aviso do SmartScreen por o executável ser novo e não possuir assinatura digital comercial. Nesse caso, confirme que o arquivo foi baixado deste repositório privado e escolha **Mais informações > Executar assim mesmo**, se desejar prosseguir.

## Execução a partir do código-fonte (opcional)

A seção abaixo é destinada somente a quem quiser editar ou desenvolver o projeto. Para uso normal no Windows, utilize exclusivamente o executável portátil descrito acima.


```bash
python3 app.py
```

No primeiro acesso, informe um nome de usuário e crie uma senha com pelo menos seis caracteres. A senha é armazenada somente como um hash `scrypt`; os dados ficam no banco SQLite local em `~/.central-de-prompts/central.db`.

## Sobre a aplicação

A Central de Prompts é uma biblioteca pessoal privada para preservar contexto entre projetos e ferramentas de IA. Ela foi desenhada para funcionar localmente, sem IA embutida, sem APIs externas, sem conta Manus e sem dependência de internet em tempo de execução.

## Recursos implementados

A janela principal possui as abas **Projetos**, **Biblioteca de Prompts**, **Dicas de Prompt**, **Biblioteca de Códigos** e **Configurações**, além de pesquisa global por texto. Projetos mantêm objetivo, repositório, ferramenta, status, último prompt e data de interação. Prompts possuem campos de contexto, gatilho, conteúdo completo, resultado esperado, observações e tags. Dicas e códigos também podem ser cadastrados, editados e pesquisados.

A aba de configurações permite exportar e importar backups JSON, alterar a senha e consultar a pasta local de dados. O logout encerra apenas a sessão e não remove informações.

## Princípio de independência

Este projeto utiliza apenas a biblioteca padrão do Python e SQLite. Não contém chaves, tokens, dados pessoais ou dependências obrigatórias do Manus, GitHub, IA ou serviços externos.

## Observação de segurança

A proteção atual cobre autenticação local, hash de senha e permissões restritas da pasta de dados. Para ambientes com exigência de criptografia de disco ou ameaça física ao computador, recomenda-se também utilizar a criptografia nativa do sistema operacional.
