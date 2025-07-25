#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🕵️ DETECTOR DE ACUMULAÇÃO SILENCIOSA V2.0
Versão melhorada com parâmetros mais sensíveis e realistas
Identifica acumulação/distribuição institucional com maior precisão
"""

import pandas as pd
import requests
import yfinance as yf
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import json
import numpy as np
import warnings
from scipy import stats
from scipy.stats import pearsonr

warnings.filterwarnings('ignore')

class SilentAccumulationDetectorV2:
    """Detector de acumulação silenciosa - Versão melhorada"""
    
    def __init__(self):
        self.finra_url = "https://api.finra.org/data/group/OTCMarket/name/regShoDaily"
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # ===== PARÂMETROS MELHORADOS =====
        self.thresholds = {
            # Scores mais realistas
            'accumulation_score_low': 3.0,      # Era 6.0
            'accumulation_score_medium': 4.5,   # Era 7.0  
            'accumulation_score_high': 6.0,     # Era 8.0
            
            # Volume e correlação mais sensíveis
            'volume_trend_threshold': 1.1,      # Era 1.3
            'low_correlation_threshold': 0.5,   # Era 0.3
            'high_correlation_threshold': 0.8,  # Era 0.7
            
            # Dark pool mais realista
            'dark_pool_low': 15,                # Era 35
            'dark_pool_medium': 25,             # Era 40
            'dark_pool_high': 35,               # Era 50
            
            # Dias de atividade mais flexível
            'high_activity_days_low': 2,        # Era 5
            'high_activity_days_medium': 4,     # Era 7
            'high_activity_days_high': 6,       # Era 10
            
            # Volume efficiency mais sensível
            'volume_efficiency_low': 0.8,       # Era 0.5
            'volume_efficiency_medium': 1.2,    # Era 1.0
            'volume_efficiency_high': 1.8,      # Era 1.5
        }
    
    def get_finra_data(self, symbol, days=30):
        """Baixa dados do FINRA para o símbolo"""
        all_data = []
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        current_date = start_date
        while current_date <= end_date:
            if current_date.weekday() >= 5:
                current_date += timedelta(days=1)
                continue
                
            date_str = current_date.strftime('%Y-%m-%d')
            payload = {
                "compareFilters": [
                    {"compareType": "EQUAL", "fieldName": "symbol", "fieldValue": symbol.upper()},
                    {"compareType": "EQUAL", "fieldName": "tradeDate", "fieldValue": date_str}
                ],
                "limit": 1000
            }
            
            try:
                response = requests.post(self.finra_url, headers=self.headers, 
                                       data=json.dumps(payload), timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    if data:
                        all_data.extend(data)
            except:
                pass
            
            current_date += timedelta(days=1)
        
        if not all_data:
            return pd.DataFrame()
        
        df = pd.DataFrame(all_data)
        df['tradeDate'] = pd.to_datetime(df['tradeDate'])
        
        df_grouped = df.groupby('tradeDate').agg({
            'shortVolume': 'sum',
            'totalVolume': 'sum'
        }).reset_index()
        
        df_grouped['date'] = df_grouped['tradeDate'].dt.date
        return df_grouped
    
    def get_market_data(self, symbol, days=30):
        """Baixa dados de mercado do Yahoo Finance"""
        try:
            ticker = yf.Ticker(symbol)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days+10)
            
            hist = ticker.history(start=start_date, end=end_date)
            hist.reset_index(inplace=True)
            hist['date'] = hist['Date'].dt.date
            return hist
        except:
            return pd.DataFrame()
    
    def calculate_enhanced_accumulation_score(self, combined_data):
        """Calcula score de acumulação melhorado"""
        
        # Volume relativo mais sensível
        combined_data['volume_ma'] = combined_data['Volume'].rolling(window=10, min_periods=3).mean()
        combined_data['relative_volume'] = combined_data['Volume'] / combined_data['volume_ma']
        
        # Movimento de preço mais preciso
        combined_data['price_change'] = combined_data['Close'].pct_change()
        combined_data['price_move_abs'] = abs(combined_data['price_change']) * 100
        combined_data['price_volatility'] = combined_data['price_change'].rolling(5).std() * 100
        
        # Volume efficiency melhorado
        combined_data['volume_efficiency'] = np.where(
            combined_data['price_move_abs'] > 0,
            combined_data['relative_volume'] / combined_data['price_move_abs'],
            combined_data['relative_volume'] * 2  # Penaliza quando não há movimento
        )
        
        # Score de acumulação MELHORADO
        combined_data['accumulation_score'] = (
            # Volume alto = +2
            (combined_data['relative_volume'] >= 1.2).astype(int) * 2 +
            
            # Volume efficiency alta = +2  
            (combined_data['volume_efficiency'] >= self.thresholds['volume_efficiency_low']).astype(int) * 2 +
            
            # Dark pool ativo = +2
            (combined_data['dark_pool_volume'] >= combined_data['Volume'] * 0.15).astype(int) * 2 +
            
            # Movimento de preço baixo = +2
            (combined_data['price_move_abs'] <= 2.0).astype(int) * 2 +
            
            # Volatilidade baixa = +1
            (combined_data['price_volatility'] <= 2.0).astype(int) * 1 +
            
            # Shorts declinando = +1
            (combined_data['dark_pool_short'].pct_change() <= -0.05).astype(int) * 1
        )
        
        return combined_data
    
    def analyze_symbol(self, symbol, days=30):
        """Análise completa de um símbolo"""
        print(f"\n🔍 Analisando {symbol.upper()}...")
        
        # Dados
        finra_data = self.get_finra_data(symbol, days)
        market_data = self.get_market_data(symbol, days)
        
        if finra_data.empty or market_data.empty:
            print(f"❌ Dados insuficientes para {symbol}")
            return None
        
        # Combinar dados
        combined_data = pd.merge(market_data, finra_data, on='date', how='left')
        combined_data['dark_pool_volume'] = combined_data['totalVolume'].fillna(0)
        combined_data['dark_pool_short'] = combined_data['shortVolume'].fillna(0)
        
        if len(combined_data) < 10:
            print(f"❌ Dados insuficientes para análise de {symbol}")
            return None
        
        # Calcular score melhorado
        combined_data = self.calculate_enhanced_accumulation_score(combined_data)
        
        # Análise dos últimos 20 dias
        recent_data = combined_data.tail(20)
        
        # Métricas melhoradas
        signals = {
            'symbol': symbol.upper(),
            'analysis_date': datetime.now().strftime('%Y-%m-%d'),
            'accumulation_score': round(recent_data['accumulation_score'].mean(), 2),
            'max_accumulation_score': round(recent_data['accumulation_score'].max(), 2),
            'high_accumulation_days': (recent_data['accumulation_score'] >= 5).sum(),
            'volume_efficiency': round(recent_data['volume_efficiency'].mean(), 3),
            'volume_trend': round(recent_data['relative_volume'].rolling(5).mean().iloc[-1], 2),
            'dark_pool_ratio': round((recent_data['dark_pool_volume'].mean() / recent_data['Volume'].mean()) * 100, 1),
            'volume_price_correlation': round(pearsonr(recent_data['Volume'], recent_data['price_move_abs'])[0] if len(recent_data) > 5 else 0, 3),
            'short_trend_pct': round(recent_data['dark_pool_short'].pct_change().mean() * 100, 2),
            'current_price': round(recent_data['Close'].iloc[-1], 2),
            'price_change_20d': round(((recent_data['Close'].iloc[-1] / recent_data['Close'].iloc[0]) - 1) * 100, 2),
            'avg_daily_volume': round(recent_data['Volume'].mean(), 0),
            'price_volatility': round(recent_data['price_volatility'].mean(), 2)
        }
        
        # Interpretação melhorada
        interpretation = self.interpret_signals_v2(signals)
        
        # Resultados
        self.print_enhanced_results(signals, interpretation)
        
        return {
            'data': combined_data,
            'signals': signals,
            'interpretation': interpretation
        }
    
    def interpret_signals_v2(self, signals):
        """Interpretação melhorada dos sinais"""
        
        interpretation = {
            'overall_signal': 'NEUTRAL',
            'confidence': 'LOW',
            'action': 'HOLD',
            'reasons': [],
            'score_breakdown': {},
            'risk_level': 'MEDIUM'
        }
        
        score = signals['accumulation_score']
        max_score = signals['max_accumulation_score']
        high_days = signals['high_accumulation_days']
        vol_trend = signals['volume_trend']
        dark_ratio = signals['dark_pool_ratio']
        vol_efficiency = signals['volume_efficiency']
        vol_price_corr = signals['volume_price_correlation']
        
        accumulation_points = 0
        distribution_points = 0
        
        # ===== ANÁLISE DE ACUMULAÇÃO (MAIS SENSÍVEL) =====
        
        # 1. Score de acumulação
        if score >= self.thresholds['accumulation_score_high']:
            accumulation_points += 4
            interpretation['reasons'].append(f"✅ Score alto de acumulação ({score})")
        elif score >= self.thresholds['accumulation_score_medium']:
            accumulation_points += 3
            interpretation['reasons'].append(f"✅ Score médio de acumulação ({score})")
        elif score >= self.thresholds['accumulation_score_low']:
            accumulation_points += 2
            interpretation['reasons'].append(f"✅ Score baixo de acumulação ({score})")
        
        # 2. Dias com alta atividade
        if high_days >= self.thresholds['high_activity_days_high']:
            accumulation_points += 3
            interpretation['reasons'].append(f"✅ {high_days} dias com alta atividade silenciosa")
        elif high_days >= self.thresholds['high_activity_days_medium']:
            accumulation_points += 2
            interpretation['reasons'].append(f"✅ {high_days} dias com atividade moderada")
        elif high_days >= self.thresholds['high_activity_days_low']:
            accumulation_points += 1
            interpretation['reasons'].append(f"✅ {high_days} dias com alguma atividade")
        
        # 3. Volume efficiency
        if vol_efficiency >= self.thresholds['volume_efficiency_high']:
            accumulation_points += 3
            interpretation['reasons'].append(f"✅ Volume muito ineficiente ({vol_efficiency}) - excelente sinal")
        elif vol_efficiency >= self.thresholds['volume_efficiency_medium']:
            accumulation_points += 2
            interpretation['reasons'].append(f"✅ Volume ineficiente ({vol_efficiency}) - bom sinal")
        elif vol_efficiency >= self.thresholds['volume_efficiency_low']:
            accumulation_points += 1
            interpretation['reasons'].append(f"✅ Volume moderadamente ineficiente ({vol_efficiency})")
        
        # 4. Dark pool activity
        if dark_ratio >= self.thresholds['dark_pool_high']:
            accumulation_points += 3
            interpretation['reasons'].append(f"✅ Alto volume dark pool ({dark_ratio}%)")
        elif dark_ratio >= self.thresholds['dark_pool_medium']:
            accumulation_points += 2
            interpretation['reasons'].append(f"✅ Volume dark pool moderado ({dark_ratio}%)")
        elif dark_ratio >= self.thresholds['dark_pool_low']:
            accumulation_points += 1
            interpretation['reasons'].append(f"✅ Algum volume dark pool ({dark_ratio}%)")
        
        # 5. Volume-price correlation
        if abs(vol_price_corr) <= self.thresholds['low_correlation_threshold']:
            accumulation_points += 2
            interpretation['reasons'].append(f"✅ Baixa correlação volume-preço ({vol_price_corr})")
        
        # 6. Short trend
        if signals['short_trend_pct'] < -5:
            accumulation_points += 2
            interpretation['reasons'].append("✅ Shorts declinando significativamente")
        elif signals['short_trend_pct'] < 0:
            accumulation_points += 1
            interpretation['reasons'].append("✅ Shorts em declínio")
        
        # ===== ANÁLISE DE DISTRIBUIÇÃO =====
        
        # 1. Volume alto com correlação alta
        if vol_price_corr >= self.thresholds['high_correlation_threshold'] and vol_trend > 1.5:
            distribution_points += 3
            interpretation['reasons'].append(f"❌ Volume alto correlacionado com preço ({vol_price_corr})")
        
        # 2. Shorts aumentando
        if signals['short_trend_pct'] > 10:
            distribution_points += 2
            interpretation['reasons'].append("❌ Shorts aumentando significativamente")
        
        # 3. Volume eficiente demais
        if vol_efficiency < 0.5:
            distribution_points += 1
            interpretation['reasons'].append("❌ Volume muito eficiente (movendo preço)")
        
        # ===== DETERMINAR SINAL FINAL =====
        
        net_accumulation = accumulation_points - distribution_points
        
        if net_accumulation >= 8:
            interpretation['overall_signal'] = 'STRONG_ACCUMULATION'
            interpretation['action'] = 'STRONG_BUY'
            interpretation['confidence'] = 'HIGH'
            interpretation['risk_level'] = 'LOW'
        elif net_accumulation >= 6:
            interpretation['overall_signal'] = 'ACCUMULATION'
            interpretation['action'] = 'BUY'
            interpretation['confidence'] = 'MEDIUM'
            interpretation['risk_level'] = 'LOW'
        elif net_accumulation >= 3:
            interpretation['overall_signal'] = 'WEAK_ACCUMULATION'
            interpretation['action'] = 'WATCH'
            interpretation['confidence'] = 'MEDIUM'
            interpretation['risk_level'] = 'MEDIUM'
        elif net_accumulation <= -4:
            interpretation['overall_signal'] = 'DISTRIBUTION'
            interpretation['action'] = 'SELL'
            interpretation['confidence'] = 'MEDIUM'
            interpretation['risk_level'] = 'HIGH'
        elif net_accumulation <= -2:
            interpretation['overall_signal'] = 'WEAK_DISTRIBUTION'
            interpretation['action'] = 'REDUCE'
            interpretation['confidence'] = 'LOW'
            interpretation['risk_level'] = 'MEDIUM'
        
        interpretation['score_breakdown'] = {
            'accumulation_points': accumulation_points,
            'distribution_points': distribution_points,
            'net_score': net_accumulation
        }
        
        return interpretation
    
    def print_enhanced_results(self, signals, interpretation):
        """Imprime resultados melhorados"""
        
        symbol = signals['symbol']
        action = interpretation['action']
        confidence = interpretation['confidence']
        signal = interpretation['overall_signal']
        
        # Cores para output
        colors = {
            'STRONG_BUY': '🟢',
            'BUY': '🟢',
            'WATCH': '🟡', 
            'HOLD': '⚪',
            'REDUCE': '🟠',
            'SELL': '🔴'
        }
        
        color = colors.get(action, '⚪')
        
        print(f"\n{color} {symbol} - {signal}")
        print("=" * 50)
        print(f"🎯 AÇÃO RECOMENDADA: {action}")
        print(f"🎚️ CONFIANÇA: {confidence}")
        print(f"⚠️ RISCO: {interpretation['risk_level']}")
        print(f"📊 SCORE ACUMULAÇÃO: {signals['accumulation_score']}/10")
        print(f"📈 PREÇO: ${signals['current_price']} ({signals['price_change_20d']:+.1f}%)")
        print(f"📊 VOLUME TREND: {signals['volume_trend']}x")
        print(f"🌑 DARK POOL: {signals['dark_pool_ratio']}%")
        print(f"⚡ EFICIÊNCIA VOLUME: {signals['volume_efficiency']}")
        
        # Score breakdown
        breakdown = interpretation['score_breakdown']
        print(f"\n📊 BREAKDOWN DOS PONTOS:")
        print(f"   ✅ Acumulação: {breakdown['accumulation_points']} pontos")
        print(f"   ❌ Distribuição: {breakdown['distribution_points']} pontos")
        print(f"   🎯 SCORE FINAL: {breakdown['net_score']} pontos")
        
        print(f"\n💡 RAZÕES:")
        for reason in interpretation['reasons'][:5]:  # Top 5 razões
            print(f"   {reason}")
        
        print("-" * 50)
    
    def scan_multiple_symbols(self, symbols, days=30):
        """Escaneia múltiplos símbolos e ranqueia por potencial"""
        results = []
        
        print(f"🔍 INICIANDO SCAN DE {len(symbols)} SÍMBOLOS...")
        print(f"📅 PERÍODO: Últimos {days} dias")
        print("=" * 60)
        
        for symbol in symbols:
            try:
                result = self.analyze_symbol(symbol.strip().upper(), days)
                if result:
                    results.append(result)
            except Exception as e:
                print(f"❌ Erro ao analisar {symbol}: {str(e)}")
        
        # Ordenar por score de acumulação
        results.sort(key=lambda x: x['interpretation']['score_breakdown']['net_score'], reverse=True)
        
        # Summary
        print(f"\n🏆 RANKING FINAL - TOP OPORTUNIDADES")
        print("=" * 60)
        
        for i, result in enumerate(results[:10], 1):
            signals = result['signals']
            interp = result['interpretation']
            action = interp['action']
            net_score = interp['score_breakdown']['net_score']
            
            # Cores
            colors = {
                'STRONG_BUY': '🟢',
                'BUY': '🟢', 
                'WATCH': '🟡',
                'HOLD': '⚪',
                'REDUCE': '🟠',
                'SELL': '🔴'
            }
            
            color = colors.get(action, '⚪')
            
            print(f"{i:2d}. {color} {signals['symbol']} - {action}")
            print(f"    Score: {net_score:+d} | Acum: {signals['accumulation_score']} | Preço: {signals['price_change_20d']:+.1f}%")
        
        return results

def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='🕵️ Detector de Acumulação Silenciosa V2.0')
    parser.add_argument('--symbol', '-s', type=str, help='Símbolo da ação para analisar')
    parser.add_argument('--scan', type=str, help='Arquivo com lista de símbolos para escanear')
    parser.add_argument('--days', '-d', type=int, default=30, help='Número de dias para análise')
    
    args = parser.parse_args()
    
    detector = SilentAccumulationDetectorV2()
    
    if args.scan:
        # Scan múltiplos símbolos
        try:
            with open(args.scan, 'r') as f:
                symbols = [line.strip() for line in f if line.strip()]
            detector.scan_multiple_symbols(symbols, args.days)
        except FileNotFoundError:
            print(f"❌ Arquivo não encontrado: {args.scan}")
    elif args.symbol:
        # Análise de um símbolo
        detector.analyze_symbol(args.symbol, args.days)
    else:
        # Exemplo padrão
        print("📊 Exemplo: Analisando AMD...")
        detector.analyze_symbol('AMD', args.days)

if __name__ == "__main__":
    main()