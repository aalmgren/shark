#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔴 DETECTOR DE DISTRIBUIÇÃO INSTITUCIONAL
Foca especificamente em identificar quando instituições estão VENDENDO/DISTRIBUINDO
"""

import pandas as pd
import numpy as np

def analyze_distribution_signals(csv_file):
    """Analisa sinais específicos de distribuição nos dados"""
    
    df = pd.read_csv(csv_file)
    
    print("🔴 ANÁLISE DE DISTRIBUIÇÃO INSTITUCIONAL")
    print("=" * 60)
    print("📅 Período: Últimos 30 dias")
    print(f"📊 Total de ações analisadas: {len(df)}")
    print()
    
    # Critérios específicos de DISTRIBUIÇÃO
    distribution_signals = []
    
    for _, row in df.iterrows():
        symbol = row['symbol']
        score = row['accumulation_score']
        vol_corr = row['volume_price_correlation']
        vol_trend = row['volume_trend']
        price_change = row['price_change_20d']
        vol_efficiency = row['volume_efficiency']
        
        distribution_score = 0
        reasons = []
        
        # 1. Volume altamente correlacionado com queda de preço
        if vol_corr > 0.6 and price_change < -5:
            distribution_score += 3
            reasons.append("Volume alto durante queda de preço")
        
        # 2. Volume crescente com preço fraco
        if vol_trend > 1.2 and price_change < 5:
            distribution_score += 2
            reasons.append("Volume crescente mas preço não acompanha")
        
        # 3. Volume muito eficiente (movendo preço para baixo)
        if vol_efficiency < 1.0 and price_change < 0:
            distribution_score += 2
            reasons.append("Volume eficiente pressionando preço para baixo")
        
        # 4. Score de acumulação baixo + volume alto
        if score < 1.5 and vol_trend > 1.0:
            distribution_score += 1
            reasons.append("Sem acumulação mas volume presente")
        
        # 5. Correlação alta (volume movendo preço)
        if vol_corr > 0.7:
            distribution_score += 1
            reasons.append("Volume altamente correlacionado com movimento")
        
        if distribution_score > 0:
            distribution_signals.append({
                'symbol': symbol,
                'distribution_score': distribution_score,
                'price_change_20d': price_change,
                'volume_correlation': vol_corr,
                'volume_trend': vol_trend,
                'reasons': reasons,
                'current_price': row['current_price']
            })
    
    # Ordenar por score de distribuição
    distribution_signals.sort(key=lambda x: x['distribution_score'], reverse=True)
    
    if not distribution_signals:
        print("✅ **RESULTADO**: Sem sinais significativos de distribuição institucional")
        print("💡 Isso indica que as instituições NÃO estão vendendo agressivamente")
        print()
        
        # Analisar as ações com melhor performance
        print("🏆 AÇÕES COM MELHOR PERFORMANCE (sem distribuição):")
        print("-" * 50)
        
        best_performers = df.nlargest(5, 'price_change_20d')
        for _, row in best_performers.iterrows():
            print(f"✅ {row['symbol']}: +{row['price_change_20d']:.1f}% | Vol.Corr: {row['volume_price_correlation']:.2f}")
        
        return None
    
    print(f"⚠️  **SINAIS DE DISTRIBUIÇÃO DETECTADOS**: {len(distribution_signals)} ações")
    print()
    
    print("🔴 RANKING - MAIOR RISCO DE DISTRIBUIÇÃO:")
    print("-" * 60)
    
    for i, signal in enumerate(distribution_signals[:10], 1):
        symbol = signal['symbol']
        d_score = signal['distribution_score']
        price_chg = signal['price_change_20d']
        vol_corr = signal['volume_correlation']
        price = signal['current_price']
        
        # Determinar nível de risco
        if d_score >= 5:
            risk_level = "🔴 ALTO"
            action = "SELL/REDUCE"
        elif d_score >= 3:
            risk_level = "🟠 MÉDIO"
            action = "WATCH/REDUCE"
        else:
            risk_level = "🟡 BAIXO"
            action = "MONITOR"
        
        print(f"{i:2d}. {symbol} - Score: {d_score} | {risk_level}")
        print(f"    Preço: ${price:.2f} ({price_chg:+.1f}%) | Vol.Corr: {vol_corr:.2f}")
        print(f"    Ação: {action}")
        print(f"    Razões: {', '.join(signal['reasons'][:2])}")
        print()
    
    return distribution_signals

def analyze_market_sentiment(df):
    """Analisa o sentimento geral do mercado"""
    
    print("📊 ANÁLISE DE SENTIMENTO DO MERCADO:")
    print("-" * 40)
    
    # Estatísticas gerais
    avg_performance = df['price_change_20d'].mean()
    positive_stocks = (df['price_change_20d'] > 0).sum()
    negative_stocks = (df['price_change_20d'] < 0).sum()
    
    avg_vol_corr = df['volume_price_correlation'].mean()
    high_corr_stocks = (df['volume_price_correlation'] > 0.6).sum()
    
    print(f"📈 Performance Média: {avg_performance:+.1f}%")
    print(f"✅ Ações Positivas: {positive_stocks}")
    print(f"❌ Ações Negativas: {negative_stocks}")
    print(f"📊 Correlação Vol-Preço Média: {avg_vol_corr:.2f}")
    print(f"⚡ Ações com Alta Correlação: {high_corr_stocks}")
    print()
    
    # Interpretação
    if avg_performance > 5:
        sentiment = "🟢 OTIMISTA"
    elif avg_performance > 0:
        sentiment = "🟡 NEUTRO POSITIVO"
    elif avg_performance > -5:
        sentiment = "🟠 NEUTRO NEGATIVO"
    else:
        sentiment = "🔴 PESSIMISTA"
    
    print(f"🎯 SENTIMENTO GERAL: {sentiment}")
    
    if avg_vol_corr < 0.4:
        print("💡 Volume desconectado do preço = Mercado equilibrado")
    elif avg_vol_corr > 0.7:
        print("⚠️  Volume altamente correlacionado = Possível pressão institucional")
    else:
        print("📊 Correlação normal volume-preço")

if __name__ == "__main__":
    # Analisar distribuição
    signals = analyze_distribution_signals('accumulation_scan_20250725_1932.csv')
    
    print()
    print("=" * 60)
    
    # Analisar sentimento geral
    df = pd.read_csv('accumulation_scan_20250725_1932.csv')
    analyze_market_sentiment(df)