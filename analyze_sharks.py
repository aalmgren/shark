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

def detect_price_pattern(ticker_data):
    """Detecta padrões de preço - rejeita apenas 3 dias consecutivos de queda após spike de volume"""
    try:
        ticker = ticker_data['ticker'].iloc[0]
        
        # Calcular volume em dinheiro
        ticker_data['volume_usd'] = ticker_data['Volume'] * ticker_data['Close']
        
        # Últimos 20 dias para análise
        recent_data = ticker_data.tail(20).copy()
        volume_mean = recent_data['volume_usd'].mean()
        
        # Verificar se há preços decrescentes após spike nos últimos dias
        last_4_volumes = recent_data['volume_usd'].tail(4).values
        last_4_prices = recent_data['Close'].tail(4).values
        
        if len(last_4_volumes) >= 4 and len(last_4_prices) >= 4:
            # Se tiver um spike de volume seguido de 3 preços decrescentes, rejeita
            if last_4_volumes[0] > (volume_mean * 2):  # Volume 2x maior que média
                if (last_4_prices[1] < last_4_prices[0] and 
                    last_4_prices[2] < last_4_prices[1] and 
                    last_4_prices[3] < last_4_prices[2]):  # 3 dias consecutivos de queda de preço
                    if ticker == 'QS':
                        print(f"❌ QS: Rejeitado por preços decrescentes por 3 dias após spike")
                        print(f"Preços: {[f'${p:.2f}' for p in last_4_prices]}")
                    return False
        return True
    except Exception as e:
        return True

def analyze_ticker(ticker_data):
    """Analisa um ticker para padrões de volume"""
    try:
        # Ordenar por data
        ticker_data = ticker_data.sort_values('Date')
        
        ticker = ticker_data['ticker'].iloc[0]
        if ticker == 'QS':
            print(f"\nDEBUG QS - Início da análise")
        
        # Verificar mínimo de dados e último preço
        if len(ticker_data) < 90:
            if ticker == 'QS':
                print(f"❌ QS: Barrado por ter menos que 90 dias de dados ({len(ticker_data)} dias)")
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
        
        if ticker == 'QS':
            print(f"Volume USD 90d: ${volume_usd_90d/1000000:.1f}M")
            print(f"Volume USD 7d: ${volume_usd_7d/1000000:.1f}M")
            print(f"Preço médio 90d: ${price_90d_avg:.2f}")
        
        # Filtros
        if volume_usd_90d < 10000000:  # Filtro de liquidez - volume em USD mínimo de $10M/dia
            if ticker == 'QS':
                print(f"❌ QS: Barrado por volume USD 90d baixo (${volume_usd_90d/1000000:.1f}M < $10M)")
            return None
            
        if price_90d_avg <= 5.0:  # Filtro de preço médio
            if ticker == 'QS':
                print(f"❌ QS: Barrado por preço médio 90d baixo (${price_90d_avg:.2f} <= $5.00)")
            return None
        
        # Calcular variações de preço
        current_price = ticker_data['Close'].iloc[-1]
        
        # Filtro de preço atual
        if current_price <= 10.0:
            if ticker == 'QS':
                print(f"❌ QS: Barrado por preço atual baixo (${current_price:.2f} <= $10.00)")
            return None
            
        price_7d_ago = ticker_data['Close'].iloc[-7]
        price_30d_ago = ticker_data['Close'].iloc[-30]
        
        price_change_7d = ((current_price - price_7d_ago) / price_7d_ago) * 100
        price_change_30d = ((current_price - price_30d_ago) / price_30d_ago) * 100
        
        if ticker == 'QS':
            print(f"Variação 7d: {price_change_7d:.1f}%")
            print(f"Variação 30d: {price_change_30d:.1f}%")
        
        # Filtrar ações que desvalorizaram
        if price_change_7d <= 0 or price_change_30d <= 0:
            if ticker == 'QS':
                print(f"❌ QS: Barrado por variação negativa (7d: {price_change_7d:.1f}%, 30d: {price_change_30d:.1f}%)")
            return None
        
        # Ratio de volume em dinheiro
        volume_ratio = volume_usd_7d / volume_usd_90d if volume_usd_90d > 0 else 0
        
        if ticker == 'QS':
            print(f"Volume ratio: {volume_ratio:.1f}x")
        
        # Nova verificação de padrão de volume
        if volume_ratio >= 1.5 and detect_price_pattern(ticker_data):  # Shark detectado
            if ticker == 'QS':
                print(f"✅ QS: Passou em todos os filtros!")
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
        elif ticker == 'QS':
            if volume_ratio < 1.5:
                print(f"❌ QS: Barrado por volume ratio baixo ({volume_ratio:.1f}x < 1.5x)")
            else:
                print(f"❌ QS: Barrado por não ter padrão de volume válido")
    except Exception as e:
        if ticker == 'QS':
            print(f"❌ QS: Erro na análise: {str(e)}")
        pass
    return None

