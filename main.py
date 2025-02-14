from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import pandas as pd
from telegram.ext import Application, Updater, CommandHandler
import time
import matplotlib.pyplot as plt
import numpy as np
from sqlalchemy import create_engine
import psycopg2
import os
import seaborn as sns


def config_chrome_driver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')                                
    wd_chrome = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options= chrome_options)

    return wd_chrome


def get_names(chromedriver, urls):
    nomes = []

    for url in urls:
        try:
            chromedriver.get(url)
            path_nome = chromedriver.find_elements(By.XPATH, '//*[@id="tickerName"]') 

            if (path_nome):
                nome = path_nome[0].text
                nomes.append(nome)
            else:
                print(f"Objeto nome nao encontrado para a url: {url}")
        except Exception as e:
            print(f"Erro ao buscar nome na url {url}: {e}")
     
    return nomes


def get_prices(chromedriver, urls):
    precos = []

    for url in urls:
        try:
            chromedriver.get(url)
            path_preco = chromedriver.find_elements(By.XPATH, '//*[@id="carbon_fields_fiis_header-2"]/div/div/div[1]/div[1]/p')

            if (path_preco):
                preco = path_preco[0].text
                preco = preco[3:]
                preco = preco.replace(',','.')
                preco = float(preco)
                precos.append(preco)
            else:
                print(f"Objeto preco nao encontrado para a url: {url}")
        except Exception as e:
            print(f"Erro ao buscar preco na url {url}: {e}")

    return precos


def get_date():
    now = datetime.now()
    date = now.strftime("%Y/%m/%d")

    return date


def get_hour():
    now = datetime.now()
    time_now = now.strftime("%H:%M:%S")

    return time_now


def create_dict(nomes, precos, date, hour):
    for i in range(len(nomes)-1):
        dict = {
            'fii': [nomes][i],
            'preco': [precos][i],
        }

        dict.update({'data': date, 'horario': hour, 'variacao': [0, 0]})

    return dict


def create_df(dict):
    df = pd.DataFrame(dict)

    return df


def connection_data_base(db_name='cotacao_fiis.db'):
    try:
        conn = psycopg2.connect(
            dbname = POSTGRES_DB,
            user = POSTGRES_USER,
            password = POSTGRES_PASSWORD,
            host = POSTGRES_HOST,
            port = POSTGRES_PORT
        )
        return conn
    
    except Exception as e:
        print(f"Erro ao conectar com o banco de dados: {e}")
        return None


