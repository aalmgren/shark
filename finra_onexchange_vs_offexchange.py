#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para analisar Volume On-Exchange vs Off-Exchange
Compara dados de exchanges oficiais vs dark pools/FINRA
"""

import pandas as pd
import requests
import yfinance as yf
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import json
import argparse
import time
import warnings
import numpy as np

warnings.filterwarnings('ignore')

class OnOffExchangeAnalyzer:
    """Classe para analisar volume on-exchange vs off-exchange"""
    
    def __init__(self):
        self.finra_url = "https://api.finra.org/data/group/OTCMarket/name/regShoDaily"
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
    def get_finra_off_exchange_data(self, symbol, days=30):
        """
        Baixa dados de volume OFF-EXCHANGE do FINRA
        FINRA reporta principalmente volume off-exchange (dark pools, internalization, etc.)
        """
        print(f"🔍 Buscando dados OFF-EXCHANGE (FINRA) para {symbol}...")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        all_data = []
        
        for i in range(days):
            current_date = start_date + timedelta(days=i)
            date_str = current_date.strftime('%Y-%m-%d')
            
            if current_date.weekday() >= 5:  # Skip weekends
                continue
                
            payload = {
                "compareFilters": [
                    {
                        "compareType": "EQUAL",
                        "fieldName": "symbol",
                        "fieldValue": symbol.upper()
                    },
                    {
                        "compareType": "EQUAL", 
                        "fieldName": "tradeDate",
                        "fieldValue": date_str
                    }
                ],
                "limit": 1000
            }
            
            try:
                response = requests.post(self.finra_url, 
                                       headers=self.headers, 
                                       data=json.dumps(payload),
                                       timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    if data:
                        all_data.extend(data)
                        print(f"  ✓ Dados OFF-EXCHANGE encontrados para {date_str}")
                    else:
                        print(f"  - Sem dados OFF-EXCHANGE para {date_str}")
                        
                time.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                print(f"  ❌ Erro ao buscar dados OFF-EXCHANGE para {date_str}: {str(e)}")
                continue
        
        if not all_data:
            return pd.DataFrame()
            
        df = pd.DataFrame(all_data)
        
        if not df.empty:
            df['tradeDate'] = pd.to_datetime(df['tradeDate'])
            df = df.sort_values('tradeDate')
            
            # Agrupar por data - somar volumes de diferentes trade facilities
            df_grouped = df.groupby('tradeDate').agg({
                'shortVolume': 'sum',
                'shortExemptVolume': 'sum', 
                'totalVolume': 'sum'
            }).reset_index()
            
            # O volume total FINRA representa principalmente volume OFF-EXCHANGE
            df_grouped['off_exchange_volume'] = df_grouped['totalVolume']
            df_grouped['off_exchange_short_volume'] = df_grouped['shortVolume']
            
            print(f"✓ {len(df_grouped)} dias de dados OFF-EXCHANGE processados")
            
        return df_grouped if not df.empty else pd.DataFrame()
    
    def get_market_total_volume(self, symbol, days=30):
        """
        Baixa volume TOTAL do mercado (on-exchange + off-exchange)
        Usando Yahoo Finance que agrega dados de todas as fontes
        """
        print(f"📊 Buscando volume TOTAL de mercado para {symbol}...")
        
        try:
            ticker = yf.Ticker(symbol)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days + 5)
            
            hist = ticker.history(start=start_date, end=end_date)
            
            if hist.empty:
                return pd.DataFrame()
            
            df = hist.reset_index()
            df = df.rename(columns={'Date': 'date', 'Volume': 'total_market_volume'})
            df['date'] = pd.to_datetime(df['date']).dt.date
            df['date'] = pd.to_datetime(df['date'])
            
            print(f"✓ {len(df)} dias de volume TOTAL obtidos")
            
            return df[['date', 'total_market_volume', 'Close']].copy()
            
        except Exception as e:
            print(f"❌ Erro ao buscar volume total: {str(e)}")
            return pd.DataFrame()
    
    def calculate_on_off_exchange(self, finra_df, market_df, symbol):
        """
        Calcula volume ON-EXCHANGE vs OFF-EXCHANGE
        
        LÓGICA:
        - Volume Total = Volume ON-EXCHANGE + Volume OFF-EXCHANGE
        - Volume OFF-EXCHANGE ≈ Volume FINRA (dark pools, internalization)
        - Volume ON-EXCHANGE ≈ Volume Total - Volume OFF-EXCHANGE
        """
        if finra_df.empty or market_df.empty:
            print("❌ Dados insuficientes para análise ON/OFF exchange")
            return pd.DataFrame()
        
        print("🔄 Calculando volumes ON-EXCHANGE vs OFF-EXCHANGE...")
        
        # Fazer merge dos dados
        finra_df['date'] = finra_df['tradeDate'].dt.date
        finra_df['date'] = pd.to_datetime(finra_df['date'])
        
        merged_df = pd.merge(finra_df, market_df, on='date', how='inner')
        
        if merged_df.empty:
            print("❌ Nenhuma data comum encontrada")
            return pd.DataFrame()
        
        # CALCULAR VOLUMES ON/OFF EXCHANGE
        merged_df['off_exchange_volume'] = merged_df['off_exchange_volume']  # Volume FINRA
        merged_df['on_exchange_volume'] = merged_df['total_market_volume'] - merged_df['off_exchange_volume']
        
        # Garantir que não temos valores negativos (pode acontecer por diferenças de fontes)
        merged_df['on_exchange_volume'] = merged_df['on_exchange_volume'].clip(lower=0)
        
        # CALCULAR PERCENTUAIS
        merged_df['off_exchange_pct'] = (merged_df['off_exchange_volume'] / merged_df['total_market_volume'] * 100).round(2)
        merged_df['on_exchange_pct'] = (merged_df['on_exchange_volume'] / merged_df['total_market_volume'] * 100).round(2)
        
        # CALCULAR DARK POOL METRICS
        merged_df['dark_pool_short_pct'] = (merged_df['off_exchange_short_volume'] / merged_df['off_exchange_volume'] * 100).round(2)
        merged_df['total_short_pct'] = (merged_df['off_exchange_short_volume'] / merged_df['total_market_volume'] * 100).round(2)
        
        # ESTATÍSTICAS
        print(f"\n📈 ANÁLISE ON-EXCHANGE vs OFF-EXCHANGE PARA {symbol.upper()}")
        print("=" * 60)
        print(f"Período: {merged_df['date'].min().strftime('%Y-%m-%d')} a {merged_df['date'].max().strftime('%Y-%m-%d')}")
        print(f"Dias analisados: {len(merged_df)}")
        
        print(f"\n💹 VOLUME MÉDIO DIÁRIO:")
        print(f"  • Volume TOTAL de mercado: {merged_df['total_market_volume'].mean():,.0f}")
        print(f"  • Volume ON-EXCHANGE:      {merged_df['on_exchange_volume'].mean():,.0f}")
        print(f"  • Volume OFF-EXCHANGE:     {merged_df['off_exchange_volume'].mean():,.0f}")
        
        print(f"\n📊 PERCENTUAIS MÉDIOS:")
        print(f"  • ON-EXCHANGE:  {merged_df['on_exchange_pct'].mean():.1f}%")
        print(f"  • OFF-EXCHANGE: {merged_df['off_exchange_pct'].mean():.1f}%")
        
        print(f"\n🎯 DARK POOL METRICS:")
        print(f"  • Vendas a descoberto em dark pools: {merged_df['total_short_pct'].mean():.1f}% do volume total")
        print(f"  • % de shorts no volume off-exchange: {merged_df['dark_pool_short_pct'].mean():.1f}%")
        
        return merged_df
    
    def create_on_off_visualizations(self, df, symbol):
        """
        Cria visualizações específicas para ON/OFF exchange
        """
        if df.empty:
            print("❌ Sem dados para visualização")
            return
        
        print("📊 Criando visualizações ON/OFF EXCHANGE...")
        
        # Configurar estilo
        plt.style.use('seaborn-v0_8')
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle(f'Análise ON-EXCHANGE vs OFF-EXCHANGE - {symbol.upper()}', 
                     fontsize=16, fontweight='bold')
        
        # 1. Volume ON vs OFF ao longo do tempo
        ax1 = axes[0, 0]
        ax1.plot(df['date'], df['on_exchange_volume'], label='Volume ON-EXCHANGE', 
                linewidth=2, alpha=0.8, color='green')
        ax1.plot(df['date'], df['off_exchange_volume'], label='Volume OFF-EXCHANGE (Dark Pools)', 
                linewidth=2, alpha=0.8, color='red')
        ax1.plot(df['date'], df['total_market_volume'], label='Volume TOTAL', 
                linewidth=1, alpha=0.6, color='blue', linestyle='--')
        ax1.set_title('Volume ON-EXCHANGE vs OFF-EXCHANGE')
        ax1.set_ylabel('Volume')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.tick_params(axis='x', rotation=45)
        
        # 2. Percentuais ON vs OFF
        ax2 = axes[0, 1]
        width = 0.35
        dates_numeric = np.arange(len(df))
        ax2.bar(dates_numeric - width/2, df['on_exchange_pct'], width, 
               label='ON-EXCHANGE %', alpha=0.7, color='green')
        ax2.bar(dates_numeric + width/2, df['off_exchange_pct'], width, 
               label='OFF-EXCHANGE %', alpha=0.7, color='red')
        ax2.set_title('Distribuição Percentual ON vs OFF EXCHANGE')
        ax2.set_ylabel('Percentual (%)')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 3. Correlação ON vs OFF
        ax3 = axes[1, 0]
        ax3.scatter(df['on_exchange_volume'], df['off_exchange_volume'], alpha=0.6, color='purple')
        ax3.set_xlabel('Volume ON-EXCHANGE')
        ax3.set_ylabel('Volume OFF-EXCHANGE')
        ax3.set_title('Correlação: ON-EXCHANGE vs OFF-EXCHANGE')
        ax3.grid(True, alpha=0.3)
        
        # Linha de tendência
        z = np.polyfit(df['on_exchange_volume'], df['off_exchange_volume'], 1)
        p = np.poly1d(z)
        ax3.plot(df['on_exchange_volume'], p(df['on_exchange_volume']), "r--", alpha=0.8)
        
        # 4. Dark Pool Activity
        ax4 = axes[1, 1]
        ax4.plot(df['date'], df['off_exchange_pct'], color='red', linewidth=2, 
                marker='o', markersize=4, label='% OFF-EXCHANGE')
        ax4.plot(df['date'], df['total_short_pct'], color='darkred', linewidth=2, 
                marker='s', markersize=3, label='% Short Selling (Dark Pools)')
        ax4.set_title('Atividade em Dark Pools')
        ax4.set_ylabel('Percentual (%)')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        ax4.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        # Salvar gráfico
        filename = f'onoff_exchange_analysis_{symbol.lower()}_{datetime.now().strftime("%Y%m%d_%H%M")}.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"✓ Gráficos salvos como: {filename}")
        
        plt.show()
    
    def save_on_off_data(self, df, symbol):
        """Salva dados ON/OFF exchange em CSV"""
        if df.empty:
            return
        
        filename = f'onoff_exchange_data_{symbol.lower()}_{datetime.now().strftime("%Y%m%d_%H%M")}.csv'
        df.to_csv(filename, index=False)
        print(f"✓ Dados ON/OFF EXCHANGE salvos como: {filename}")
    
    def analyze_on_off_exchange(self, symbol, days=30):
        """Análise completa ON-EXCHANGE vs OFF-EXCHANGE"""
        
        print(f"\n🚀 ANÁLISE ON-EXCHANGE vs OFF-EXCHANGE PARA {symbol.upper()}")
        print("=" * 70)
        
        # Baixar dados
        finra_data = self.get_finra_off_exchange_data(symbol, days)
        market_data = self.get_market_total_volume(symbol, days)
        
        # Calcular ON/OFF exchange
        analysis_data = self.calculate_on_off_exchange(finra_data, market_data, symbol)
        
        if not analysis_data.empty:
            # Criar visualizações
            self.create_on_off_visualizations(analysis_data, symbol)
            
            # Salvar dados
            self.save_on_off_data(analysis_data, symbol)
            
            print(f"\n✅ Análise ON/OFF EXCHANGE concluída para {symbol.upper()}")
            
            # Resumo final
            print(f"\n🎯 RESUMO EXECUTIVO:")
            print(f"  • Em média, {analysis_data['off_exchange_pct'].mean():.1f}% do volume é OFF-EXCHANGE")
            print(f"  • Dark pools representam {analysis_data['total_short_pct'].mean():.1f}% do volume total em vendas a descoberto")
            print(f"  • Volume médio diário OFF-EXCHANGE: {analysis_data['off_exchange_volume'].mean():,.0f}")
            
        else:
            print(f"\n❌ Não foi possível completar a análise ON/OFF EXCHANGE para {symbol.upper()}")
        
        return analysis_data

def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description='Analisar volume ON-EXCHANGE vs OFF-EXCHANGE')
    parser.add_argument('symbol', help='Símbolo da ação (ex: AAPL)')
    parser.add_argument('--days', type=int, default=30, help='Número de dias (padrão: 30)')
    
    args = parser.parse_args()
    
    if not args.symbol or len(args.symbol) > 10:
        print("❌ Símbolo de ação inválido")
        return
    
    analyzer = OnOffExchangeAnalyzer()
    analyzer.analyze_on_off_exchange(args.symbol, args.days)

if __name__ == "__main__":
    try:
        import sys
        if len(sys.argv) > 1:
            main()
        else:
            # Exemplo com AAPL
            print("🔧 Modo exemplo - analisando AAPL")
            analyzer = OnOffExchangeAnalyzer()
            analyzer.analyze_on_off_exchange('AAPL', 30)
    except KeyboardInterrupt:
        print("\n\n❌ Análise interrompida pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro na execução: {str(e)}")