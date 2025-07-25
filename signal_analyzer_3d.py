#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📊 ANALISADOR DE SINAIS - ÚLTIMOS 3 DIAS COMPLETOS (SEM HOJE)
Analisa apenas dias com dados completos do FINRA para detectar ciclos
"""

import pandas as pd
import glob
import os
from datetime import datetime

class SignalAnalyzer3D:
    def __init__(self):
        self.signals = []
        
    def analyze_stock(self, symbol, data):
        """Analisa uma ação específica para sinais"""
        # Filtra apenas dias com dados completos de FINRA (off_exchange > 0)
        complete_data = data[data['total_off_exchange_volume'] > 0].copy()
        
        if len(complete_data) < 3:
            return None
            
        # Últimos 3 dias COM DADOS COMPLETOS
        recent = complete_data.tail(3).copy()
        
        # Calcula métricas
        avg_off_exchange = recent['total_off_exchange_volume'].mean()
        total_volume = recent['total_market_volume'].mean()
        off_exchange_pct = (avg_off_exchange / total_volume * 100) if total_volume > 0 else 0
        
        # Variação de preço nos últimos 3 dias completos
        price_change = ((recent['Close'].iloc[-1] - recent['Close'].iloc[0]) / recent['Close'].iloc[0] * 100)
        
        # Tendência de volume off-exchange (crescendo ou diminuindo?)
        off_exchange_trend = (recent['total_off_exchange_volume'].iloc[-1] / recent['total_off_exchange_volume'].iloc[0] - 1) * 100
        
        # Tendência de volume total
        volume_trend = recent['total_market_volume'].iloc[-1] / recent['total_market_volume'].mean()
        
        # Volatilidade do off-exchange (consistência)
        off_exchange_std = recent['off_exchange_pct'].std()
        
        # Análise de padrões do CICLO
        signal_strength = 0
        signal_type = "NEUTRO"
        reasons = []
        cycle_status = "INDEFINIDO"
        
        # 🔴 DISTRIBUIÇÃO EM CURSO (Ciclo de venda)
        if off_exchange_pct > 35 and price_change < -1.5:
            if off_exchange_trend > 0:
                signal_strength = 4
                signal_type = "🔴 DISTRIBUIÇÃO ACELERANDO"
                cycle_status = "VENDAS INTENSIFICANDO"
                reasons.append(f"Off-exchange alto ({off_exchange_pct:.1f}%) + crescendo ({off_exchange_trend:+.1f}%) + preço caindo ({price_change:.1f}%)")
            else:
                signal_strength = 3
                signal_type = "🔴 DISTRIBUIÇÃO DESACELERANDO"
                cycle_status = "VENDAS DIMINUINDO"
                reasons.append(f"Off-exchange alto ({off_exchange_pct:.1f}%) mas diminuindo ({off_exchange_trend:+.1f}%) + preço caindo ({price_change:.1f}%)")
                
        elif off_exchange_pct > 40:
            signal_strength = 2
            signal_type = "🟠 DISTRIBUIÇÃO MASSIVA"
            cycle_status = "VENDAS INSTITUCIONAIS"
            reasons.append(f"Off-exchange muito alto ({off_exchange_pct:.1f}%)")
            
        # 🟢 ACUMULAÇÃO (Ciclo de compra)
        elif off_exchange_pct > 25 and abs(price_change) < 2 and volume_trend > 1.1:
            if off_exchange_trend > 5:
                signal_strength = 4
                signal_type = "🟢 ACUMULAÇÃO CRESCENDO"
                cycle_status = "COMPRAS INTENSIFICANDO"
                reasons.append(f"Off-exchange crescendo ({off_exchange_trend:+.1f}%) + preço estável ({price_change:.1f}%) + volume alto")
            else:
                signal_strength = 3
                signal_type = "🟡 ACUMULAÇÃO ESTÁVEL"
                cycle_status = "COMPRAS CONSTANTES"
                reasons.append(f"Off-exchange alto ({off_exchange_pct:.1f}%) + preço estável ({price_change:.1f}%)")
        
        # 📊 TRANSIÇÃO DE CICLO
        elif abs(off_exchange_trend) > 15:
            signal_strength = 2
            signal_type = "⚠️ MUDANÇA DE CICLO"
            if off_exchange_trend > 0:
                cycle_status = "ENTRANDO EM DISTRIBUIÇÃO"
            else:
                cycle_status = "SAINDO DE DISTRIBUIÇÃO"
            reasons.append(f"Mudança brusca no off-exchange: {off_exchange_trend:+.1f}%")
        
        # Datas do período analisado
        period_start = recent['date'].iloc[0].strftime('%d/%m')
        period_end = recent['date'].iloc[-1].strftime('%d/%m')
        
        return {
            'symbol': symbol,
            'signal_type': signal_type,
            'signal_strength': signal_strength,
            'cycle_status': cycle_status,
            'off_exchange_pct': off_exchange_pct,
            'off_exchange_trend': off_exchange_trend,
            'price_change_3d': price_change,
            'volume_trend': volume_trend,
            'current_price': recent['Close'].iloc[-1],
            'period': f"{period_start} - {period_end}",
            'reasons': '; '.join(reasons) if reasons else 'Sem sinais claros',
            'avg_volume': int(total_volume),
            'volatility': off_exchange_std
        }
    
    def scan_all_stocks(self):
        """Escaneia todas as ações que temos dados"""
        csv_files = glob.glob("volume_analysis_*_current.csv")
        
        print("🔍 ANALISANDO CICLO DOS ÚLTIMOS 3 DIAS COMPLETOS")
        print("📅 (Excluindo hoje - apenas dados completos do FINRA)")
        print("=" * 70)
        
        for csv_file in csv_files:
            symbol = csv_file.replace("volume_analysis_", "").replace("_current.csv", "").upper()
            
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
        print(f"\n📈 ANÁLISE DE {len(self.signals)} AÇÕES")
        print("=" * 80)
        
        # Agrupa por tipo de ciclo
        acelerando = [s for s in self.signals if "ACELERANDO" in s['signal_type']]
        desacelerando = [s for s in self.signals if "DESACELERANDO" in s['signal_type']]
        crescendo = [s for s in self.signals if "CRESCENDO" in s['signal_type']]
        
        if acelerando:
            print("\n🔥 DISTRIBUIÇÃO ACELERANDO (VENDA URGENTE):")
            for signal in acelerando:
                print(f"   {signal['symbol']} | {signal['period']} | ${signal['current_price']:.2f} | Off-Ex: {signal['off_exchange_pct']:.1f}% ({signal['off_exchange_trend']:+.1f}%)")
        
        if desacelerando:
            print("\n📉 DISTRIBUIÇÃO DESACELERANDO (CICLO TERMINANDO):")
            for signal in desacelerando:
                print(f"   {signal['symbol']} | {signal['period']} | ${signal['current_price']:.2f} | Off-Ex: {signal['off_exchange_pct']:.1f}% ({signal['off_exchange_trend']:+.1f}%)")
        
        if crescendo:
            print("\n📈 ACUMULAÇÃO CRESCENDO (COMPRA):")
            for signal in crescendo:
                print(f"   {signal['symbol']} | {signal['period']} | ${signal['current_price']:.2f} | Off-Ex: {signal['off_exchange_pct']:.1f}% ({signal['off_exchange_trend']:+.1f}%)")
        
        print(f"\n📊 DETALHES COMPLETOS:")
        for signal in self.signals[:10]:  # Top 10
            print(f"\n{signal['symbol']} - {signal['signal_type']}")
            print(f"   📅 Período: {signal['period']}")
            print(f"   💰 Preço: ${signal['current_price']:.2f}")
            print(f"   📊 Off-Exchange: {signal['off_exchange_pct']:.1f}% (tendência: {signal['off_exchange_trend']:+.1f}%)")
            print(f"   📈 Variação Preço: {signal['price_change_3d']:+.1f}%")
            print(f"   🔄 Status do Ciclo: {signal['cycle_status']}")
            print(f"   🔍 Razão: {signal['reasons']}")
    
    def save_signals(self):
        """Salva os sinais em CSV"""
        if self.signals:
            df = pd.DataFrame(self.signals)
            filename = f"cycle_analysis_3d_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
            df.to_csv(filename, index=False)
            print(f"\n💾 Análise de ciclo salva em: {filename}")

if __name__ == "__main__":
    analyzer = SignalAnalyzer3D()
    analyzer.scan_all_stocks()