def setup_db(connection):
    cursor = connection.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cotacao_fiis (
        id SERIAL PRIMARY KEY,
        fii VARCHAR(20),
        preco REAL,
        data DATE,
        horario TEXT,
        variacao REAL)
    ''')
    connection.commit()
    cursor.close()
    

def get_last_two_prices(connection):
    last_prices = []

    cursor = connection.cursor()
    cursor.execute(
        '''
            SELECT preco
            FROM cotacao_fiis
            ORDER BY id DESC
            LIMIT 2
        ''')
    results = cursor.fetchall()

    for result in results:
        result = float(result[0])
        last_prices.append(result)

    cursor.close()

    return last_prices


def calculate_price_variation(prices, df):
    prices_variation = []
    j = len(prices)

    for i in range(j):
        variation = df.preco[i] - prices[j-1]
        variation = round(variation, 2)
        prices_variation.append(variation)
        j -= 1

    return prices_variation


def update_df(df, price_variation):
    df['variacao'] = price_variation

    return df


async def atualizar_info(update, context, df):
    query_last_2 = ''' SELECT *
                FROM cotacao_fiis
                ORDER BY id DESC
                LIMIT 2
            '''

    df_last_2 = pd.read_sql(query_last_2, engine)
    df_last_2 = df_last_2.drop(columns=['id'])
    df_last_2 = df_last_2.iloc[::-1].reset_index(drop=True)

    df_atualizado = pd.concat([df, df_last_2], ignore_index=True)

    resultado = df_atualizado.head().to_string(index=False)
    mensagem = f"Atualizações:\n```\n{resultado}\n```"
    await update.message.reply_text(mensagem, parse_mode='MarkdownV2')


async def salvar_info(update, context, df):
  df.to_sql('cotacao_fiis', con=engine, if_exists='append', index=False)

  resultado = df.head().to_string(index=False)
  mensagem = f"Informação salva:\n```\n{resultado}\n```"
  await update.message.reply_text(mensagem, parse_mode='MarkdownV2')


async def exibir_grafico(update, context):
    query_all = '''
                    WITH RegistrosOrdenados AS (
                    SELECT
                        fii,
                        preco,
                        data,
                        horario,
                        variacao,
                        ROW_NUMBER() OVER (PARTITION BY fii, data ORDER BY horario DESC) AS ordem
                    FROM cotacao_fiis
                    )
                    SELECT
                        fii,
                        preco,
                        data,
                        horario,
                        variacao
                    FROM RegistrosOrdenados
                    WHERE ordem = 1
                    ORDER BY data, fii;
                '''

    df_all = pd.read_sql(query_all, engine)
    df_all['data'] = pd.to_datetime(df_all['data'], errors='coerce')

    plt.figure(figsize=(10, 6))
    sns.lineplot(data=df_all, x='data', y='preco', hue='fii', marker='o', palette='tab10')

    unique_dates = df_all['data'].dt.date.unique()
    plt.xticks(ticks=pd.to_datetime(unique_dates), labels=unique_dates)
    plt.xticks(rotation=45, ha='right')

    for i, row in df_all.iterrows():
        plt.text(
        x=row['data'], 
        y=row['preco'] + 0.5, 
        s=f"{row['preco']:.2f}",  
        color="black", 
        fontsize=10, 
        ha='center',
        va='bottom',  
        rotation=45
    )

    plt.title("Preços dos FIIs por Data", fontsize=14, pad=20)
    plt.xlabel("Data", fontsize=12)
    plt.ylabel("Preço", fontsize=12)
    plt.ylim(0, 100)

    plt.legend(title="FII", loc="center left", bbox_to_anchor=(1, 0.5))  
    plt.grid(True)
    plt.tight_layout()

    #Salvar o gráfico como imagem
    graph_path = "graph.png"
    plt.savefig(graph_path)
    plt.close()

    #Enviar o gráfico como imagem
    with open(graph_path, "rb") as graph_file:
        await update.message.reply_photo(graph_file)


#Definição de configurações do banco PostgreSQL
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")

DATABASE_URL = f'postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}/{POSTGRES_DB}'
engine = create_engine(DATABASE_URL)

#Configuração telegram
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

def main():
    chromedriver = config_chrome_driver()

    #Funções para conectar no banco de dados sqlite3
    connection = connection_data_base()
    setup_db(connection)

    urls = ['https://www.fundsexplorer.com.br/funds/mxrf11', 'https://www.fundsexplorer.com.br/funds/xplg11']

    #Funções para extrair dados que vão para o dicionário e, posteriormente, para o DataFrame
    names = get_names(chromedriver, urls)
    prices = get_prices(chromedriver, urls)
    date = get_date()
    hour = get_hour()
    dict = create_dict(names, prices, date, hour)
    df = create_df(dict)

    last_prices = get_last_two_prices(connection)
    price_variation = calculate_price_variation(last_prices, df)
    df = update_df(df, price_variation)

    #Declarações de comandos executados via telegram
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler('atualizar', lambda update, context: atualizar_info(update, context, df)))
    application.add_handler(CommandHandler('salvar', lambda update, context: salvar_info(update, context, df)))
    application.add_handler(CommandHandler('grafico', exibir_grafico))
    application.run_polling()

if __name__ == '__main__':
    main()