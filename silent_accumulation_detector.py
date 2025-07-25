#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🕵️ DETECTOR DE ACUMULAÇÃO SILENCIOSA
Identifica ações com volume institucional "silencioso" que podem indicar 
acumulação ou distribuição antes de grandes movimentos de preço.
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

class SilentAccumulationDetector:
    """Detecta acumulação/distribuição silenciosa em ações"""
    
    def __init__(self):
        self.finra_url = "https://api.finra.org/data/group/OTCMarket/name/regShoDaily"
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def get_stock_data(self, symbol, days=60):
        """Baixa dados de preço e volume da ação"""
        print(f"📊 Baixando dados de mercado para {symbol}...")
        
        try:
            ticker = yf.Ticker(symbol)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days + 10)
            
            hist = ticker.history(start=start_date, end=end_date, interval='1d')
            
            if hist.empty:
                return pd.DataFrame()
            
            df = hist.reset_index()
            df['date'] = pd.to_datetime(df['Date']).dt.date
            df['date'] = pd.to_datetime(df['date'])
            
            # Calcular métricas técnicas
            df['price_change'] = df['Close'].pct_change() * 100
            df['volume_ma_20'] = df['Volume'].rolling(20).mean()
            df['price_ma_20'] = df['Close'].rolling(20).mean()
            df['volume_ratio'] = df['Volume'] / df['volume_ma_20']
            df['atr'] = self.calculate_atr(df, 14)
            df['relative_volume'] = df['Volume'] / df['Volume'].rolling(10).mean()
            
            print(f"✓ {len(df)} dias de dados de mercado obtidos")
            return df
            
        except Exception as e:
            print(f"❌ Erro ao buscar dados: {str(e)}")
            return pd.DataFrame()
    
    def calculate_atr(self, df, period=14):
        """Calcula Average True Range para medir volatilidade"""
        high_low = df['High'] - df['Low']
        high_close_prev = np.abs(df['High'] - df['Close'].shift())
        low_close_prev = np.abs(df['Low'] - df['Close'].shift())
        
        true_range = np.maximum(high_low, np.maximum(high_close_prev, low_close_prev))
        return true_range.rolling(period).mean()
    
    def get_dark_pool_data(self, symbol, days=60):
        """Baixa dados de dark pools (volume off-exchange)"""
        print(f"🕵️ Buscando dados de dark pools para {symbol}...")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        all_data = []
        
        for i in range(days):
            current_date = start_date + timedelta(days=i)
            if current_date.weekday() >= 5:
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
                time.sleep(0.3)
            except:
                continue
        
        if not all_data:
            return pd.DataFrame()
        
        df = pd.DataFrame(all_data)
        df['tradeDate'] = pd.to_datetime(df['tradeDate'])
        
        # Agrupar por data
        df_grouped = df.groupby('tradeDate').agg({
            'shortVolume': 'sum',
            'totalVolume': 'sum'
        }).reset_index()
        
        df_grouped['date'] = df_grouped['tradeDate'].dt.date
        df_grouped['date'] = pd.to_datetime(df_grouped['date'])
        df_grouped['dark_pool_volume'] = df_grouped['totalVolume']
        df_grouped['dark_pool_short'] = df_grouped['shortVolume']
        
        print(f"✓ {len(df_grouped)} dias de dados de dark pools obtidos")
        return df_grouped
    
    def detect_silent_accumulation(self, symbol, days=60):
        """
        🎯 ALGORITMO PRINCIPAL: Detecta acumulação silenciosa
        
        SINAIS DE ACUMULAÇÃO SILENCIOSA:
        1. Alto volume off-exchange vs baixo movimento de preço
        2. Volume acima da média mas preço estável
        3. Redução de vendas a descoberto em dark pools
        4. Correlação negativa entre volume e volatilidade
        """
        print(f"\n🕵️ DETECTANDO ACUMULAÇÃO SILENCIOSA EM {symbol.upper()}")
        print("=" * 60)
        
        # Baixar dados
        market_data = self.get_stock_data(symbol, days)
        dark_pool_data = self.get_dark_pool_data(symbol, days)
        
        if market_data.empty:
            print("❌ Sem dados de mercado suficientes")
            return None
        
        # Merge dos dados
        if not dark_pool_data.empty:
            combined_data = pd.merge(market_data, dark_pool_data, on='date', how='left')
            combined_data['dark_pool_volume'].fillna(0, inplace=True)
            combined_data['dark_pool_short'].fillna(0, inplace=True)
        else:
            combined_data = market_data.copy()
            combined_data['dark_pool_volume'] = 0
            combined_data['dark_pool_short'] = 0
        
        # ===== CÁLCULOS DE ACUMULAÇÃO SILENCIOSA =====
        
        # 1. Volume Efficiency Index (VEI)
        # Mede quanto movimento de preço é gerado por unidade de volume
        combined_data['price_move_abs'] = np.abs(combined_data['price_change'])
        combined_data['volume_efficiency'] = combined_data['price_move_abs'] / (combined_data['relative_volume'] + 0.1)
        combined_data['vei_ma'] = combined_data['volume_efficiency'].rolling(10).mean()
        
        # 2. Silent Accumulation Score (SAS)
        # Alto volume + baixo movimento de preço = possível acumulação
        combined_data['volume_score'] = (combined_data['relative_volume'] > 1.2).astype(int) * 2
        combined_data['low_volatility_score'] = (combined_data['volume_efficiency'] < combined_data['vei_ma']).astype(int) * 2
        combined_data['dark_pool_score'] = np.where(combined_data['dark_pool_volume'] > 0, 
                                                   (combined_data['dark_pool_volume'] / combined_data['Volume'] > 0.3).astype(int) * 3, 0)
        
        # 3. Accumulation Score (0-10)
        combined_data['accumulation_score'] = (
            combined_data['volume_score'] + 
            combined_data['low_volatility_score'] + 
            combined_data['dark_pool_score'] +
            (combined_data['relative_volume'] > 1.5).astype(int) * 2 +
            (combined_data['price_move_abs'] < 1.0).astype(int) * 1
        )
        
        # 4. Trend Analysis
        recent_data = combined_data.tail(20)
        
        # Correlações importantes
        volume_price_corr = pearsonr(recent_data['Volume'], recent_data['price_move_abs'])[0] if len(recent_data) > 5 else 0
        dark_pool_price_corr = pearsonr(recent_data['dark_pool_volume'], recent_data['price_move_abs'])[0] if len(recent_data) > 5 and recent_data['dark_pool_volume'].sum() > 0 else 0
        
        # 5. Análise de padrões
        avg_accumulation_score = recent_data['accumulation_score'].mean()
        high_accumulation_days = (recent_data['accumulation_score'] >= 7).sum()
        volume_trend = recent_data['relative_volume'].rolling(5).mean().iloc[-1] if len(recent_data) > 5 else 1
        
        # 6. Dark Pool Analysis
        if recent_data['dark_pool_volume'].sum() > 0:
            dark_pool_ratio = recent_data['dark_pool_volume'].mean() / recent_data['Volume'].mean()
            short_ratio_trend = recent_data['dark_pool_short'].rolling(5).mean().pct_change().iloc[-1] if len(recent_data) > 5 else 0
        else:
            dark_pool_ratio = 0
            short_ratio_trend = 0
        
        # ===== SINAIS DE ACUMULAÇÃO =====
        signals = {
            'symbol': symbol.upper(),
            'analysis_date': datetime.now().strftime('%Y-%m-%d'),
            'accumulation_score': round(avg_accumulation_score, 2),
            'high_accumulation_days': high_accumulation_days,
            'volume_efficiency': round(recent_data['volume_efficiency'].mean(), 3),
            'volume_trend': round(volume_trend, 2),
            'dark_pool_ratio': round(dark_pool_ratio * 100, 1),
            'volume_price_correlation': round(volume_price_corr, 3),
            'dark_pool_price_correlation': round(dark_pool_price_corr, 3),
            'short_trend': 'Declining' if short_ratio_trend < -0.05 else 'Stable' if abs(short_ratio_trend) <= 0.05 else 'Increasing',
            'current_price': round(recent_data['Close'].iloc[-1], 2),
            'price_change_20d': round(((recent_data['Close'].iloc[-1] / recent_data['Close'].iloc[0]) - 1) * 100, 2)
        }
        
        # ===== INTERPRETAÇÃO =====
        interpretation = self.interpret_signals(signals)
        
        # ===== RESULTADOS =====
        self.print_analysis_results(signals, interpretation)
        self.create_accumulation_charts(combined_data, symbol, signals)
        
        return {
            'data': combined_data,
            'signals': signals,
            'interpretation': interpretation
        }
    
    def interpret_signals(self, signals):
        """Interpreta os sinais e fornece recomendações"""
        
        interpretation = {
            'overall_signal': 'NEUTRAL',
            'confidence': 'LOW',
            'action': 'HOLD',
            'reasons': [],
            'risk_level': 'MEDIUM'
        }
        
        score = signals['accumulation_score']
        high_days = signals['high_accumulation_days']
        vol_trend = signals['volume_trend']
        dark_ratio = signals['dark_pool_ratio']
        
        # Lógica de interpretação
        accumulation_indicators = 0
        distribution_indicators = 0
        
        # Sinais de ACUMULAÇÃO
        if score >= 6:
            accumulation_indicators += 2
            interpretation['reasons'].append(f"Alto score de acumulação ({score})")
        
        if high_days >= 5:
            accumulation_indicators += 2
            interpretation['reasons'].append(f"{high_days} dias com alta atividade silenciosa")
        
        if vol_trend > 1.3 and abs(signals['volume_price_correlation']) < 0.3:
            accumulation_indicators += 2
            interpretation['reasons'].append("Volume alto com baixa correlação de preço")
        
        if dark_ratio > 35 and signals['short_trend'] == 'Declining':
            accumulation_indicators += 3
            interpretation['reasons'].append("Alto volume dark pool com shorts declinando")
        
        if signals['volume_efficiency'] < 0.5:
            accumulation_indicators += 1
            interpretation['reasons'].append("Volume ineficiente (preço não acompanha volume)")
        
        # Sinais de DISTRIBUIÇÃO
        if score <= 3 and vol_trend > 1.5:
            distribution_indicators += 2
            interpretation['reasons'].append("Volume alto mas sem acumulação")
        
        if signals['short_trend'] == 'Increasing' and dark_ratio > 30:
            distribution_indicators += 2
            interpretation['reasons'].append("Aumento de vendas a descoberto em dark pools")
        
        if signals['volume_price_correlation'] > 0.7:
            distribution_indicators += 1
            interpretation['reasons'].append("Volume altamente correlacionado com movimento de preço")
        
        # Determinar sinal final
        if accumulation_indicators >= 5:
            interpretation['overall_signal'] = 'STRONG_ACCUMULATION'
            interpretation['action'] = 'BUY'
            interpretation['confidence'] = 'HIGH' if accumulation_indicators >= 7 else 'MEDIUM'
        elif accumulation_indicators >= 3:
            interpretation['overall_signal'] = 'ACCUMULATION'
            interpretation['action'] = 'BUY'
            interpretation['confidence'] = 'MEDIUM'
        elif distribution_indicators >= 4:
            interpretation['overall_signal'] = 'DISTRIBUTION'
            interpretation['action'] = 'SELL'
            interpretation['confidence'] = 'MEDIUM'
        elif distribution_indicators >= 2:
            interpretation['overall_signal'] = 'WEAK_DISTRIBUTION'
            interpretation['action'] = 'REDUCE'
            interpretation['confidence'] = 'LOW'
        
        # Nível de risco
        if interpretation['confidence'] == 'HIGH':
            interpretation['risk_level'] = 'LOW'
        elif interpretation['confidence'] == 'MEDIUM':
            interpretation['risk_level'] = 'MEDIUM'
        else:
            interpretation['risk_level'] = 'HIGH'
        
        return interpretation
    
    def print_analysis_results(self, signals, interpretation):
        """Imprime resultados da análise"""
        
        print(f"\n📈 ANÁLISE DE ACUMULAÇÃO SILENCIOSA - {signals['symbol']}")
        print("=" * 60)
        
        print(f"🎯 SINAL PRINCIPAL: {interpretation['overall_signal']}")
        print(f"📊 AÇÃO RECOMENDADA: {interpretation['action']}")
        print(f"🎲 CONFIANÇA: {interpretation['confidence']}")
        print(f"⚠️  RISCO: {interpretation['risk_level']}")
        
        print(f"\n📊 MÉTRICAS CHAVE:")
        print(f"  • Score de Acumulação: {signals['accumulation_score']}/10")
        print(f"  • Dias com Alta Atividade: {signals['high_accumulation_days']}")
        print(f"  • Eficiência de Volume: {signals['volume_efficiency']}")
        print(f"  • Tendência de Volume: {signals['volume_trend']}x")
        print(f"  • Ratio Dark Pool: {signals['dark_pool_ratio']}%")
        print(f"  • Tendência Shorts: {signals['short_trend']}")
        
        print(f"\n💹 DADOS DE PREÇO:")
        print(f"  • Preço Atual: ${signals['current_price']}")
        print(f"  • Variação 20 dias: {signals['price_change_20d']:+.2f}%")
        
        print(f"\n🔍 RAZÕES DA ANÁLISE:")
        for reason in interpretation['reasons']:
            print(f"  • {reason}")
        
        # Alertas especiais
        if interpretation['overall_signal'] in ['STRONG_ACCUMULATION', 'ACCUMULATION']:
            print(f"\n🚨 ALERTA DE OPORTUNIDADE!")
            print(f"   Possível acumulação institucional detectada.")
            print(f"   Considere posição longa com stop loss.")
        
        elif interpretation['overall_signal'] in ['DISTRIBUTION', 'WEAK_DISTRIBUTION']:
            print(f"\n⚠️  ALERTA DE RISCO!")
            print(f"   Possível distribuição institucional detectada.")
            print(f"   Considere reduzir exposição ou posição curta.")
    
    def create_accumulation_charts(self, df, symbol, signals):
        """Cria gráficos da análise de acumulação"""
        
        print("📊 Criando gráficos de análise...")
        
        plt.style.use('seaborn-v0_8')
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle(f'Análise de Acumulação Silenciosa - {symbol.upper()}', fontsize=16, fontweight='bold')
        
        recent_data = df.tail(30)
        
        # 1. Preço vs Volume
        ax1 = axes[0, 0]
        ax1_twin = ax1.twinx()
        
        ax1.plot(recent_data['date'], recent_data['Close'], 'b-', linewidth=2, label='Preço')
        ax1_twin.bar(recent_data['date'], recent_data['Volume'], alpha=0.3, color='gray', label='Volume')
        ax1_twin.bar(recent_data['date'], recent_data['dark_pool_volume'], alpha=0.6, color='red', label='Dark Pool Volume')
        
        ax1.set_ylabel('Preço ($)', color='blue')
        ax1_twin.set_ylabel('Volume', color='gray')
        ax1.set_title('Preço vs Volume (Dark Pool em Vermelho)')
        ax1.tick_params(axis='x', rotation=45)
        
        # 2. Score de Acumulação
        ax2 = axes[0, 1]
        colors = ['red' if x < 4 else 'yellow' if x < 7 else 'green' for x in recent_data['accumulation_score']]
        ax2.bar(recent_data['date'], recent_data['accumulation_score'], color=colors, alpha=0.7)
        ax2.axhline(y=7, color='green', linestyle='--', alpha=0.7, label='Alto (7+)')
        ax2.axhline(y=4, color='orange', linestyle='--', alpha=0.7, label='Médio (4+)')
        ax2.set_ylabel('Score de Acumulação')
        ax2.set_title('Score de Acumulação Diário')
        ax2.legend()
        ax2.tick_params(axis='x', rotation=45)
        
        # 3. Eficiência de Volume
        ax3 = axes[1, 0]
        ax3.plot(recent_data['date'], recent_data['volume_efficiency'], 'purple', linewidth=2, label='Eficiência de Volume')
        ax3.plot(recent_data['date'], recent_data['vei_ma'], 'orange', linewidth=1, label='Média Móvel')
        ax3.fill_between(recent_data['date'], recent_data['volume_efficiency'], 
                        recent_data['vei_ma'], alpha=0.3, color='purple')
        ax3.set_ylabel('Eficiência de Volume')
        ax3.set_title('Eficiência de Volume (Baixo = Acumulação)')
        ax3.legend()
        ax3.tick_params(axis='x', rotation=45)
        
        # 4. Volume Relativo vs Movimento de Preço
        ax4 = axes[1, 1]
        scatter = ax4.scatter(recent_data['relative_volume'], recent_data['price_move_abs'], 
                            c=recent_data['accumulation_score'], cmap='RdYlGn', alpha=0.7, s=60)
        ax4.set_xlabel('Volume Relativo')
        ax4.set_ylabel('Movimento Absoluto de Preço (%)')
        ax4.set_title('Volume vs Movimento de Preço (Verde = Acumulação)')
        plt.colorbar(scatter, ax=ax4)
        
        plt.tight_layout()
        
        # Salvar
        filename = f'accumulation_analysis_{symbol.lower()}_{datetime.now().strftime("%Y%m%d_%H%M")}.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"✓ Gráficos salvos como: {filename}")
        
        plt.show()
    
    def scan_multiple_stocks(self, symbols_list, days=60):
        """Escaneia múltiplas ações para detectar acumulação"""
        
        print(f"\n🔍 ESCANEANDO {len(symbols_list)} AÇÕES PARA ACUMULAÇÃO SILENCIOSA")
        print("=" * 70)
        
        results = []
        
        for i, symbol in enumerate(symbols_list, 1):
            print(f"\n[{i}/{len(symbols_list)}] Analisando {symbol}...")
            try:
                result = self.detect_silent_accumulation(symbol, days)
                if result:
                    results.append(result['signals'])
                    print(f"✓ {symbol} analisado")
            except Exception as e:
                print(f"❌ Erro em {symbol}: {str(e)}")
            
            # Delay para não sobrecarregar APIs
            import time
            time.sleep(2)
        
        # Ranking das melhores oportunidades
        if results:
            df_results = pd.DataFrame(results)
            df_results = df_results.sort_values('accumulation_score', ascending=False)
            
            print(f"\n🏆 TOP OPORTUNIDADES DE ACUMULAÇÃO:")
            print("=" * 50)
            
            for i, row in df_results.head(10).iterrows():
                print(f"{row['symbol']:>6} | Score: {row['accumulation_score']:>4.1f} | "
                      f"Dark Pool: {row['dark_pool_ratio']:>5.1f}% | "
                      f"Vol Trend: {row['volume_trend']:>4.1f}x | "
                      f"Price Δ: {row['price_change_20d']:>+6.1f}%")
            
            # Salvar resultados
            filename = f'accumulation_scan_{datetime.now().strftime("%Y%m%d_%H%M")}.csv'
            df_results.to_csv(filename, index=False)
            print(f"\n✓ Resultados salvos em: {filename}")
            
            return df_results
        
        return None

def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Detectar acumulação silenciosa em ações')
    parser.add_argument('--symbol', help='Símbolo da ação para análise individual')
    parser.add_argument('--scan', help='Arquivo com lista de símbolos para scan', type=str)
    parser.add_argument('--days', type=int, default=60, help='Dias de histórico (padrão: 60)')
    
    args = parser.parse_args()
    
    detector = SilentAccumulationDetector()
    
    if args.symbol:
        # Análise individual
        detector.detect_silent_accumulation(args.symbol, args.days)
    elif args.scan:
        # Scan de múltiplas ações
        try:
            with open(args.scan, 'r') as f:
                symbols = [line.strip().upper() for line in f if line.strip()]
            detector.scan_multiple_stocks(symbols, args.days)
        except FileNotFoundError:
            print(f"❌ Arquivo {args.scan} não encontrado")
    else:
        # Exemplo com ações populares
        print("🔧 Modo exemplo - escaneando ações populares")
        popular_stocks = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN', 'NVDA', 'META', 'NFLX']
        detector.scan_multiple_stocks(popular_stocks, args.days)

if __name__ == "__main__":
    main()