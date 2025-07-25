#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔥 FINRA VOLUME ANALYZER - VERSÃO ATUAL COM DADOS REAIS
Usa arquivos TXT diários do FINRA (dados atuais) + Yahoo Finance
"""

import requests
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import io
from collections import defaultdict

class FinraVolumeAnalyzerCurrent:
    """Análise atual de volume on-exchange vs off-exchange usando dados reais do FINRA"""
    
    def __init__(self):
        self.finra_base_url = "https://cdn.finra.org/equity/regsho/daily"
        # Arquivos TXT disponíveis (Consolidated NMS)
        self.finra_file_pattern = "CNMSshvol{date}.txt"
    
    def get_finra_data_current(self, days=10):
        """Baixa dados atuais do FINRA dos arquivos TXT diários"""
        print("📡 Baixando dados ATUAIS do FINRA (arquivos TXT)...")
        
        all_data = []
        dates_tried = []
        dates_success = []
        
        for i in range(days):
            # Calcular data (hoje - i dias)
            date = datetime.now() - timedelta(days=i)
            
            # Pular finais de semana
            if date.weekday() >= 5:  # 5=Saturday, 6=Sunday
                continue
                
            date_str = date.strftime('%Y%m%d')
            dates_tried.append(date_str)
            
            # URL do arquivo
            filename = self.finra_file_pattern.format(date=date_str)
            url = f"{self.finra_base_url}/{filename}"
            
            try:
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    # Parse CSV data
                    csv_data = response.text
                    
                    # Skip header and trailer
                    lines = csv_data.strip().split('\n')
                    data_lines = [line for line in lines if not line.startswith('Date|Symbol') and '|' in line and not line.isdigit()]
                    
                    for line in data_lines:
                        parts = line.split('|')
                        if len(parts) >= 5:
                            try:
                                record = {
                                    'date': datetime.strptime(parts[0], '%Y%m%d').date(),
                                    'symbol': parts[1],
                                    'short_volume': int(parts[2]),
                                    'short_exempt_volume': int(parts[3]),
                                    'total_off_exchange_volume': int(parts[4]),
                                    'markets': parts[5] if len(parts) > 5 else 'N/A'
                                }
                                all_data.append(record)
                            except (ValueError, IndexError):
                                continue
                    
                    dates_success.append(date_str)
                    
            except Exception as e:
                print(f"   ⚠️ Erro ao baixar {date_str}: {str(e)}")
                continue
        
        print(f"✅ Tentou {len(dates_tried)} datas, conseguiu {len(dates_success)} arquivos")
        print(f"📅 Datas obtidas: {', '.join(dates_success)}")
        print(f"📊 Total de registros: {len(all_data)}")
        
        if all_data:
            df = pd.DataFrame(all_data)
            return df
        else:
            return pd.DataFrame()
    
    def get_yahoo_data(self, symbol, days=30):
        """Pega dados do Yahoo Finance (volume total + preços)"""
        try:
            ticker = yf.Ticker(symbol)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days+5)
            
            hist = ticker.history(start=start_date, end=end_date)
            
            if hist.empty:
                return pd.DataFrame()
            
            df = hist.reset_index()
            df['date'] = df['Date'].dt.date
            df['total_market_volume'] = df['Volume']
            df['symbol'] = symbol.upper()
            
            return df[['date', 'symbol', 'total_market_volume', 'Close', 'Open', 'High', 'Low']].copy()
            
        except Exception as e:
            print(f"❌ Erro Yahoo Finance para {symbol}: {str(e)}")
            return pd.DataFrame()
    
    def analyze_symbol(self, symbol, finra_df):
        """Analisa um símbolo específico"""
        print(f"\n🔍 ANALISANDO {symbol.upper()}")
        print("=" * 50)
        
        # Filtrar dados FINRA para este símbolo
        symbol_finra = finra_df[finra_df['symbol'] == symbol.upper()].copy()
        
        # Dados do Yahoo Finance
        yahoo_df = self.get_yahoo_data(symbol, 15)
        
        if yahoo_df.empty:
            print(f"❌ Sem dados Yahoo Finance para {symbol}")
            return None
        
        if symbol_finra.empty:
            print(f"⚠️ {symbol} não encontrado nos dados FINRA")
            print("💡 Isso significa que não há volume off-exchange reportado para esta ação")
            
            # Mostrar apenas dados Yahoo Finance
            recent_data = yahoo_df.tail(5)
            print(f"\n📊 ÚLTIMOS 5 DIAS (apenas dados Yahoo Finance):")
            for _, row in recent_data.iterrows():
                date = row['date']
                volume = row['total_market_volume']
                price = row['Close']
                print(f"📅 {date}: Volume = {volume:,} | Preço = ${price:.2f}")
                print(f"    🟢 Volume On-Exchange ≈ {volume:,} (100%)")
                print(f"    🔴 Volume Off-Exchange ≈ 0 (0%)")
                print()
            
            return yahoo_df
        
        # Agrupar dados FINRA por data (somar volumes de diferentes markets)
        finra_grouped = symbol_finra.groupby('date').agg({
            'total_off_exchange_volume': 'sum',
            'short_volume': 'sum',
            'short_exempt_volume': 'sum'
        }).reset_index()
        
        # Combinar dados Yahoo + FINRA
        combined = pd.merge(yahoo_df, finra_grouped, on='date', how='left')
        combined['total_off_exchange_volume'] = combined['total_off_exchange_volume'].fillna(0)
        combined['short_volume'] = combined['short_volume'].fillna(0)
        combined['short_exempt_volume'] = combined['short_exempt_volume'].fillna(0)
        
        # Calcular on-exchange volume
        combined['on_exchange_volume'] = combined['total_market_volume'] - combined['total_off_exchange_volume']
        combined['on_exchange_volume'] = combined['on_exchange_volume'].clip(lower=0)
        
        # Calcular percentuais
        combined['off_exchange_pct'] = (combined['total_off_exchange_volume'] / combined['total_market_volume'] * 100).round(1)
        combined['on_exchange_pct'] = (combined['on_exchange_volume'] / combined['total_market_volume'] * 100).round(1)
        combined['short_pct_of_off_exchange'] = (
            (combined['short_volume'] / combined['total_off_exchange_volume'] * 100)
            .fillna(0).round(1)
        )
        
        # Mostrar dados mais recentes
        recent_data = combined.tail(5)
        
        print(f"📊 VOLUME ON-EXCHANGE vs OFF-EXCHANGE - {symbol.upper()}")
        print("-" * 70)
        
        for _, row in recent_data.iterrows():
            date = row['date']
            total = row['total_market_volume']
            on_ex = row['on_exchange_volume']
            off_ex = row['total_off_exchange_volume']
            short_vol = row['short_volume']
            on_pct = row['on_exchange_pct']
            off_pct = row['off_exchange_pct']
            short_pct = row['short_pct_of_off_exchange']
            price = row['Close']
            
            print(f"📅 {date} | Preço: ${price:.2f}")
            print(f"  📊 Volume TOTAL:        {total:,}")
            print(f"  🟢 Volume ON-EXCHANGE:  {on_ex:,} ({on_pct:.1f}%)")
            print(f"  🔴 Volume OFF-EXCHANGE: {off_ex:,} ({off_pct:.1f}%)")
            if off_ex > 0:
                print(f"  🔻 Short Off-Exchange:  {short_vol:,} ({short_pct:.1f}% do off-ex)")
            print()
        
        # Estatísticas médias (só dias com dados)
        valid_data = combined[combined['total_off_exchange_volume'] > 0]
        
        if len(valid_data) > 0:
            avg_off_pct = valid_data['off_exchange_pct'].mean()
            avg_on_pct = valid_data['on_exchange_pct'].mean()
            avg_short_pct = valid_data['short_pct_of_off_exchange'].mean()
            
            print(f"📈 MÉDIAS (dias com dados off-exchange):")
            print(f"  🟢 On-Exchange Médio:  {avg_on_pct:.1f}%")
            print(f"  🔴 Off-Exchange Médio: {avg_off_pct:.1f}%")
            print(f"  🔻 Short % do Off-Ex:  {avg_short_pct:.1f}%")
        
        return combined
    
    def create_summary_table(self, results):
        """Cria tabela resumo de todos os símbolos"""
        
        summary_data = []
        
        for symbol, data in results.items():
            if data is not None and not data.empty:
                # Pegar dados mais recentes
                recent = data.tail(3)  # Últimos 3 dias
                
                # Calcular médias
                avg_off_pct = recent['off_exchange_pct'].mean() if 'off_exchange_pct' in recent.columns else 0
                avg_total_volume = recent['total_market_volume'].mean()
                latest_price = recent['Close'].iloc[-1] if len(recent) > 0 else 0
                
                # Determinar categoria
                if avg_off_pct >= 40:
                    category = "🔴 Alto Off-Exchange"
                elif avg_off_pct >= 20:
                    category = "🟡 Médio Off-Exchange"
                elif avg_off_pct > 0:
                    category = "🟢 Baixo Off-Exchange"
                else:
                    category = "⚪ Apenas On-Exchange"
                
                summary_data.append({
                    'Symbol': symbol,
                    'Categoria': category,
                    'Off-Exchange %': f"{avg_off_pct:.1f}%",
                    'Volume Médio': f"{avg_total_volume:,.0f}",
                    'Preço Atual': f"${latest_price:.2f}"
                })
        
        summary_df = pd.DataFrame(summary_data)
        summary_df = summary_df.sort_values('Off-Exchange %', ascending=False)
        
        return summary_df

def main():
    analyzer = FinraVolumeAnalyzerCurrent()
    
    # Lista completa de tickers
    symbols = [
        'AMD', 'TLN', 'SNPS', 'DDOG', 'ANET', 'MRVL', 'SVM', 'AVAV', 
        'ZETA', 'FCX', 'RKLB', 'INTR', 'U', 'OUST', 'XP',
        'DASH', 'MSFT', 'TTD', 'AVGO', 'MA', 'GOOGL', 'NVDA', 
        'AMZN', 'WBD', 'TRIP', 'VNET', 'SOUN', 'BBAI', 'QS'
    ]
    
    print("🚀 ANÁLISE DE VOLUME ON-EXCHANGE vs OFF-EXCHANGE")
    print("=" * 80)
    print(f"📅 Analisando {len(symbols)} símbolos com dados ATUAIS do FINRA")
    print()
    
    # Baixar dados FINRA uma vez para todos os símbolos
    finra_df = analyzer.get_finra_data_current(days=10)
    
    if finra_df.empty:
        print("❌ Não foi possível obter dados do FINRA")
        return
    
    print(f"✅ Dados FINRA obtidos para {finra_df['symbol'].nunique()} símbolos únicos")
    print()
    
    # Analisar cada símbolo
    results = {}
    
    for symbol in symbols:
        try:
            result = analyzer.analyze_symbol(symbol, finra_df)
            results[symbol] = result
            
            if result is not None:
                # Salvar dados individuais
                filename = f"volume_analysis_{symbol.lower()}_current.csv"
                result.to_csv(filename, index=False)
                print(f"💾 Dados salvos em: {filename}")
            
            print("\n" + "-"*80 + "\n")
            
        except Exception as e:
            print(f"❌ Erro ao analisar {symbol}: {str(e)}")
            results[symbol] = None
            continue
    
    # Criar tabela resumo
    print("📋 RESUMO GERAL:")
    print("=" * 80)
    
    summary = analyzer.create_summary_table(results)
    print(summary.to_string(index=False))
    
    # Salvar resumo
    summary.to_csv("volume_summary_current.csv", index=False)
    print(f"\n💾 Resumo salvo em: volume_summary_current.csv")
    
    # Estatísticas gerais
    print(f"\n📊 ESTATÍSTICAS GERAIS:")
    symbols_with_data = len([r for r in results.values() if r is not None])
    print(f"✅ Símbolos analisados: {symbols_with_data}/{len(symbols)}")
    
    if len(finra_df) > 0:
        dates_available = sorted(finra_df['date'].unique())
        print(f"📅 Datas com dados FINRA: {dates_available[0]} a {dates_available[-1]}")

if __name__ == "__main__":
    main()