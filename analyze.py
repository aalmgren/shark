import pandas as pd
import numpy as np
import os
from datetime import datetime
import multiprocessing as mp
from functools import partial

def process_file(file_info):
    """Processa um único arquivo CSV"""
    file_path, filename = file_info
    try:
        # Ignorar warrants, units, rights, preferreds e outros derivativos
        ticker = filename.split('_')[0]
        if ticker.endswith(('W', 'WS', 'U', 'R', 'P', 'PR', 'X', 'L', 'Z')):
            return None
            
        # Ler apenas colunas necessárias
        df = pd.read_csv(file_path, usecols=['Date', 'Close', 'Volume'])
        if len(df) < 50:
            return None
            
        df['ticker'] = ticker
        df['Date'] = pd.to_datetime(df['Date'], utc=True)
        return df
    except:
        pass
    return None

def detect_volume_pattern(ticker_data):
    """Detecta padrões de volume - gradual ou recente"""
    # Calcular MA3 do volume em dinheiro
    ticker_data['volume_usd'] = ticker_data['Volume'] * ticker_data['Close']
    ticker_data['volume_ma3'] = ticker_data['volume_usd'].rolling(window=3).mean()
    
    # Últimos 20 dias para análise
    recent_data = ticker_data.tail(20).copy()
    volume_mean = recent_data['volume_usd'].mean()
    
    # Verificar crescimento dos últimos dias (MA3)
    last_3_ma = recent_data['volume_ma3'].tail(3).values
    last_5_ma = recent_data['volume_ma3'].tail(5).values
    
    # Verificar se há volumes decrescentes após spike nos últimos dias
    last_3_volumes = recent_data['volume_usd'].tail(3).values
    if len(last_3_volumes) >= 3:
        # Se tiver um spike seguido de volumes decrescentes, rejeita
        if last_3_volumes[0] > (volume_mean * 2):  # Volume 2x maior que média
            if last_3_volumes[1] < last_3_volumes[0] and last_3_volumes[2] < last_3_volumes[1]:
                return False
    
    # Padrão Gradual (4+ dias)
    gradual_pattern = False
    if len(last_5_ma) >= 4:
        # Verificar se há 4 dias consecutivos de crescimento
        for i in range(len(last_5_ma)-3):
            if all(last_5_ma[j] > last_5_ma[j-1] for j in range(i+1, i+4)):
                gradual_pattern = True
                break
    
    # Padrão Recente (2-3 dias)
    recent_pattern = False
    if len(last_3_ma) >= 2:
        # Volume crescente nos últimos 2-3 dias
        volume_growing = all(last_3_ma[i] > last_3_ma[i-1] for i in range(1, len(last_3_ma)))
        # Volume atual pelo menos 2x a média anterior
        volume_significant = last_3_ma[-1] > 2 * volume_mean
        # Preço subindo junto
        price_up = recent_data['Close'].iloc[-1] > recent_data['Close'].iloc[-2]
        
        # Verificar se não há queda significativa após crescimento
        if volume_growing:
            last_volumes = recent_data['volume_usd'].tail(3).values
            if len(last_volumes) >= 2:
                # Se o último volume for significativamente menor que o anterior, rejeita
                if last_volumes[-1] < last_volumes[-2] * 0.7:  # Queda de mais de 30%
                    volume_growing = False
        
        recent_pattern = volume_growing and volume_significant and price_up
    
    return gradual_pattern or recent_pattern

