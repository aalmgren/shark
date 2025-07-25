#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🌪️ SUPER MEGA BACKTESTER FINRA - ACUMULAÇÃO SILENCIOSA REAL
Testa TODAS as combinações usando dados reais de on-exchange vs off-exchange
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime

class SuperMegaBacktesterFinra:
    def __init__(self):
        self.all_results = []
        self.ticker_list = [
            'AMD', 'TLN', 'SNPS', 'DDOG', 'ANET', 'MRVL', 'SVM', 'AVAV', 'ZETA', 
            'FCX', 'RKLB', 'INTR', 'U', 'OUST', 'XP', 'DASH', 'MSFT', 'TTD', 
            'AVGO', 'MA', 'GOOGL', 'NVDA', 'AMZN', 'WBD', 'TRIP', 'VNET', 
            'SOUN', 'BBAI', 'QS'
        ]
        
        # Parâmetros para testar ACUMULAÇÃO SILENCIOSA
        self.analysis_windows = [1, 2, 3, 4, 5]  # Dias de análise
        self.holding_periods = [1, 2, 3, 4, 5, 6, 7]  # Dias de holding
        self.off_exchange_thresholds = [15, 20, 25, 30, 35, 40]  # % off-exchange mínimo
        self.price_stability_thresholds = [0.5, 1.0, 1.5, 2.0]  # Máxima variação de preço para ser "silenciosa"
        
    def calculate_accumulation_signal(self, data, start_idx, analysis_days, off_exchange_thresh, price_stability_thresh):
        """Detecta sinais de acumulação/distribuição silenciosa"""
        if start_idx + analysis_days >= len(data):
            return None
            
        window = data.iloc[start_idx:start_idx + analysis_days].copy()
        
        if len(window) < analysis_days:
            return None
            
        # Métricas de ACUMULAÇÃO SILENCIOSA
        avg_off_exchange_pct = window['off_exchange_pct'].mean()
        price_change = ((window['Close'].iloc[-1] - window['Close'].iloc[0]) / window['Close'].iloc[0] * 100)
        price_volatility = window['Close'].std() / window['Close'].mean() * 100 if window['Close'].mean() > 0 else 0
        
        # Volume total médio
        avg_volume = window['total_market_volume'].mean()
        
        # Tendência de off-exchange (crescendo ou diminuindo?)
        if len(window) >= 2:
            off_exchange_trend = (window['off_exchange_pct'].iloc[-1] - window['off_exchange_pct'].iloc[0])
        else:
            off_exchange_trend = 0
        
        # Consistência do off-exchange (baixa variação = mais suspeito)
        off_exchange_std = window['off_exchange_pct'].std()
        
        # LÓGICA DE ACUMULAÇÃO SILENCIOSA
        signal = "HOLD"
        confidence = 1
        
        # ACUMULAÇÃO SILENCIOSA: Alto off-exchange + preço estável + volume significativo
        if (avg_off_exchange_pct >= off_exchange_thresh and 
            abs(price_change) <= price_stability_thresh and 
            price_volatility <= 3.0):  # Baixa volatilidade
            
            if off_exchange_trend > 0:  # Off-exchange crescendo
                signal = "ACCUMULATION_STRONG"
                confidence = 4
            else:
                signal = "ACCUMULATION_MODERATE" 
                confidence = 3
                
        # DISTRIBUIÇÃO SILENCIOSA: Alto off-exchange + preço caindo levemente
        elif (avg_off_exchange_pct >= off_exchange_thresh and 
              price_change < -price_stability_thresh and 
              price_change > -price_stability_thresh * 2):  # Queda controlada
            
            signal = "DISTRIBUTION_STRONG"
            confidence = 4
            
        return {
            'signal': signal,
            'confidence': confidence,
            'avg_off_exchange_pct': avg_off_exchange_pct,
            'off_exchange_trend': off_exchange_trend,
            'price_change': price_change,
            'price_volatility': price_volatility,
            'off_exchange_consistency': off_exchange_std,
            'entry_price': window['Close'].iloc[-1]
        }
    
    def backtest_configuration(self, symbol, data, analysis_days, holding_days, off_exchange_thresh, price_stability_thresh):
        """Testa uma configuração específica de acumulação silenciosa"""
        data = data.sort_values('date').reset_index(drop=True)
        trades = []
        
        # Para cada possível ponto de entrada
        for start_idx in range(10, len(data) - holding_days - analysis_days, 1):
            
            signal_result = self.calculate_accumulation_signal(
                data, start_idx, analysis_days, off_exchange_thresh, price_stability_thresh
            )
            
            if not signal_result or signal_result['signal'] == 'HOLD':
                continue
                
            # Ponto de entrada e saída
            entry_idx = start_idx + analysis_days - 1
            exit_idx = entry_idx + holding_days
            
            if exit_idx >= len(data):
                continue
                
            entry_price = signal_result['entry_price']
            exit_price = data.iloc[exit_idx]['Close']
            
            # Calcula retorno baseado no tipo de sinal
            if signal_result['signal'].startswith('ACCUMULATION'):
                # Esperamos que suba após acumulação
                return_pct = ((exit_price - entry_price) / entry_price * 100)
                expected_direction = "UP"
            else:  # DISTRIBUTION
                # Esperamos que caia após distribuição
                return_pct = -((exit_price - entry_price) / entry_price * 100)
                expected_direction = "DOWN"
            
            # Verifica se a direção foi correta
            actual_direction = "UP" if exit_price > entry_price else "DOWN"
            correct = (expected_direction == actual_direction)
            
            trades.append({
                'symbol': symbol,
                'signal': signal_result['signal'],
                'return_pct': return_pct,
                'correct': correct,
                'avg_off_exchange_pct': signal_result['avg_off_exchange_pct'],
                'off_exchange_trend': signal_result['off_exchange_trend'],
                'price_change_before': signal_result['price_change'],
                'price_volatility': signal_result['price_volatility'],
                'confidence': signal_result['confidence']
            })
        
        return trades
    
    def test_all_accumulation_configs(self):
        """Testa TODAS as configurações de acumulação silenciosa"""
        print(f"🌪️ SUPER MEGA BACKTESTING - ACUMULAÇÃO SILENCIOSA REAL")
        print(f"🎯 Objetivo: Encontrar configurações de acumulação com 80%+ hit rate")
        print("=" * 70)
        
        total_configs = (len(self.analysis_windows) * len(self.holding_periods) * 
                        len(self.off_exchange_thresholds) * len(self.price_stability_thresholds))
        
        print(f"📊 Total de configurações: {total_configs:,}")
        print(f"📈 Testando acumulação silenciosa real (on/off exchange)")
        
        config_num = 0
        
        # Loop gigante sobre todas as combinações
        for analysis_days in self.analysis_windows:
            for holding_days in self.holding_periods:
                for off_exchange_thresh in self.off_exchange_thresholds:
                    for price_stability_thresh in self.price_stability_thresholds:
                        
                        config_num += 1
                        
                        if config_num % 20 == 0:
                            print(f"🔄 Processando configuração {config_num:,}/{total_configs:,}...")
                        
                        all_trades = []
                        processed_tickers = 0
                        
                        for ticker in self.ticker_list:
                            finra_file = f"finra_historical_{ticker.lower()}.csv"
                            
                            if not os.path.exists(finra_file):
                                continue
                                
                            try:
                                data = pd.read_csv(finra_file)
                                data['date'] = pd.to_datetime(data['date'])
                                
                                if len(data) < 20:
                                    continue
                                
                                trades = self.backtest_configuration(
                                    ticker, data, analysis_days, holding_days, 
                                    off_exchange_thresh, price_stability_thresh
                                )
                                
                                all_trades.extend(trades)
                                processed_tickers += 1
                                
                            except Exception as e:
                                continue
                        
                        # Analisa resultados desta configuração
                        if len(all_trades) >= 10:  # Mínimo de trades para ser válido
                            self.analyze_accumulation_config(
                                all_trades, analysis_days, holding_days,
                                off_exchange_thresh, price_stability_thresh, processed_tickers
                            )
        
        # Apresenta melhores resultados
        self.show_best_accumulation_configs()
    
    def analyze_accumulation_config(self, trades, analysis_days, holding_days, 
                                  off_exchange_thresh, price_stability_thresh, tickers_count):
        """Analisa uma configuração de acumulação específica"""
        df = pd.DataFrame(trades)
        
        # Estatísticas por tipo de sinal
        for signal_type in df['signal'].unique():
            signal_trades = df[df['signal'] == signal_type]
            
            if len(signal_trades) < 5:  # Muito poucos trades
                continue
                
            hit_rate = (signal_trades['correct'].sum() / len(signal_trades) * 100)
            avg_return = signal_trades['return_pct'].mean()
            trade_count = len(signal_trades)
            avg_off_exchange = signal_trades['avg_off_exchange_pct'].mean()
            
            # Salva resultado
            self.all_results.append({
                'signal_type': signal_type,
                'analysis_days': analysis_days,
                'holding_days': holding_days,
                'off_exchange_threshold': off_exchange_thresh,
                'price_stability_threshold': price_stability_thresh,
                'hit_rate': hit_rate,
                'avg_return': avg_return,
                'trade_count': trade_count,
                'tickers_count': tickers_count,
                'avg_off_exchange_pct': avg_off_exchange
            })
    
    def show_best_accumulation_configs(self):
        """Mostra as melhores configurações de acumulação encontradas"""
        if not self.all_results:
            print("❌ Nenhum resultado encontrado!")
            return
            
        df = pd.DataFrame(self.all_results)
        
        print(f"\n🏆 RESULTADOS - ACUMULAÇÃO SILENCIOSA REAL")
        print("=" * 80)
        print(f"📊 Total de configurações testadas: {len(df):,}")
        
        # Filtra configurações com hit rate alto
        perfect_configs = df[df['hit_rate'] >= 90].copy()
        excellent_configs = df[df['hit_rate'] >= 80].copy()
        good_configs = df[df['hit_rate'] >= 70].copy()
        
        print(f"\n🎯 CONFIGURAÇÕES DE ACUMULAÇÃO SILENCIOSA:")
        print(f"   🔥 ≥90% hit rate: {len(perfect_configs)} (PERFEITAS)")
        print(f"   🟡 ≥80% hit rate: {len(excellent_configs)} (EXCELENTES)")
        print(f"   🟢 ≥70% hit rate: {len(good_configs)} (BOAS)")
        
        if len(perfect_configs) > 0:
            print(f"\n🔥 CONFIGURAÇÕES PERFEITAS (≥90% HIT RATE):")
            perfect_configs = perfect_configs.sort_values('hit_rate', ascending=False)
            
            for _, config in perfect_configs.head(10).iterrows():
                print(f"\n   📊 {config['hit_rate']:.1f}% hit rate | {config['avg_return']:+.2f}% retorno")
                print(f"      🎯 {config['signal_type']}")
                print(f"      📈 Análise: {config['analysis_days']}d | Holding: {config['holding_days']}d")
                print(f"      📊 Off-exchange: ≥{config['off_exchange_threshold']}% | Estabilidade: ≤{config['price_stability_threshold']}%")
                print(f"      💹 Off-exchange médio: {config['avg_off_exchange_pct']:.1f}%")
                print(f"      📈 {config['trade_count']} trades | {config['tickers_count']} tickers")
        
        elif len(excellent_configs) > 0:
            print(f"\n🟡 CONFIGURAÇÕES EXCELENTES (≥80% HIT RATE):")
            excellent_configs = excellent_configs.sort_values('hit_rate', ascending=False)
            
            for _, config in excellent_configs.head(10).iterrows():
                print(f"\n   📊 {config['hit_rate']:.1f}% hit rate | {config['avg_return']:+.2f}% retorno")
                print(f"      🎯 {config['signal_type']}")
                print(f"      📈 Análise: {config['analysis_days']}d | Holding: {config['holding_days']}d")
                print(f"      📊 Off-exchange: ≥{config['off_exchange_threshold']}% | Estabilidade: ≤{config['price_stability_threshold']}%")
                print(f"      💹 Off-exchange médio: {config['avg_off_exchange_pct']:.1f}%")
                print(f"      📈 {config['trade_count']} trades | {config['tickers_count']} tickers")
        
        # Análise por tipo de sinal
        print(f"\n📊 ANÁLISE POR TIPO DE SINAL:")
        signal_analysis = df.groupby('signal_type').agg({
            'hit_rate': ['mean', 'max', 'count'],
            'avg_return': 'mean',
            'trade_count': 'sum'
        }).round(2)
        
        signal_analysis.columns = ['hit_rate_medio', 'hit_rate_max', 'configuracoes', 'retorno_medio', 'total_trades']
        print(signal_analysis)
        
        # Salva resultados detalhados
        self.save_accumulation_results(df)
    
    def save_accumulation_results(self, df):
        """Salva resultados de acumulação silenciosa"""
        filename = f"accumulation_backtest_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        df.to_csv(filename, index=False)
        print(f"\n💾 Resultados de acumulação salvos em: {filename}")
        
        # Salva apenas as melhores configurações
        best_configs = df[df['hit_rate'] >= 80].copy()
        if len(best_configs) > 0:
            best_filename = f"best_accumulation_configs_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
            best_configs.to_csv(best_filename, index=False)
            print(f"🏆 Melhores configurações de acumulação salvas em: {best_filename}")

if __name__ == "__main__":
    accumulation_tester = SuperMegaBacktesterFinra()
    accumulation_tester.test_all_accumulation_configs()