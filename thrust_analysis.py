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
        df = df.dropna()  # Remove linhas com valores ausentes
        if len(df) > 0:
            df['Date'] = pd.to_datetime(df['Date'])
            df.set_index('Date', inplace=True)
    
    return df

def detect_thrust_pattern(df: pd.DataFrame, price_period: int = 20, volume_period: int = 10) -> pd.Series:
    """
    Detecta o padrão de Força Compradora (Thrust) com filtros mais rigorosos
    
    Parâmetros:
    - price_period: Período para calcular a máxima anterior e média móvel (default: 20 dias)
    - volume_period: Período para calcular a média do volume (default: 10 dias)
    """
    # Calcula indicadores técnicos
    rolling_high = df['High'].rolling(window=price_period).max().shift(1)
    volume_ma = df['Volume'].rolling(window=volume_period).mean().shift(1)
    price_ma = df['Close'].rolling(window=price_period).mean().shift(1)
    
    # 1. Condição de preço: fechamento acima da máxima anterior
    price_breakout = df['Close'] > rolling_high
    
    # 2. Tamanho do rompimento: pelo menos 2% acima da máxima
    breakout_size = (df['Close'] - rolling_high) / rolling_high * 100
    significant_breakout = breakout_size > 2.0
    
    # 3. Volume muito expressivo: 200% acima da média
    volume_surge = df['Volume'] > (volume_ma * 3.0)
    
    # 4. Tendência de alta: preço acima da média móvel
    uptrend = df['Close'] > price_ma
    
    # 5. Liquidez mínima: volume médio maior que 100,000
    good_liquidity = volume_ma > 100000
    
    # 6. Movimento consistente: fechamento próximo da máxima do dia
    strong_close = (df['High'] - df['Close']) / (df['High'] - df['Low']) < 0.3
    
    # Combina todas as condições
    thrust_pattern = (
        price_breakout &        # Rompimento de preço
        significant_breakout &  # Rompimento significativo
        volume_surge &         # Volume expressivo
        uptrend &             # Tendência de alta
        good_liquidity &      # Boa liquidez
        strong_close          # Fechamento forte
    )
    
    return thrust_pattern

def calculate_future_returns(df: pd.DataFrame, signal_dates: pd.Series, periods: List[int]) -> pd.DataFrame:
    """
    Calcula os retornos futuros após cada sinal
    """
    results = []
    
    for date in signal_dates.index[signal_dates]:
        if date in df.index:
            signal_idx = df.index.get_loc(date)
            signal_price = df['Close'].iloc[signal_idx]
            
            # Dados do sinal
            returns = {
                'Data': date,
                'Ativo': df.name if hasattr(df, 'name') else 'Unknown',
                'Preço_Sinal': signal_price,
                'Volume': df['Volume'].iloc[signal_idx],
                'Volume_Medio': df['Volume'].rolling(window=10).mean().shift(1).iloc[signal_idx],
                'Aumento_Volume_%': round((df['Volume'].iloc[signal_idx] / df['Volume'].rolling(window=10).mean().shift(1).iloc[signal_idx] - 1) * 100, 2),
                'Tamanho_Rompimento_%': round((df['Close'].iloc[signal_idx] / df['High'].rolling(window=20).max().shift(1).iloc[signal_idx] - 1) * 100, 2)
            }
            
            # Calcula retornos para diferentes períodos
            for period in periods:
                if signal_idx + period < len(df):
                    future_price = df['Close'].iloc[signal_idx + period]
                    ret = ((future_price - signal_price) / signal_price) * 100
                    max_ret = ((df['High'].iloc[signal_idx:signal_idx+period+1].max() - signal_price) / signal_price) * 100
                    min_ret = ((df['Low'].iloc[signal_idx:signal_idx+period+1].min() - signal_price) / signal_price) * 100
                    
                    returns[f'Retorno_{period}d'] = round(ret, 2)
                    returns[f'Retorno_Máximo_{period}d'] = round(max_ret, 2)
                    returns[f'Retorno_Mínimo_{period}d'] = round(min_ret, 2)
                else:
                    returns[f'Retorno_{period}d'] = None
                    returns[f'Retorno_Máximo_{period}d'] = None
                    returns[f'Retorno_Mínimo_{period}d'] = None
            
            results.append(returns)
    
    return pd.DataFrame(results)

