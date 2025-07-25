#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para baixar dados do FINRA e comparar volume negociado com volume de dark pool/vendas a descoberto
Autor: Assistente Python
Data: 2025
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

# Configurar warnings
warnings.filterwarnings('ignore')

class FINRAVolumeAnalyzer:
    """Classe para analisar volumes do FINRA e comparar com dados de mercado"""
    
    def __init__(self):
        self.base_url = "https://api.finra.org/data/group/OTCMarket/name/regShoDaily"
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
    def get_finra_data(self, symbol, days=30):
        """
        Baixa dados de volume de vendas a descoberto do FINRA
        
        Args:
            symbol (str): Símbolo da ação (ex: 'AAPL')
            days (int): Número de dias para buscar dados
            
        Returns:
            pd.DataFrame: DataFrame com dados do FINRA
        """
        print(f"🔍 Buscando dados do FINRA para {symbol}...")
        
        # Calcular intervalo de datas
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        all_data = []
        
        # Buscar dados para cada dia no intervalo
        for i in range(days):
            current_date = start_date + timedelta(days=i)
            date_str = current_date.strftime('%Y-%m-%d')
            
            # Pular fins de semana
            if current_date.weekday() >= 5:
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
                response = requests.post(self.base_url, 
                                       headers=self.headers, 
                                       data=json.dumps(payload),
                                       timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    if data:
                        all_data.extend(data)
                        print(f"  ✓ Dados encontrados para {date_str}")
                    else:
                        print(f"  - Sem dados para {date_str}")
                else:
                    print(f"  ❌ Erro na API para {date_str}: {response.status_code}")
                    
                # Rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                print(f"  ❌ Erro ao buscar dados para {date_str}: {str(e)}")
                continue
        
        if not all_data:
            print(f"❌ Nenhum dado encontrado para {symbol}")
            return pd.DataFrame()
            
        df = pd.DataFrame(all_data)
        
        # Processar dados se encontrados
        if not df.empty:
            df['tradeDate'] = pd.to_datetime(df['tradeDate'])
            df = df.sort_values('tradeDate')
            
            # Agrupar por data para somar volumes de diferentes trade facilities
            df_grouped = df.groupby('tradeDate').agg({
                'shortVolume': 'sum',
                'shortExemptVolume': 'sum', 
                'totalVolume': 'sum'
            }).reset_index()
            
            # Calcular percentual de vendas a descoberto
            df_grouped['short_percentage'] = (df_grouped['shortVolume'] / df_grouped['totalVolume'] * 100).round(2)
            
            print(f"✓ {len(df_grouped)} dias de dados processados para {symbol}")
            
        return df_grouped if not df.empty else pd.DataFrame()
    
    def get_yfinance_data(self, symbol, days=30):
        """
        Baixa dados de volume do Yahoo Finance usando yfinance
        
        Args:
            symbol (str): Símbolo da ação
            days (int): Número de dias
            
        Returns:
            pd.DataFrame: DataFrame com dados do Yahoo Finance
        """
        print(f"📊 Buscando dados do Yahoo Finance para {symbol}...")
        
        try:
            # Criar objeto ticker
            ticker = yf.Ticker(symbol)
            
            # Calcular datas
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days + 5)  # Margem extra
            
            # Baixar dados históricos
            hist = ticker.history(start=start_date, end=end_date)
            
            if hist.empty:
                print(f"❌ Nenhum dado encontrado no Yahoo Finance para {symbol}")
                return pd.DataFrame()
            
            # Preparar DataFrame
            df = hist.reset_index()
            df = df.rename(columns={'Date': 'date', 'Volume': 'market_volume'})
            df['date'] = pd.to_datetime(df['date']).dt.date
            df['date'] = pd.to_datetime(df['date'])
            
            print(f"✓ {len(df)} dias de dados do Yahoo Finance obtidos")
            
            return df[['date', 'market_volume', 'Close']].copy()
            
        except Exception as e:
            print(f"❌ Erro ao buscar dados do Yahoo Finance: {str(e)}")
            return pd.DataFrame()
    
    def merge_and_analyze(self, finra_df, yfinance_df, symbol):
        """
        Combina dados do FINRA e Yahoo Finance e realiza análise
        
        Args:
            finra_df (pd.DataFrame): Dados do FINRA
            yfinance_df (pd.DataFrame): Dados do Yahoo Finance
            symbol (str): Símbolo da ação
            
        Returns:
            pd.DataFrame: DataFrame combinado com análise
        """
        if finra_df.empty or yfinance_df.empty:
            print("❌ Dados insuficientes para análise")
            return pd.DataFrame()
        
        print("🔄 Combinando e analisando dados...")
        
        # Fazer merge dos dados
        finra_df['date'] = finra_df['tradeDate'].dt.date
        finra_df['date'] = pd.to_datetime(finra_df['date'])
        
        merged_df = pd.merge(finra_df, yfinance_df, on='date', how='inner')
        
        if merged_df.empty:
            print("❌ Nenhuma data comum encontrada entre FINRA e Yahoo Finance")
            return pd.DataFrame()
        
        # Calcular métricas adicionais
        merged_df['dark_pool_ratio'] = (merged_df['shortVolume'] / merged_df['market_volume'] * 100).round(2)
        merged_df['volume_difference'] = merged_df['market_volume'] - merged_df['totalVolume']
        merged_df['volume_ratio'] = (merged_df['totalVolume'] / merged_df['market_volume'] * 100).round(2)
        
        # Estatísticas
        print(f"\n📈 ANÁLISE DE VOLUME PARA {symbol.upper()}")
        print("=" * 50)
        print(f"Período analisado: {merged_df['date'].min().strftime('%Y-%m-%d')} a {merged_df['date'].max().strftime('%Y-%m-%d')}")
        print(f"Dias com dados: {len(merged_df)}")
        print(f"\nVOLUME MÉDIO:")
        print(f"  • Volume de mercado (Yahoo): {merged_df['market_volume'].mean():,.0f}")
        print(f"  • Volume FINRA total: {merged_df['totalVolume'].mean():,.0f}")
        print(f"  • Volume de vendas a descoberto: {merged_df['shortVolume'].mean():,.0f}")
        print(f"\nPERCENTUAIS MÉDIOS:")
        print(f"  • Vendas a descoberto do total: {merged_df['short_percentage'].mean():.1f}%")
        print(f"  • Dark pool vs mercado: {merged_df['dark_pool_ratio'].mean():.1f}%")
        print(f"  • Volume FINRA vs Yahoo: {merged_df['volume_ratio'].mean():.1f}%")
        
        return merged_df
    
    def create_visualizations(self, df, symbol):
        """
        Cria visualizações dos dados
        
        Args:
            df (pd.DataFrame): DataFrame com dados combinados
            symbol (str): Símbolo da ação
        """
        if df.empty:
            print("❌ Sem dados para visualização")
            return
        
        print("📊 Criando visualizações...")
        
        # Configurar estilo
        plt.style.use('seaborn-v0_8')
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle(f'Análise de Volume - {symbol.upper()}', fontsize=16, fontweight='bold')
        
        # 1. Comparação de volumes ao longo do tempo
        ax1 = axes[0, 0]
        ax1.plot(df['date'], df['market_volume'], label='Volume Yahoo Finance', linewidth=2, alpha=0.8)
        ax1.plot(df['date'], df['totalVolume'], label='Volume Total FINRA', linewidth=2, alpha=0.8)
        ax1.plot(df['date'], df['shortVolume'], label='Volume Vendas a Descoberto', linewidth=2, alpha=0.8)
        ax1.set_title('Comparação de Volumes')
        ax1.set_ylabel('Volume')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.tick_params(axis='x', rotation=45)
        
        # 2. Percentual de vendas a descoberto
        ax2 = axes[0, 1]
        ax2.bar(df['date'], df['short_percentage'], alpha=0.7, color='red')
        ax2.set_title('Percentual de Vendas a Descoberto')
        ax2.set_ylabel('Percentual (%)')
        ax2.grid(True, alpha=0.3)
        ax2.tick_params(axis='x', rotation=45)
        
        # 3. Correlação entre volumes
        ax3 = axes[1, 0]
        ax3.scatter(df['market_volume'], df['shortVolume'], alpha=0.6)
        ax3.set_xlabel('Volume de Mercado (Yahoo)')
        ax3.set_ylabel('Volume Vendas a Descoberto (FINRA)')
        ax3.set_title('Correlação: Volume de Mercado vs Vendas a Descoberto')
        ax3.grid(True, alpha=0.3)
        
        # Adicionar linha de tendência
        z = np.polyfit(df['market_volume'], df['shortVolume'], 1)
        p = np.poly1d(z)
        ax3.plot(df['market_volume'], p(df['market_volume']), "r--", alpha=0.8)
        
        # 4. Ratio dark pool vs mercado
        ax4 = axes[1, 1]
        ax4.plot(df['date'], df['dark_pool_ratio'], color='purple', linewidth=2, marker='o', markersize=4)
        ax4.set_title('Ratio Dark Pool vs Volume de Mercado')
        ax4.set_ylabel('Ratio (%)')
        ax4.grid(True, alpha=0.3)
        ax4.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        # Salvar gráfico
        filename = f'finra_analysis_{symbol.lower()}_{datetime.now().strftime("%Y%m%d_%H%M")}.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"✓ Gráfico salvo como: {filename}")
        
        plt.show()
    
    def save_data(self, df, symbol):
        """
        Salva dados em arquivo CSV
        
        Args:
            df (pd.DataFrame): DataFrame para salvar
            symbol (str): Símbolo da ação
        """
        if df.empty:
            return
        
        filename = f'finra_data_{symbol.lower()}_{datetime.now().strftime("%Y%m%d_%H%M")}.csv'
        df.to_csv(filename, index=False)
        print(f"✓ Dados salvos como: {filename}")
    
    def analyze_stock(self, symbol, days=30):
        """
        Análise completa de uma ação
        
        Args:
            symbol (str): Símbolo da ação
            days (int): Número de dias para análise
        """
        print(f"\n🚀 INICIANDO ANÁLISE DE {symbol.upper()}")
        print("=" * 60)
        
        # Baixar dados
        finra_data = self.get_finra_data(symbol, days)
        yfinance_data = self.get_yfinance_data(symbol, days)
        
        # Combinar e analisar
        combined_data = self.merge_and_analyze(finra_data, yfinance_data, symbol)
        
        if not combined_data.empty:
            # Criar visualizações
            self.create_visualizations(combined_data, symbol)
            
            # Salvar dados
            self.save_data(combined_data, symbol)
            
            print(f"\n✅ Análise concluída para {symbol.upper()}")
        else:
            print(f"\n❌ Não foi possível completar a análise para {symbol.upper()}")
        
        return combined_data

def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description='Analisar volume FINRA vs mercado para uma ação')
    parser.add_argument('symbol', help='Símbolo da ação (ex: AAPL)')
    parser.add_argument('--days', type=int, default=30, help='Número de dias para análise (padrão: 30)')
    
    args = parser.parse_args()
    
    # Validar símbolo
    if not args.symbol or len(args.symbol) > 10:
        print("❌ Símbolo de ação inválido")
        return
    
    # Criar analisador e executar análise
    analyzer = FINRAVolumeAnalyzer()
    analyzer.analyze_stock(args.symbol, args.days)

if __name__ == "__main__":
    # Se executado diretamente, usar exemplo padrão
    try:
        import sys
        if len(sys.argv) > 1:
            main()
        else:
            # Exemplo com AAPL
            print("🔧 Modo exemplo - analisando AAPL")
            analyzer = FINRAVolumeAnalyzer()
            analyzer.analyze_stock('AAPL', 30)
    except KeyboardInterrupt:
        print("\n\n❌ Análise interrompida pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro na execução: {str(e)}")