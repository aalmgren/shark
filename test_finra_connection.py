#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script simples para testar conexão com API do FINRA
"""

import requests
import json
from datetime import datetime, timedelta

def test_finra_api():
    """Testa diferentes endpoints e configurações da API do FINRA"""
    
    print("🔍 TESTANDO CONEXÃO COM API DO FINRA")
    print("=" * 50)
    
    # URLs possíveis
    endpoints = [
        "https://api.finra.org/data/group/OTCMarket/name/regShoDaily",
        "https://api.finra.org/data/group/otcMarket/name/regShoDaily", 
        "https://www.finra.org/finra-data/browse-catalog/short-sale-volume-data",
        "https://otce.finra.org/otce/regShoDailyFile"
    ]
    
    # Headers possíveis
    headers_options = [
        {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        },
        {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        },
        {
            'Accept': 'application/json'
        }
    ]
    
    # Payload de teste para AAPL de ontem
    yesterday = datetime.now() - timedelta(days=1)
    test_date = yesterday.strftime('%Y-%m-%d')
    
    payload = {
        "compareFilters": [
            {"compareType": "EQUAL", "fieldName": "symbol", "fieldValue": "AAPL"},
            {"compareType": "EQUAL", "fieldName": "tradeDate", "fieldValue": test_date}
        ],
        "limit": 10
    }
    
    print(f"📅 Testando data: {test_date}")
    print(f"🎯 Symbol: AAPL")
    print()
    
    for i, url in enumerate(endpoints, 1):
        print(f"📡 Teste {i}: {url}")
        
        for j, headers in enumerate(headers_options, 1):
            try:
                print(f"  Headers {j}: {headers}")
                
                # GET simples primeiro
                response_get = requests.get(url, headers=headers, timeout=10)
                print(f"  GET Status: {response_get.status_code}")
                
                if response_get.status_code == 200:
                    print(f"  ✅ GET funcionou! Conteúdo: {len(response_get.text)} chars")
                    if response_get.text:
                        print(f"  Primeiros 200 chars: {response_get.text[:200]}")
                
                # POST com payload
                response_post = requests.post(url, headers=headers, 
                                            data=json.dumps(payload), timeout=10)
                print(f"  POST Status: {response_post.status_code}")
                
                if response_post.status_code == 200:
                    print(f"  ✅ POST funcionou!")
                    try:
                        data = response_post.json()
                        print(f"  📊 Dados recebidos: {len(data) if isinstance(data, list) else 'objeto'}")
                        if isinstance(data, list) and len(data) > 0:
                            print(f"  📋 Primeiro item: {data[0]}")
                            return True
                    except:
                        print(f"  📄 Resposta não-JSON: {response_post.text[:200]}")
                
                print()
                
            except requests.RequestException as e:
                print(f"  ❌ Erro: {str(e)}")
                print()
    
    print("🔍 TESTANDO ENDPOINTS ALTERNATIVOS")
    print("=" * 40)
    
    # Testar se conseguimos acessar qualquer dado do FINRA
    simple_urls = [
        "https://www.finra.org/",
        "https://finra-markets.morningstar.com/MarketData/Default.jsp",
        "https://otce.finra.org/"
    ]
    
    for url in simple_urls:
        try:
            response = requests.get(url, timeout=10)
            print(f"📡 {url}: Status {response.status_code}")
            if response.status_code == 200:
                print(f"   ✅ Acessível! Tamanho: {len(response.text)} chars")
        except Exception as e:
            print(f"   ❌ Erro: {str(e)}")
    
    return False

if __name__ == "__main__":
    success = test_finra_api()
    
    if success:
        print("\n🎉 SUCESSO! Conseguimos dados do FINRA")
    else:
        print("\n❌ FALHOU! Não conseguimos dados do FINRA")
        print("\n💡 POSSÍVEIS SOLUÇÕES:")
        print("1. API do FINRA pode ter mudado de endpoint")
        print("2. Pode precisar de autenticação/API key")
        print("3. Pode ter limitação geográfica")
        print("4. Pode precisar de User-Agent específico")
        print("5. Dados podem estar em formato diferente")