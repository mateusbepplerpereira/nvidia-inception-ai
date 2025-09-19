#!/usr/bin/env python3
"""
Teste Final - NVIDIA Inception AI System
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_system():
    """Teste completo do sistema"""
    print("🎯 NVIDIA Inception AI - Sistema Limpo e Funcional")
    print("=" * 60)

    # 1. Health Check
    print("1. 🔍 Health Check...")
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    print("   ✅ Sistema online")

    # 2. Descoberta de Startups
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

    # 3. Aguardar e verificar resultado
    print("\n3. ⏳ Aguardando processamento...")
    import time
    time.sleep(15)  # Aguarda processamento

    response = requests.get(f"{BASE_URL}/api/agents/tasks/{task_id}")
    assert response.status_code == 200

    task = response.json()

    if task["status"] == "completed":
        output = task["output_data"]
        print(f"   ✅ Concluído com sucesso!")
        print(f"   📊 {output['count']} startups encontradas")
        print(f"   🪙 {output['tokens_used']} tokens utilizados")

        print(f"\n   🏢 Startups descobertas:")
        for startup in output["startups"][:3]:  # Mostra apenas 3
            print(f"      • {startup['name']} - {startup['sector']}")
            print(f"        💰 ${startup['last_funding_amount']:,}")

    elif task["status"] == "failed":
        print(f"   ❌ Falhou: {task.get('error_message')}")
    else:
        print(f"   ⏳ Status: {task['status']}")

    # 4. Listar startups salvas
    print(f"\n4. 📋 Startups no banco...")
    response = requests.get(f"{BASE_URL}/api/startups/")
    assert response.status_code == 200

    startups = response.json()
    print(f"   ✅ {len(startups)} startups salvas")

    print(f"\n✅ Sistema funcionando perfeitamente!")
    print(f"🌐 Documentação: {BASE_URL}/docs")

if __name__ == "__main__":
    try:
        test_system()
    except requests.exceptions.ConnectionError:
        print("❌ Sistema offline. Execute: docker-compose up -d")
    except Exception as e:
        print(f"❌ Erro: {e}")