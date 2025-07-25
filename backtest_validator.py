#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔬 VALIDADOR ESTATÍSTICO - TESTA SE NOSSAS INTERPRETAÇÕES FUNCIONAM
Executa backtest automático com ciclos semanais
"""

import pandas as pd
import numpy as np
import glob
from datetime import datetime

class BacktestValidator:
    def __init__(self):
        self.all_results = {}
        
    def calculate_signal(self, data, end_idx):
        """Calcula sinal usando nosso algoritmo atual"""
        if end_idx < 3:
            return None
            
        recent = data.iloc[end_idx-3:end_idx].copy()
        recent = recent[recent['total_off_exchange_volume'] > 0]
        
        if len(recent) < 2:
            return None
            
        # Métricas
        avg_off_exchange = recent['total_off_exchange_volume'].mean()
        total_volume = recent['total_market_volume'].mean()
        off_exchange_pct = (avg_off_exchange / total_volume * 100) if total_volume > 0 else 0
        
        price_change = ((recent['Close'].iloc[-1] - recent['Close'].iloc[0]) / recent['Close'].iloc[0] * 100)
        
        if len(recent) >= 2:
            off_exchange_trend = (recent['total_off_exchange_volume'].iloc[-1] / recent['total_off_exchange_volume'].iloc[0] - 1) * 100
        else:
            off_exchange_trend = 0
            
        volume_trend = recent['total_market_volume'].iloc[-1] / recent['total_market_volume'].mean()
        
        # Lógica de sinal
        if off_exchange_pct > 35 and price_change < -1.5:
            return "SELL" if off_exchange_trend > 0 else "SELL_WEAK"
        elif off_exchange_pct > 40:
            return "SELL_MODERATE"
        elif off_exchange_pct > 25 and abs(price_change) < 2 and volume_trend > 1.1:
            return "BUY" if off_exchange_trend > 5 else "BUY_MODERATE"
        
        return "HOLD"
    
    def test_holding_period(self, holding_days=5):
        """Testa um período específico de holding"""
        csv_files = glob.glob("volume_analysis_*_current.csv")
        results = []
        
        print(f"🧪 Testando {holding_days} dias de holding...")
        
        for csv_file in csv_files:
            symbol = csv_file.replace("volume_analysis_", "").replace("_current.csv", "").upper()
            
            try:
                data = pd.read_csv(csv_file)
                data['date'] = pd.to_datetime(data['date'])
                data = data.sort_values('date').reset_index(drop=True)
                
                # Para cada possível ponto de entrada
                for i in range(10, len(data) - holding_days):
                    signal = self.calculate_signal(data, i)
                    
                    if signal in ['HOLD']:
                        continue
                        
                    entry_price = data.iloc[i-1]['Close']
                    exit_price = data.iloc[i + holding_days]['Close']
                    entry_date = data.iloc[i-1]['date']
                    
                    # Calcula retorno baseado no sinal
                    if signal.startswith('BUY'):
                        return_pct = ((exit_price - entry_price) / entry_price * 100)
                        expected_up = True
                    else:  # SELL
                        return_pct = -((exit_price - entry_price) / entry_price * 100)
                        expected_up = False
                    
                    actual_up = exit_price > entry_price
                    correct = (expected_up == actual_up)
                    
                    results.append({
                        'symbol': symbol,
                        'signal': signal,
                        'return_pct': return_pct,
                        'correct': correct,
                        'entry_date': entry_date,
                        'holding_days': holding_days
                    })
                    
            except Exception as e:
                print(f"❌ Erro em {symbol}: {e}")
        
        return results
    
    def run_validation(self):
        """Executa validação completa"""
        print("🔬 INICIANDO VALIDAÇÃO ESTATÍSTICA")
        print("=" * 50)
        
        # Testa diferentes períodos
        for holding_days in [3, 5, 7]:
            results = self.test_holding_period(holding_days)
            self.all_results[holding_days] = results
            
            if results:
                df = pd.DataFrame(results)
                
                # Estatísticas básicas
                total_trades = len(df)
                correct_trades = df['correct'].sum()
                hit_rate = (correct_trades / total_trades * 100) if total_trades > 0 else 0
                avg_return = df['return_pct'].mean()
                
                print(f"\n📊 RESULTADOS - {holding_days} DIAS:")
                print(f"   Trades: {total_trades}")
                print(f"   Hit Rate: {hit_rate:.1f}%")
                print(f"   Retorno Médio: {avg_return:+.2f}%")
                
                # Por tipo de sinal
                signal_performance = df.groupby('signal').agg({
                    'return_pct': ['count', 'mean'],
                    'correct': 'sum'
                }).round(2)
                
                signal_performance.columns = ['trades', 'avg_return', 'hits']
                signal_performance['hit_rate'] = (signal_performance['hits'] / signal_performance['trades'] * 100).round(1)
                
                print(f"\n   📈 Por Tipo de Sinal:")
                for signal_type in signal_performance.index:
                    stats = signal_performance.loc[signal_type]
                    print(f"      {signal_type}: {stats['hit_rate']:.1f}% hit rate, {stats['avg_return']:+.2f}% retorno ({stats['trades']} trades)")
        
        # Análise consolidada
        self.consolidated_analysis()
    
    def consolidated_analysis(self):
        """Análise consolidada de todos os períodos"""
        print(f"\n🎯 ANÁLISE CONSOLIDADA")
        print("=" * 50)
        
        best_hit_rate = 0
        best_period = 0
        best_return = -999
        
        for period, results in self.all_results.items():
            if results:
                df = pd.DataFrame(results)
                hit_rate = (df['correct'].sum() / len(df) * 100)
                avg_return = df['return_pct'].mean()
                
                if hit_rate > best_hit_rate:
                    best_hit_rate = hit_rate
                    best_period = period
                    
                if avg_return > best_return:
                    best_return = avg_return
        
        print(f"🏆 Melhor Hit Rate: {best_hit_rate:.1f}% ({best_period} dias)")
        print(f"💰 Melhor Retorno: {best_return:+.2f}%")
        
        # Validação final
        if best_hit_rate > 55:
            print(f"\n✅ SISTEMA ESTATISTICAMENTE VÁLIDO!")
            print(f"   Hit rate > 55% indica que nossas interpretações funcionam")
        elif best_hit_rate > 50:
            print(f"\n⚠️ SISTEMA MARGINALMENTE VÁLIDO")
            print(f"   Pode funcionar mas precisa refinamento")
        else:
            print(f"\n❌ SISTEMA PRECISA SER REPENSADO")
            print(f"   Hit rate muito baixo, algoritmo não está funcionando")
        
        # Salva resultados
        self.save_detailed_results()
    
    def save_detailed_results(self):
        """Salva resultados detalhados"""
        all_data = []
        for period, results in self.all_results.items():
            all_data.extend(results)
        
        if all_data:
            df = pd.DataFrame(all_data)
            filename = f"validation_results_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
            df.to_csv(filename, index=False)
            print(f"\n💾 Resultados detalhados salvos em: {filename}")

if __name__ == "__main__":
    validator = BacktestValidator()
    validator.run_validation()