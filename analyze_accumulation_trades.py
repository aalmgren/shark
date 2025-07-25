#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 ANÁLISE DETALHADA DOS TRADES DE ACUMULAÇÃO
Mostra EXATAMENTE quando ocorreram as situações de acumulação silenciosa
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

class AccumulationTradeAnalyzer:
    def __init__(self):
        self.ticker_list = [
            'AMD', 'TLN', 'SNPS', 'DDOG', 'ANET', 'MRVL', 'SVM', 'AVAV', 'ZETA', 
            'FCX', 'RKLB', 'INTR', 'U', 'OUST', 'XP', 'DASH', 'MSFT', 'TTD', 
            'AVGO', 'MA', 'GOOGL', 'NVDA', 'AMZN', 'WBD', 'TRIP', 'VNET', 
            'SOUN', 'BBAI', 'QS'
        ]
        
    def find_accumulation_signals(self, data, analysis_days=3, off_exchange_thresh=15, price_stability_thresh=0.5):
        """Encontra os sinais de acumulação exatos que geraram trades"""
        data = data.sort_values('date').reset_index(drop=True)
        signals = []
        
        # Para cada possível ponto de análise
        for start_idx in range(10, len(data) - 7 - analysis_days, 1):
            
            window = data.iloc[start_idx:start_idx + analysis_days].copy()
            
            if len(window) < analysis_days:
                continue
                
            # Verifica se temos dados FINRA reais (não zerados)
            if window['total_off_exchange_volume'].sum() == 0:
                continue
                
            # Métricas de ACUMULAÇÃO SILENCIOSA
            avg_off_exchange_pct = window['off_exchange_pct'].mean()
            price_change = ((window['Close'].iloc[-1] - window['Close'].iloc[0]) / window['Close'].iloc[0] * 100)
            price_volatility = window['Close'].std() / window['Close'].mean() * 100 if window['Close'].mean() > 0 else 0
            
            # Tendência de off-exchange
            off_exchange_trend = (window['off_exchange_pct'].iloc[-1] - window['off_exchange_pct'].iloc[0])
            
            # LÓGICA DE ACUMULAÇÃO SILENCIOSA
            signal_type = None
            
            # ACUMULAÇÃO SILENCIOSA: Alto off-exchange + preço estável
            if (avg_off_exchange_pct >= off_exchange_thresh and 
                abs(price_change) <= price_stability_thresh and 
                price_volatility <= 3.0):
                
                if off_exchange_trend > 0:
                    signal_type = "ACCUMULATION_STRONG"
                else:
                    signal_type = "ACCUMULATION_MODERATE"
            
            if signal_type:
                # Calcula retorno após 3 dias
                entry_idx = start_idx + analysis_days - 1
                exit_idx = entry_idx + 3  # 3 dias de holding
                
                if exit_idx < len(data):
                    entry_price = window['Close'].iloc[-1]
                    exit_price = data.iloc[exit_idx]['Close']
                    return_pct = ((exit_price - entry_price) / entry_price * 100)
                    
                    signals.append({
                        'signal_type': signal_type,
                        'analysis_start_date': window['date'].iloc[0].strftime('%Y-%m-%d'),
                        'analysis_end_date': window['date'].iloc[-1].strftime('%Y-%m-%d'),
                        'entry_date': data.iloc[entry_idx]['date'].strftime('%Y-%m-%d'),
                        'exit_date': data.iloc[exit_idx]['date'].strftime('%Y-%m-%d'),
                        'entry_price': entry_price,
                        'exit_price': exit_price,
                        'return_pct': return_pct,
                        'avg_off_exchange_pct': avg_off_exchange_pct,
                        'off_exchange_trend': off_exchange_trend,
                        'price_change_analysis': price_change,
                        'price_volatility': price_volatility,
                        'day1_off_exchange': window['off_exchange_pct'].iloc[0],
                        'day2_off_exchange': window['off_exchange_pct'].iloc[1] if len(window) > 1 else None,
                        'day3_off_exchange': window['off_exchange_pct'].iloc[2] if len(window) > 2 else None,
                        'day1_volume': window['total_market_volume'].iloc[0],
                        'day2_volume': window['total_market_volume'].iloc[1] if len(window) > 1 else None,
                        'day3_volume': window['total_market_volume'].iloc[2] if len(window) > 2 else None,
                        'day1_close': window['Close'].iloc[0],
                        'day2_close': window['Close'].iloc[1] if len(window) > 1 else None,
                        'day3_close': window['Close'].iloc[2] if len(window) > 2 else None,
                    })
        
        return signals
    
    def analyze_all_accumulation_trades(self):
        """Analisa todos os trades de acumulação encontrados"""
        print("🔍 ANÁLISE DETALHADA DOS TRADES DE ACUMULAÇÃO SILENCIOSA")
        print("=" * 70)
        
        all_signals = []
        
        for ticker in self.ticker_list:
            # Tenta dados atuais primeiro (com FINRA real)
            current_file = f"volume_analysis_{ticker.lower()}_current.csv"
            
            if os.path.exists(current_file):
                try:
                    data = pd.read_csv(current_file)
                    data['date'] = pd.to_datetime(data['date'])
                    
                    # Verifica se tem dados FINRA reais
                    if data['total_off_exchange_volume'].sum() > 0:
                        signals = self.find_accumulation_signals(data)
                        
                        for signal in signals:
                            signal['ticker'] = ticker
                            signal['data_source'] = 'current_real'
                            all_signals.append(signal)
                            
                        if signals:
                            print(f"✅ {ticker}: {len(signals)} sinais encontrados (dados reais)")
                    else:
                        print(f"⚪ {ticker}: Sem dados FINRA reais")
                        
                except Exception as e:
                    print(f"❌ {ticker}: Erro - {e}")
            else:
                print(f"❌ {ticker}: Arquivo não encontrado")
        
        if not all_signals:
            print("\n❌ NENHUM SINAL DE ACUMULAÇÃO ENCONTRADO!")
            print("💡 Isso pode acontecer porque:")
            print("   - Dados FINRA reais são limitados (poucos dias)")
            print("   - Acumulação silenciosa é evento raro")
            print("   - Parâmetros muito restritivos")
            return
        
        # Converte para DataFrame
        df = pd.DataFrame(all_signals)
        
        print(f"\n📊 TOTAL DE SINAIS ENCONTRADOS: {len(df)}")
        print(f"🎯 Distribuição por ticker:")
        
        ticker_counts = df['ticker'].value_counts()
        for ticker, count in ticker_counts.head(10).items():
            print(f"   {ticker}: {count} sinais")
        
        # Mostra os melhores casos
        self.show_detailed_signals(df)
        
        # Salva resultados
        self.save_detailed_analysis(df)
        
        return df
    
    def show_detailed_signals(self, df):
        """Mostra os sinais detalhados"""
        print(f"\n🏆 CASOS DE ACUMULAÇÃO SILENCIOSA DETECTADOS:")
        print("=" * 80)
        
        # Ordena por retorno
        df_sorted = df.sort_values('return_pct', ascending=False)
        
        for idx, signal in df_sorted.head(10).iterrows():
            print(f"\n📊 CASO #{idx + 1} - {signal['ticker']} | {signal['signal_type']}")
            print(f"   🗓️  Período de Análise: {signal['analysis_start_date']} a {signal['analysis_end_date']}")
            print(f"   💰 Entrada: {signal['entry_date']} a ${signal['entry_price']:.2f}")
            print(f"   🎯 Saída: {signal['exit_date']} a ${signal['exit_price']:.2f}")
            print(f"   📈 Retorno: {signal['return_pct']:+.2f}%")
            print(f"   \n   📊 VOLUMES OFF-EXCHANGE durante análise:")
            print(f"      Dia 1: {signal['day1_off_exchange']:.1f}% | Vol: {signal['day1_volume']:,.0f} | Preço: ${signal['day1_close']:.2f}")
            if signal['day2_off_exchange']:
                print(f"      Dia 2: {signal['day2_off_exchange']:.1f}% | Vol: {signal['day2_volume']:,.0f} | Preço: ${signal['day2_close']:.2f}")
            if signal['day3_off_exchange']:
                print(f"      Dia 3: {signal['day3_off_exchange']:.1f}% | Vol: {signal['day3_volume']:,.0f} | Preço: ${signal['day3_close']:.2f}")
            print(f"   \n   🎯 MÉTRICAS:")
            print(f"      Off-exchange médio: {signal['avg_off_exchange_pct']:.1f}%")
            print(f"      Tendência off-exchange: {signal['off_exchange_trend']:+.1f}pp")
            print(f"      Variação de preço: {signal['price_change_analysis']:+.2f}%")
            print(f"      Volatilidade: {signal['price_volatility']:.2f}%")
            print("   " + "="*50)
        
        # Estatísticas gerais
        print(f"\n📊 ESTATÍSTICAS GERAIS:")
        print(f"   📈 Retorno médio: {df['return_pct'].mean():+.2f}%")
        print(f"   🎯 Taxa de acerto: {(df['return_pct'] > 0).sum()}/{len(df)} = {(df['return_pct'] > 0).mean()*100:.1f}%")
        print(f"   📊 Off-exchange médio: {df['avg_off_exchange_pct'].mean():.1f}%")
        print(f"   🔄 Tendência off-exchange média: {df['off_exchange_trend'].mean():+.1f}pp")
    
    def save_detailed_analysis(self, df):
        """Salva análise detalhada"""
        filename = f"detailed_accumulation_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        df.to_csv(filename, index=False)
        print(f"\n💾 Análise detalhada salva em: {filename}")

if __name__ == "__main__":
    analyzer = AccumulationTradeAnalyzer()
    analyzer.analyze_all_accumulation_trades()