import pandas as pd
import yfinance as yf
import time
import os
from datetime import datetime, timedelta

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
                          group_by='ticker')
        
        print(f"✅ Dados recebidos")
        
        # Processar cada empresa do lote
        for ticker in tickers_batch:
            try:
                # Extrair dados da empresa específica do batch
                if ticker in data.columns.get_level_values(0):
                    ticker_data = data[ticker]  # Método correto para MultiIndex
                    
                    if len(ticker_data) >= 10:  # Mínimo absoluto
                        # Salvar CSV
                        filename = f"nasdaq_database/{ticker}.csv"
                        ticker_data.to_csv(filename)
                        print(f"✅ {ticker} - {len(ticker_data)} dias")
                        success_count += 1
                    else:
                        print(f"❌ {ticker} - Poucos dados ({len(ticker_data)} dias)")
                else:
                    print(f"❌ {ticker} - Não encontrado no batch")
                    
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
                hist = stock.history(start=start_date, end=end_date)
                
                if len(hist) >= 10:
                    filename = f"nasdaq_database/{ticker}_{timestamp}.csv"
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
        df = pd.read_csv('tickers.csv')
        all_tickers = df['ticker'].tolist()
        print(f"📋 {len(all_tickers)} tickers carregados")
    except:
        print("❌ Erro ao carregar tickers.csv")
        return
    
    # Criar diretório se não existir
    os.makedirs('nasdaq_database', exist_ok=True)
    
    # Processar em lotes maiores (otimizado para batch download)
    batch_size = 100  # Pode ser maior já que é 1 request por lote
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
            print(f"⏸️  Aguardando 3 segundos...")
            time.sleep(3)  # Reduzido de 5s para 3s
    
    # Resumo final
    elapsed = datetime.now() - start_time
    print(f"\n🏁 CONCLUÍDO")
    print(f"✅ {total_success}/{len(all_tickers)} sucessos")
    print(f"⏱️  Tempo total: {elapsed}")
    print(f"📁 Arquivos salvos em: nasdaq_database/")
    print(f"🚀 Otimização: ~{batch_size}x menos requests!")

if __name__ == "__main__":
    main() 