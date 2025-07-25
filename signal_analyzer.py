#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📊 ANALISADOR DE SINAIS - BASEADO EM DADOS REAIS DO FINRA
Analisa os CSVs gerados para identificar sinais de compra/venda
"""

import pandas as pd
import glob
import os
from datetime import datetime

class SignalAnalyzer:
    def __init__(self):
        self.signals = []
        
    def analyze_stock(self, symbol, data):
        """Analisa uma ação específica para sinais"""
        if len(data) < 3:
            return None
            
        # Últimos 3 dias de dados
        recent = data.tail(3).copy()
        
        # Calcula métricas
        avg_off_exchange = recent['total_off_exchange_volume'].mean()
        total_volume = recent['total_market_volume'].mean()
        off_exchange_pct = (avg_off_exchange / total_volume * 100) if total_volume > 0 else 0
        
        # Variação de preço nos últimos 3 dias
        price_change = ((recent['Close'].iloc[-1] - recent['Close'].iloc[0]) / recent['Close'].iloc[0] * 100)
        
        # Volume médio vs volume recente
        volume_trend = recent['total_market_volume'].iloc[-1] / recent['total_market_volume'].mean()
        
        # Análise de padrões
        signal_strength = 0
        signal_type = "NEUTRO"
        reasons = []
        
        # 🔴 SINAIS DE VENDA (Distribuição)
        if off_exchange_pct > 35 and price_change < -2:
            signal_strength = 3
            signal_type = "🔴 VENDA FORTE"
            reasons.append(f"Alto off-exchange ({off_exchange_pct:.1f}%) + queda de preço ({price_change:.1f}%)")
            
        elif off_exchange_pct > 40:
            signal_strength = 2
            signal_type = "🟠 VENDA MODERADA"
            reasons.append(f"Off-exchange muito alto ({off_exchange_pct:.1f}%)")
            
        # 🟢 SINAIS DE COMPRA (Acumulação)
        elif off_exchange_pct > 25 and abs(price_change) < 2 and volume_trend > 1.2:
            signal_strength = 3
            signal_type = "🟢 COMPRA FORTE"
            reasons.append(f"Acumulação silenciosa: off-exchange alto ({off_exchange_pct:.1f}%), preço estável ({price_change:.1f}%), volume alto")
            
        elif off_exchange_pct > 30 and abs(price_change) < 1:
            signal_strength = 2
            signal_type = "🟡 COMPRA MODERADA"
            reasons.append(f"Off-exchange alto ({off_exchange_pct:.1f}%) com preço estável")
            
        # ⚠️ ATENÇÃO
        elif volume_trend > 2 and abs(price_change) > 5:
            signal_strength = 1
            signal_type = "⚠️ ATENÇÃO"
            reasons.append(f"Volume anômalo ({volume_trend:.1f}x) com movimento de preço significativo ({price_change:.1f}%)")
        
        return {
            'symbol': symbol,
            'signal_type': signal_type,
            'signal_strength': signal_strength,
            'off_exchange_pct': off_exchange_pct,
            'price_change_3d': price_change,
            'volume_trend': volume_trend,
            'current_price': recent['Close'].iloc[-1],
            'reasons': '; '.join(reasons) if reasons else 'Sem sinais claros',
            'avg_volume': int(total_volume)
        }
    
    def scan_all_stocks(self):
        """Escaneia todas as ações que temos dados"""
        csv_files = glob.glob("volume_analysis_*.csv")
        
        print("🔍 ANALISANDO SINAIS DE COMPRA/VENDA")
        print("=" * 60)
        
        for csv_file in csv_files:
            symbol = csv_file.replace("volume_analysis_", "").replace(".csv", "")
            
            try:
                data = pd.read_csv(csv_file)
                data['date'] = pd.to_datetime(data['date'])
                data = data.sort_values('date')
                
                signal = self.analyze_stock(symbol, data)
                if signal:
                    self.signals.append(signal)
                    
            except Exception as e:
                print(f"❌ Erro ao analisar {symbol}: {e}")
        
        # Ordena por força do sinal
        self.signals.sort(key=lambda x: x['signal_strength'], reverse=True)
        
        # Exibe resultados
        self.display_signals()
        
        # Salva em CSV
        self.save_signals()
    
    def display_signals(self):
        """Exibe os sinais encontrados"""
        print(f"\n📈 ENCONTRADOS {len(self.signals)} SINAIS")
        print("=" * 80)
        
        for signal in self.signals:
            if signal['signal_strength'] > 0:
                print(f"\n{signal['symbol']} - {signal['signal_type']}")
                print(f"   💰 Preço: ${signal['current_price']:.2f}")
                print(f"   📊 Off-Exchange: {signal['off_exchange_pct']:.1f}%")
                print(f"   📈 Variação 3D: {signal['price_change_3d']:+.1f}%")
                print(f"   📦 Volume Trend: {signal['volume_trend']:.1f}x")
                print(f"   🔍 Razão: {signal['reasons']}")
        
        # Resumo por tipo
        venda_forte = len([s for s in self.signals if "VENDA FORTE" in s['signal_type']])
        venda_mod = len([s for s in self.signals if "VENDA MODERADA" in s['signal_type']])
        compra_forte = len([s for s in self.signals if "COMPRA FORTE" in s['signal_type']])
        compra_mod = len([s for s in self.signals if "COMPRA MODERADA" in s['signal_type']])
        atencao = len([s for s in self.signals if "ATENÇÃO" in s['signal_type']])
        
        print(f"\n📊 RESUMO DOS SINAIS:")
        print(f"   🔴 Venda Forte: {venda_forte}")
        print(f"   🟠 Venda Moderada: {venda_mod}")
        print(f"   🟢 Compra Forte: {compra_forte}")
        print(f"   🟡 Compra Moderada: {compra_mod}")
        print(f"   ⚠️ Atenção: {atencao}")
    
    def save_signals(self):
        """Salva os sinais em CSV"""
        if self.signals:
            df = pd.DataFrame(self.signals)
            filename = f"trading_signals_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
            df.to_csv(filename, index=False)
            print(f"\n💾 Sinais salvos em: {filename}")

if __name__ == "__main__":
    analyzer = SignalAnalyzer()
    analyzer.scan_all_stocks()