#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔥 FINRA VOLUME ANALYZER - VERSÃO CORRIGIDA
Usa GET para pegar dados reais do FINRA e calcular on-exchange vs off-exchange
"""

import requests
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import json

class FinraVolumeAnalyzer:
    """Análise correta de volume on-exchange vs off-exchange"""
    
    def __init__(self):
        self.finra_url = "https://api.finra.org/data/group/OTCMarket/name/regShoDaily"
        self.headers = {'Accept': 'application/json'}
    
    def get_finra_data(self):
        """Pega todos os dados do FINRA via GET"""
        print("📡 Baixando dados do FINRA...")
        
        try:
            response = requests.get(self.finra_url, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                df = pd.DataFrame(data)
                
                print(f"✅ {len(df)} registros obtidos do FINRA")
                
                # Renomear colunas para ficar mais claro
                df = df.rename(columns={
                    'securitiesInformationProcessorSymbolIdentifier': 'symbol',
                    'tradeReportDate': 'date',
                    'totalParQuantity': 'off_exchange_volume',
                    'shortParQuantity': 'off_exchange_short_volume',
                    'reportingFacilityCode': 'facility'
                })
                
                # Converter data
                df['date'] = pd.to_datetime(df['date']).dt.date
                
                return df
            else:
                print(f"❌ Erro na API: {response.status_code}")
                return pd.DataFrame()
                
        except Exception as e:
            print(f"❌ Erro: {str(e)}")
            return pd.DataFrame()
    
    def get_yahoo_data(self, symbol, days=30):
        """Pega dados do Yahoo Finance (volume total de mercado)"""
        try:
            ticker = yf.Ticker(symbol)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days+10)
            
            hist = ticker.history(start=start_date, end=end_date)
            
            if hist.empty:
                return pd.DataFrame()
            
            df = hist.reset_index()
            df['date'] = df['Date'].dt.date
            df['total_market_volume'] = df['Volume']
            df['symbol'] = symbol.upper()
            
            return df[['date', 'symbol', 'total_market_volume', 'Close']].copy()
            
        except Exception as e:
            print(f"❌ Erro Yahoo Finance para {symbol}: {str(e)}")
            return pd.DataFrame()
    
    def analyze_symbol(self, symbol):
        """Analisa um símbolo específico"""
        print(f"\n🔍 ANALISANDO {symbol.upper()}")
        print("=" * 40)
        
        # Dados do FINRA (off-exchange)
        finra_df = self.get_finra_data()
        
        if finra_df.empty:
            print(f"❌ Sem dados FINRA")
            return None
        
        # Filtrar dados do símbolo
        symbol_finra = finra_df[finra_df['symbol'] == symbol.upper()]
        
        if symbol_finra.empty:
            print(f"❌ {symbol} não encontrado nos dados FINRA")
            print("💡 Isso significa que não há volume off-exchange significativo para esta ação")
            
            # Tentar Yahoo Finance apenas
            yahoo_df = self.get_yahoo_data(symbol, 30)
            if not yahoo_df.empty:
                recent_data = yahoo_df.tail(5)
                print(f"\n📊 DADOS YAHOO FINANCE (Volume Total):")
                for _, row in recent_data.iterrows():
                    date = row['date']
                    volume = row['total_market_volume']
                    price = row['Close']
                    print(f"  📅 {date}: Volume Total = {volume:,} | Preço = ${price:.2f}")
                    print(f"    📊 Volume On-Exchange ≈ {volume:,} (100%)")
                    print(f"    📊 Volume Off-Exchange ≈ 0 (0%)")
                    print()
            
            return None
        
        # Agrupar dados FINRA por data
        finra_grouped = symbol_finra.groupby('date').agg({
            'off_exchange_volume': 'sum',
            'off_exchange_short_volume': 'sum'
        }).reset_index()
        
        # Dados do Yahoo Finance (volume total)
        yahoo_df = self.get_yahoo_data(symbol, 30)
        
        if yahoo_df.empty:
            print(f"❌ Sem dados Yahoo Finance para {symbol}")
            return None
        
        # Combinar dados
        combined = pd.merge(yahoo_df, finra_grouped, on='date', how='left')
        combined['off_exchange_volume'] = combined['off_exchange_volume'].fillna(0)
        combined['off_exchange_short_volume'] = combined['off_exchange_short_volume'].fillna(0)
        
        # Calcular on-exchange volume
        combined['on_exchange_volume'] = combined['total_market_volume'] - combined['off_exchange_volume']
        combined['on_exchange_volume'] = combined['on_exchange_volume'].clip(lower=0)
        
        # Calcular percentuais
        combined['off_exchange_pct'] = (combined['off_exchange_volume'] / combined['total_market_volume'] * 100).round(1)
        combined['on_exchange_pct'] = (combined['on_exchange_volume'] / combined['total_market_volume'] * 100).round(1)
        
        # Mostrar dados mais recentes
        recent_data = combined.tail(5)
        
        print(f"📊 VOLUME ON-EXCHANGE vs OFF-EXCHANGE - {symbol.upper()}")
        print("-" * 60)
        
        for _, row in recent_data.iterrows():
            date = row['date']
            total = row['total_market_volume']
            on_ex = row['on_exchange_volume']
            off_ex = row['off_exchange_volume']
            off_short = row['off_exchange_short_volume']
            on_pct = row['on_exchange_pct']
            off_pct = row['off_exchange_pct']
            price = row['Close']
            
            print(f"📅 {date} | Preço: ${price:.2f}")
            print(f"  📊 Volume TOTAL:      {total:,}")
            print(f"  🟢 Volume ON-EXCHANGE:  {on_ex:,} ({on_pct:.1f}%)")
            print(f"  🔴 Volume OFF-EXCHANGE: {off_ex:,} ({off_pct:.1f}%)")
            print(f"  🔻 Short Off-Exchange:  {off_short:,}")
            print()
        
        # Estatísticas médias
        avg_off_pct = combined['off_exchange_pct'].mean()
        avg_on_pct = combined['on_exchange_pct'].mean()
        
        print(f"📈 MÉDIAS ÚLTIMOS 30 DIAS:")
        print(f"  🟢 On-Exchange Médio:  {avg_on_pct:.1f}%")
        print(f"  🔴 Off-Exchange Médio: {avg_off_pct:.1f}%")
        
        return combined

def main():
    analyzer = FinraVolumeAnalyzer()
    
    # Testar com OUST e outras ações
    symbols = ['OUST', 'AAPL', 'MSFT', 'AMD']
    
    for symbol in symbols:
        result = analyzer.analyze_symbol(symbol)
        
        if result is not None:
            # Salvar resultado
            filename = f"volume_analysis_{symbol.lower()}.csv"
            result.to_csv(filename, index=False)
            print(f"💾 Dados salvos em: {filename}")
        
        print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    main()