def analyze_ticker(ticker_data):
    """Analisa um ticker para padrões de momentum"""
    try:
        # Ordenar por data
        ticker_data = ticker_data.sort_values('Date')
        
        ticker = ticker_data['ticker'].iloc[0]
        
        # Verificar mínimo de dados e último preço
        if len(ticker_data) < 90:
            return None
            
        # Calcular volume em dinheiro (quantidade × preço)
        ticker_data['volume_usd'] = ticker_data['Volume'] * ticker_data['Close']
            
        # Calcular médias de volume e preço
        last_7d = ticker_data.tail(7)
        previous_90d = ticker_data.iloc[-97:-7] if len(ticker_data) >= 97 else ticker_data.iloc[:-7]
        
        volume_usd_90d = previous_90d['volume_usd'].mean()
        volume_usd_7d = last_7d['volume_usd'].mean()
        volume_90d = previous_90d['Volume'].mean()
        volume_7d = last_7d['Volume'].mean()
        price_90d_avg = ticker_data['Close'].tail(90).mean()
        
        # Filtros
        if volume_usd_90d < 10000000:  # Filtro de liquidez - volume em USD mínimo de $10M/dia
            return None
            
        if price_90d_avg <= 5.0:  # Filtro de preço médio
            return None
        
        # Calcular variações de preço
        current_price = ticker_data['Close'].iloc[-1]
        
        # Filtro de preço atual
        if current_price <= 10.0:
            return None
            
        price_7d_ago = ticker_data['Close'].iloc[-7]
        price_30d_ago = ticker_data['Close'].iloc[-30]
        
        price_change_7d = ((current_price - price_7d_ago) / price_7d_ago) * 100
        price_change_30d = ((current_price - price_30d_ago) / price_30d_ago) * 100
        
        # Filtrar ações que desvalorizaram
        if price_change_7d <= 0 or price_change_30d <= 0:
            return None
        
        # Ratio de volume em dinheiro
        volume_ratio = volume_usd_7d / volume_usd_90d if volume_usd_90d > 0 else 0
        
        # Nova verificação de padrão de volume
        if volume_ratio >= 1.5 and detect_volume_pattern(ticker_data):  # Candidato a momentum detectado
            # Score baseado em volume e preço
            score = volume_ratio * (1 + price_change_7d / 100)
            
            return {
                'ticker': ticker_data['ticker'].iloc[0],
                'ratio': volume_ratio,
                'volume_7d': volume_7d,
                'volume_90d': volume_90d,
                'volume_usd_7d': volume_usd_7d,
                'volume_usd_90d': volume_usd_90d,
                'price': current_price,
                'price_90d_avg': price_90d_avg,
                'change_7d': price_change_7d,
                'change_30d': price_change_30d,
                'score': score
            }
    except Exception as e:
        pass
    return None

