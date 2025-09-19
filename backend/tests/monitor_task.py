#!/usr/bin/env python3
"""
Script para monitorar o status de uma task de descoberta
Execute: python3 monitor_task.py <task_id>
"""

import requests
import json
import time
import sys

BASE_URL = "http://localhost:8000"

def check_task_status(task_id):
    """Verifica o status de uma task"""
    try:
        response = requests.get(f"{BASE_URL}/api/agents/tasks/{task_id}")

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            print(f"❌ Task {task_id} não encontrada")
            return None
        else:
            print(f"❌ Erro ao verificar task: {response.status_code}")
            return None

    except requests.exceptions.ConnectionError:
        print("❌ Erro: Não foi possível conectar à API")
        return None

def monitor_task(task_id):
    """Monitora uma task até completar"""
    print(f"🔍 Monitorando Task ID: {task_id}")
    print("=" * 50)

    while True:
        task = check_task_status(task_id)

        if not task:
            break

        status = task.get('status')
        print(f"⏱️  Status: {status}")

        if status == "completed":
            print("✅ Task completada com sucesso!")
            print("\n📊 Resultados:")

            output_data = task.get('output_data', {})
            if 'startups' in output_data:
                startups = output_data['startups']
                print(f"🏢 Startups encontradas: {len(startups)}")
                print(f"🪙 Tokens utilizados: {output_data.get('tokens_used', 'N/A')}")

                print("\n📋 Lista de Startups:")
                for i, startup in enumerate(startups, 1):
                    print(f"\n{i}. {startup.get('name', 'N/A')}")
                    print(f"   🌐 Website: {startup.get('website', 'N/A')}")
                    print(f"   🏭 Setor: {startup.get('sector', 'N/A')}")
                    print(f"   🤖 Tecnologias IA: {startup.get('ai_technologies', [])}")
                    print(f"   💰 Funding: ${startup.get('last_funding_amount', 0):,}")
                    print(f"   💼 Investidores: {startup.get('investor_names', [])}")
            else:
                print("📋 Dados de saída:")
                print(json.dumps(output_data, indent=2))
            break

        elif status == "failed":
            print("❌ Task falhou!")
            error_msg = task.get('error_message')
            if error_msg:
                print(f"Erro: {error_msg}")
            break

        elif status in ["pending", "running"]:
            print("⏳ Aguardando conclusão...")
            time.sleep(5)  # Aguarda 5 segundos antes de verificar novamente

        else:
            print(f"❓ Status desconhecido: {status}")
            break

def start_discovery_and_monitor():
    """Inicia uma descoberta e monitora automaticamente"""
    print("🚀 Iniciando nova descoberta de startups...")

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
            print()

            # Monitora automaticamente
            monitor_task(task_id)

        else:
            print(f"❌ Erro ao criar task: {response.status_code}")
            print(response.text)

    except requests.exceptions.ConnectionError:
        print("❌ Erro: Não foi possível conectar à API")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Monitor task específica
        task_id = sys.argv[1]
        try:
            task_id = int(task_id)
            monitor_task(task_id)
        except ValueError:
            print("❌ Task ID deve ser um número")
    else:
        # Inicia nova descoberta e monitora
        start_discovery_and_monitor()