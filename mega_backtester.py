#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🌪️ MEGA BACKTESTER - LOOP MALUCO COM JANELAS SOBREPOSTAS
Roda análises semanais em TODOS os pontos possíveis dos últimos 180 dias
"""

import pandas as pd
import numpy as np
import glob
from datetime import datetime, timedelta
from collections import defaultdict

class MegaBacktester:
    def __init__(self):
        self.all_trades = []
        self.summary_stats = {}
        
    def calculate_signal_for_window(self, data, start_idx, analysis_days=3):
        """Calcula sinal para uma janela específica"""
        if start_idx + analysis_days >= len(data):
            return None
            
        # Pega os dias da análise
        window = data.iloc[start_idx:start_idx + analysis_days].copy()
        
        # Filtra apenas dias com dados completos
        complete_window = window[window['total_off_exchange_volume'] > 0]
        if len(complete_window) < 2:
            return None
            
        # Métricas (mesmo algoritmo validado)
        avg_off_exchange = complete_window['total_off_exchange_volume'].mean()
        total_volume = complete_window['total_market_volume'].mean()
        off_exchange_pct = (avg_off_exchange / total_volume * 100) if total_volume > 0 else 0
        
        # Variação de preço na janela
        price_change = ((complete_window['Close'].iloc[-1] - complete_window['Close'].iloc[0]) / complete_window['Close'].iloc[0] * 100)
        
        # Tendência off-exchange
        if len(complete_window) >= 2:
            off_exchange_trend = (complete_window['total_off_exchange_volume'].iloc[-1] / complete_window['total_off_exchange_volume'].iloc[0] - 1) * 100
        else:
            off_exchange_trend = 0
            
        # Volume trend
        volume_trend = complete_window['total_market_volume'].iloc[-1] / complete_window['total_market_volume'].mean()
        
        # Determina sinal
        signal = "HOLD"
        confidence = 1
        
        # Lógica de sinais
        if off_exchange_pct > 35 and price_change < -1.5:
            if off_exchange_trend > 0:
                signal = "SELL_STRONG"
                confidence = 4
            else:
                signal = "SELL_WEAK"
                confidence = 2
        elif off_exchange_pct > 40:
            signal = "SELL_MODERATE"
            confidence = 3
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
            'entry_price': complete_window['Close'].iloc[-1],
            'entry_date': complete_window['date'].iloc[-1],
            'volume_trend': volume_trend
        }
    
    def mega_backtest_symbol(self, symbol, data, holding_days=5):
        """Executa backtest massivo para um símbolo"""
        data = data.sort_values('date').reset_index(drop=True)
        symbol_trades = []
        
        print(f"🌪️ Processando {symbol} - {len(data)} dias de dados...")
        
        # Para cada possível ponto de entrada (janelas sobrepostas)
        for start_idx in range(0, len(data) - holding_days - 3, 1):  # Avança 1 dia por vez
            
            signal_result = self.calculate_signal_for_window(data, start_idx, analysis_days=3)
            if not signal_result or signal_result['signal'] == 'HOLD':
                continue
                
            # Ponto de entrada e saída
            entry_idx = start_idx + 2  # Final da janela de análise
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
                'off_exchange_pct': signal_result['off_exchange_pct'],
                'off_exchange_trend': signal_result['off_exchange_trend'],
                'price_change_before': signal_result['price_change'],
                'volume_trend': signal_result['volume_trend'],
                'holding_days': holding_days,
                'week_start': entry_date.strftime('%a'),  # Dia da semana
                'month': entry_date.month
            }
            
            symbol_trades.append(trade)
            self.all_trades.append(trade)
        
        print(f"   ✅ {len(symbol_trades)} trades gerados para {symbol}")
        return symbol_trades
    
    def run_mega_backtest(self, holding_days=5):
        """Executa o mega backtest para todas as ações"""
        csv_files = glob.glob("volume_analysis_*_current.csv")
        
        print(f"🌪️ INICIANDO MEGA BACKTESTING")
        print(f"📊 Janelas sobrepostas de 3 dias + {holding_days} dias holding")
        print(f"🎯 Objetivo: 100+ trades por ticker")
        print("=" * 70)
        
        for csv_file in csv_files:
            symbol = csv_file.replace("volume_analysis_", "").replace("_current.csv", "").upper()
            
            try:
                data = pd.read_csv(csv_file)
                data['date'] = pd.to_datetime(data['date'])
                
                # Filtra últimos 180 dias se tiver dados suficientes
                if len(data) > 180:
                    data = data.tail(180)
                
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
        
        print(f"\n🏆 RESULTADOS DO MEGA BACKTESTING")
        print("=" * 60)
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
        
        print(f"\n🏆 TOP 10 SÍMBOLOS (por hit rate):")
        print(symbol_stats.head(10)[['trades', 'hit_rate', 'avg_return']])
        
        # Por dia da semana
        weekday_stats = df.groupby('week_start').agg({
            'return_pct': ['count', 'mean'],
            'correct': 'mean'
        }).round(3)
        weekday_stats.columns = ['trades', 'avg_return', 'hit_rate_decimal']
        weekday_stats['hit_rate'] = (weekday_stats['hit_rate_decimal'] * 100).round(1)
        
        print(f"\n📅 PERFORMANCE POR DIA DA SEMANA:")
        print(weekday_stats[['trades', 'hit_rate', 'avg_return']])
        
        # Validação estatística
        print(f"\n🔬 VALIDAÇÃO ESTATÍSTICA:")
        if hit_rate > 55:
            print(f"✅ SISTEMA ALTAMENTE VALIDADO! ({len(df):,} trades, {hit_rate:.2f}% hit rate)")
        elif hit_rate > 50:
            print(f"⚠️ SISTEMA MODERADAMENTE VÁLIDO ({len(df):,} trades, {hit_rate:.2f}% hit rate)")
        else:
            print(f"❌ SISTEMA PRECISA MELHORAR ({len(df):,} trades, {hit_rate:.2f}% hit rate)")
        
        # Calcula novos thresholds baseados nos dados massivos
        self.calculate_new_probabilities(df)
        
        # Salva resultados
        self.save_mega_results(df)
    
    def calculate_new_probabilities(self, df):
        """Calcula novas probabilidades baseadas no mega dataset"""
        print(f"\n🎲 NOVAS PROBABILIDADES (baseadas em {len(df):,} trades):")
        print("=" * 60)
        
        for signal_type in df['signal'].unique():
            signal_data = df[df['signal'] == signal_type]
            hit_rate = (signal_data['correct'].sum() / len(signal_data) * 100)
            avg_return = signal_data['return_pct'].mean()
            trade_count = len(signal_data)
            
            confidence_level = "ALTA" if hit_rate > 60 else "MÉDIA" if hit_rate > 50 else "BAIXA"
            
            print(f"   {signal_type}:")
            print(f"      📊 {hit_rate:.1f}% hit rate ({trade_count:,} trades)")
            print(f"      💰 {avg_return:+.2f}% retorno médio")
            print(f"      🎯 Confiança: {confidence_level}")
    
    def save_mega_results(self, df):
        """Salva todos os resultados"""
        filename = f"mega_backtest_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        df.to_csv(filename, index=False)
        print(f"\n💾 Mega dataset salvo em: {filename}")

if __name__ == "__main__":
    mega_tester = MegaBacktester()
    mega_tester.run_mega_backtest(holding_days=5)