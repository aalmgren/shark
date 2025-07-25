#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analisa dados reais do FINRA via GET
"""

import requests
import json
from datetime import datetime, timedelta

def get_finra_data_via_get():
    """Pega dados do FINRA via GET e analisa especificamente o OUST"""
    
    print("📡 PEGANDO DADOS REAIS DO FINRA VIA GET")
    print("=" * 50)
    
    url = "https://api.finra.org/data/group/OTCMarket/name/regShoDaily"
    headers = {'Accept': 'application/json'}
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📊 Total de registros: {len(data)}")
            
            # Analisar estrutura dos dados
            if len(data) > 0:
                print(f"\n📋 ESTRUTURA DOS DADOS:")
                first_record = data[0]
                for key, value in first_record.items():
                    print(f"  {key}: {value} ({type(value).__name__})")
                
                # Procurar OUST especificamente
                print(f"\n🔍 PROCURANDO DADOS DO OUST:")
                oust_records = []
                for record in data:
                    symbol = record.get('securitiesInformationProcessorSymbolIdentifier', '')
                    if symbol == 'OUST':
                        oust_records.append(record)
                
                if oust_records:
                    print(f"✅ Encontrados {len(oust_records)} registros do OUST:")
                    for i, record in enumerate(oust_records[:5], 1):  # Mostrar até 5
                        print(f"\n  Registro {i}:")
                        for key, value in record.items():
                            print(f"    {key}: {value}")
                else:
                    print("❌ Nenhum registro do OUST encontrado")
                    
                    # Mostrar alguns símbolos disponíveis
                    symbols = set()
                    for record in data[:100]:  # Primeiros 100
                        symbol = record.get('securitiesInformationProcessorSymbolIdentifier', '')
                        if symbol:
                            symbols.add(symbol)
                    
                    print(f"\n📈 Alguns símbolos disponíveis (primeiros 20):")
                    for symbol in sorted(list(symbols))[:20]:
                        print(f"  - {symbol}")
                
                # Analisar datas disponíveis
                print(f"\n📅 DATAS DISPONÍVEIS:")
                dates = set()
                for record in data[:100]:  # Primeiros 100
                    date = record.get('tradeReportDate', '')
                    if date:
                        dates.add(date)
                
                sorted_dates = sorted(list(dates))
                print(f"  Datas mais recentes: {sorted_dates[-5:] if len(sorted_dates) >= 5 else sorted_dates}")
                print(f"  Datas mais antigas: {sorted_dates[:5] if len(sorted_dates) >= 5 else sorted_dates}")
                
                # Verificar se temos dados de ontem para AAPL
                yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                today = datetime.now().strftime('%Y-%m-%d')
                
                print(f"\n🔍 PROCURANDO AAPL de {yesterday} ou {today}:")
                aapl_recent = []
                for record in data:
                    symbol = record.get('securitiesInformationProcessorSymbolIdentifier', '')
                    date = record.get('tradeReportDate', '')
                    if symbol == 'AAPL' and date in [yesterday, today]:
                        aapl_recent.append(record)
                
                if aapl_recent:
                    print(f"✅ Encontrados {len(aapl_recent)} registros recentes do AAPL:")
                    for record in aapl_recent:
                        date = record.get('tradeReportDate', '')
                        total_vol = record.get('totalParQuantity', 0)
                        short_vol = record.get('shortParQuantity', 0) 
                        print(f"  📅 {date}: Total={total_vol:,}, Short={short_vol:,}")
                else:
                    print("❌ Nenhum registro recente do AAPL encontrado")
                
                return data
        else:
            print(f"❌ Erro: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return None

def analyze_volume_data(data, symbol):
    """Analisa dados de volume para um símbolo específico"""
    
    if not data:
        return None
    
    print(f"\n🔍 ANÁLISE DETALHADA DE VOLUME - {symbol.upper()}")
    print("=" * 50)
    
    symbol_records = []
    for record in data:
        rec_symbol = record.get('securitiesInformationProcessorSymbolIdentifier', '')
        if rec_symbol == symbol.upper():
            symbol_records.append(record)
    
    if not symbol_records:
        print(f"❌ Nenhum dado encontrado para {symbol}")
        return None
    
    print(f"📊 Total de registros para {symbol}: {len(symbol_records)}")
    
    # Agrupar por data
    by_date = {}
    for record in symbol_records:
        date = record.get('tradeReportDate', '')
        if date:
            if date not in by_date:
                by_date[date] = []
            by_date[date].append(record)
    
    print(f"📅 Dados disponíveis para {len(by_date)} datas")
    
    # Mostrar dados mais recentes
    recent_dates = sorted(by_date.keys())[-5:]
    
    for date in recent_dates:
        records = by_date[date]
        total_volume = sum(r.get('totalParQuantity', 0) for r in records)
        short_volume = sum(r.get('shortParQuantity', 0) for r in records)
        
        print(f"\n📅 {date}:")
        print(f"  📊 Volume Total (Off-Exchange): {total_volume:,}")
        print(f"  🔻 Volume Short: {short_volume:,}")
        print(f"  📈 % Short do Off-Exchange: {(short_volume/total_volume*100):.1f}%" if total_volume > 0 else "  📈 % Short: N/A")
        print(f"  🏢 Número de facilities: {len(records)}")
    
    return symbol_records

if __name__ == "__main__":
    # Pegar dados do FINRA
    finra_data = get_finra_data_via_get()
    
    if finra_data:
        # Analisar OUST especificamente
        analyze_volume_data(finra_data, "OUST")
        
        # Analisar AAPL para comparação
        analyze_volume_data(finra_data, "AAPL")
        
        print(f"\n✅ SUCESSO! Conseguimos dados de volume off-exchange do FINRA!")
        print(f"📊 Total de registros analisados: {len(finra_data)}")