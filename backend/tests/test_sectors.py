#!/usr/bin/env python3
"""
Testa descoberta de startups por diferentes setores
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

# Setores para testar
SETORES = [
    "Fintech",
    "Healthtech",
    "Edtech",
    "Agtech",
    "Retailtech"
]

def test_sector(sector):
    """Testa descoberta para um setor específico"""
    print(f"🔍 Testando setor: {sector}")

    data = {
        "country": "Brazil",
        "sector": sector,
        "limit": 3
    }

    try:
        response = requests.post(f"{BASE_URL}/api/agents/discover", json=data)

        if response.status_code == 200:
            result = response.json()
            task_id = result.get('task_id')
            print(f"✅ Task criada: ID {task_id}")
            return task_id
        else:
            print(f"❌ Erro: {response.status_code}")
            return None

    except Exception as e:
        print(f"❌ Erro: {e}")
        return None

def test_all_sectors():
    """Testa descoberta para todos os setores"""
    print("🔍 Testando TODOS os setores")

    data = {
        "country": "Brazil",
        "sector": None,  # Todos os setores
        "limit": 10
    }

    try:
        response = requests.post(f"{BASE_URL}/api/agents/discover", json=data)

        if response.status_code == 200:
            result = response.json()
            task_id = result.get('task_id')
            print(f"✅ Task criada: ID {task_id}")
            return task_id
        else:
            print(f"❌ Erro: {response.status_code}")
            return None

    except Exception as e:
        print(f"❌ Erro: {e}")
        return None

if __name__ == "__main__":
    print("🎯 NVIDIA Inception AI - Teste por Setores")
    print("=" * 50)

    task_ids = []

    # Testa setores específicos
    for setor in SETORES:
        task_id = test_sector(setor)
        if task_id:
            task_ids.append((setor, task_id))
        print()
        time.sleep(1)  # Pausa entre requests

    # Testa todos os setores
    task_id = test_all_sectors()
    if task_id:
        task_ids.append(("TODOS", task_id))

    print("\n📋 Tasks Criadas:")
    for setor, task_id in task_ids:
        print(f"- {setor}: Task ID {task_id}")

    print(f"\n💡 Para monitorar uma task específica:")
    print(f"python3 monitor_task.py <task_id>")

    print(f"\n🌐 Ou verifique via API:")
    for setor, task_id in task_ids:
        print(f"curl http://localhost:8000/api/agents/tasks/{task_id}")