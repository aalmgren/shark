#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 CASOS REAIS DE ACUMULAÇÃO - DADOS FINRA ATUAIS
Mostra EXATAMENTE quando ocorreram situações suspeitas nos dados reais
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime

def analyze_real_finra_patterns():
    """Analisa padrões reais nos dados FINRA atuais"""
    
    ticker_list = [
        'AMD', 'TLN', 'SNPS', 'DDOG', 'ANET', 'MRVL', 'SVM', 'AVAV', 'ZETA', 
        'FCX', 'RKLB', 'INTR', 'U', 'OUST', 'XP', 'DASH', 'MSFT', 'TTD', 
        'AVGO', 'MA', 'GOOGL', 'NVDA', 'AMZN', 'WBD', 'TRIP', 'VNET', 
        'SOUN', 'BBAI', 'QS'
    ]
    
    print("🔍 ANÁLISE DE PADRÕES REAIS NOS DADOS FINRA")
    print("=" * 60)
    
    all_patterns = []
    
    for ticker in ticker_list:
        current_file = f"volume_analysis_{ticker.lower()}_current.csv"
        
        if not os.path.exists(current_file):
            continue
            
        try:
            data = pd.read_csv(current_file)
            data['date'] = pd.to_datetime(data['date'])
            
            # Filtra apenas dias com dados FINRA reais
            real_data = data[data['total_off_exchange_volume'] > 0].copy()
            
            if len(real_data) < 3:
                continue
                
            print(f"\n📊 {ticker}: {len(real_data)} dias com dados FINRA reais")
            
            # Analisa cada possível sequência de 3 dias
            for i in range(len(real_data) - 2):
                window = real_data.iloc[i:i+3].copy()
                
                # Métricas da janela
                avg_off_exchange = window['off_exchange_pct'].mean()
                off_exchange_trend = window['off_exchange_pct'].iloc[-1] - window['off_exchange_pct'].iloc[0]
                price_change = ((window['Close'].iloc[-1] - window['Close'].iloc[0]) / window['Close'].iloc[0] * 100)
                price_volatility = window['Close'].std() / window['Close'].mean() * 100
                
                # Procura por ALTA atividade off-exchange (≥30%)
                if avg_off_exchange >= 30:
                    
                    # Calcula retorno se tivéssemos comprado
                    entry_date = window['date'].iloc[-1]
                    entry_price = window['Close'].iloc[-1]
                    
                    # Procura próximos 3 dias para calcular retorno
                    future_data = real_data[real_data['date'] > entry_date]
                    if len(future_data) >= 3:
                        exit_price = future_data.iloc[2]['Close']  # 3 dias depois
                        return_pct = ((exit_price - entry_price) / entry_price * 100)
                        exit_date = future_data.iloc[2]['date']
                    else:
                        # Usa último preço disponível
                        exit_price = real_data['Close'].iloc[-1]
                        return_pct = ((exit_price - entry_price) / entry_price * 100)
                        exit_date = real_data['date'].iloc[-1]
                    
                    # Classifica o padrão
                    pattern_type = "NEUTRAL"
                    if avg_off_exchange >= 40 and abs(price_change) <= 2:
                        if off_exchange_trend > 0:
                            pattern_type = "STRONG_ACCUMULATION"
                        else:
                            pattern_type = "MODERATE_ACCUMULATION"
                    elif avg_off_exchange >= 35 and abs(price_change) <= 3:
                        pattern_type = "POTENTIAL_ACCUMULATION"
                    elif avg_off_exchange >= 30 and price_change < -2:
                        pattern_type = "POTENTIAL_DISTRIBUTION"
                    
                    pattern = {
                        'ticker': ticker,
                        'pattern_type': pattern_type,
                        'analysis_start': window['date'].iloc[0].strftime('%Y-%m-%d'),
                        'analysis_end': window['date'].iloc[-1].strftime('%Y-%m-%d'),
                        'entry_date': entry_date.strftime('%Y-%m-%d'),
                        'exit_date': exit_date.strftime('%Y-%m-%d'),
                        'entry_price': entry_price,
                        'exit_price': exit_price,
                        'return_pct': return_pct,
                        'avg_off_exchange_pct': avg_off_exchange,
                        'off_exchange_trend': off_exchange_trend,
                        'price_change': price_change,
                        'price_volatility': price_volatility,
                        'day1_date': window['date'].iloc[0].strftime('%Y-%m-%d'),
                        'day1_off_exchange': window['off_exchange_pct'].iloc[0],
                        'day1_volume': window['total_market_volume'].iloc[0],
                        'day1_close': window['Close'].iloc[0],
                        'day2_date': window['date'].iloc[1].strftime('%Y-%m-%d'),
                        'day2_off_exchange': window['off_exchange_pct'].iloc[1],
                        'day2_volume': window['total_market_volume'].iloc[1],
                        'day2_close': window['Close'].iloc[1],
                        'day3_date': window['date'].iloc[2].strftime('%Y-%m-%d'),
                        'day3_off_exchange': window['off_exchange_pct'].iloc[2],
                        'day3_volume': window['total_market_volume'].iloc[2],
                        'day3_close': window['Close'].iloc[2],
                    }
                    
                    all_patterns.append(pattern)
        
        except Exception as e:
            print(f"❌ {ticker}: Erro - {e}")
    
    if not all_patterns:
        print("\n❌ NENHUM PADRÃO INTERESSANTE ENCONTRADO!")
        return
    
    # Converte para DataFrame e analisa
    df = pd.DataFrame(all_patterns)
    
    print(f"\n📊 TOTAL DE PADRÕES ENCONTRADOS: {len(df)}")
    
    # Agrupa por tipo
    pattern_counts = df['pattern_type'].value_counts()
    print(f"\n🎯 DISTRIBUIÇÃO POR TIPO:")
    for pattern_type, count in pattern_counts.items():
        avg_return = df[df['pattern_type'] == pattern_type]['return_pct'].mean()
        print(f"   {pattern_type}: {count} casos | Retorno médio: {avg_return:+.2f}%")
    
    # Mostra os melhores casos
    print(f"\n🏆 MELHORES CASOS DE ACUMULAÇÃO ENCONTRADOS:")
    print("=" * 80)
    
    # Filtra apenas acumulações e ordena por retorno
    accumulations = df[df['pattern_type'].str.contains('ACCUMULATION', na=False)].copy()
    if len(accumulations) > 0:
        accumulations = accumulations.sort_values('return_pct', ascending=False)
        
        for idx, case in accumulations.head(10).iterrows():
            print(f"\n📊 CASO #{idx + 1} - {case['ticker']} | {case['pattern_type']}")
            print(f"   🗓️  Análise: {case['analysis_start']} a {case['analysis_end']}")
            print(f"   💰 Trade: {case['entry_date']} (${case['entry_price']:.2f}) → {case['exit_date']} (${case['exit_price']:.2f})")
            print(f"   📈 Retorno: {case['return_pct']:+.2f}%")
            print(f"   \n   📊 SEQUÊNCIA OFF-EXCHANGE:")
            print(f"      {case['day1_date']}: {case['day1_off_exchange']:.1f}% | Vol: {case['day1_volume']:,.0f} | ${case['day1_close']:.2f}")
            print(f"      {case['day2_date']}: {case['day2_off_exchange']:.1f}% | Vol: {case['day2_volume']:,.0f} | ${case['day2_close']:.2f}")
            print(f"      {case['day3_date']}: {case['day3_off_exchange']:.1f}% | Vol: {case['day3_volume']:,.0f} | ${case['day3_close']:.2f}")
            print(f"   🎯 Off-exchange médio: {case['avg_off_exchange_pct']:.1f}% | Tendência: {case['off_exchange_trend']:+.1f}pp")
            print("   " + "="*50)
    
    # Mostra todos os casos interessantes
    print(f"\n📋 TODOS OS CASOS COM ALTA ATIVIDADE OFF-EXCHANGE (≥30%):")
    print("=" * 80)
    
    df_sorted = df.sort_values('avg_off_exchange_pct', ascending=False)
    
    for idx, case in df_sorted.head(15).iterrows():
        success = "✅" if case['return_pct'] > 0 else "❌"
        print(f"{success} {case['ticker']} | {case['pattern_type']} | {case['analysis_start']} a {case['analysis_end']}")
        print(f"    Off-exchange: {case['avg_off_exchange_pct']:.1f}% | Retorno: {case['return_pct']:+.2f}% | Preço: {case['price_change']:+.2f}%")
    
    # Salva resultados
    filename = f"real_accumulation_patterns_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    df.to_csv(filename, index=False)
    print(f"\n💾 Padrões reais salvos em: {filename}")
    
    return df

if __name__ == "__main__":
    analyze_real_finra_patterns()