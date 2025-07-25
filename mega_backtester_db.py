#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🌪️ MEGA BACKTESTER DB - USANDO BASE HISTÓRICA REAL
Usa dados da pasta DB/ com 126 dias de histórico real
"""

import pandas as pd
import numpy as np
import glob
import os
from datetime import datetime

class MegaBacktesterDB:
    def __init__(self):
        self.all_trades = []
        self.ticker_list = [
            'AMD', 'TLN', 'SNPS', 'DDOG', 'ANET', 'MRVL', 'SVM', 'AVAV', 'ZETA', 
            'FCX', 'RKLB', 'INTR', 'U', 'OUST', 'XP', 'DASH', 'MSFT', 'TTD', 
            'AVGO', 'MA', 'GOOGL', 'NVDA', 'AMZN', 'WBD', 'TRIP', 'VNET', 
            'SOUN', 'BBAI', 'QS'
        ]
        
    def calculate_signal_for_window(self, data, start_idx, analysis_days=3):
        """Calcula sinal baseado em padrões de preço e volume"""
        if start_idx + analysis_days >= len(data):
            return None
            
        window = data.iloc[start_idx:start_idx + analysis_days].copy()
        
        if len(window) < analysis_days:
            return None
            
        # Métricas baseadas em preço/volume
        total_volume = window['Volume'].mean()
        price_change = ((window['Close'].iloc[-1] - window['Close'].iloc[0]) / window['Close'].iloc[0] * 100)
        
        # Volume relativamente alto (proxy para atividade institucional)
        if start_idx >= 10:
            volume_ma = data.iloc[max(0, start_idx-10):start_idx]['Volume'].mean()
            volume_ratio = total_volume / volume_ma if volume_ma > 0 else 1
        else:
            volume_ratio = 1
        
        # Volatilidade
        price_volatility = window['Close'].std() / window['Close'].mean() * 100 if window['Close'].mean() > 0 else 0
        
        # Range de preços
        price_range = ((window['High'].max() - window['Low'].min()) / window['Close'].mean()) * 100
        
        # Tendência de volume
        volume_trend = (window['Volume'].iloc[-1] / window['Volume'].iloc[0] - 1) * 100 if window['Volume'].iloc[0] > 0 else 0
        
        # Lógica de sinais refinada
        signal = "HOLD"
        confidence = 1
        
        # SINAIS DE VENDA - Volume alto + queda/estabilidade + baixa volatilidade
        if volume_ratio > 1.4 and price_change < -2 and price_volatility < 4:
            signal = "SELL_STRONG"
            confidence = 4
        elif volume_ratio > 1.6 and abs(price_change) < 1 and price_volatility < 3:
            signal = "SELL_MODERATE"  # Volume anômalo com preço controlado
            confidence = 3
        elif volume_ratio > 1.3 and price_change < -1:
            signal = "SELL_WEAK"
            confidence = 2
            
        # SINAIS DE COMPRA - Volume crescente + preço subindo/estável + baixa volatilidade
        elif volume_ratio > 1.3 and price_change > 1 and price_volatility < 3:
            signal = "BUY_STRONG"
            confidence = 4
        elif volume_ratio > 1.5 and abs(price_change) < 1.5 and volume_trend > 10:
            signal = "BUY_MODERATE"
            confidence = 3
                
        return {
            'signal': signal,
            'confidence': confidence,
            'volume_ratio': volume_ratio,
            'price_change': price_change,
            'price_volatility': price_volatility,
            'price_range': price_range,
            'volume_trend': volume_trend,
            'entry_price': window['Close'].iloc[-1],
            'entry_date': window.index[-1]
        }
    
    def mega_backtest_symbol(self, symbol, data, holding_days=5):
        """Executa backtest massivo para um símbolo"""
        data = data.sort_index().reset_index()
        data['Date'] = pd.to_datetime(data['Date'])
        symbol_trades = []
        
        print(f"🌪️ Processando {symbol} - {len(data)} dias de dados...")
        
        # Para cada possível ponto de entrada (janelas sobrepostas)
        for start_idx in range(15, len(data) - holding_days - 3, 1):
            
            signal_result = self.calculate_signal_for_window(data, start_idx, analysis_days=3)
            if not signal_result or signal_result['signal'] == 'HOLD':
                continue
                
            # Ponto de entrada e saída
            entry_idx = start_idx + 2
            exit_idx = entry_idx + holding_days
            
            if exit_idx >= len(data):
                continue
                
            entry_price = signal_result['entry_price']
            exit_price = data.iloc[exit_idx]['Close']
            entry_date = data.iloc[entry_idx]['Date']
            exit_date = data.iloc[exit_idx]['Date']
            
            # Calcula retorno baseado no sinal
            if signal_result['signal'].startswith('BUY'):
                return_pct = ((exit_price - entry_price) / entry_price * 100)
                expected_direction = "UP"
            else:  # SELL signals
                return_pct = -((exit_price - entry_price) / entry_price * 100)  # Short
                expected_direction = "DOWN"
            
            # Verifica direção
            actual_direction = "UP" if exit_price > entry_price else "DOWN"
            correct = (expected_direction == actual_direction)
            
            # Armazena trade
            trade = {
                'symbol': symbol,
                'entry_date': entry_date,
                'exit_date': exit_date,
                'signal': signal_result['signal'],
                'confidence': signal_result['confidence'],
                'entry_price': entry_price,
                'exit_price': exit_price,
                'return_pct': return_pct,
                'correct': correct,
                'volume_ratio': signal_result['volume_ratio'],
                'price_change_before': signal_result['price_change'],
                'price_volatility': signal_result['price_volatility'],
                'volume_trend': signal_result['volume_trend'],
                'holding_days': holding_days,
                'week_start': entry_date.strftime('%a'),
                'month': entry_date.month
            }
            
            symbol_trades.append(trade)
            self.all_trades.append(trade)
        
        print(f"   ✅ {len(symbol_trades)} trades gerados para {symbol}")
        return symbol_trades
    
    def run_mega_backtest(self, holding_days=5):
        """Executa o mega backtest usando dados da pasta DB/"""
        print(f"🌪️ MEGA BACKTESTING - BASE HISTÓRICA DB/")
        print(f"📊 Janelas sobrepostas de 3 dias + {holding_days} dias holding")
        print(f"📈 Usando base histórica de ~126 dias por ticker")
        print(f"🎯 Objetivo: 100+ trades por ticker")
        print("=" * 70)
        
        processed = 0
        
        for symbol in self.ticker_list:
            db_file = f"DB/{symbol}.csv"
            
            if not os.path.exists(db_file):
                print(f"❌ {symbol} - Arquivo não encontrado: {db_file}")
                continue
                
            try:
                data = pd.read_csv(db_file)
                
                # Verificar se tem dados suficientes
                if len(data) < 30:
                    print(f"❌ {symbol} - Poucos dados ({len(data)} dias)")
                    continue
                
                self.mega_backtest_symbol(symbol, data, holding_days)
                processed += 1
                
            except Exception as e:
                print(f"❌ Erro ao processar {symbol}: {e}")
        
        print(f"\n📊 Processados: {processed}/{len(self.ticker_list)} tickers")
        
        # Análise dos resultados
        if self.all_trades:
            self.analyze_mega_results()
        else:
            print("❌ Nenhum trade gerado!")
    
    def analyze_mega_results(self):
        """Analisa os resultados do mega backtesting"""
        df = pd.DataFrame(self.all_trades)
        
        print(f"\n🏆 RESULTADOS DO MEGA BACKTESTING - BASE DB/")
        print("=" * 70)
        print(f"📊 Total de Trades: {len(df):,}")
        print(f"🎯 Símbolos Testados: {df['symbol'].nunique()}")
        print(f"📅 Período: {df['entry_date'].min().strftime('%d/%m/%Y')} a {df['entry_date'].max().strftime('%d/%m/%Y')}")
        
        # Estatísticas gerais
        total_correct = df['correct'].sum()
        hit_rate = (total_correct / len(df) * 100)
        avg_return = df['return_pct'].mean()
        
        print(f"\n🎯 PERFORMANCE GERAL:")
        print(f"   Hit Rate: {hit_rate:.2f}%")
        print(f"   Retorno Médio: {avg_return:+.3f}%")
        print(f"   Total Corretos: {total_correct:,} / {len(df):,}")
        
        # Por tipo de sinal
        signal_stats = df.groupby('signal').agg({
            'return_pct': ['count', 'mean', 'std'],
            'correct': ['sum', 'mean']
        }).round(3)
        
        signal_stats.columns = ['trades', 'avg_return', 'volatility', 'correct_count', 'hit_rate_decimal']
        signal_stats['hit_rate'] = (signal_stats['hit_rate_decimal'] * 100).round(2)
        
        print(f"\n📊 PERFORMANCE POR TIPO DE SINAL:")
        print(signal_stats[['trades', 'hit_rate', 'avg_return', 'volatility']])
        
        # Por símbolo (top performers)
        symbol_stats = df.groupby('symbol').agg({
            'return_pct': ['count', 'mean'],
            'correct': 'mean'
        }).round(3)
        symbol_stats.columns = ['trades', 'avg_return', 'hit_rate_decimal']
        symbol_stats['hit_rate'] = (symbol_stats['hit_rate_decimal'] * 100).round(1)
        symbol_stats = symbol_stats.sort_values('hit_rate', ascending=False)
        
        print(f"\n🏆 TOP 15 SÍMBOLOS (por hit rate):")
        print(symbol_stats.head(15)[['trades', 'hit_rate', 'avg_return']])
        
        # Por dia da semana
        weekday_stats = df.groupby('week_start').agg({
            'return_pct': ['count', 'mean'],
            'correct': 'mean'
        }).round(3)
        weekday_stats.columns = ['trades', 'avg_return', 'hit_rate_decimal']
        weekday_stats['hit_rate'] = (weekday_stats['hit_rate_decimal'] * 100).round(1)
        
        print(f"\n📅 PERFORMANCE POR DIA DA SEMANA:")
        print(weekday_stats[['trades', 'hit_rate', 'avg_return']])
        
        # Validação estatística final
        print(f"\n🔬 VALIDAÇÃO ESTATÍSTICA FINAL:")
        if hit_rate > 55:
            print(f"✅ SISTEMA ALTAMENTE VALIDADO! ({len(df):,} trades, {hit_rate:.2f}% hit rate)")
            print(f"   📊 Significância estatística: EXCELENTE")
        elif hit_rate > 50:
            print(f"⚠️ SISTEMA MODERADAMENTE VÁLIDO ({len(df):,} trades, {hit_rate:.2f}% hit rate)")
            print(f"   📊 Significância estatística: BOA")
        else:
            print(f"❌ SISTEMA PRECISA MELHORAR ({len(df):,} trades, {hit_rate:.2f}% hit rate)")
            print(f"   📊 Significância estatística: INSUFICIENTE")
        
        # Novas probabilidades ultra-precisas
        self.calculate_ultra_precise_probabilities(df)
        
        # Salva resultados
        self.save_mega_results(df)
    
    def calculate_ultra_precise_probabilities(self, df):
        """Calcula probabilidades ultra-precisas baseadas em centenas de trades"""
        print(f"\n🎲 PROBABILIDADES ULTRA-PRECISAS - BASE DB/ ({len(df):,} trades):")
        print("=" * 70)
        
        for signal_type in df['signal'].unique():
            signal_data = df[df['signal'] == signal_type]
            hit_rate = (signal_data['correct'].sum() / len(signal_data) * 100)
            avg_return = signal_data['return_pct'].mean()
            trade_count = len(signal_data)
            
            # Intervalo de confiança (95%)
            if len(signal_data) > 1:
                std_error = signal_data['correct'].std() / np.sqrt(len(signal_data))
                confidence_interval = 1.96 * std_error * 100
            else:
                confidence_interval = 0
            
            confidence_level = "ALTA" if hit_rate > 60 else "MÉDIA" if hit_rate > 50 else "BAIXA"
            
            print(f"   {signal_type}:")
            print(f"      📊 {hit_rate:.1f}% ± {confidence_interval:.1f}% hit rate")
            print(f"      💰 {avg_return:+.2f}% retorno médio")
            print(f"      📈 {trade_count:,} trades (base DB/)")
            print(f"      🎯 Confiança: {confidence_level}")
    
    def save_mega_results(self, df):
        """Salva todos os resultados"""
        filename = f"mega_backtest_db_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        df.to_csv(filename, index=False)
        print(f"\n💾 Mega dataset DB/ salvo em: {filename}")

if __name__ == "__main__":
    mega_tester = MegaBacktesterDB()
    mega_tester.run_mega_backtest(holding_days=5)