import csv
from ib_insync import *

def create_watchlist():
    # Conectar ao IBKR
    ib = IB()
    ib.connect('127.0.0.1', 7497, clientId=1)
    
    # Ler tickers do CSV
    tickers = []
    with open('institutional_accumulation_candidates.csv', 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            ticker = row['ticker'].replace('.csv', '')  # Remove .csv do nome
            tickers.append(ticker)
    
    print(f"Encontrados {len(tickers)} tickers")
    
    # Criar watchlist
    stocks = []
    for ticker in tickers:
        stock = Stock(ticker, 'SMART', 'USD')
        stocks.append(stock)
    
    # Adicionar à watchlist do TWS
    for stock in stocks:
        ib.reqMktData(stock, '', False, False)
        print(f"Adicionado: {stock.symbol}")
    
    print("Watchlist criada! Pressione Ctrl+C para desconectar")
    
    try:
        ib.run()
    except KeyboardInterrupt:
        print("Desconectando...")
        ib.disconnect()

if __name__ == "__main__":
    create_watchlist() 