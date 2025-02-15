# Monitoramento de Fundos Imobiliários

### Descrição
Bot para armazenar informações sobre FIIs, permitindo atualização, consulta e visualização dos dados diretamente pelo Telegram.

### Video de Demonstração
[Link para o video](https://drive.google.com/file/d/1Aj9UEfQY9VbOuzrvaB3eLvHSmBcNuc_k/view?usp=sharing)

## índice
- [📥 Instalação](#Instalação)
- [⚙️ Como Funciona](#⚙️-como-funciona)
- [🛠 Tecnologias](#🛠-tecnologias)
- [Observações](#Observações)

## Instalação
#### Crie uma pasta e clone o projeto com os comandos:
- "git clone https://github.com/guolivv/nome-da-pasta.git"
- cd nome-da-pasta

#### Instale as dependências necessárias:
- pip install -r requirements.txt

#### Configure as variáveis de ambiente criando um arquivo .env. No projeto, foi usada a configuração para PostgreSQL:
POSTGRES_DB = "seu_banco_de_dados" <br>
POSTGRES_USER = "seu_usuario" <br>
POSTGRES_PASSWORD = "sua_senha" <br>
POSTGRES_HOST = "seu_host" <br>
POSTGRES_PORT = "5432" <br>
TELEGRAM_TOKEN = "seu_token_do_bot"

## Como funciona
#### O projeto usa um modelo ETL (Extract, Transform, Load) simples:
- Extract: Utilização do Selenium e WebDriver para extrair dados de nome e preço dos FIIs de forma automatizada;
- Transform: Cálculo da variação de preço dos FIIs com base no preço atual e atribuição do valor em uma nova coluna "Variação"
- Load: Armazenamento dos dados sobre os FIIs (nome, preço, data e horário de extração, e variação) em um banco de dados PostgreSQL.

#### Bot no telegram para tratar comandos:
- /atualizar: Busca novas cotações e exibe as atualizações para cada fundo (atualmente, 2);
- /salvar: Salva as atualizações no banco;
- /grafico: Exibe um gráfico ilustrativo dos preços dos FIIs ao longo do tempo, com base nos registros salvos

## Tecnologias
- 🐍 Python (Linguagem de Programação)
- 🌍 Selenium e WebDriver (Web Scraping para extração de dados)
- 📊 Pandas & Matplotlib (Manipulação e visualização de dados)
- 🗄 PostgreSQL & SQLAlchemy (Banco de dados)
- 🤖 Telegram Bot API (Interface para usuário)

## Observações
- Houve problemas com o projeto inicial apresentado no video de demonstração, constatando a ausência dos arquivos Dockerfile e .dockerignore. Os arquivos estão sendo reconstruídos.