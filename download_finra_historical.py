#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📈 DOWNLOAD FINRA HISTÓRICO - 180 DIAS
Baixa dados FINRA dos últimos 180 dias usando arquivos TXT diários
"""

import requests
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import io
import time
from collections import defaultdict

class FinraHistoricalDownloader:
    def __init__(self):
        self.finra_base_url = "https://cdn.finra.org/equity/regsho/daily/CNMSshvol{date}.txt"
        self.ticker_list = [
            'AMD', 'TLN', 'SNPS', 'DDOG', 'ANET', 'MRVL', 'SVM', 'AVAV', 'ZETA', 
            'FCX', 'RKLB', 'INTR', 'U', 'OUST', 'XP', 'DASH', 'MSFT', 'TTD', 
            'AVGO', 'MA', 'GOOGL', 'NVDA', 'AMZN', 'WBD', 'TRIP', 'VNET', 
            'SOUN', 'BBAI', 'QS'
        ]
        self.all_finra_data = defaultdict(list)
        
    def download_finra_day(self, date):
        """Baixa dados FINRA de um dia específico"""
        date_str = date.strftime('%Y%m%d')
        url = self.finra_base_url.format(date=date_str)
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                # Parse do arquivo TXT
                content = response.text
                lines = content.strip().split('\n')
                
                # Remove header e footer
                data_lines = []
                for line in lines:
                    if '|' in line and not line.startswith('Date') and not line.startswith('Total'):
                        data_lines.append(line)
                
                if data_lines:
                    # Parse das linhas de dados
                    data = []
                    for line in data_lines:
                        parts = line.split('|')
                        if len(parts) >= 4:
                            try:
                                data.append({
                                    'Date': parts[0].strip(),
                                    'Symbol': parts[1].strip(), 
                                    'ShortVolume': int(parts[2].strip()),
                                    'ShortExemptVolume': int(parts[3].strip()),
                                    'TotalVolume': int(parts[4].strip()) if len(parts) > 4 else 0
                                })
                            except (ValueError, IndexError):
                                continue
                    
                    return pd.DataFrame(data) if data else None
                    
            return None
            
        except Exception as e:
            print(f"❌ Erro ao baixar {date_str}: {e}")
            return None
    
    def download_finra_range(self, days=180):
        """Baixa dados FINRA para um range de dias"""
        print(f"📊 BAIXANDO DADOS FINRA HISTÓRICOS")
        print(f"📅 Período: Últimos {days} dias")
        print(f"🎯 Tickers: {len(self.ticker_list)}")
        print("=" * 60)
        
        end_date = datetime.now()
        success_days = 0
        total_records = 0
        
        for i in range(days):
            current_date = end_date - timedelta(days=i)
            
            # Pula finais de semana
            if current_date.weekday() >= 5:  # 5=Saturday, 6=Sunday
                continue
                
            print(f"📈 Baixando {current_date.strftime('%d/%m/%Y')}...", end=" ")
            
            day_data = self.download_finra_day(current_date)
            
            if day_data is not None and len(day_data) > 0:
                # Filtra apenas nossos tickers
                filtered_data = day_data[day_data['Symbol'].isin(self.ticker_list)]
                
                if len(filtered_data) > 0:
                    # Adiciona data formatada
                    filtered_data['date'] = current_date.strftime('%Y-%m-%d')
                    
                    # Agrupa por ticker
                    for _, row in filtered_data.iterrows():
                        self.all_finra_data[row['Symbol']].append({
                            'date': row['date'],
                            'short_volume': row['ShortVolume'],
                            'short_exempt_volume': row['ShortExemptVolume'], 
                            'total_off_exchange_volume': row['TotalVolume']
                        })
                    
                    print(f"✅ {len(filtered_data)} registros")
                    success_days += 1
                    total_records += len(filtered_data)
                else:
                    print("⚪ Sem dados para nossos tickers")
            else:
                print("❌ Sem dados")
            
            # Delay para não sobrecarregar
            time.sleep(0.1)
        
        print(f"\n📊 RESUMO DOWNLOAD FINRA:")
        print(f"✅ Dias com sucesso: {success_days}")
        print(f"📈 Total de registros: {total_records}")
        print(f"🎯 Tickers com dados: {len(self.all_finra_data)}")
        
        return self.all_finra_data
    
    def combine_with_yahoo(self):
        """Combina dados FINRA com Yahoo Finance"""
        print(f"\n🔄 COMBINANDO COM DADOS DO YAHOO FINANCE")
        print("=" * 50)
        
        combined_results = {}
        
        for ticker in self.ticker_list:
            print(f"📊 Processando {ticker}...", end=" ")
            
            # Dados FINRA
            finra_records = self.all_finra_data.get(ticker, [])
            if not finra_records:
                print("❌ Sem dados FINRA")
                continue
                
            finra_df = pd.DataFrame(finra_records)
            finra_df['date'] = pd.to_datetime(finra_df['date'])
            
            # Dados Yahoo Finance
            try:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=200)  # Margem extra
                
                stock = yf.Ticker(ticker)
                yahoo_data = stock.history(start=start_date, end=end_date)
                yahoo_data.reset_index(inplace=True)
                yahoo_data['date'] = pd.to_datetime(yahoo_data['Date']).dt.tz_localize(None)
                
                # Combina dados
                merged = pd.merge(finra_df, yahoo_data, on='date', how='inner')
                
                if len(merged) > 0:
                    # Calcula métricas
                    merged['total_market_volume'] = merged['Volume']
                    merged['on_exchange_volume'] = merged['total_market_volume'] - merged['total_off_exchange_volume']
                    merged['off_exchange_pct'] = (merged['total_off_exchange_volume'] / merged['total_market_volume'] * 100).round(1)
                    merged['on_exchange_pct'] = (merged['on_exchange_volume'] / merged['total_market_volume'] * 100).round(1)
                    merged['short_pct_of_off_exchange'] = (merged['short_volume'] / merged['total_off_exchange_volume'] * 100).round(1)
                    
                    # Seleciona colunas relevantes
                    final_columns = [
                        'date', 'symbol', 'total_market_volume', 'Close', 'Open', 'High', 'Low',
                        'total_off_exchange_volume', 'short_volume', 'short_exempt_volume',
                        'on_exchange_volume', 'off_exchange_pct', 'on_exchange_pct', 'short_pct_of_off_exchange'
                    ]
                    
                    merged['symbol'] = ticker
                    result_df = merged[final_columns].copy()
                    
                    # Salva arquivo individual
                    filename = f"finra_historical_{ticker.lower()}.csv"
                    result_df.to_csv(filename, index=False)
                    
                    combined_results[ticker] = result_df
                    print(f"✅ {len(result_df)} dias combinados")
                else:
                    print("❌ Sem sobreposição de datas")
                    
            except Exception as e:
                print(f"❌ Erro: {e}")
                continue
        
        print(f"\n📊 RESUMO FINAL:")
        print(f"✅ Tickers processados: {len(combined_results)}")
        
        for ticker, df in combined_results.items():
            avg_off_pct = df['off_exchange_pct'].mean()
            print(f"   {ticker}: {len(df)} dias, {avg_off_pct:.1f}% off-exchange médio")
        
        return combined_results
    
    def run_full_download(self):
        """Executa download completo"""
        print("🚀 INICIANDO DOWNLOAD FINRA HISTÓRICO COMPLETO")
        print("=" * 60)
        
        # Download FINRA
        finra_data = self.download_finra_range(days=180)
        
        if not finra_data:
            print("❌ Nenhum dado FINRA baixado!")
            return None
        
        # Combina com Yahoo
        combined_data = self.combine_with_yahoo()
        
        print(f"\n🎉 CONCLUÍDO!")
        print(f"📁 Arquivos salvos: finra_historical_[ticker].csv")
        print(f"🚀 Agora você pode rodar o super mega backtester com dados FINRA reais!")
        
        return combined_data

if __name__ == "__main__":
    downloader = FinraHistoricalDownloader()
    downloader.run_full_download()