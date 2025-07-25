#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📈 DOWNLOAD DE DADOS HISTÓRICOS - 180 DIAS
Baixa dados extensos para permitir mega backtesting com janelas sobrepostas
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import time

def download_extended_data():
    """Baixa dados históricos estendidos para todos os tickers"""
    
    # Lista completa de tickers
    tickers = [
        'AMD', 'TLN', 'SNPS', 'DDOG', 'ANET', 'MRVL', 'SVM', 'AVAV', 'ZETA', 
        'FCX', 'RKLB', 'INTR', 'U', 'OUST', 'XP', 'DASH', 'MSFT', 'TTD', 
        'AVGO', 'MA', 'GOOGL', 'NVDA', 'AMZN', 'WBD', 'TRIP', 'VNET', 
        'SOUN', 'BBAI', 'QS'
    ]
    
    # Período: últimos 180 dias
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)
    
    print(f"📊 BAIXANDO DADOS HISTÓRICOS ESTENDIDOS")
    print(f"📅 Período: {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}")
    print(f"🎯 {len(tickers)} tickers")
    print("=" * 60)
    
    all_success = []
    all_failures = []
    
    for ticker in tickers:
        try:
            print(f"📈 Baixando {ticker}...")
            
            # Baixa dados do Yahoo Finance
            stock = yf.Ticker(ticker)
            hist_data = stock.history(start=start_date, end=end_date)
            
            if len(hist_data) < 50:  # Muito poucos dados
                print(f"   ⚠️ {ticker}: Poucos dados ({len(hist_data)} dias)")
                all_failures.append(ticker)
                continue
            
            # Formata dados
            hist_data.reset_index(inplace=True)
            hist_data['symbol'] = ticker
            hist_data['date'] = hist_data['Date']
            
            # Adiciona colunas vazias do FINRA (serão preenchidas depois)
            hist_data['total_off_exchange_volume'] = 0
            hist_data['short_volume'] = 0
            hist_data['short_exempt_volume'] = 0
            hist_data['on_exchange_volume'] = hist_data['Volume']  # Provisório
            hist_data['off_exchange_pct'] = 0
            hist_data['on_exchange_pct'] = 100
            hist_data['short_pct_of_off_exchange'] = 0
            hist_data['total_market_volume'] = hist_data['Volume']
            
            # Seleciona colunas na ordem correta
            columns_order = [
                'date', 'symbol', 'total_market_volume', 'Close', 'Open', 'High', 'Low',
                'total_off_exchange_volume', 'short_volume', 'short_exempt_volume',
                'on_exchange_volume', 'off_exchange_pct', 'on_exchange_pct', 'short_pct_of_off_exchange'
            ]
            
            hist_data = hist_data[columns_order]
            
            # Salva arquivo
            filename = f"historical_data_{ticker.lower()}.csv"
            hist_data.to_csv(filename, index=False)
            
            print(f"   ✅ {ticker}: {len(hist_data)} dias salvos em {filename}")
            all_success.append(ticker)
            
            # Pequena pausa para não sobrecarregar API
            time.sleep(0.1)
            
        except Exception as e:
            print(f"   ❌ {ticker}: Erro - {e}")
            all_failures.append(ticker)
    
    print(f"\n📊 RESUMO:")
    print(f"✅ Sucessos: {len(all_success)}")
    print(f"❌ Falhas: {len(all_failures)}")
    
    if all_failures:
        print(f"⚠️ Falhas: {', '.join(all_failures)}")
    
    print(f"\n🚀 Agora você pode rodar o mega backtester com dados de ~180 dias!")

if __name__ == "__main__":
    download_extended_data()