def analyze_pattern_success(returns_df: pd.DataFrame, periods: List[int]) -> Dict:
    """
    Analisa a taxa de sucesso do padrão
    """
    results = {}
    
    for period in periods:
        ret_col = f'Retorno_{period}d'
        max_col = f'Retorno_Máximo_{period}d'
        min_col = f'Retorno_Mínimo_{period}d'
        
        valid_returns = returns_df[ret_col].dropna()
        valid_max = returns_df[max_col].dropna()
        valid_min = returns_df[min_col].dropna()
        
        if len(valid_returns) > 0:
            success_rate = (valid_returns > 0).mean() * 100
            avg_gain = valid_returns[valid_returns > 0].mean()
            avg_loss = valid_returns[valid_returns < 0].mean()
            
            results[period] = {
                'Total_Sinais': len(valid_returns),
                'Taxa_Sucesso': round(success_rate, 2),
                'Retorno_Médio_Positivo': round(avg_gain, 2) if not pd.isna(avg_gain) else 0,
                'Retorno_Médio_Negativo': round(avg_loss, 2) if not pd.isna(avg_loss) else 0,
                'Relação_Ganho_Perda': round(abs(avg_gain/avg_loss) if avg_loss != 0 else 0, 2),
                'Máximo_Alcançado': round(valid_max.max(), 2),
                'Mínimo_Alcançado': round(valid_min.min(), 2),
                'Média_Máximos': round(valid_max.mean(), 2),
                'Média_Mínimos': round(valid_min.mean(), 2)
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
            df.name = stock  # Adiciona o nome do ativo ao DataFrame
            stocks_analyzed += 1
            
            # Detecta padrões
            signals = detect_thrust_pattern(df)
            
            if signals.any():
                patterns_found += signals.sum()
                # Calcula retornos
                returns = calculate_future_returns(df, signals, periods)
                if len(returns) > 0:
                    all_results.append(returns)
    
    print(f"\nAções analisadas: {stocks_analyzed}")
    print(f"Total de padrões encontrados: {patterns_found}")
    
    # Combina resultados de todas as ações
    if all_results:
        final_results = pd.concat(all_results, ignore_index=True)
        
        # Analisa resultados gerais
        success_stats = analyze_pattern_success(final_results, periods)
        
        # Salva resultados detalhados
        final_results.to_csv('thrust_results_filtered.csv', index=False)
        
        # Imprime estatísticas
        print("\nEstatísticas do Padrão de Força Compradora (Thrust) - Filtros Rigorosos:")
        print("-" * 75)
        for period, stats in success_stats.items():
            print(f"\nPeríodo de {period} dias:")
            for metric, value in stats.items():
                print(f"{metric}: {value}")
        
        # Encontra os melhores sinais (maior retorno em 10 dias)
        best_signals = final_results.nlargest(10, 'Retorno_10d')
        print("\nTop 10 Melhores Sinais:")
        print("-" * 75)
        for _, signal in best_signals.iterrows():
            print(f"\nAtivo: {signal['Ativo']}")
            print(f"Data: {signal['Data']}")
            print(f"Retorno 10d: {signal['Retorno_10d']}%")
            print(f"Aumento Volume: {signal['Aumento_Volume_%']}%")
            print(f"Tamanho Rompimento: {signal['Tamanho_Rompimento_%']}%")
            print(f"Máximo Alcançado 10d: {signal['Retorno_Máximo_10d']}%")
            print(f"Mínimo Alcançado 10d: {signal['Retorno_Mínimo_10d']}%")
    
    else:
        print("Nenhum padrão encontrado nas ações analisadas.")

if __name__ == "__main__":
    main() 