import csv
from ib_insync import *
import logging

# Suprimir todas as mensagens de erro
logging.getLogger('ib_insync').setLevel(logging.CRITICAL)

def create_watchlist():
    ib = IB()
    ib.connect('127.0.0.1', 7497, clientId=1)
    
    # Ler tickers do CSV
    tickers = []
    with open('institutional_accumulation_candidates.csv', 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            ticker = row['ticker'].replace('.csv', '')
            tickers.append(ticker)
    
    # Criar contratos
    contracts = []
    for ticker in tickers:
        contract = Stock(ticker, 'SMART', 'USD')
        contracts.append(contract)
    
    # Adicionar tickers à watchlist do TWS
    for i, contract in enumerate(contracts):
        ib.reqMktData(contract, '', False, False)
        print(f"Adicionado: {contract.symbol} ({i+1}/{len(contracts)})")
    
    print(f"✓ {len(contracts)} tickers adicionados! Agora crie a watchlist manualmente no TWS com o nome 'sharks_07_17'")
    
    ib.disconnect()

if __name__ == "__main__":
    create_watchlist() 