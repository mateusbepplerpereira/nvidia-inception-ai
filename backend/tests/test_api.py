#!/usr/bin/env python3
"""
Script de teste para a API NVIDIA Inception AI
Execute: python test_api.py
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Testa o endpoint de health"""
    print("🔍 Testando Health Check...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_main_endpoint():
    """Testa o endpoint principal"""
    print("🔍 Testando Endpoint Principal...")
    response = requests.get(f"{BASE_URL}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_discover_startups():
    """Testa descoberta de startups"""
    print("🚀 Testando Descoberta de Startups...")
    data = {
        "country": "Brazil",
        "sector": "Fintech",
        "limit": 5
    }

    response = requests.post(f"{BASE_URL}/api/agents/discover", json=data)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"Task ID: {result.get('task_id')}")
        print(f"Status: {result.get('status')}")
        print(f"Message: {result.get('message')}")
    else:
        print(f"Error: {response.text}")
    print()

def test_list_startups():
    """Testa listagem de startups"""
    print("📋 Testando Listagem de Startups...")
    response = requests.get(f"{BASE_URL}/api/startups")
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        startups = response.json()
        print(f"Total de startups: {len(startups)}")
        if startups:
            print("Primeira startup:", json.dumps(startups[0], indent=2))
    else:
        print(f"Error: {response.text}")
    print()

def test_dashboard():
    """Testa dashboard de análise"""
    print("📊 Testando Dashboard...")
    response = requests.get(f"{BASE_URL}/api/analysis/dashboard")
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        dashboard = response.json()
        print("Dashboard data:", json.dumps(dashboard, indent=2))
    else:
        print(f"Error: {response.text}")
    print()

if __name__ == "__main__":
    print("🎯 NVIDIA Inception AI - Teste da API")
    print("=" * 50)

    try:
        test_health()
        test_main_endpoint()
        test_discover_startups()
        test_list_startups()
        test_dashboard()

        print("✅ Todos os testes concluídos!")
        print()
        print("🌐 Acesse a documentação em: http://localhost:8000/docs")

    except requests.exceptions.ConnectionError:
        print("❌ Erro: Não foi possível conectar à API")
        print("Certifique-se de que o sistema está rodando com: docker-compose up -d")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")