#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 INVESTIGAÇÃO DAS DATAS DO FINRA
Por que só temos dados antigos?
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
from collections import Counter

def investigate_finra_dates():
    """Investiga detalhadamente as datas nos dados do FINRA"""
    
    print("🔍 INVESTIGANDO DATAS DOS DADOS FINRA")
    print("=" * 60)
    
    url = "https://api.finra.org/data/group/OTCMarket/name/regShoDaily"
    headers = {'Accept': 'application/json'}
    
    try:
        print("📡 Fazendo requisição para FINRA...")
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Erro: {response.status_code}")
            return
        
        data = response.json()
        df = pd.DataFrame(data)
        
        print(f"✅ {len(data)} registros recebidos")
        print()
        
        # Analisar todas as datas disponíveis
        print("📅 ANÁLISE COMPLETA DAS DATAS:")
        print("-" * 40)
        
        dates = []
        for record in data:
            date = record.get('tradeReportDate', '')
            if date:
                dates.append(date)
        
        # Contar ocorrências de cada data
        date_counts = Counter(dates)
        
        print(f"📊 Total de datas únicas: {len(date_counts)}")
        print()
        
        # Mostrar todas as datas (ordenadas)
        sorted_dates = sorted(date_counts.keys())
        
        print("📋 TODAS AS DATAS DISPONÍVEIS:")
        for date in sorted_dates:
            count = date_counts[date]
            print(f"  📅 {date}: {count} registros")
        
        print()
        
        # Analisar gap temporal
        if len(sorted_dates) > 0:
            oldest_date = sorted_dates[0]
            newest_date = sorted_dates[-1]
            
            print(f"🗓️  DATA MAIS ANTIGA: {oldest_date}")
            print(f"🗓️  DATA MAIS RECENTE: {newest_date}")
            
            # Calcular quantos dias atrás
            try:
                newest_dt = datetime.strptime(newest_date, '%Y-%m-%d')
                today = datetime.now()
                days_ago = (today - newest_dt).days
                
                print(f"⏰ DADOS MAIS RECENTES SÃO DE: {days_ago} dias atrás")
                
                if days_ago > 7:
                    print(f"⚠️  PROBLEMA: Dados estão muito desatualizados!")
                    print(f"   Esperávamos dados de pelo menos 1-3 dias atrás")
                
            except:
                print("❌ Erro ao calcular diferença de datas")
        
        print()
        
        # Verificar se há padrão nos dados
        print("🔍 ANÁLISE DE PADRÕES:")
        print("-" * 30)
        
        # Verificar símbolos mais comuns
        symbols = []
        for record in data:
            symbol = record.get('securitiesInformationProcessorSymbolIdentifier', '')
            if symbol:
                symbols.append(symbol)
        
        symbol_counts = Counter(symbols)
        top_symbols = symbol_counts.most_common(10)
        
        print("📈 TOP 10 SÍMBOLOS NOS DADOS:")
        for symbol, count in top_symbols:
            print(f"  {symbol}: {count} registros")
        
        print()
        
        # Verificar facilities
        facilities = []
        for record in data:
            facility = record.get('reportingFacilityCode', '')
            if facility:
                facilities.append(facility)
        
        facility_counts = Counter(facilities)
        
        print("🏢 FACILITIES REPORTANDO:")
        for facility, count in facility_counts.items():
            print(f"  {facility}: {count} registros")
        
        print()
        
        # Verificar volumes típicos
        volumes = []
        for record in data:
            vol = record.get('totalParQuantity', 0)
            if vol > 0:
                volumes.append(vol)
        
        if volumes:
            avg_vol = sum(volumes) / len(volumes)
            max_vol = max(volumes)
            min_vol = min(volumes)
            
            print("📊 ESTATÍSTICAS DE VOLUME:")
            print(f"  Volume médio: {avg_vol:,.0f}")
            print(f"  Volume máximo: {max_vol:,}")
            print(f"  Volume mínimo: {min_vol:,}")
        
        return df
        
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return None

def check_finra_system_status():
    """Verifica se há informações sobre status do sistema FINRA"""
    
    print("\n🔍 VERIFICANDO STATUS DO SISTEMA FINRA")
    print("=" * 50)
    
    # Tentar diferentes endpoints para verificar status
    status_urls = [
        "https://www.finra.org/filing-reporting/finra-gateway",
        "https://www.finra.org/about/news",
        "https://otce.finra.org/",
    ]
    
    for url in status_urls:
        try:
            response = requests.get(url, timeout=10)
            print(f"📡 {url}: Status {response.status_code}")
            
            if response.status_code == 200:
                # Procurar por avisos de manutenção ou problemas
                content = response.text.lower()
                
                keywords = ['maintenance', 'outage', 'unavailable', 'delayed', 'manutenção', 'problema']
                
                for keyword in keywords:
                    if keyword in content:
                        print(f"   ⚠️ Palavra-chave encontrada: '{keyword}'")
                        break
                else:
                    print(f"   ✅ Nenhum aviso de problema encontrado")
        
        except Exception as e:
            print(f"   ❌ Erro ao acessar: {str(e)}")

def suggest_solutions():
    """Sugere possíveis soluções para dados antigos"""
    
    print("\n💡 POSSÍVEIS SOLUÇÕES:")
    print("=" * 30)
    
    solutions = [
        "1. 📅 FINRA pode ter delay de reportagem (normal: 1-3 dias)",
        "2. 🔄 API pode estar retornando dados cached/antigos",
        "3. 📊 Dados off-exchange podem ser reportados com delay maior",
        "4. 🏢 Endpoint pode estar apontando para dados históricos",
        "5. 📋 Pode precisar de parâmetros específicos para dados recentes",
        "6. ⏰ Finais de semana/feriados podem afetar reportagem",
        "7. 🔐 Dados mais recentes podem precisar de autenticação"
    ]
    
    for solution in solutions:
        print(f"  {solution}")
    
    print(f"\n🎯 PRÓXIMOS PASSOS:")
    print(f"  • Verificar documentação oficial da API FINRA")
    print(f"  • Testar endpoints alternativos")
    print(f"  • Verificar se há parâmetros de data")
    print(f"  • Usar dados Yahoo Finance para volume total recente")

if __name__ == "__main__":
    df = investigate_finra_dates()
    check_finra_system_status()
    suggest_solutions()
    
    if df is not None:
        print(f"\n📁 Dados analisados: {len(df)} registros")
    else:
        print(f"\n❌ Não foi possível analisar os dados")