def process_nasdaq_data():
    """NADAR COM OS SHARKS - Detecta acumulação institucional via análise de volume"""
    print("🦈 DETECTANDO SMART MONEY - NADAR COM OS SHARKS")
    print("=" * 60)
    
    # 1. Listar todos os arquivos CSV
    all_files = []
    for data_dir in ['nasdaq_database', 'additional_database']:
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
        sharks = [shark for shark in analyzed if shark is not None]
    
    if not sharks:
        print("❌ Nenhum shark detectado")
        return
    
    # 5. Ordenar e salvar resultados
    sharks_df = pd.DataFrame(sharks)
    sharks_df = sharks_df.sort_values('score', ascending=False)
    
    # Salvar todos os sharks
    sharks_df.to_csv('institutional_accumulation_candidates.csv', index=False)
    
    # Salvar silent sharks (baixa variação de preço)
    silent_sharks = sharks_df[sharks_df['change_7d'] <= 5.0]
    silent_sharks.to_csv('silent_sharks.csv', index=False)
    
    # 6. Exibir resultados
    print("\n🦈 TOP 15 SHARKS DETECTADOS!")
    print("=" * 115)
    print("TICKER  RATIO   VOL_7D($M)   VOL_90D($M)   PREÇO    AVG90    7D%    30D%    SCORE")
    print("-" * 115)
    
    for _, shark in sharks_df.head(15).iterrows():
        print(f"{shark['ticker']:<7} {shark['ratio']:.1f}x   ${shark['volume_usd_7d']/1000000:,.1f}M    ${shark['volume_usd_90d']/1000000:,.1f}M     ${shark['price']:<7.2f} ${shark['price_90d_avg']:<7.2f} {shark['change_7d']:>6.1f}% {shark['change_30d']:>6.1f}% {shark['score']:.1f}")
    
    # Exibir Silent Sharks
    print("\n🤫 SILENT SHARKS (Variação ≤ 5%):")
    print("=" * 115)
    print("TICKER  RATIO   VOL_7D($M)   VOL_90D($M)   PREÇO    AVG90    7D%    30D%    SCORE")
    print("-" * 115)
    
    for _, shark in silent_sharks.iterrows():
        print(f"{shark['ticker']:<7} {shark['ratio']:.1f}x   ${shark['volume_usd_7d']/1000000:,.1f}M    ${shark['volume_usd_90d']/1000000:,.1f}M     ${shark['price']:<7.2f} ${shark['price_90d_avg']:<7.2f} {shark['change_7d']:>6.1f}% {shark['change_30d']:>6.1f}% {shark['score']:.1f}")
    
    # Estatísticas
    print(f"\n📊 CATEGORIZAÇÃO DOS SHARKS:")
    print(f"🦈 MEGA SHARKS (3x+ volume):     {len(sharks_df[sharks_df['ratio'] >= 3])} ações")
    print(f"🦈 BIG SHARKS (2-3x volume):     {len(sharks_df[(sharks_df['ratio'] >= 2) & (sharks_df['ratio'] < 3)])} ações")
    print(f"🦈 SHARKS (1.5-2x volume):       {len(sharks_df[(sharks_df['ratio'] >= 1.5) & (sharks_df['ratio'] < 2)])} ações")
    print(f"🤫 SILENT SHARKS (estável ≤5%):  {len(silent_sharks)} ações")
    
    print(f"\n💾 ARQUIVOS ATUALIZADOS:")
    print(f"🦈 Todos os sharks:   institutional_accumulation_candidates.csv ({len(sharks_df)} tickers)")
    print(f"🤫 Silent sharks:     silent_sharks.csv ({len(silent_sharks)} tickers)")
    print(f"📅 Última atualização: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    print("\n✅ SHARK DETECTION CONCLUÍDA!")
    print("🏊‍♂️ Hora de nadar com os sharks! 🦈")

if __name__ == "__main__":
    process_nasdaq_data() 