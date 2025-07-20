import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict
import os

def load_stock_data(ticker: str, db_path: str = "DB") -> pd.DataFrame:
    """Carrega os dados de uma ação específica"""
    file_path = Path(db_path) / f"{ticker}.csv"
    df = pd.DataFrame()
    
    if file_path.exists():
        df = pd.read_csv(file_path)
        # Remove linhas com valores ausentes
        df = df.dropna()
        if len(df) > 0:
            df['Date'] = pd.to_datetime(df['Date'])
            df.set_index('Date', inplace=True)
    
    return df

def detect_bullish_engulfing(df: pd.DataFrame) -> pd.Series:
    """
    Detecta padrões de engolfo de alta
    Retorna uma série com True nos dias onde ocorre o padrão
    """
    # Dia anterior foi de baixa (Close < Open)
    prev_bearish = df['Close'].shift(1) < df['Open'].shift(1)
    
    # Dia atual é de alta (Close > Open)
    current_bullish = df['Close'] > df['Open']
    
    # Abertura atual menor que fechamento anterior
    opens_lower = df['Open'] < df['Close'].shift(1)
    
    # Fechamento atual maior que abertura anterior
    closes_higher = df['Close'] > df['Open'].shift(1)
    
    # Corpo atual maior que corpo anterior
    current_body = abs(df['Close'] - df['Open'])
    prev_body = abs(df['Close'].shift(1) - df['Open'].shift(1))
    larger_body = current_body > prev_body
    
    # Combina todas as condições
    return prev_bearish & current_bullish & opens_lower & closes_higher & larger_body

def calculate_future_returns(df: pd.DataFrame, signal_dates: pd.Series, periods: List[int]) -> pd.DataFrame:
    """
    Calcula os retornos futuros após cada sinal
    """
    results = []
    
    for date in signal_dates.index[signal_dates]:
        if date in df.index:
            # Pega o índice da data do sinal
            signal_idx = df.index.get_loc(date)
            
            # Preço no dia do sinal
            signal_price = df['Close'].iloc[signal_idx]
            
            # Calcula retornos para cada período
            returns = {}
            returns['Data'] = date
            returns['Preço_Sinal'] = signal_price
            
            for period in periods:
                # Verifica se temos dados suficientes
                if signal_idx + period < len(df):
                    future_price = df['Close'].iloc[signal_idx + period]
                    ret = ((future_price - signal_price) / signal_price) * 100
                    returns[f'Retorno_{period}d'] = round(ret, 2)
                    returns[f'Preço_{period}d'] = round(future_price, 2)
                else:
                    returns[f'Retorno_{period}d'] = None
                    returns[f'Preço_{period}d'] = None
            
            results.append(returns)
    
    return pd.DataFrame(results)

def analyze_pattern_success(returns_df: pd.DataFrame, periods: List[int]) -> Dict:
    """
    Analisa a taxa de sucesso do padrão
    """
    results = {}
    
    for period in periods:
        ret_col = f'Retorno_{period}d'
        valid_returns = returns_df[ret_col].dropna()
        
        if len(valid_returns) > 0:
            success_rate = (valid_returns > 0).mean() * 100
            avg_gain = valid_returns[valid_returns > 0].mean()
            avg_loss = valid_returns[valid_returns < 0].mean()
            
            results[period] = {
                'Total_Sinais': len(valid_returns),
                'Taxa_Sucesso': round(success_rate, 2),
                'Retorno_Médio_Positivo': round(avg_gain, 2) if not pd.isna(avg_gain) else 0,
                'Retorno_Médio_Negativo': round(avg_loss, 2) if not pd.isna(avg_loss) else 0
            }
    
    return results

def main():
    # Períodos para análise
    periods = [5, 10, 20]
    
    # Lista todas as ações
    stocks = [f.replace('.csv', '') for f in os.listdir('DB') if f.endswith('.csv')]
    print(f"\nAnalisando {len(stocks)} ações...")
    
    all_results = []
    stocks_analyzed = 0
    patterns_found = 0
    
    # Analisa cada ação
    for stock in stocks:
        df = load_stock_data(stock)
        if len(df) > 0:
            stocks_analyzed += 1
            # Detecta padrões
            signals = detect_bullish_engulfing(df)
            
            if signals.any():
                patterns_found += signals.sum()
                # Calcula retornos
                returns = calculate_future_returns(df, signals, periods)
                if len(returns) > 0:
                    returns['Stock'] = stock
                    all_results.append(returns)
    
    print(f"\nAções analisadas: {stocks_analyzed}")
    print(f"Total de padrões encontrados: {patterns_found}")
    
    # Combina resultados de todas as ações
    if all_results:
        final_results = pd.concat(all_results, ignore_index=True)
        
        # Analisa resultados gerais
        success_stats = analyze_pattern_success(final_results, periods)
        
        # Salva resultados
        final_results.to_csv('engulfing_results.csv', index=False)
        
        # Imprime estatísticas
        print("\nEstatísticas do Padrão Engolfo de Alta:")
        print("-" * 50)
        for period, stats in success_stats.items():
            print(f"\nPeríodo de {period} dias:")
            for metric, value in stats.items():
                print(f"{metric}: {value}")
    else:
        print("Nenhum padrão encontrado nas ações analisadas.")

if __name__ == "__main__":
    main() 