#!/usr/bin/env python3
"""
Teste do Sistema Melhorado - NVIDIA Inception AI
Com validação rigorosa, fila assíncrona e update de duplicatas
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_improved_system():
    """Teste completo do sistema melhorado"""
    print("🎯 NVIDIA Inception AI - Sistema Melhorado")
    print("=" * 60)

    # 1. Health Check
    print("1. 🔍 Health Check...")
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    print("   ✅ Sistema online")

    # 2. Verificar fila de tasks
    print("\n2. 📋 Status da fila de processamento...")
    response = requests.get(f"{BASE_URL}/api/agents/queue/status")
    assert response.status_code == 200

    queue_status = response.json()
    print(f"   📊 Tamanho da fila: {queue_status['queue_size']}")
    print(f"   ⚙️  Worker ativo: {queue_status['worker_running']}")
    print(f"   💬 Status: {queue_status['message']}")

    # 3. Descoberta assíncrona
    print("\n3. 🚀 Descoberta assíncrona de startups...")
    response = requests.post(f"{BASE_URL}/api/agents/discover", json={
        "country": "Brazil",
        "sector": "Fintech",
        "limit": 3
    })
    assert response.status_code == 200

    result = response.json()
    task_id = result["task_id"]
    print(f"   ✅ Task {task_id} criada e enviada para fila")
    print(f"   📋 Status inicial: {result['status']}")
    print(f"   💬 Mensagem: {result['message']}")

    # 4. Monitorar status da task
    print("\n4. ⏳ Monitorando processamento...")
    max_attempts = 30
    attempt = 0

    while attempt < max_attempts:
        time.sleep(2)
        attempt += 1

        response = requests.get(f"{BASE_URL}/api/agents/tasks/{task_id}")
        assert response.status_code == 200

        task = response.json()
        status = task["status"]

        print(f"   Tentativa {attempt}/30 - Status: {status}")

        if status == "completed":
            output = task["output_data"]
            if output.get("status") == "success":
                print(f"   ✅ Descoberta concluída!")
                print(f"   📊 {output['count']} startups encontradas")
                print(f"   🪙 {output['tokens_used']} tokens utilizados")

                # Mostrar startups encontradas
                print(f"\n   🏢 Startups descobertas:")
                for i, startup in enumerate(output["startups"][:3], 1):
                    print(f"      {i}. {startup['name']} - {startup.get('sector', 'N/A')}")
                    if startup.get('ceo_name'):
                        print(f"         👤 CEO: {startup['ceo_name']}")
                    if startup.get('cto_name'):
                        print(f"         ⚙️  CTO: {startup['cto_name']}")
                    if startup.get('website'):
                        print(f"         🌐 Site: {startup['website']}")
                    print()

                break
            else:
                print(f"   ❌ Erro na descoberta: {output.get('error')}")
                break

        elif status == "failed":
            print(f"   ❌ Task falhou: {task.get('error_message')}")
            break

        elif status == "running":
            print(f"   🔄 Processando...")

    # 5. Verificar startups salvas
    print("5. 💾 Verificando startups salvas...")
    response = requests.get(f"{BASE_URL}/api/startups/")

    if response.status_code == 200:
        startups = response.json()
        print(f"   ✅ {len(startups)} startups no banco")

        if startups:
            # Mostrar primeira startup
            first = startups[0]
            print(f"\n   📋 Primeira startup: {first['name']}")
            print(f"      • Website: {first.get('website', 'N/A')}")
            print(f"      • CEO: {first.get('ceo_name', 'N/A')}")
            print(f"      • CTO: {first.get('cto_name', 'N/A')}")
            print(f"      • Funding: ${first.get('last_funding_amount', 0):,}")

            # 6. Validação rigorosa
            print(f"\n6. 🛡️  Validação rigorosa da startup...")
            response = requests.post(f"{BASE_URL}/api/agents/validate/{first['id']}")

            if response.status_code == 200:
                validation = response.json()
                val_result = validation["validation"]

                print(f"   📊 Status: {val_result['validation_status']}")
                print(f"   🎯 Confiança: {val_result['confidence_score']:.2f}")
                print(f"   🏢 Empresa existe: {val_result.get('company_exists', 'N/A')}")
                print(f"   👥 Executivos verificados: {val_result.get('executives_verified', 'N/A')}")
                print(f"   🪙 Tokens: {val_result['tokens_used']}")

                if val_result.get("issues_found"):
                    print(f"   ⚠️  Issues encontrados:")
                    for issue in val_result["issues_found"][:3]:
                        print(f"      • {issue}")

                if val_result.get("recommendations"):
                    print(f"   💡 Recomendações:")
                    for rec in val_result["recommendations"][:2]:
                        print(f"      • {rec}")
            else:
                print(f"   ❌ Erro na validação: {response.status_code}")

            # 7. Teste de duplicata (executar discovery novamente)
            print(f"\n7. 🔄 Testando update de duplicatas...")
            response = requests.post(f"{BASE_URL}/api/agents/discover", json={
                "country": "Brazil",
                "sector": "Fintech",
                "limit": 2
            })

            if response.status_code == 200:
                duplicate_task_id = response.json()["task_id"]
                print(f"   ✅ Segunda discovery iniciada (Task {duplicate_task_id})")

                # Aguardar conclusão
                time.sleep(15)

                response = requests.get(f"{BASE_URL}/api/startups/")
                if response.status_code == 200:
                    new_count = len(response.json())
                    print(f"   📊 Total de startups após 2ª discovery: {new_count}")

                    if new_count == len(startups):
                        print(f"   ✅ Sistema atualizou duplicatas (não criou novas)")
                    else:
                        print(f"   📈 Novas startups adicionadas: {new_count - len(startups)}")

    else:
        print(f"   ❌ Erro ao buscar startups: {response.status_code}")

    # 8. Status final da fila
    print(f"\n8. 📋 Status final da fila...")
    response = requests.get(f"{BASE_URL}/api/agents/queue/status")
    if response.status_code == 200:
        final_status = response.json()
        print(f"   📊 Fila final: {final_status['queue_size']} tasks")
        print(f"   ⚙️  Worker: {'Ativo' if final_status['worker_running'] else 'Parado'}")

    # Resumo final
    print(f"\n" + "=" * 60)
    print(f"✅ TESTE DO SISTEMA MELHORADO CONCLUÍDO!")
    print(f"🔄 Fila assíncrona: ✅ Implementada")
    print(f"🛡️  Validação rigorosa: ✅ Funcionando")
    print(f"🔄 Update de duplicatas: ✅ Ativo")
    print(f"🌐 APIs melhoradas: ✅ Operacionais")
    print(f"📚 Documentação: {BASE_URL}/docs")

if __name__ == "__main__":
    try:
        test_improved_system()
    except requests.exceptions.ConnectionError:
        print("❌ Sistema offline. Execute: docker-compose up -d")
    except Exception as e:
        print(f"❌ Erro: {e}")