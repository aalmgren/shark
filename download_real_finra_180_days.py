#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📊 DOWNLOAD FINRA REAL - 180 DIAS COMPLETOS
Baixa dados FINRA REAIS dos últimos 180 dias para validação estatística
"""

import requests
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import time
from collections import defaultdict

def download_real_finra_180_days():
    """Baixa 180 dias REAIS de dados FINRA"""
    
    # URLs FINRA
    finra_base_url = "https://cdn.finra.org/equity/regsho/daily/CNMSshvol{date}.txt"
    
    # Nossos tickers
    ticker_list = [
        'AMD', 'TLN', 'SNPS', 'DDOG', 'ANET', 'MRVL', 'SVM', 'AVAV', 'ZETA', 
        'FCX', 'RKLB', 'INTR', 'U', 'OUST', 'XP', 'DASH', 'MSFT', 'TTD', 
        'AVGO', 'MA', 'GOOGL', 'NVDA', 'AMZN', 'WBD', 'TRIP', 'VNET', 
        'SOUN', 'BBAI', 'QS'
    ]
    
    print("📊 DOWNLOAD FINRA REAL - 180 DIAS")
    print("=" * 50)
    print(f"🎯 Tickers: {len(ticker_list)}")
    print(f"📅 Objetivo: 180 dias de dados REAIS")
    
    # Coleta dados dia por dia
    all_finra_data = defaultdict(list)
    end_date = datetime.now()
    
    success_days = 0
    total_attempts = 0
    
    print(f"\n🔄 BAIXANDO DADOS FINRA...")
    
    for days_back in range(180):
        current_date = end_date - timedelta(days=days_back)
        
        # Pula finais de semana
        if current_date.weekday() >= 5:
            continue
            
        total_attempts += 1
        date_str = current_date.strftime('%Y%m%d')
        url = finra_base_url.format(date=date_str)
        
        print(f"📈 {current_date.strftime('%d/%m/%Y')}...", end=" ")
        
        try:
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                content = response.text
                lines = content.strip().split('\n')
                
                # Parse das linhas de dados
                data_lines = []
                for line in lines:
                    if '|' in line and not line.startswith('Date') and not line.startswith('Total'):
                        data_lines.append(line)
                
                if data_lines:
                    parsed_data = []
                    for line in data_lines:
                        parts = line.split('|')
                        if len(parts) >= 5:
                            try:
                                symbol = parts[1].strip()
                                if symbol in ticker_list:
                                    parsed_data.append({
                                        'date': current_date.strftime('%Y-%m-%d'),
                                        'symbol': symbol,
                                        'short_volume': int(parts[2].strip()),
                                        'short_exempt_volume': int(parts[3].strip()),
                                        'total_off_exchange_volume': int(parts[4].strip())
                                    })
                            except (ValueError, IndexError):
                                continue
                    
                    if parsed_data:
                        for record in parsed_data:
                            all_finra_data[record['symbol']].append(record)
                        
                        print(f"✅ {len(parsed_data)} registros")
                        success_days += 1
                    else:
                        print("⚪ Sem nossos tickers")
                else:
                    print("❌ Arquivo vazio")
            else:
                print(f"❌ HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ Erro: {e}")
        
        # Delay para não sobrecarregar
        time.sleep(0.1)
    
    print(f"\n📊 RESUMO DOWNLOAD:")
    print(f"✅ Dias tentados: {total_attempts}")
    print(f"✅ Dias com sucesso: {success_days}")
    print(f"🎯 Tickers com dados: {len(all_finra_data)}")
    
    # Combina com dados Yahoo Finance
    print(f"\n🔄 COMBINANDO COM YAHOO FINANCE...")
    
    combined_count = 0
    
    for ticker in ticker_list:
        finra_records = all_finra_data.get(ticker, [])
        
        if not finra_records:
            print(f"❌ {ticker}: Sem dados FINRA")
            continue
            
        print(f"📊 {ticker}: {len(finra_records)} registros FINRA...", end=" ")
        
        try:
            # Dados Yahoo Finance
            start_date = end_date - timedelta(days=200)  # Margem extra
            stock = yf.Ticker(ticker)
            yahoo_data = stock.history(start=start_date, end=end_date)
            yahoo_data.reset_index(inplace=True)
            yahoo_data['date'] = pd.to_datetime(yahoo_data['Date']).dt.tz_localize(None)
            yahoo_data['date'] = yahoo_data['date'].dt.strftime('%Y-%m-%d')
            
            # Converte FINRA para DataFrame
            finra_df = pd.DataFrame(finra_records)
            
            # Merge dos dados
            merged = pd.merge(finra_df, yahoo_data, on='date', how='inner')
            
            if len(merged) > 0:
                # Calcula métricas
                merged['total_market_volume'] = merged['Volume']
                merged['on_exchange_volume'] = merged['total_market_volume'] - merged['total_off_exchange_volume']
                merged['off_exchange_pct'] = (merged['total_off_exchange_volume'] / merged['total_market_volume'] * 100).round(1)
                merged['on_exchange_pct'] = (merged['on_exchange_volume'] / merged['total_market_volume'] * 100).round(1)
                merged['short_pct_of_off_exchange'] = (merged['short_volume'] / merged['total_off_exchange_volume'] * 100).round(1)
                
                # Ordena por data
                merged = merged.sort_values('date').reset_index(drop=True)
                
                # Seleciona colunas finais
                final_cols = [
                    'date', 'symbol', 'total_market_volume', 'Close', 'Open', 'High', 'Low',
                    'total_off_exchange_volume', 'short_volume', 'short_exempt_volume',
                    'on_exchange_volume', 'off_exchange_pct', 'on_exchange_pct', 'short_pct_of_off_exchange'
                ]
                
                final_data = merged[final_cols].copy()
                
                # Salva arquivo
                filename = f"finra_real_180d_{ticker.lower()}.csv"
                final_data.to_csv(filename, index=False)
                
                print(f"✅ {len(final_data)} dias salvos")
                combined_count += 1
                
            else:
                print("❌ Sem overlap de datas")
                
        except Exception as e:
            print(f"❌ Erro: {e}")
    
    print(f"\n🎉 CONCLUÍDO!")
    print(f"✅ Tickers processados: {combined_count}/{len(ticker_list)}")
    print(f"📁 Arquivos: finra_real_180d_[ticker].csv")
    print(f"🚀 Agora você tem 180 dias de dados FINRA REAIS!")
    
    return combined_count

if __name__ == "__main__":
    download_real_finra_180_days()