def process_nasdaq_data():
    """MOMENTUM ANALYSIS - Detecta acumulação institucional via análise de volume"""
    print("⚡ DETECTING MOMENTUM - FINDING HIGH-MOMENTUM STOCKS")
    print("=" * 60)
    
    # 0. Carregar dados de tickers com setores e indústrias
    ticker_info_path = 'tick/tickers_with_sectors_deduped.csv'
    if not os.path.exists(ticker_info_path):
        print(f"❌ Arquivo de informações de ticker não encontrado em {ticker_info_path}")
        return
        
    column_names = ['sector', 'industry', 'mcap', 'conid', 'name', 'ticker', 'exchange']
    ticker_info_df = pd.read_csv(ticker_info_path, header=None, names=column_names)
    print(f"ℹ️ Carregadas informações de {ticker_info_df['ticker'].nunique()} tickers.")
    
    # 1. Listar todos os arquivos CSV
    all_files = []
    for data_dir in ['DB', 'additional_database']:
        if os.path.exists(data_dir):
            files = [(os.path.join(data_dir, f), f) for f in os.listdir(data_dir) if f.endswith('.csv')]
            all_files.extend(files)
    
    if not all_files:
        print("❌ Nenhum arquivo CSV encontrado")
        return
    
    print(f"📊 Processando {len(all_files)} arquivos...")
    
    # 2. Processar arquivos em paralelo
    with mp.Pool() as pool:
        processed = pool.map(process_file, all_files)
        all_data = [df for df in processed if df is not None]
    
    if not all_data:
        print("❌ Nenhum dado válido encontrado")
        return
    
    # 3. Consolidar dados
    df = pd.concat(all_data, ignore_index=True)
    print(f"✅ Dados carregados: {len(df):,} registros de {df['ticker'].nunique()} empresas")
    
    # 4. Analisar cada ticker em paralelo
    ticker_groups = [group for _, group in df.groupby('ticker')]
    with mp.Pool() as pool:
        analyzed = pool.map(analyze_ticker, ticker_groups)
        candidates = [candidate for candidate in analyzed if candidate is not None]
    
    if not candidates:
        print("❌ Nenhum ativo com momentum detectado")
        return
    
    # 5. Ordenar e salvar resultados
    momentum_df = pd.DataFrame(candidates)
    
    # Adicionar informações de setor e indústria
    momentum_df = pd.merge(momentum_df, ticker_info_df[['ticker', 'sector', 'industry']], on='ticker', how='left')
    momentum_df['sector'].fillna('Unknown', inplace=True)
    momentum_df['industry'].fillna('Unknown', inplace=True)
    
    momentum_df = momentum_df.sort_values('score', ascending=False)
    
    # Salvar todos os candidatos
    momentum_df.to_csv('momentum_candidates.csv', index=False)
    
    # Salvar candidatos com momentum latente (baixa variação de preço)
    latent_momentum = momentum_df[momentum_df['change_7d'] <= 5.0]
    latent_momentum.to_csv('latent_momentum_candidates.csv', index=False)
    
    # 6. Exibir resultados
    print("\n⚡ TOP 15 MOMENTUM CANDIDATES!")
    print("=" * 115)
    print("TICKER  RATIO   VOL_7D($M)   VOL_90D($M)   PREÇO    AVG90    7D%    30D%    SCORE")
    print("-" * 115)
    
    for _, candidate in momentum_df.head(15).iterrows():
        print(f"{candidate['ticker']:<7} {candidate['ratio']:.1f}x   ${candidate['volume_usd_7d']/1000000:,.1f}M    ${candidate['volume_usd_90d']/1000000:,.1f}M     ${candidate['price']:<7.2f} {candidate['price_90d_avg']:<7.2f} {candidate['change_7d']:>6.1f}% {candidate['change_30d']:>6.1f}% {candidate['score']:.1f}")
    
    # Exibir Latent Momentum
    print("\n🤫 LATENT MOMENTUM (Variação de preço ≤ 5%):")
    print("=" * 115)
    print("TICKER  RATIO   VOL_7D($M)   VOL_90D($M)   PREÇO    AVG90    7D%    30D%    SCORE")
    print("-" * 115)
    
    for _, candidate in latent_momentum.iterrows():
        print(f"{candidate['ticker']:<7} {candidate['ratio']:.1f}x   ${candidate['volume_usd_7d']/1000000:,.1f}M    ${candidate['volume_usd_90d']/1000000:,.1f}M     ${candidate['price']:<7.2f} {candidate['price_90d_avg']:<7.2f} {candidate['change_7d']:>6.1f}% {candidate['change_30d']:>6.1f}% {candidate['score']:.1f}")
    
    # Estatísticas
    print(f"\n📊 CATEGORIZAÇÃO DO MOMENTUM:")
    print(f"⚡ VERY HIGH MOMENTUM (3x+ volume):     {len(momentum_df[momentum_df['ratio'] >= 3])} ativos")
    print(f"⚡ HIGH MOMENTUM (2-3x volume):         {len(momentum_df[(momentum_df['ratio'] >= 2) & (momentum_df['ratio'] < 3)])} ativos")
    print(f"⚡ MOMENTUM (1.5-2x volume):          {len(momentum_df[(momentum_df['ratio'] >= 1.5) & (momentum_df['ratio'] < 2)])} ativos")
    print(f"🤫 LATENT MOMENTUM (preço estável ≤5%): {len(latent_momentum)} ativos")
    
    print(f"\n💾 ARQUIVOS ATUALIZADOS:")
    print(f"⚡ Todos os candidatos:   momentum_candidates.csv ({len(momentum_df)} tickers)")
    print(f"🤫 Momentum latente:      latent_momentum_candidates.csv ({len(latent_momentum)} tickers)")
    print(f"📅 Última atualização: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    print("\n✅ MOMENTUM ANALYSIS CONCLUÍDA!")
    print("🚀 Hora de surfar na onda do momentum!")

if __name__ == "__main__":
    process_nasdaq_data() 