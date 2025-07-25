#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🏆 ANÁLISE DA ESTRATÉGIA CAMPEÃ
Mostra EXATAMENTE quando ocorreram os casos da configuração com 72.7% hit rate
"""

import pandas as pd
import numpy as np
from datetime import datetime

def analyze_champion_strategy():
    """Analisa a estratégia campeã: 5d análise + 6d holding + off-exchange ≥50% + estabilidade ≤1.0%"""
    
    print("🏆 ANÁLISE DA ESTRATÉGIA CAMPEÃ - 72.7% HIT RATE")
    print("=" * 70)
    print("📊 Configuração: 5 dias análise + 6 dias holding")
    print("📈 Off-exchange: ≥50% + Estabilidade: ≤1.0%")
    print()
    
    # Carrega dados do mega backtesting
    try:
        df = pd.read_csv('mega_backtest_all_trades_20250725_2237.csv')
    except FileNotFoundError:
        print("❌ Arquivo de trades não encontrado!")
        return
    
    # Filtra apenas a configuração campeã
    champion_trades = df[
        (df['analysis_days'] == 5) &
        (df['holding_days'] == 6) &
        (df['off_exchange_threshold'] == 50) &
        (df['price_stability_threshold'] == 1.0)
    ].copy()
    
    if len(champion_trades) == 0:
        print("❌ Nenhum trade encontrado para a configuração campeã!")
        return
    
    print(f"✅ Total de trades da estratégia campeã: {len(champion_trades)}")
    
    # Converte datas
    champion_trades['entry_date'] = pd.to_datetime(champion_trades['entry_date'])
    champion_trades['exit_date'] = pd.to_datetime(champion_trades['exit_date'])
    
    # Calcula hit rate
    winners = (champion_trades['return_pct'] > 0).sum()
    hit_rate = (winners / len(champion_trades) * 100)
    avg_return = champion_trades['return_pct'].mean()
    
    print(f"🎯 Hit rate confirmado: {hit_rate:.1f}%")
    print(f"💰 Retorno médio: {avg_return:+.3f}%")
    print(f"✅ Trades vencedores: {winners}/{len(champion_trades)}")
    
    # Ordena por retorno (melhores primeiro)
    champion_trades = champion_trades.sort_values('return_pct', ascending=False)
    
    print(f"\n🎯 CASOS ESPECÍFICOS DA ESTRATÉGIA CAMPEÃ:")
    print("=" * 70)
    
    # Mostra todos os casos
    for idx, trade in champion_trades.iterrows():
        status = "✅ GANHOU" if trade['return_pct'] > 0 else "❌ PERDEU"
        
        print(f"\n📊 CASO #{idx + 1} - {trade['symbol']} | {status}")
        print(f"   📅 Análise: {trade['entry_date'].strftime('%d/%m/%Y')} (entrada)")
        print(f"   📅 Saída: {trade['exit_date'].strftime('%d/%m/%Y')}")
        print(f"   💰 Preço: ${trade['entry_price']:.2f} → ${trade['exit_price']:.2f}")
        print(f"   📈 Retorno: {trade['return_pct']:+.2f}%")
        print(f"   📊 Off-exchange médio: {trade['avg_off_exchange_pct']:.1f}%")
        print(f"   🔄 Tendência off-exchange: {trade['off_exchange_trend']:+.1f}pp")
        print(f"   📉 Mudança de preço durante análise: {trade['price_change']:+.2f}%")
        print(f"   🎯 Força do sinal: {trade['signal_strength']}")
    
    # Análise por ticker
    print(f"\n📊 ANÁLISE POR TICKER:")
    ticker_analysis = champion_trades.groupby('symbol').agg({
        'return_pct': ['count', 'mean', lambda x: (x > 0).sum(), lambda x: (x > 0).mean() * 100],
        'avg_off_exchange_pct': 'mean'
    }).round(2)
    
    ticker_analysis.columns = ['total_trades', 'avg_return', 'winners', 'hit_rate', 'avg_off_exchange']
    ticker_analysis = ticker_analysis.sort_values('hit_rate', ascending=False)
    
    for ticker, stats in ticker_analysis.iterrows():
        print(f"   {ticker}: {stats['hit_rate']:.0f}% hit rate | {stats['avg_return']:+.2f}% retorno | {stats['total_trades']:.0f} trades | {stats['avg_off_exchange']:.1f}% off-exchange")
    
    # Análise temporal
    print(f"\n📅 ANÁLISE TEMPORAL:")
    champion_trades['entry_month'] = champion_trades['entry_date'].dt.strftime('%Y-%m')
    monthly_analysis = champion_trades.groupby('entry_month').agg({
        'return_pct': ['count', 'mean', lambda x: (x > 0).mean() * 100]
    }).round(2)
    
    monthly_analysis.columns = ['trades', 'avg_return', 'hit_rate']
    
    for month, stats in monthly_analysis.iterrows():
        print(f"   {month}: {stats['hit_rate']:.0f}% hit rate | {stats['avg_return']:+.2f}% retorno | {stats['trades']:.0f} trades")
    
    # Casos de maior sucesso
    print(f"\n🏆 TOP 10 MAIORES SUCESSOS:")
    top_winners = champion_trades.head(10)
    
    for idx, trade in top_winners.iterrows():
        print(f"   🥇 {trade['symbol']}: {trade['return_pct']:+.2f}% | {trade['entry_date'].strftime('%d/%m')} a {trade['exit_date'].strftime('%d/%m')} | Off-exchange: {trade['avg_off_exchange_pct']:.1f}%")
    
    # Casos de maior fracasso
    print(f"\n💸 TOP 5 MAIORES FRACASSOS:")
    worst_losers = champion_trades.tail(5)
    
    for idx, trade in worst_losers.iterrows():
        print(f"   💥 {trade['symbol']}: {trade['return_pct']:+.2f}% | {trade['entry_date'].strftime('%d/%m')} a {trade['exit_date'].strftime('%d/%m')} | Off-exchange: {trade['avg_off_exchange_pct']:.1f}%")
    
    # Salva análise detalhada
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    filename = f"champion_strategy_analysis_{timestamp}.csv"
    champion_trades.to_csv(filename, index=False)
    
    print(f"\n💾 Análise detalhada salva em: {filename}")
    
    return champion_trades

if __name__ == "__main__":
    analyze_champion_strategy()