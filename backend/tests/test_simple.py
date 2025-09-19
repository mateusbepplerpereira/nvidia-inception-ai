#!/usr/bin/env python3
"""
Teste Simples - Verificar se descoberta funciona
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_discovery_only():
    """Teste apenas a descoberta"""
    print("🎯 Teste Simples - Descoberta de Startups")
    print("=" * 50)

    # 1. Health Check
    print("1. 🔍 Health Check...")
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    print("   ✅ Sistema online")

    # 2. Descoberta
    print("\n2. 🚀 Descoberta de Startups...")
    response = requests.post(f"{BASE_URL}/api/agents/discover", json={
        "country": "Brazil",
        "sector": "Fintech",
        "limit": 3
    })
    assert response.status_code == 200

    result = response.json()
    task_id = result["task_id"]
    print(f"   ✅ Task criada: ID {task_id}")

    # 3. Aguardar resultado
    print("\n3. ⏳ Aguardando resultado...")
    time.sleep(15)

    response = requests.get(f"{BASE_URL}/api/agents/tasks/{task_id}")
    assert response.status_code == 200

    task = response.json()
    print(f"   📊 Status: {task['status']}")

    if task["status"] == "completed":
        output = task["output_data"]
        if output.get("status") == "success":
            print(f"   ✅ {output['count']} startups encontradas")
            print(f"   🪙 {output['tokens_used']} tokens utilizados")

            # Mostrar primeira startup com detalhes
            if output["startups"]:
                startup = output["startups"][0]
                print(f"\n   📋 Primeira startup:")
                print(f"      • Nome: {startup['name']}")
                print(f"      • Setor: {startup['sector']}")
                print(f"      • CEO: {startup.get('ceo_name', 'N/A')}")
                print(f"      • LinkedIn CEO: {startup.get('ceo_linkedin', 'N/A')}")
                print(f"      • CTO: {startup.get('cto_name', 'N/A')}")
                print(f"      • LinkedIn CTO: {startup.get('cto_linkedin', 'N/A')}")
        else:
            print(f"   ❌ Erro: {output.get('error')}")

    print(f"\n✅ Teste concluído!")

if __name__ == "__main__":
    try:
        test_discovery_only()
    except Exception as e:
        print(f"❌ Erro: {e}")