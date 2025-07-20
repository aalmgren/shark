import pandas as pd
import yfinance as yf
import time
import os
from datetime import datetime, timedelta
import warnings

# Suprimir warnings do yfinance
warnings.filterwarnings('ignore', category=FutureWarning)

def filter_valid_tickers(tickers):
    """Filtra tickers válidos, removendo formatos problemáticos"""
    filtered = []
    removed = []
    
    for ticker in tickers:
        # Remover tickers com formatos problemáticos
        if any(pattern in ticker for pattern in ['.UN', '-', 'WARR', 'UNIT']):
            removed.append(ticker)
        else:
            filtered.append(ticker)
    
    print(f"🧹 Filtrados {len(removed)} tickers problemáticos")
    if removed[:10]:  # Mostrar primeiros 10 removidos
        print(f"   Exemplos removidos: {removed[:10]}")
    
    return filtered

def download_batch_data(tickers_batch, batch_num, total_batches):
    """Baixa dados para um lote de tickers usando batch download"""
    print(f"\n📦 LOTE {batch_num}/{total_batches} - {len(tickers_batch)} empresas")
    print("=" * 50)
    
    success_count = 0
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    
    try:
        # Baixar dados dos últimos 6 meses para todas as empresas do lote
        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)
        
        print(f"📊 Baixando {len(tickers_batch)} empresas em 1 request...", end=" ")
        
        # BATCH DOWNLOAD - 1 request para múltiplas empresas
        data = yf.download(tickers_batch, 
                          start=start_date, 
                          end=end_date, 
                          progress=False,
                          group_by='ticker',
                          auto_adjust=True,  # Definir explicitamente
                          show_errors=False)  # Suprimir erros do yfinance
        
        print(f"✅ Dados recebidos")
        
        # Processar cada empresa do lote
        for ticker in tickers_batch:
            try:
                # Para um único ticker, dados vêm sem MultiIndex
                if len(tickers_batch) == 1:
                    ticker_data = data
                else:
                    # Para múltiplos tickers, extrair dados da empresa específica
                    if hasattr(data.columns, 'get_level_values') and ticker in data.columns.get_level_values(0):
                        ticker_data = data[ticker]
                    else:
                        # Tentar acesso direto se não há MultiIndex
                        if ticker in data.columns:
                            ticker_data = data[ticker]
                        else:
                            print(f"❌ {ticker} - Não encontrado nos dados")
                            continue
                
                # Verificar se há dados suficientes
                if len(ticker_data) >= 10:  # Mínimo absoluto
                    # Remover linhas com todos os valores NaN
                    ticker_data = ticker_data.dropna(how='all')
                    
                    if len(ticker_data) >= 5:  # Ainda tem dados após limpeza
                        # Salvar CSV
                        filename = f"DB/{ticker}.csv"
                        ticker_data.to_csv(filename)
                        print(f"✅ {ticker} - {len(ticker_data)} dias")
                        success_count += 1
                    else:
                        print(f"❌ {ticker} - Dados insuficientes após limpeza")
                else:
                    print(f"❌ {ticker} - Poucos dados ({len(ticker_data) if hasattr(ticker_data, '__len__') else 0} dias)")
                    
            except Exception as e:
                print(f"❌ {ticker} - Erro: {str(e)[:30]}")
                continue
        
    except Exception as e:
        print(f"❌ Erro no batch download: {str(e)[:50]}")
        # Fallback: tentar individualmente se o batch falhar
        print("🔄 Tentando download individual...")
        for ticker in tickers_batch:
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(start=start_date, end=end_date, auto_adjust=True)
                
                if len(hist) >= 10:
                    filename = f"DB/{ticker}.csv"
                    hist.to_csv(filename)
                    print(f"✅ {ticker} - {len(hist)} dias (individual)")
                    success_count += 1
                else:
                    print(f"❌ {ticker} - Sem dados")
                    
                time.sleep(0.1)  # Delay entre requests individuais
                
            except Exception as e:
                print(f"❌ {ticker} - Erro individual: {str(e)[:30]}")
                continue
    
    print(f"\n📊 Lote {batch_num}: {success_count}/{len(tickers_batch)} sucessos")
    return success_count

def main():
    """Download otimizado com batch download"""
    print("🚀 DOWNLOAD MASSIVO OTIMIZADO - BATCH DOWNLOAD")
    print("=" * 60)
    
    # Carregar tickers
    try:
        df = pd.read_csv('tick/tickers.csv')
        all_tickers = df['ticker'].unique().tolist()  # Remove duplicatas
        print(f"📋 {len(df)} tickers carregados, {len(all_tickers)} únicos")
    except:
        print("❌ Erro ao carregar tick/tickers.csv")
        return
    
    # Filtrar tickers válidos
    all_tickers = filter_valid_tickers(all_tickers)
    print(f"✅ {len(all_tickers)} tickers válidos para download")
    
    # Criar diretório se não existir
    os.makedirs('DB', exist_ok=True)
    
    # Processar em lotes menores para melhor controle de erros
    batch_size = 50  # Reduzido para melhor controle
    total_batches = (len(all_tickers) + batch_size - 1) // batch_size
    total_success = 0
    
    print(f"🎯 {total_batches} lotes de {batch_size} empresas")

    start_time = datetime.now()
    
    for i in range(0, len(all_tickers), batch_size):
        batch_tickers = all_tickers[i:i+batch_size]
        batch_num = (i // batch_size) + 1
        
        # Download do lote otimizado
        batch_success = download_batch_data(batch_tickers, batch_num, total_batches)
        total_success += batch_success
        
        # Delay menor entre lotes (exceto último)
        if batch_num < total_batches:
            print(f"⏸️  Aguardando 2 segundos...")
            time.sleep(2)  # Reduzido para 2s
    
    # Resumo final
    elapsed = datetime.now() - start_time
    print(f"\n🏁 CONCLUÍDO")
    print(f"✅ {total_success}/{len(all_tickers)} sucessos")
    print(f"📈 Taxa de sucesso: {(total_success/len(all_tickers)*100):.1f}%")
    print(f"⏱️  Tempo total: {elapsed}")
    print(f"📁 Arquivos salvos em: DB/")

if __name__ == "__main__":
    main() 