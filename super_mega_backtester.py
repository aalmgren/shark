#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🌪️ SUPER MEGA BACKTESTER - LOOP SOBRE LOOP GIGANTE
Testa TODAS as combinações possíveis para encontrar 80%+ hit rate
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime
from itertools import product

class SuperMegaBacktester:
    def __init__(self):
        self.all_results = []
        self.ticker_info = {
            # Tech stocks
            'TECH': ['AMD', 'NVDA', 'GOOGL', 'MSFT', 'AVGO', 'SNPS', 'DDOG', 'ANET', 'TTD'],
            # Non-tech stocks  
            'NON_TECH': ['TLN', 'MRVL', 'SVM', 'AVAV', 'ZETA', 'FCX', 'RKLB', 'INTR', 'U', 
                         'OUST', 'XP', 'DASH', 'MA', 'AMZN', 'WBD', 'TRIP', 'VNET', 'SOUN', 
                         'BBAI', 'QS']
        }
        
        # Parâmetros para testar
        self.analysis_windows = [1, 2, 3, 4, 5]  # Dias de análise
        self.holding_periods = [1, 2, 3, 4, 5, 6, 7]  # Dias de holding
        self.volume_thresholds = [1.2, 1.3, 1.4, 1.5, 1.6, 1.7]  # Multiplicadores de volume
        self.price_change_thresholds = [0.5, 1.0, 1.5, 2.0, 2.5]  # % mudança de preço
        
    def calculate_signal_advanced(self, data, start_idx, analysis_days, volume_thresh, price_thresh):
        """Calcula sinal com parâmetros customizáveis"""
        if start_idx + analysis_days >= len(data):
            return None
            
        window = data.iloc[start_idx:start_idx + analysis_days].copy()
        
        if len(window) < analysis_days:
            return None
            
        # Métricas
        total_volume = window['Volume'].mean()
        price_change = ((window['Close'].iloc[-1] - window['Close'].iloc[0]) / window['Close'].iloc[0] * 100)
        
        # Volume ratio
        if start_idx >= 10:
            volume_ma = data.iloc[max(0, start_idx-10):start_idx]['Volume'].mean()
            volume_ratio = total_volume / volume_ma if volume_ma > 0 else 1
        else:
            volume_ratio = 1
        
        # Volatilidade
        price_volatility = window['Close'].std() / window['Close'].mean() * 100 if window['Close'].mean() > 0 else 0
        
        # Lógica de sinais com parâmetros customizáveis
        signal = "HOLD"
        
        # COMPRA: Volume alto + preço subindo + baixa volatilidade
        if (volume_ratio > volume_thresh and 
            price_change > price_thresh and 
            price_volatility < 4):
            signal = "BUY_STRONG"
        elif (volume_ratio > volume_thresh * 1.2 and 
              abs(price_change) < price_thresh/2 and 
              price_volatility < 3):
            signal = "BUY_MODERATE"
            
        # VENDA: Volume alto + preço caindo + baixa volatilidade  
        elif (volume_ratio > volume_thresh and 
              price_change < -price_thresh and 
              price_volatility < 4):
            signal = "SELL_STRONG"
        elif (volume_ratio > volume_thresh * 1.2 and 
              abs(price_change) < price_thresh/2 and 
              price_volatility < 3):
            signal = "SELL_MODERATE"
                
        return {
            'signal': signal,
            'volume_ratio': volume_ratio,
            'price_change': price_change,
            'price_volatility': price_volatility,
            'entry_price': window['Close'].iloc[-1]
        }
    
    def backtest_configuration(self, symbol, data, analysis_days, holding_days, volume_thresh, price_thresh):
        """Testa uma configuração específica"""
        data = data.reset_index(drop=True)
        trades = []
        
        # Para cada possível ponto de entrada
        for start_idx in range(15, len(data) - holding_days - analysis_days, 1):
            
            signal_result = self.calculate_signal_advanced(data, start_idx, analysis_days, volume_thresh, price_thresh)
            if not signal_result or signal_result['signal'] == 'HOLD':
                continue
                
            # Ponto de entrada e saída
            entry_idx = start_idx + analysis_days - 1
            exit_idx = entry_idx + holding_days
            
            if exit_idx >= len(data):
                continue
                
            entry_price = signal_result['entry_price']
            exit_price = data.iloc[exit_idx]['Close']
            
            # Calcula retorno
            if signal_result['signal'].startswith('BUY'):
                return_pct = ((exit_price - entry_price) / entry_price * 100)
                expected_direction = "UP"
            else:  # SELL
                return_pct = -((exit_price - entry_price) / entry_price * 100)
                expected_direction = "DOWN"
            
            # Verifica direção
            actual_direction = "UP" if exit_price > entry_price else "DOWN"
            correct = (expected_direction == actual_direction)
            
            trades.append({
                'symbol': symbol,
                'signal': signal_result['signal'],
                'return_pct': return_pct,
                'correct': correct,
                'volume_ratio': signal_result['volume_ratio'],
                'price_change_before': signal_result['price_change']
            })
        
        return trades
    
    def test_all_configurations(self):
        """Testa TODAS as configurações possíveis"""
        print(f"🌪️ SUPER MEGA BACKTESTING - LOOP SOBRE LOOP GIGANTE")
        print(f"🎯 Objetivo: Encontrar configurações com 80%+ hit rate")
        print("=" * 70)
        
        total_configs = (len(self.analysis_windows) * len(self.holding_periods) * 
                        len(self.volume_thresholds) * len(self.price_change_thresholds))
        
        print(f"📊 Total de configurações: {total_configs:,}")
        print(f"📈 Por setor: TECH ({len(self.ticker_info['TECH'])}) vs NON-TECH ({len(self.ticker_info['NON_TECH'])})")
        
        config_num = 0
        
        # Loop gigante sobre todas as combinações
        for analysis_days in self.analysis_windows:
            for holding_days in self.holding_periods:
                for volume_thresh in self.volume_thresholds:
                    for price_thresh in self.price_change_thresholds:
                        
                        config_num += 1
                        
                        if config_num % 50 == 0:
                            print(f"🔄 Processando configuração {config_num:,}/{total_configs:,}...")
                        
                        # Testa para cada setor
                        for sector, tickers in self.ticker_info.items():
                            
                            all_trades = []
                            processed_tickers = 0
                            
                            for ticker in tickers:
                                db_file = f"DB/{ticker}.csv"
                                
                                if not os.path.exists(db_file):
                                    continue
                                    
                                try:
                                    data = pd.read_csv(db_file)
                                    if len(data) < 30:
                                        continue
                                    
                                    data['Date'] = pd.to_datetime(data['Date'])
                                    
                                    trades = self.backtest_configuration(
                                        ticker, data, analysis_days, holding_days, 
                                        volume_thresh, price_thresh
                                    )
                                    
                                    all_trades.extend(trades)
                                    processed_tickers += 1
                                    
                                except Exception as e:
                                    continue
                            
                            # Analisa resultados desta configuração
                            if len(all_trades) >= 10:  # Mínimo de trades para ser válido
                                self.analyze_configuration(
                                    all_trades, sector, analysis_days, holding_days,
                                    volume_thresh, price_thresh, processed_tickers
                                )
        
        # Apresenta melhores resultados
        self.show_best_configurations()
    
    def analyze_configuration(self, trades, sector, analysis_days, holding_days, 
                            volume_thresh, price_thresh, tickers_count):
        """Analisa uma configuração específica"""
        df = pd.DataFrame(trades)
        
        # Estatísticas por tipo de sinal
        for signal_type in df['signal'].unique():
            signal_trades = df[df['signal'] == signal_type]
            
            if len(signal_trades) < 5:  # Muito poucos trades
                continue
                
            hit_rate = (signal_trades['correct'].sum() / len(signal_trades) * 100)
            avg_return = signal_trades['return_pct'].mean()
            trade_count = len(signal_trades)
            
            # Salva resultado
            self.all_results.append({
                'sector': sector,
                'signal_type': signal_type,
                'analysis_days': analysis_days,
                'holding_days': holding_days,
                'volume_threshold': volume_thresh,
                'price_threshold': price_thresh,
                'hit_rate': hit_rate,
                'avg_return': avg_return,
                'trade_count': trade_count,
                'tickers_count': tickers_count
            })
    
    def show_best_configurations(self):
        """Mostra as melhores configurações encontradas"""
        if not self.all_results:
            print("❌ Nenhum resultado encontrado!")
            return
            
        df = pd.DataFrame(self.all_results)
        
        print(f"\n🏆 RESULTADOS DO SUPER MEGA BACKTESTING")
        print("=" * 80)
        print(f"📊 Total de configurações testadas: {len(df):,}")
        
        # Filtra configurações com hit rate alto
        high_performance = df[df['hit_rate'] >= 80].copy()
        good_performance = df[df['hit_rate'] >= 70].copy()
        decent_performance = df[df['hit_rate'] >= 60].copy()
        
        print(f"\n🎯 CONFIGURAÇÕES DE ALTO DESEMPENHO:")
        print(f"   🔥 ≥80% hit rate: {len(high_performance)}")
        print(f"   🟡 ≥70% hit rate: {len(good_performance)}")
        print(f"   🟢 ≥60% hit rate: {len(decent_performance)}")
        
        if len(high_performance) > 0:
            print(f"\n🔥 TOP CONFIGURAÇÕES (≥80% HIT RATE):")
            high_performance = high_performance.sort_values('hit_rate', ascending=False)
            
            for _, config in high_performance.head(10).iterrows():
                print(f"\n   📊 {config['hit_rate']:.1f}% hit rate | {config['avg_return']:+.2f}% retorno")
                print(f"      🎯 {config['signal_type']} | {config['sector']} setor")
                print(f"      📈 Análise: {config['analysis_days']}d | Holding: {config['holding_days']}d")
                print(f"      ⚙️ Volume: {config['volume_threshold']}x | Preço: {config['price_threshold']}%")
                print(f"      📊 {config['trade_count']} trades | {config['tickers_count']} tickers")
        
        elif len(good_performance) > 0:
            print(f"\n🟡 TOP CONFIGURAÇÕES (≥70% HIT RATE):")
            good_performance = good_performance.sort_values('hit_rate', ascending=False)
            
            for _, config in good_performance.head(10).iterrows():
                print(f"\n   📊 {config['hit_rate']:.1f}% hit rate | {config['avg_return']:+.2f}% retorno")
                print(f"      🎯 {config['signal_type']} | {config['sector']} setor")
                print(f"      📈 Análise: {config['analysis_days']}d | Holding: {config['holding_days']}d")
                print(f"      ⚙️ Volume: {config['volume_threshold']}x | Preço: {config['price_threshold']}%")
                print(f"      📊 {config['trade_count']} trades | {config['tickers_count']} tickers")
        
        # Análise por setor
        print(f"\n📊 ANÁLISE POR SETOR:")
        sector_analysis = df.groupby('sector').agg({
            'hit_rate': ['mean', 'max', 'count'],
            'avg_return': 'mean'
        }).round(2)
        
        sector_analysis.columns = ['hit_rate_medio', 'hit_rate_max', 'configuracoes', 'retorno_medio']
        print(sector_analysis)
        
        # Salva resultados detalhados
        self.save_detailed_results(df)
    
    def save_detailed_results(self, df):
        """Salva resultados detalhados"""
        filename = f"super_mega_backtest_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        df.to_csv(filename, index=False)
        print(f"\n💾 Resultados detalhados salvos em: {filename}")
        
        # Salva apenas as melhores configurações
        best_configs = df[df['hit_rate'] >= 70].copy()
        if len(best_configs) > 0:
            best_filename = f"best_configurations_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
            best_configs.to_csv(best_filename, index=False)
            print(f"🏆 Melhores configurações salvas em: {best_filename}")

if __name__ == "__main__":
    super_tester = SuperMegaBacktester()
    super_tester.test_all_configurations()