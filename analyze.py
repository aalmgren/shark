import pandas as pd
import numpy as np
import os
from datetime import datetime
import multiprocessing as mp
from functools import partial
from shared_params import load_analysis_params

def process_file(file_info):
    """Processa um único arquivo CSV"""
    file_path, filename = file_info
    try:
        # Ignorar warrants, units, rights, preferreds e outros derivativos
        ticker = filename.split('.')[0] # Corrigido para pegar o ticker corretamente
        if ticker.endswith(('.WT', '.U', '.R', '.P', 'W', 'WS', 'PR', 'X', 'L', 'Z')):
            return None
            
        # Ler apenas colunas necessárias
        df = pd.read_csv(file_path, usecols=['Date', 'Close', 'Volume'])
        if len(df) < 50:
            return None
            
        df['ticker'] = ticker
        df['Date'] = pd.to_datetime(df['Date'], utc=True)
        return df
    except Exception as e:
        # print(f"Erro processando {filename}: {e}") # Opcional: para depuração
        pass
    return None

def analyze_ticker(ticker_data, params):
    """Analisa um ticker para padrões de momentum"""
    try:
        # Ordenar por data
        ticker_data = ticker_data.sort_values('Date')
        
        ticker = ticker_data['ticker'].iloc[0]
        
        # Parâmetros da análise
        long_period = params.get('volume_period_long', 90)
        short_period = params.get('volume_period_short', 7)
        
        # Verificar mínimo de dados para os períodos
        if len(ticker_data) < (long_period + short_period):
            return None
            
        # Calcular volume em dinheiro (quantidade × preço)
        ticker_data['volume_usd'] = ticker_data['Volume'] * ticker_data['Close']
            
        # Calcular médias de volume
        last_short_period = ticker_data.tail(short_period)
        previous_long_period = ticker_data.iloc[-(long_period + short_period):-short_period]
        
        volume_usd_long = previous_long_period['volume_usd'].mean()
        volume_usd_short = last_short_period['volume_usd'].mean()
        
        # Se o ratio for zero ou menor que 1, não há porque continuar
        if volume_usd_long == 0 or (volume_usd_short / volume_usd_long) < 1.0:
            return None
        
        # Continuar com outros cálculos se o ratio for válido
        volume_long = previous_long_period['Volume'].mean()
        volume_short = last_short_period['Volume'].mean()
        
        # Calcular médias de preço para os períodos de baseline e spike
        avg_price_long = previous_long_period['Close'].mean()
        avg_price_short = last_short_period['Close'].mean()

        # Calcular variação percentual entre as médias de preço
        avg_price_change_pct = ((avg_price_short - avg_price_long) / avg_price_long) * 100 if avg_price_long > 0 else 0
        
        # Filtro: Descartar se a variação de preço entre as médias for negativa
        if avg_price_change_pct < 0:
            return None

        # Calcular ratio de volume
        volume_ratio = volume_usd_short / volume_usd_long
        
        # Score baseado em volume e na nova variação de preço
        score = volume_ratio * (1 + avg_price_change_pct / 100)
        
        result = {
            'ticker': ticker,
            'ratio': volume_ratio,
            'volume_short': volume_short,
            'volume_long': volume_long,
            'volume_usd_short': volume_usd_short,
            'volume_usd_long': volume_usd_long,
            'price': ticker_data['Close'].iloc[-1], # Manter o preço atual para referência
            'avg_price_long': avg_price_long,
            'avg_price_short': avg_price_short,
            'avg_price_change_pct': avg_price_change_pct,
            'score': score
        }
        return result

    except Exception as e:
        # print(f"Erro analisando {ticker_data['ticker'].iloc[0]}: {e}") # Opcional: para depuração
        pass
    return None

