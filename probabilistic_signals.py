#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎲 SISTEMA PROBABILÍSTICO DE SINAIS
Baseado na validação histórica - mostra probabilidade real de cada recomendação
"""

import pandas as pd
import glob
from datetime import datetime

class ProbabilisticSignals:
    def __init__(self):
        # Probabilidades baseadas no backtest (55.9% geral)
        self.signal_probabilities = {
            'SELL': {
                'success_rate': 80.0,  # 4/5 trades corretos
                'avg_return': 2.37,
                'confidence': 'ALTA',
                'sample_size': 5,
                'description': 'Distribuição acelerando'
            },
            'BUY': {
                'success_rate': 66.7,  # 2/3 trades corretos  
                'avg_return': 0.52,
                'confidence': 'MÉDIA-ALTA',
                'sample_size': 3,
                'description': 'Acumulação crescendo'
            },
            'SELL_MODERATE': {
                'success_rate': 52.9,  # 9/17 trades corretos
                'avg_return': 2.37,
                'confidence': 'MÉDIA',
                'sample_size': 17,
                'description': 'Distribuição massiva'
            },
            'SELL_WEAK': {
                'success_rate': 44.4,  # 4/9 trades corretos
                'avg_return': -0.73,
                'confidence': 'BAIXA',
                'sample_size': 9,
                'description': 'Distribuição desacelerando'
            }
        }
        
        self.signals = []
    
    def calculate_signal_with_probability(self, symbol, data):
        """Calcula sinal incluindo probabilidade de sucesso"""
        # Filtra apenas dias com dados completos
        complete_data = data[data['total_off_exchange_volume'] > 0].copy()
        
        if len(complete_data) < 3:
            return None
            
        # Últimos 3 dias completos
        recent = complete_data.tail(3).copy()
        
        # Métricas básicas
        avg_off_exchange = recent['total_off_exchange_volume'].mean()
        total_volume = recent['total_market_volume'].mean()
        off_exchange_pct = (avg_off_exchange / total_volume * 100) if total_volume > 0 else 0
        
        price_change = ((recent['Close'].iloc[-1] - recent['Close'].iloc[0]) / recent['Close'].iloc[0] * 100)
        off_exchange_trend = (recent['total_off_exchange_volume'].iloc[-1] / recent['total_off_exchange_volume'].iloc[0] - 1) * 100
        volume_trend = recent['total_market_volume'].iloc[-1] / recent['total_market_volume'].mean()
        
        # Determina sinal usando mesma lógica validada
        signal_type = "HOLD"
        
        if off_exchange_pct > 35 and price_change < -1.5:
            signal_type = "SELL" if off_exchange_trend > 0 else "SELL_WEAK"
        elif off_exchange_pct > 40:
            signal_type = "SELL_MODERATE"
        elif off_exchange_pct > 25 and abs(price_change) < 2 and volume_trend > 1.1:
            signal_type = "BUY" if off_exchange_trend > 5 else "BUY_MODERATE"
        
        if signal_type == "HOLD" or signal_type == "BUY_MODERATE":
            return None
            
        # Busca probabilidades
        prob_data = self.signal_probabilities.get(signal_type, {})
        
        return {
            'symbol': symbol,
            'signal_type': signal_type,
            'probability': prob_data.get('success_rate', 0),
            'confidence': prob_data.get('confidence', 'DESCONHECIDA'),
            'expected_return': prob_data.get('avg_return', 0),
            'sample_size': prob_data.get('sample_size', 0),
            'description': prob_data.get('description', ''),
            'current_price': recent['Close'].iloc[-1],
            'off_exchange_pct': off_exchange_pct,
            'off_exchange_trend': off_exchange_trend,
            'price_change_3d': price_change,
            'period': f"{recent['date'].iloc[0].strftime('%d/%m')} - {recent['date'].iloc[-1].strftime('%d/%m')}"
        }
    
    def scan_with_probabilities(self):
        """Escaneia todas as ações com probabilidades"""
        csv_files = glob.glob("volume_analysis_*_current.csv")
        
        print("🎲 SISTEMA PROBABILÍSTICO DE SINAIS")
        print("📊 Baseado em validação histórica de 34 trades")
        print("=" * 70)
        
        for csv_file in csv_files:
            symbol = csv_file.replace("volume_analysis_", "").replace("_current.csv", "").upper()
            
            try:
                data = pd.read_csv(csv_file)
                data['date'] = pd.to_datetime(data['date'])
                data = data.sort_values('date')
                
                signal = self.calculate_signal_with_probability(symbol, data)
                if signal:
                    self.signals.append(signal)
                    
            except Exception as e:
                print(f"❌ Erro ao analisar {symbol}: {e}")
        
        # Ordena por probabilidade de sucesso
        self.signals.sort(key=lambda x: x['probability'], reverse=True)
        
        # Exibe resultados
        self.display_probabilistic_signals()
        
        # Salva resultados
        self.save_probabilistic_results()
    
    def display_probabilistic_signals(self):
        """Exibe sinais com probabilidades"""
        print(f"\n🎯 SINAIS ENCONTRADOS: {len(self.signals)}")
        print("=" * 80)
        
        # Agrupa por nível de confiança
        high_prob = [s for s in self.signals if s['probability'] >= 70]
        medium_prob = [s for s in self.signals if 50 <= s['probability'] < 70]
        low_prob = [s for s in self.signals if s['probability'] < 50]
        
        if high_prob:
            print("\n🔥 ALTA PROBABILIDADE (≥70% chance de sucesso):")
            for signal in high_prob:
                direction = "📉 VENDA" if signal['signal_type'].startswith('SELL') else "📈 COMPRA"
                print(f"   {signal['symbol']} | {direction} | {signal['probability']:.1f}% chance | ${signal['current_price']:.2f}")
                print(f"      💡 {signal['description']} | Retorno esperado: {signal['expected_return']:+.2f}%")
                print(f"      📊 Off-exchange: {signal['off_exchange_pct']:.1f}% | Período: {signal['period']}")
        
        if medium_prob:
            print("\n⚠️ PROBABILIDADE MÉDIA (50-69% chance):")
            for signal in medium_prob:
                direction = "📉 VENDA" if signal['signal_type'].startswith('SELL') else "📈 COMPRA"
                print(f"   {signal['symbol']} | {direction} | {signal['probability']:.1f}% chance | ${signal['current_price']:.2f}")
                print(f"      💡 {signal['description']} | Retorno esperado: {signal['expected_return']:+.2f}%")
        
        if low_prob:
            print("\n🤔 BAIXA PROBABILIDADE (<50% chance - EVITAR):")
            for signal in low_prob:
                direction = "📉 VENDA" if signal['signal_type'].startswith('SELL') else "📈 COMPRA"
                print(f"   {signal['symbol']} | {direction} | {signal['probability']:.1f}% chance | ${signal['current_price']:.2f}")
        
        # Resumo estatístico
        print(f"\n📈 RESUMO ESTATÍSTICO:")
        print(f"   🔥 Sinais de Alta Confiança: {len(high_prob)}")
        print(f"   ⚠️ Sinais de Média Confiança: {len(medium_prob)}")
        print(f"   🤔 Sinais de Baixa Confiança: {len(low_prob)}")
        
        if high_prob:
            avg_prob = sum(s['probability'] for s in high_prob) / len(high_prob)
            print(f"   🎯 Probabilidade média dos melhores sinais: {avg_prob:.1f}%")
    
    def save_probabilistic_results(self):
        """Salva resultados com probabilidades"""
        if self.signals:
            df = pd.DataFrame(self.signals)
            filename = f"probabilistic_signals_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
            df.to_csv(filename, index=False)
            print(f"\n💾 Sinais probabilísticos salvos em: {filename}")
    
    def get_recommendation_summary(self):
        """Resumo de recomendações claras"""
        high_prob = [s for s in self.signals if s['probability'] >= 70]
        
        print(f"\n🎯 RECOMENDAÇÕES DE ALTA PROBABILIDADE:")
        print("=" * 50)
        
        sells = [s for s in high_prob if s['signal_type'].startswith('SELL')]
        buys = [s for s in high_prob if s['signal_type'].startswith('BUY')]
        
        if sells:
            print(f"\n📉 VENDAS RECOMENDADAS (80% de chance de dar certo):")
            for signal in sells:
                print(f"   • {signal['symbol']} - {signal['probability']:.0f}% chance de queda")
        
        if buys:
            print(f"\n📈 COMPRAS RECOMENDADAS (67% de chance de dar certo):")
            for signal in buys:
                print(f"   • {signal['symbol']} - {signal['probability']:.0f}% chance de subida")
        
        if not high_prob:
            print("   Nenhum sinal de alta probabilidade no momento.")

if __name__ == "__main__":
    prob_system = ProbabilisticSignals()
    prob_system.scan_with_probabilities()
    prob_system.get_recommendation_summary()