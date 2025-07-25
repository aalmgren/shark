#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📊 DASHBOARD VISUAL - Acumulação Silenciosa
Cria visualizações dos resultados da análise
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path
import json

def create_dashboard():
    """Cria dashboard visual dos resultados"""
    
    # Verificar se existe arquivo de resultados
    results_file = Path("accumulation_results.csv")
    if not results_file.exists():
        print("❌ Arquivo de resultados não encontrado!")
        print("Execute primeiro: python3 silent_accumulation_detector.py --scan watchlist.txt --days 30")
        return
    
    # Carregar dados
    df = pd.read_csv(results_file)
    
    # Configurar estilo
    plt.style.use('seaborn-v0_8-darkgrid')
    sns.set_palette("husl")
    
    # Criar figura com subplots
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('📊 DASHBOARD - ACUMULAÇÃO SILENCIOSA\nAnálise dos Últimos 30 Dias', 
                 fontsize=16, fontweight='bold')
    
    # 1. Ranking por Score de Acumulação
    ax1 = axes[0, 0]
    df_sorted = df.sort_values('accumulation_score', ascending=True)
    bars = ax1.barh(df_sorted['symbol'], df_sorted['accumulation_score'], 
                   color=['red' if x < 3 else 'orange' if x < 6 else 'green' 
                         for x in df_sorted['accumulation_score']])
    ax1.set_title('🏆 RANKING - Score de Acumulação', fontweight='bold')
    ax1.set_xlabel('Score (0-10)')
    ax1.grid(axis='x', alpha=0.3)
    
    # Adicionar valores nas barras
    for i, bar in enumerate(bars):
        width = bar.get_width()
        ax1.text(width + 0.1, bar.get_y() + bar.get_height()/2, 
                f'{width:.2f}', ha='left', va='center', fontweight='bold')
    
    # 2. Eficiência de Volume
    ax2 = axes[0, 1]
    colors = ['green' if x > 1.3 else 'orange' if x > 1.1 else 'red' 
              for x in df['volume_efficiency']]
    bars = ax2.bar(range(len(df)), df['volume_efficiency'], color=colors, alpha=0.7)
    ax2.set_title('📈 EFICIÊNCIA DE VOLUME\n(>1.3 = Volume Ineficiente = BOM)', fontweight='bold')
    ax2.set_xlabel('Ações')
    ax2.set_ylabel('Eficiência')
    ax2.set_xticks(range(len(df)))
    ax2.set_xticklabels(df['symbol'], rotation=45)
    ax2.axhline(y=1.3, color='green', linestyle='--', alpha=0.7, label='Threshold Bom')
    ax2.axhline(y=1.1, color='orange', linestyle='--', alpha=0.7, label='Threshold Médio')
    ax2.legend()
    ax2.grid(axis='y', alpha=0.3)
    
    # 3. Retorno vs Score de Acumulação
    ax3 = axes[1, 0]
    scatter = ax3.scatter(df['accumulation_score'], df['period_return'], 
                         s=100, alpha=0.7, c=df['accumulation_score'], 
                         cmap='RdYlGn')
    ax3.set_title('💰 RETORNO vs SCORE DE ACUMULAÇÃO', fontweight='bold')
    ax3.set_xlabel('Score de Acumulação')
    ax3.set_ylabel('Retorno do Período (%)')
    ax3.grid(alpha=0.3)
    
    # Adicionar labels aos pontos
    for i, txt in enumerate(df['symbol']):
        ax3.annotate(txt, (df['accumulation_score'].iloc[i], df['period_return'].iloc[i]),
                    xytext=(5, 5), textcoords='offset points', fontsize=9)
    
    # Adicionar linha de tendência
    z = np.polyfit(df['accumulation_score'], df['period_return'], 1)
    p = np.poly1d(z)
    ax3.plot(df['accumulation_score'], p(df['accumulation_score']), 
             "r--", alpha=0.8, label=f'Tendência')
    ax3.legend()
    
    # 4. Tendência de Volume
    ax4 = axes[1, 1]
    colors = ['red' if x < 0.8 else 'orange' if x < 1.2 else 'green' 
              for x in df['volume_trend']]
    bars = ax4.bar(range(len(df)), df['volume_trend'], color=colors, alpha=0.7)
    ax4.set_title('📊 TENDÊNCIA DE VOLUME\n(<0.8 = Declinante, >1.2 = Crescente)', fontweight='bold')
    ax4.set_xlabel('Ações')
    ax4.set_ylabel('Múltiplo de Volume')
    ax4.set_xticks(range(len(df)))
    ax4.set_xticklabels(df['symbol'], rotation=45)
    ax4.axhline(y=1.0, color='gray', linestyle='-', alpha=0.5, label='Neutro')
    ax4.axhline(y=0.8, color='red', linestyle='--', alpha=0.7, label='Declinante')
    ax4.axhline(y=1.2, color='green', linestyle='--', alpha=0.7, label='Crescente')
    ax4.legend()
    ax4.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('dashboard_acumulacao_silenciosa.png', dpi=300, bbox_inches='tight')
    print("✅ Dashboard salvo como: dashboard_acumulacao_silenciosa.png")
    
    # Criar tabela resumo
    print("\n" + "="*80)
    print("📊 RESUMO EXECUTIVO - ACUMULAÇÃO SILENCIOSA")
    print("="*80)
    
    # Top 3
    top3 = df.nlargest(3, 'accumulation_score')
    print("\n🏆 TOP 3 AÇÕES COM MAIOR POTENCIAL:")
    for i, (_, row) in enumerate(top3.iterrows(), 1):
        print(f"\n{i}. {row['symbol']}")
        print(f"   Score: {row['accumulation_score']:.2f}/10")
        print(f"   Retorno: {row['period_return']:.2f}%")
        print(f"   Eficiência Volume: {row['volume_efficiency']:.3f}")
        print(f"   Tendência Volume: {row['volume_trend']:.2f}x")
        print(f"   Confiança: {row['confidence']}")
    
    # Estatísticas gerais
    print(f"\n📈 ESTATÍSTICAS GERAIS:")
    print(f"   Média Score: {df['accumulation_score'].mean():.2f}")
    print(f"   Ações c/ Score > 2.0: {len(df[df['accumulation_score'] > 2.0])}")
    print(f"   Ações c/ Volume Ineficiente: {len(df[df['volume_efficiency'] > 1.3])}")
    print(f"   Retorno médio: {df['period_return'].mean():.2f}%")
    
    # Recomendações
    print(f"\n🎯 RECOMENDAÇÕES:")
    high_potential = df[df['accumulation_score'] > 1.5]
    if len(high_potential) > 0:
        print(f"   ✅ Monitorar de perto: {', '.join(high_potential['symbol'].tolist())}")
    else:
        print(f"   ⚠️  Nenhuma ação com acumulação significativa detectada")
    
    inefficient_volume = df[df['volume_efficiency'] > 1.3]
    if len(inefficient_volume) > 0:
        print(f"   📊 Volume ineficiente (bom sinal): {', '.join(inefficient_volume['symbol'].tolist())}")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    create_dashboard()