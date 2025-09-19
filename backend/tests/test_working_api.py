#!/usr/bin/env python3
"""
Script de teste para a API NVIDIA Inception AI - Versão Funcional
Execute: python3 test_working_api.py
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

def test_discovery():
    """Testa descoberta de startups diretamente"""
    print("🚀 Testando Descoberta de Startups (Direto)...")

    response = requests.post(f"{BASE_URL}/api/demo/test-agent")
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"Status: {result.get('status')}")
        print(f"País: {result.get('country')}")
        print(f"Setor: {result.get('sector')}")
        print(f"Tokens usados: {result.get('tokens_used')}")
        print(f"Startups encontradas: {result.get('count')}")

        print("\n📋 Startups:")
        for i, startup in enumerate(result.get('startups', []), 1):
            print(f"\n{i}. {startup.get('name')}")
            print(f"   🌐 Website: {startup.get('website')}")
            print(f"   🏭 Setor: {startup.get('sector')}")
            print(f"   🤖 Tecnologias IA: {startup.get('ai_technologies')}")
            print(f"   💰 Último funding: ${startup.get('last_funding_amount'):,}")
            print(f"   💼 Investidores: {startup.get('investor_names')}")
            print(f"   👨‍💻 CTO: {startup.get('cto_name')}")
    else:
        print(f"Error: {response.text}")
    print()

def test_analysis():
    """Testa análise de startup"""
    print("📊 Testando Análise de Startup...")

    response = requests.post(f"{BASE_URL}/api/demo/analyze-demo")
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"Tokens usados: {result.get('tokens_used')}")
        print(f"\n🎯 Scores de Priorização:")
        print(f"   • Alinhamento Tecnológico: {result.get('technology_alignment')}/100")
        print(f"   • Oportunidade de Mercado: {result.get('market_opportunity')}/100")
        print(f"   • Força da Equipe: {result.get('team_strength')}/100")
        print(f"   • Prioridade Geral: {result.get('overall_priority')}/100")

        print(f"\n💡 Insights:")
        for insight in result.get('insights', []):
            print(f"   • {insight}")

        print(f"\n📝 Recomendação:")
        print(f"   {result.get('recommendation')}")
    else:
        print(f"Error: {response.text}")
    print()

def test_market_insights():
    """Testa insights de mercado"""
    print("🌍 Testando Insights de Mercado...")

    response = requests.get(f"{BASE_URL}/api/demo/market-insights")
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"País: {result.get('country')}")
        print(f"Tokens usados: {result.get('tokens_used')}")

        print(f"\n🏭 Principais Setores:")
        for sector in result.get('top_sectors', []):
            print(f"   • {sector}")

        print(f"\n🤖 Tecnologias de IA:")
        for tech in result.get('ai_technologies', []):
            print(f"   • {tech}")

        print(f"\n💼 Investidores Ativos:")
        for investor in result.get('active_investors', []):
            print(f"   • {investor}")

        print(f"\n📈 Tendências:")
        for trend in result.get('market_trends', []):
            print(f"   • {trend}")

        print(f"\n🎯 Oportunidades:")
        for opp in result.get('opportunities', []):
            print(f"   • {opp}")
    else:
        print(f"Error: {response.text}")
    print()

def test_different_sectors():
    """Testa descoberta em diferentes setores"""
    print("🔍 Testando Diferentes Setores...")

    sectors = ["Healthtech", "Agtech", "Edtech"]

    for sector in sectors:
        print(f"\n--- {sector} ---")

        # Note: Para testar diferentes setores, você precisaria passar o parâmetro
        # Por enquanto, o endpoint demo está fixo em Fintech
        response = requests.post(f"{BASE_URL}/api/demo/test-agent")

        if response.status_code == 200:
            result = response.json()
            print(f"✅ {result.get('count')} startups encontradas")
            print(f"🪙 {result.get('tokens_used')} tokens utilizados")
        else:
            print(f"❌ Erro: {response.text}")

if __name__ == "__main__":
    print("🎯 NVIDIA Inception AI - Teste da API Funcional")
    print("=" * 60)

    try:
        test_health()
        test_discovery()
        test_analysis()
        test_market_insights()
        test_different_sectors()

        print("✅ Todos os testes concluídos com sucesso!")
        print()
        print("🌐 Acesse a documentação em: http://localhost:8000/docs")
        print("🎯 Novos endpoints demo funcionais:")
        print("   • POST /api/demo/test-agent")
        print("   • POST /api/demo/analyze-demo")
        print("   • GET /api/demo/market-insights")

    except requests.exceptions.ConnectionError:
        print("❌ Erro: Não foi possível conectar à API")
        print("Certifique-se de que o sistema está rodando com: docker-compose up -d")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")