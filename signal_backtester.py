#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📊 BACKTESTER DE SINAIS - VALIDAÇÃO ESTATÍSTICA
Testa historicamente se nossas interpretações teriam funcionado
"""

import pandas as pd
import numpy as np
import glob
from datetime import datetime, timedelta
from collections import defaultdict
import yfinance as yf

class SignalBacktester:
    def __init__(self):
        self.results = []
        self.summary_stats = {}
        
    def calculate_signal_for_period(self, data, end_date_idx):
        """Calcula sinal para um período específico (simulando decisão no passado)"""
        if end_date_idx < 3:
            return None
            
        # Pega os 3 dias anteriores ao end_date_idx
        recent = data.iloc[end_date_idx-3:end_date_idx].copy()
        
        # Filtra apenas dias com dados completos
        recent = recent[recent['total_off_exchange_volume'] > 0]
        if len(recent) < 2:
            return None
            
        # Calcula métricas (mesmo algoritmo do analisador)
        avg_off_exchange = recent['total_off_exchange_volume'].mean()
        total_volume = recent['total_market_volume'].mean()
        off_exchange_pct = (avg_off_exchange / total_volume * 100) if total_volume > 0 else 0
        
        # Variação de preço
        price_change = ((recent['Close'].iloc[-1] - recent['Close'].iloc[0]) / recent['Close'].iloc[0] * 100)
        
        # Tendência off-exchange
        if len(recent) >= 2:
            off_exchange_trend = (recent['total_off_exchange_volume'].iloc[-1] / recent['total_off_exchange_volume'].iloc[0] - 1) * 100
        else:
            off_exchange_trend = 0
            
        # Volume trend
        volume_trend = recent['total_market_volume'].iloc[-1] / recent['total_market_volume'].mean()
        
        # Determina sinal
        signal = "HOLD"
        confidence = 0
        
        # SINAIS DE VENDA
        if off_exchange_pct > 35 and price_change < -1.5:
            if off_exchange_trend > 0:
                signal = "SELL_STRONG"
                confidence = 4
            else:
                signal = "SELL_WEAK"
                confidence = 3
        elif off_exchange_pct > 40:
            signal = "SELL_MODERATE"
            confidence = 2
            
        # SINAIS DE COMPRA
        elif off_exchange_pct > 25 and abs(price_change) < 2 and volume_trend > 1.1:
            if off_exchange_trend > 5:
                signal = "BUY_STRONG"
                confidence = 4
            else:
                signal = "BUY_MODERATE"
                confidence = 3
                
        return {
            'signal': signal,
            'confidence': confidence,
            'off_exchange_pct': off_exchange_pct,
            'off_exchange_trend': off_exchange_trend,
            'price_change': price_change,
            'entry_price': recent['Close'].iloc[-1],
            'analysis_date': recent.index[-1]
        }
    
    def backtest_symbol(self, symbol, data, holding_days=5):
        """Executa backtest para um símbolo específico"""
        data = data.sort_values('date').reset_index(drop=True)
        
        # Para cada período possível, simula uma decisão
        for i in range(10, len(data) - holding_days):  # Deixa espaço para holding period
            
            signal_result = self.calculate_signal_for_period(data, i)
            if not signal_result or signal_result['signal'] == 'HOLD':
                continue
                
            # Preço de entrada
            entry_price = signal_result['entry_price']
            entry_date = data.iloc[i-1]['date']
            
            # Preço de saída (após holding_days)
            exit_price = data.iloc[i + holding_days]['Close']
            exit_date = data.iloc[i + holding_days]['date']
            
            # Calcula retorno
            if signal_result['signal'].startswith('BUY'):
                return_pct = ((exit_price - entry_price) / entry_price * 100)
                expected_direction = "UP"
            else:  # SELL signals
                return_pct = -((exit_price - entry_price) / entry_price * 100)  # Inverte para short
                expected_direction = "DOWN"
            
            # Verifica se a direção foi correta
            actual_direction = "UP" if exit_price > entry_price else "DOWN"
            correct_direction = (expected_direction == actual_direction)
            
            # Salva resultado
            self.results.append({
                'symbol': symbol,
                'entry_date': entry_date,
                'exit_date': exit_date,
                'signal': signal_result['signal'],
                'confidence': signal_result['confidence'],
                'entry_price': entry_price,
                'exit_price': exit_price,
                'return_pct': return_pct,
                'off_exchange_pct': signal_result['off_exchange_pct'],
                'off_exchange_trend': signal_result['off_exchange_trend'],
                'price_change_before': signal_result['price_change'],
                'expected_direction': expected_direction,
                'actual_direction': actual_direction,
                'correct_direction': correct_direction,
                'holding_days': holding_days
            })
    
    def run_backtest(self, holding_days=5):
        """Executa backtest para todas as ações"""
        csv_files = glob.glob("volume_analysis_*_current.csv")
        
        print(f"🔄 INICIANDO BACKTESTING COM {holding_days} DIAS DE HOLDING")
        print("=" * 60)
        
        for csv_file in csv_files:
            symbol = csv_file.replace("volume_analysis_", "").replace("_current.csv", "").upper()
            
            try:
                data = pd.read_csv(csv_file)
                data['date'] = pd.to_datetime(data['date'])
                
                print(f"📊 Testando {symbol}...")
                self.backtest_symbol(symbol, data, holding_days)
                
            except Exception as e:
                print(f"❌ Erro ao testar {symbol}: {e}")
        
        # Calcula estatísticas
        self.calculate_statistics()
        
        # Exibe resultados
        self.display_results()
        
        # Salva resultados
        self.save_results()
    
    def calculate_statistics(self):
        """Calcula estatísticas de performance"""
        if not self.results:
            return
            
        df = pd.DataFrame(self.results)
        
        # Estatísticas gerais
        total_trades = len(df)
        correct_predictions = df['correct_direction'].sum()
        hit_rate = (correct_predictions / total_trades * 100) if total_trades > 0 else 0
        
        avg_return = df['return_pct'].mean()
        total_return = df['return_pct'].sum()
        
        # Por tipo de sinal
        signal_stats = df.groupby('signal').agg({
            'return_pct': ['count', 'mean', 'sum', 'std'],
            'correct_direction': 'sum'
        }).round(2)
        
        signal_stats.columns = ['trades', 'avg_return', 'total_return', 'volatility', 'correct_count']
        signal_stats['hit_rate'] = (signal_stats['correct_count'] / signal_stats['trades'] * 100).round(1)
        
        # Por nível de confiança
        confidence_stats = df.groupby('confidence').agg({
            'return_pct': ['count', 'mean'],
            'correct_direction': 'sum'
        }).round(2)
        confidence_stats.columns = ['trades', 'avg_return', 'correct_count']
        confidence_stats['hit_rate'] = (confidence_stats['correct_count'] / confidence_stats['trades'] * 100).round(1)
        
        self.summary_stats = {
            'total_trades': total_trades,
            'hit_rate': hit_rate,
            'avg_return': avg_return,
            'total_return': total_return,
            'signal_stats': signal_stats,
            'confidence_stats': confidence_stats,
            'best_signals': df.nlargest(10, 'return_pct'),
            'worst_signals': df.nsmallest(10, 'return_pct')
        }
    
    def display_results(self):
        """Exibe resultados do backtesting"""
        stats = self.summary_stats
        
        print(f"\n🎯 RESULTADOS DO BACKTESTING")
        print("=" * 60)
        print(f"📊 Total de Trades: {stats['total_trades']}")
        print(f"🎯 Hit Rate: {stats['hit_rate']:.1f}%")
        print(f"💰 Retorno Médio por Trade: {stats['avg_return']:+.2f}%")
        print(f"📈 Retorno Total: {stats['total_return']:+.2f}%")
        
        print(f"\n📊 PERFORMANCE POR TIPO DE SINAL:")
        print(stats['signal_stats'])
        
        print(f"\n🔢 PERFORMANCE POR CONFIANÇA:")
        print(stats['confidence_stats'])
        
        print(f"\n🏆 TOP 5 MELHORES TRADES:")
        for _, trade in stats['best_signals'].head().iterrows():
            print(f"   {trade['symbol']} | {trade['signal']} | {trade['entry_date'].strftime('%d/%m')} | {trade['return_pct']:+.1f}%")
        
        print(f"\n💸 TOP 5 PIORES TRADES:")
        for _, trade in stats['worst_signals'].head().iterrows():
            print(f"   {trade['symbol']} | {trade['signal']} | {trade['entry_date'].strftime('%d/%m')} | {trade['return_pct']:+.1f}%")
        
        # Validação estatística
        if stats['hit_rate'] > 55:
            print(f"\n✅ SISTEMA VALIDADO! Hit rate de {stats['hit_rate']:.1f}% > 55%")
        elif stats['hit_rate'] > 50:
            print(f"\n⚠️ SISTEMA MARGINALMENTE VÁLIDO. Hit rate de {stats['hit_rate']:.1f}%")
        else:
            print(f"\n❌ SISTEMA PRECISA MELHORAR. Hit rate de {stats['hit_rate']:.1f}% < 50%")
    
    def save_results(self):
        """Salva resultados detalhados"""
        if self.results:
            df = pd.DataFrame(self.results)
            filename = f"backtest_results_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
            df.to_csv(filename, index=False)
            print(f"\n💾 Resultados salvos em: {filename}")

if __name__ == "__main__":
    backtester = SignalBacktester()
    
    # Testa com diferentes períodos de holding
    for holding_days in [3, 5, 7]:
        print(f"\n{'='*80}")
        print(f"🔄 TESTANDO COM {holding_days} DIAS DE HOLDING")
        print(f"{'='*80}")
        
        backtester.results = []  # Reset results
        backtester.run_backtest(holding_days)
        
        input(f"\nPressione Enter para testar próximo período ({holding_days+2} dias)...")