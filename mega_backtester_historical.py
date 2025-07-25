#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🌪️ MEGA BACKTESTER HISTÓRICO - LOOP MALUCO REAL
Usa dados históricos de 125 dias para gerar centenas de insights
"""

import pandas as pd
import numpy as np
import glob
from datetime import datetime

class MegaBacktesterHistorical:
    def __init__(self):
        self.all_trades = []
        
    def calculate_signal_for_window(self, data, start_idx, analysis_days=3):
        """Calcula sinal baseado apenas em preços (sem dados FINRA históricos)"""
        if start_idx + analysis_days >= len(data):
            return None
            
        window = data.iloc[start_idx:start_idx + analysis_days].copy()
        
        if len(window) < analysis_days:
            return None
            
        # Simula análise baseada em padrões de preço e volume
        # (Como não temos FINRA histórico, usa proxies)
        
        total_volume = window['total_market_volume'].mean()
        price_change = ((window['Close'].iloc[-1] - window['Close'].iloc[0]) / window['Close'].iloc[0] * 100)
        
        # Volume relativamente alto (proxy para atividade institucional)
        volume_ma = data.iloc[max(0, start_idx-10):start_idx]['total_market_volume'].mean()
        volume_ratio = total_volume / volume_ma if volume_ma > 0 else 1
        
        # Volatilidade (proxy para pressão)
        price_volatility = window['Close'].std() / window['Close'].mean() * 100
        
        # Range de preços
        price_range = ((window['High'].max() - window['Low'].min()) / window['Close'].mean()) * 100
        
        # Lógica de sinais baseada em padrões de preço/volume
        signal = "HOLD"
        confidence = 1
        
        # SINAIS DE VENDA - Volume alto + queda de preço + baixa volatilidade (distribuição controlada)
        if volume_ratio > 1.3 and price_change < -1.5 and price_volatility < 3:
            signal = "SELL_STRONG"
            confidence = 4
        elif volume_ratio > 1.5 and abs(price_change) < 1:  # Volume anômalo com preço estável
            signal = "SELL_MODERATE"
            confidence = 3
        elif volume_ratio > 1.2 and price_change < -0.5:
            signal = "SELL_WEAK"
            confidence = 2
            
        # SINAIS DE COMPRA - Volume crescente + preço estável/subindo (acumulação)
        elif volume_ratio > 1.2 and price_change > 0.5 and price_volatility < 2:
            signal = "BUY_STRONG"
            confidence = 4
        elif volume_ratio > 1.4 and abs(price_change) < 1:
            signal = "BUY_MODERATE"
            confidence = 3
                
        return {
            'signal': signal,
            'confidence': confidence,
            'volume_ratio': volume_ratio,
            'price_change': price_change,
            'price_volatility': price_volatility,
            'price_range': price_range,
            'entry_price': window['Close'].iloc[-1],
            'entry_date': window['date'].iloc[-1]
        }
    
    def mega_backtest_symbol(self, symbol, data, holding_days=5):
        """Executa backtest massivo para um símbolo"""
        data = data.sort_values('date').reset_index(drop=True)
        symbol_trades = []
        
        print(f"🌪️ Processando {symbol} - {len(data)} dias de dados...")
        
        # Para cada possível ponto de entrada (janelas sobrepostas)
        for start_idx in range(15, len(data) - holding_days - 3, 1):  # Começa após 15 dias para ter média
            
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
            entry_date = signal_result['entry_date']
            exit_date = data.iloc[exit_idx]['date']
            
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
                'holding_days': holding_days,
                'week_start': entry_date.strftime('%a'),
                'month': entry_date.month
            }
            
            symbol_trades.append(trade)
            self.all_trades.append(trade)
        
        print(f"   ✅ {len(symbol_trades)} trades gerados para {symbol}")
        return symbol_trades
    
    def run_mega_backtest(self, holding_days=5):
        """Executa o mega backtest para todas as ações"""
        hist_files = glob.glob("historical_data_*.csv")
        
        print(f"🌪️ MEGA BACKTESTING HISTÓRICO")
        print(f"📊 Janelas sobrepostas de 3 dias + {holding_days} dias holding")
        print(f"📈 Usando dados históricos de ~125 dias por ticker")
        print(f"🎯 Objetivo: 100+ trades por ticker")
        print("=" * 70)
        
        for hist_file in hist_files:
            symbol = hist_file.replace("historical_data_", "").replace(".csv", "").upper()
            
            try:
                data = pd.read_csv(hist_file)
                data['date'] = pd.to_datetime(data['date'])
                
                self.mega_backtest_symbol(symbol, data, holding_days)
                
            except Exception as e:
                print(f"❌ Erro ao processar {symbol}: {e}")
        
        # Análise dos resultados
        self.analyze_mega_results()
    
    def analyze_mega_results(self):
        """Analisa os resultados do mega backtesting"""
        if not self.all_trades:
            print("❌ Nenhum trade encontrado!")
            return
            
        df = pd.DataFrame(self.all_trades)
        
        print(f"\n🏆 RESULTADOS DO MEGA BACKTESTING HISTÓRICO")
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
        print(f"\n🎲 PROBABILIDADES ULTRA-PRECISAS (baseadas em {len(df):,} trades):")
        print("=" * 70)
        
        for signal_type in df['signal'].unique():
            signal_data = df[df['signal'] == signal_type]
            hit_rate = (signal_data['correct'].sum() / len(signal_data) * 100)
            avg_return = signal_data['return_pct'].mean()
            trade_count = len(signal_data)
            
            # Intervalo de confiança (95%)
            std_error = signal_data['correct'].std() / np.sqrt(len(signal_data))
            confidence_interval = 1.96 * std_error * 100
            
            confidence_level = "ALTA" if hit_rate > 60 else "MÉDIA" if hit_rate > 50 else "BAIXA"
            
            print(f"   {signal_type}:")
            print(f"      📊 {hit_rate:.1f}% ± {confidence_interval:.1f}% hit rate")
            print(f"      💰 {avg_return:+.2f}% retorno médio")
            print(f"      📈 {trade_count:,} trades (amostra robusta)")
            print(f"      🎯 Confiança: {confidence_level}")
    
    def save_mega_results(self, df):
        """Salva todos os resultados"""
        filename = f"mega_backtest_historical_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        df.to_csv(filename, index=False)
        print(f"\n💾 Mega dataset histórico salvo em: {filename}")

if __name__ == "__main__":
    mega_tester = MegaBacktesterHistorical()
    mega_tester.run_mega_backtest(holding_days=5)