def process_nasdaq_data():
    """MOMENTUM ANALYSIS - Detecta acumulação institucional via análise de volume"""
    print("DETECTING MOMENTUM - FINDING HIGH-MOMENTUM STOCKS")
    print("=" * 60)

    # Carregar parâmetros de análise
    params = load_analysis_params()
    print(f"Analysis Parameters: Long Period={params['volume_period_long']}d, Short Period={params['volume_period_short']}d")
    
    # 0. Carregar dados de tickers com setores e indústrias
    ticker_info_path = 'tick/tickers.csv' # Usando o arquivo original de tickers
    if not os.path.exists(ticker_info_path):
        print(f"Ticker info file not found at {ticker_info_path}")
        return
        
    ticker_info_df = pd.read_csv(ticker_info_path)
    # A coluna 'ticker' já existe, o rename não é necessário e pode causar erro se 'Symbol' não existir.
    # ticker_info_df.rename(columns={'Symbol': 'ticker'}, inplace=True) 
    print(f"Loaded info for {ticker_info_df['ticker'].nunique()} tickers.")
    
    # 1. Listar todos os arquivos CSV no diretório DB
    data_dir = 'DB'
    if not os.path.exists(data_dir):
        print(f"Data directory '{data_dir}' not found.")
        return

    all_files = [(os.path.join(data_dir, f), f) for f in os.listdir(data_dir) if f.endswith('.csv')]
    
    if not all_files:
        print("No CSV files found in the DB directory")
        return
    
    print(f"Processing {len(all_files)} files...")
    
    # 2. Processar arquivos em paralelo
    with mp.Pool() as pool:
        processed = pool.map(process_file, all_files)
        all_data = [df for df in processed if df is not None]
    
    if not all_data:
        print("No valid data found after initial processing.")
        return
    
    # 3. Consolidar dados
    df = pd.concat(all_data, ignore_index=True)
    print(f"Data loaded: {len(df):,} records from {df['ticker'].nunique()} companies")
    
    # 4. Analisar cada ticker em paralelo
    ticker_groups = [group for _, group in df.groupby('ticker')]
    
    # Criar uma função parcial com os parâmetros fixos
    analyze_func = partial(analyze_ticker, params=params)

    with mp.Pool() as pool:
        analyzed = pool.map(analyze_func, ticker_groups)
        candidates = [candidate for candidate in analyzed if candidate is not None]
    
    if not candidates:
        print("No candidates with volume increase detected with current parameters.")
        return
    
    # 5. Ordenar e salvar resultados
    momentum_df = pd.DataFrame(candidates)
    
    # Adicionar informações de setor e indústria (usando nomes de coluna em minúsculo)
    if 'sector' in ticker_info_df.columns and 'industry' in ticker_info_df.columns:
        momentum_df = pd.merge(momentum_df, ticker_info_df[['ticker', 'sector', 'industry']], on='ticker', how='left')
    else:
        momentum_df['sector'] = 'Unknown'
        momentum_df['industry'] = 'Unknown'

    momentum_df['sector'] = momentum_df['sector'].fillna('Unknown')
    momentum_df['industry'] = momentum_df['industry'].fillna('Unknown')
    
    momentum_df = momentum_df.sort_values('score', ascending=False)

    # Renomear colunas para clareza no arquivo de saída
    final_columns = {
        'volume_short': f'volume_{params["volume_period_short"]}d',
        'volume_long': f'volume_{params["volume_period_long"]}d',
        'volume_usd_short': f'volume_usd_{params["volume_period_short"]}d',
        'volume_usd_long': f'volume_usd_{params["volume_period_long"]}d',
        'avg_price_long': f'avg_price_{params["volume_period_long"]}d',
        'avg_price_short': f'avg_price_{params["volume_period_short"]}d'
    }
    momentum_df.rename(columns=final_columns, inplace=True)
    
    # Salvar todos os candidatos
    output_file = 'institutional_accumulation_candidates.csv'
    momentum_df.to_csv(output_file, index=False)
    
    # 6. Exibir resultados
    print(f"\nTOP 15 CANDIDATES ({params['volume_period_short']}d vs {params['volume_period_long']}d)")
    print("=" * 115)
    header = f"TICKER  RATIO   VOL_{params['volume_period_short']}D($M)   VOL_{params['volume_period_long']}D($M)   PRECO    AVG_PRICE_{params['volume_period_long']}D   CHANGE(%)    SCORE"
    print(header)
    print("-" * 115)
    
    # Nomes das colunas para usar na impressão
    vol_usd_short_col = f'volume_usd_{params["volume_period_short"]}d'
    vol_usd_long_col = f'volume_usd_{params["volume_period_long"]}d'
    avg_price_long_col = f'avg_price_{params["volume_period_long"]}d'

    for _, candidate in momentum_df.head(15).iterrows():
        print(f"{candidate['ticker']:<7} {candidate['ratio']:.1f}x   ${candidate[vol_usd_short_col]/1000000:,.1f}M    ${candidate[vol_usd_long_col]/1000000:,.1f}M     ${candidate['price']:<7.2f} {candidate[avg_price_long_col]:<7.2f} {candidate['avg_price_change_pct']:>11.1f}% {candidate['score']:.1f}")
    
    # Estatísticas
    print(f"\nVOLUME STATISTICS:")
    print(f"  - Total candidates with volume increase: {len(momentum_df)} tickers")
    
    print(f"\nFILE UPDATED:")
    print(f"  - Candidates saved to: {output_file} ({len(momentum_df)} tickers)")
    print(f"  - Last update: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    print("\nANALYSIS COMPLETED!")
    print("Use the results for your own analysis.")

if __name__ == "__main__":
    process_nasdaq_data() 