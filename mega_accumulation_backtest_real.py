#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 SUPER MEGA BACKTESTING ESTATÍSTICO - DADOS FINRA REAIS
Testa acumulação silenciosa com 125 dias reais × 29 tickers × janelas sobrepostas
= MILHARES de insights para validação estatística robusta
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime

class MegaAccumulationBacktestReal:
    def __init__(self):
        self.ticker_list = [
            'AMD', 'TLN', 'SNPS', 'DDOG', 'ANET', 'MRVL', 'SVM', 'AVAV', 'ZETA', 
            'FCX', 'RKLB', 'INTR', 'U', 'OUST', 'XP', 'DASH', 'MSFT', 'TTD', 
            'AVGO', 'MA', 'GOOGL', 'NVDA', 'AMZN', 'WBD', 'TRIP', 'VNET', 
            'SOUN', 'BBAI', 'QS'
        ]
        
        # Parâmetros para testar TODAS as combinações
        self.analysis_windows = [2, 3, 4, 5]  # Dias de análise
        self.holding_periods = [1, 2, 3, 4, 5, 6, 7]  # Dias de holding
        self.off_exchange_thresholds = [20, 25, 30, 35, 40, 45, 50]  # % mínimo off-exchange
        self.price_stability_thresholds = [0.5, 1.0, 1.5, 2.0, 2.5]  # Máx variação para ser "silencioso"
        
        self.all_trades = []
        
    def detect_accumulation_signal(self, data, start_idx, analysis_days, off_exchange_thresh, price_stability_thresh):
        """Detecta sinal de acumulação silenciosa"""
        if start_idx + analysis_days >= len(data):
            return None
            
        window = data.iloc[start_idx:start_idx + analysis_days].copy()
        
        if len(window) < analysis_days:
            return None
            
        # Métricas de acumulação silenciosa
        avg_off_exchange_pct = window['off_exchange_pct'].mean()
        price_change = ((window['Close'].iloc[-1] - window['Close'].iloc[0]) / window['Close'].iloc[0] * 100)
        price_volatility = window['Close'].std() / window['Close'].mean() * 100 if window['Close'].mean() > 0 else 0
        
        # Tendência de off-exchange
        off_exchange_trend = window['off_exchange_pct'].iloc[-1] - window['off_exchange_pct'].iloc[0]
        
        # Critérios de ACUMULAÇÃO SILENCIOSA
        if (avg_off_exchange_pct >= off_exchange_thresh and 
            abs(price_change) <= price_stability_thresh and 
            price_volatility <= 5.0):  # Volatilidade baixa
            
            signal_strength = 1
            if off_exchange_trend > 0:  # Crescendo
                signal_strength = 2
            if avg_off_exchange_pct >= 50:  # Muito alto
                signal_strength = 3
                
            return {
                'signal': 'ACCUMULATION',
                'strength': signal_strength,
                'avg_off_exchange_pct': avg_off_exchange_pct,
                'off_exchange_trend': off_exchange_trend,
                'price_change': price_change,
                'price_volatility': price_volatility,
                'entry_price': window['Close'].iloc[-1]
            }
        
        return None
    
    def backtest_configuration(self, symbol, data, analysis_days, holding_days, off_exchange_thresh, price_stability_thresh):
        """Testa uma configuração específica em uma ação"""
        data = data.sort_values('date').reset_index(drop=True)
        trades = []
        
        # JANELAS SOBREPOSTAS: Move 1 dia por vez para máxima cobertura
        for start_idx in range(len(data) - analysis_days - holding_days):
            
            signal = self.detect_accumulation_signal(
                data, start_idx, analysis_days, off_exchange_thresh, price_stability_thresh
            )
            
            if not signal:
                continue
                
            # Ponto de entrada e saída
            entry_idx = start_idx + analysis_days - 1
            exit_idx = entry_idx + holding_days
            
            if exit_idx >= len(data):
                continue
                
            entry_price = signal['entry_price']
            exit_price = data.iloc[exit_idx]['Close']
            return_pct = ((exit_price - entry_price) / entry_price * 100)
            
            trades.append({
                'symbol': symbol,
                'entry_date': data.iloc[entry_idx]['date'],
                'exit_date': data.iloc[exit_idx]['date'],
                'entry_price': entry_price,
                'exit_price': exit_price,
                'return_pct': return_pct,
                'signal_strength': signal['strength'],
                'avg_off_exchange_pct': signal['avg_off_exchange_pct'],
                'off_exchange_trend': signal['off_exchange_trend'],
                'price_change': signal['price_change'],
                'analysis_days': analysis_days,
                'holding_days': holding_days,
                'off_exchange_threshold': off_exchange_thresh,
                'price_stability_threshold': price_stability_thresh
            })
        
        return trades
    
    def run_mega_backtest(self):
        """Executa o mega backtesting com TODAS as combinações"""
        print("🚀 SUPER MEGA BACKTESTING ESTATÍSTICO - DADOS FINRA REAIS")
        print("=" * 80)
        
        total_configs = (len(self.analysis_windows) * len(self.holding_periods) * 
                        len(self.off_exchange_thresholds) * len(self.price_stability_thresholds))
        
        print(f"📊 Configurações totais: {total_configs:,}")
        print(f"🎯 Tickers: {len(self.ticker_list)}")
        print(f"📅 Dados: 125 dias reais por ticker")
        print(f"🔄 Janelas sobrepostas: Máxima cobertura estatística")
        print("")
        
        config_count = 0
        total_trades_generated = 0
        
        # Loop gigante sobre TODAS as combinações
        for analysis_days in self.analysis_windows:
            for holding_days in self.holding_periods:
                for off_exchange_thresh in self.off_exchange_thresholds:
                    for price_stability_thresh in self.price_stability_thresholds:
                        
                        config_count += 1
                        config_trades = []
                        
                        if config_count % 50 == 0:
                            print(f"🔄 Configuração {config_count:,}/{total_configs:,} | Trades: {total_trades_generated:,}")
                        
                        # Testa em todos os tickers
                        for ticker in self.ticker_list:
                            finra_file = f"finra_real_180d_{ticker.lower()}.csv"
                            
                            if not os.path.exists(finra_file):
                                continue
                                
                            try:
                                data = pd.read_csv(finra_file)
                                data['date'] = pd.to_datetime(data['date'])
                                
                                if len(data) < 20:
                                    continue
                                
                                ticker_trades = self.backtest_configuration(
                                    ticker, data, analysis_days, holding_days,
                                    off_exchange_thresh, price_stability_thresh
                                )
                                
                                config_trades.extend(ticker_trades)
                                
                            except Exception as e:
                                continue
                        
                        # Adiciona trades desta configuração
                        self.all_trades.extend(config_trades)
                        total_trades_generated += len(config_trades)
        
        print(f"\n🎉 BACKTESTING CONCLUÍDO!")
        print(f"📊 Total de configurações testadas: {config_count:,}")
        print(f"🎯 Total de trades gerados: {total_trades_generated:,}")
        print(f"📈 Média de trades por configuração: {total_trades_generated/config_count:.1f}")
        
        # Analisa resultados
        self.analyze_mega_results()
    
    def analyze_mega_results(self):
        """Analisa os resultados do mega backtesting"""
        if not self.all_trades:
            print("❌ Nenhum trade encontrado!")
            return
            
        df = pd.DataFrame(self.all_trades)
        
        print(f"\n📊 ANÁLISE ESTATÍSTICA ROBUSTA")
        print("=" * 60)
        
        # Estatísticas gerais
        total_trades = len(df)
        winning_trades = (df['return_pct'] > 0).sum()
        hit_rate = (winning_trades / total_trades * 100)
        avg_return = df['return_pct'].mean()
        
        print(f"🎯 RESULTADOS GLOBAIS:")
        print(f"   Total de trades: {total_trades:,}")
        print(f"   Trades positivos: {winning_trades:,}")
        print(f"   Hit rate: {hit_rate:.2f}%")
        print(f"   Retorno médio: {avg_return:+.3f}%")
        print(f"   Desvio padrão: {df['return_pct'].std():.3f}%")
        
        # Análise por força do sinal
        print(f"\n🔥 ANÁLISE POR FORÇA DO SINAL:")
        for strength in sorted(df['signal_strength'].unique()):
            subset = df[df['signal_strength'] == strength]
            subset_hit_rate = (subset['return_pct'] > 0).mean() * 100
            subset_avg_return = subset['return_pct'].mean()
            
            print(f"   Força {strength}: {subset_hit_rate:.1f}% hit rate | {subset_avg_return:+.3f}% retorno | {len(subset):,} trades")
        
        # Melhores configurações
        print(f"\n🏆 MELHORES CONFIGURAÇÕES:")
        
        # Agrupa por configuração
        config_results = df.groupby([
            'analysis_days', 'holding_days', 'off_exchange_threshold', 'price_stability_threshold'
        ]).agg({
            'return_pct': ['count', 'mean', lambda x: (x > 0).mean() * 100],
            'avg_off_exchange_pct': 'mean'
        }).round(3)
        
        config_results.columns = ['trade_count', 'avg_return', 'hit_rate', 'avg_off_exchange']
        
        # Filtra configurações com pelo menos 50 trades
        valid_configs = config_results[config_results['trade_count'] >= 50].copy()
        
        if len(valid_configs) > 0:
            # Ordena por hit rate
            top_configs = valid_configs.sort_values('hit_rate', ascending=False).head(10)
            
            print(f"📈 TOP 10 CONFIGURAÇÕES (≥50 trades):")
            for idx, (config, results) in enumerate(top_configs.iterrows(), 1):
                analysis_days, holding_days, off_thresh, price_thresh = config
                print(f"\n   #{idx} Hit Rate: {results['hit_rate']:.1f}% | Retorno: {results['avg_return']:+.3f}%")
                print(f"       📊 Análise: {analysis_days}d | Holding: {holding_days}d")
                print(f"       📈 Off-exchange: ≥{off_thresh}% | Estabilidade: ≤{price_thresh}%")
                print(f"       🎯 Trades: {results['trade_count']} | Off-exchange médio: {results['avg_off_exchange']:.1f}%")
        
        # Análise por ticker
        print(f"\n🎯 ANÁLISE POR TICKER:")
        ticker_results = df.groupby('symbol').agg({
            'return_pct': ['count', 'mean', lambda x: (x > 0).mean() * 100],
            'avg_off_exchange_pct': 'mean'
        }).round(3)
        
        ticker_results.columns = ['trade_count', 'avg_return', 'hit_rate', 'avg_off_exchange']
        ticker_results = ticker_results.sort_values('hit_rate', ascending=False)
        
        print(f"📊 TOP 10 TICKERS por hit rate:")
        for ticker, results in ticker_results.head(10).iterrows():
            print(f"   {ticker}: {results['hit_rate']:.1f}% hit rate | {results['avg_return']:+.3f}% retorno | {results['trade_count']} trades")
        
        # Salva resultados
        self.save_mega_results(df, config_results, ticker_results)
    
    def save_mega_results(self, df, config_results, ticker_results):
        """Salva todos os resultados"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        
        # Todos os trades
        df.to_csv(f"mega_backtest_all_trades_{timestamp}.csv", index=False)
        
        # Resultados por configuração
        config_results.to_csv(f"mega_backtest_config_results_{timestamp}.csv")
        
        # Resultados por ticker
        ticker_results.to_csv(f"mega_backtest_ticker_results_{timestamp}.csv")
        
        print(f"\n💾 RESULTADOS SALVOS:")
        print(f"   📊 Todos os trades: mega_backtest_all_trades_{timestamp}.csv")
        print(f"   ⚙️  Por configuração: mega_backtest_config_results_{timestamp}.csv")
        print(f"   🎯 Por ticker: mega_backtest_ticker_results_{timestamp}.csv")

if __name__ == "__main__":
    backtester = MegaAccumulationBacktestReal()
    backtester.run_mega_backtest()