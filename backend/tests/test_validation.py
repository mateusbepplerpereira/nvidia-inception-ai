#!/usr/bin/env python3
"""
Teste de Validação - NVIDIA Inception AI System
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_discovery_and_validation():
    """Teste completo: descoberta com novos campos + validação"""
    print("🎯 NVIDIA Inception AI - Teste de Validação")
    print("=" * 60)

    # 1. Health Check
    print("1. 🔍 Health Check...")
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    print("   ✅ Sistema online")

    # 2. Descoberta de Startups com novos campos
    print("\n2. 🚀 Descoberta de Startups (com CEO/CTO/LinkedIn)...")
    response = requests.post(f"{BASE_URL}/api/agents/discover", json={
        "country": "Brazil",
        "sector": "Fintech",
        "limit": 3
    })
    assert response.status_code == 200

    result = response.json()
    task_id = result["task_id"]
    print(f"   ✅ Task criada: ID {task_id}")

    # 3. Aguardar processamento
    print("\n3. ⏳ Aguardando processamento...")
    time.sleep(15)

    response = requests.get(f"{BASE_URL}/api/agents/tasks/{task_id}")
    assert response.status_code == 200

    task = response.json()

    if task["status"] == "completed":
        output = task["output_data"]

        if output.get("status") == "success":
            print(f"   ✅ Concluído com sucesso!")
            print(f"   📊 {output['count']} startups encontradas")
            print(f"   🪙 {output['tokens_used']} tokens utilizados")

            print(f"\n   🏢 Startups descobertas:")
            for startup in output["startups"][:3]:
                print(f"      • {startup['name']} - {startup['sector']}")
                print(f"        💰 ${startup['last_funding_amount']:,}")
                if startup.get('ceo_name'):
                    print(f"        👤 CEO: {startup['ceo_name']}")
                if startup.get('cto_name'):
                    print(f"        ⚙️  CTO: {startup['cto_name']}")
                if startup.get('ceo_linkedin'):
                    print(f"        🔗 CEO LinkedIn: {startup['ceo_linkedin']}")
                print()
        else:
            print(f"   ❌ Erro na descoberta: {output.get('error', 'Unknown error')}")
            if output.get('raw_response'):
                print(f"   📝 Resposta bruta (primeiros 200 chars): {output['raw_response'][:200]}...")

    elif task["status"] == "failed":
        print(f"   ❌ Falhou: {task.get('error_message')}")
    else:
        print(f"   ⏳ Status: {task['status']}")

    # 4. Listar startups salvas
    print(f"4. 📋 Startups no banco...")
    response = requests.get(f"{BASE_URL}/api/startups/")
    assert response.status_code == 200

    startups = response.json()
    print(f"   ✅ {len(startups)} startups salvas")

    if startups:
        # 5. Validar primeira startup
        first_startup = startups[0]
        print(f"\n5. ✅ Validando startup: {first_startup['name']}")

        response = requests.post(f"{BASE_URL}/api/agents/validate/{first_startup['id']}")

        if response.status_code == 200:
            validation = response.json()
            result = validation["validation"]

            print(f"   📊 Status: {result['validation_status']}")
            print(f"   🎯 Confiança: {result['confidence_score']:.2f}")
            print(f"   🪙 Tokens usados: {result['tokens_used']}")

            if result.get("issues_found"):
                print(f"   ⚠️  Problemas encontrados:")
                for issue in result["issues_found"]:
                    print(f"      • {issue['field']}: {issue['issue']} ({issue['severity']})")

            if result.get("recommendations"):
                print(f"   💡 Recomendações:")
                for rec in result["recommendations"]:
                    print(f"      • {rec}")
        else:
            print(f"   ❌ Erro na validação: {response.status_code}")

        # 6. Validação em lote
        print(f"\n6. 🔄 Validação em lote (3 startups)...")
        response = requests.post(f"{BASE_URL}/api/agents/validate-batch?limit=3")

        if response.status_code == 200:
            batch_validation = response.json()
            summary = batch_validation["summary"]

            print(f"   📊 Resumo da validação:")
            print(f"      • Total: {summary['total_startups']}")
            print(f"      • Válidas: {summary['valid']}")
            print(f"      • Suspeitas: {summary['suspicious']}")
            print(f"      • Inválidas: {summary['invalid']}")
            print(f"      • Erros: {summary['errors']}")
            print(f"   🪙 Total de tokens: {batch_validation['total_tokens_used']}")
        else:
            print(f"   ❌ Erro na validação em lote: {response.status_code}")

    print(f"\n✅ Teste de validação concluído!")
    print(f"🌐 Documentação: {BASE_URL}/docs")

if __name__ == "__main__":
    try:
        test_discovery_and_validation()
    except requests.exceptions.ConnectionError:
        print("❌ Sistema offline. Execute: docker-compose up -d")
    except Exception as e:
        print(f"❌ Erro: {e}")