import requests
import pandas as pd
import os

def get_nasdaq_tickers():
    """Baixa tickers NASDAQ"""
    url = 'https://raw.githubusercontent.com/datasets/nasdaq-listings/master/data/nasdaq-listed.csv'
    df = pd.read_csv(url)
    return [{'ticker': row['Symbol'], 'exchange': 'NASDAQ'} for _, row in df.iterrows()]

def get_nyse_tickers():
    """Baixa tickers NYSE"""
    url = "https://www.nyse.com/api/quotes/filter"
    headers = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}
    payload = {"instrumentType": "EQUITY", "pageNumber": 1, "maxResultsPerPage": 10000}
    
    response = requests.post(url, headers=headers, json=payload)
    data = response.json()
    return [{'ticker': stock['symbolTicker'], 'exchange': 'NYSE'} for stock in data]

def main():
    # Buscar tickers
    tickers = get_nasdaq_tickers() + get_nyse_tickers()
    
    # Criar DataFrame e ordenar
    df = pd.DataFrame(tickers)
    df = df.sort_values('ticker')
    
    # Salvar na pasta tick
    os.makedirs('tick', exist_ok=True)
    df.to_csv('tick/tickers.csv', index=False)
    print(f"✅ Salvos {len(df)} tickers em tick/tickers.csv")

if __name__ == "__main__":
    main() 