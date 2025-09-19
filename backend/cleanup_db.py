#!/usr/bin/env python3
"""
Script para limpar banco de dados removendo startups inválidas
"""

import sys
sys.path.append('/app')

import requests
from agents.validation_agent import StartupValidationAgent
from services.startup_service import StartupService
from database.connection import get_db

def cleanup_database():
    """Limpa o banco removendo startups inválidas"""

    print("🧹 Iniciando limpeza do banco de dados...")

    # Get database session
    db = next(get_db())
    startup_service = StartupService(db)
    validator = StartupValidationAgent()

    # Get all startups
    startups = startup_service.get_startups(limit=1000)
    print(f"📊 {len(startups)} startups encontradas no banco")

    invalid_startups = []
    total_tokens = 0

    for startup in startups:
        print(f"\n🔍 Validando: {startup.name}")

        # Convert to dict for validation
        startup_data = {
            "name": startup.name,
            "website": str(startup.website) if startup.website else None,
            "sector": startup.sector,
            "founded_year": startup.founded_year,
            "country": startup.country,
            "city": startup.city,
            "description": startup.description,
            "ai_technologies": startup.ai_technologies,
            "last_funding_amount": startup.last_funding_amount,
            "investor_names": startup.investor_names,
            "ceo_name": startup.ceo_name,
            "ceo_linkedin": startup.ceo_linkedin,
            "cto_name": startup.cto_name,
            "cto_linkedin": startup.cto_linkedin,
            "has_venture_capital": startup.has_venture_capital
        }

        # Validate
        validation = validator.validate_startup_info(startup_data)
        total_tokens += validation.get("tokens_used", 0)

        print(f"   Status: {validation['validation_status']}")
        print(f"   Confiança: {validation['confidence_score']:.2f}")

        # Mark for removal if invalid or company doesn't exist
        if (validation['validation_status'] == 'invalid' or
            validation.get('company_exists') == False or
            validation['confidence_score'] < 0.3):

            invalid_startups.append({
                "id": startup.id,
                "name": startup.name,
                "reason": validation.get('issues_found', ['Low confidence'])
            })
            print(f"   ❌ Marcada para remoção")
        else:
            print(f"   ✅ Mantida")

    # Show summary
    print(f"\n📊 RESUMO DA LIMPEZA:")
    print(f"   • Total startups analisadas: {len(startups)}")
    print(f"   • Startups inválidas encontradas: {len(invalid_startups)}")
    print(f"   • Tokens utilizados: {total_tokens}")

    if invalid_startups:
        print(f"\n❌ Startups marcadas para remoção:")
        for startup in invalid_startups:
            print(f"   • {startup['name']} (ID: {startup['id']})")
            print(f"     Motivo: {startup['reason'][:100]}...")

        # Ask for confirmation
        confirm = input(f"\n⚠️  Deseja remover {len(invalid_startups)} startups inválidas? (y/N): ")

        if confirm.lower() == 'y':
            removed_count = 0
            for startup in invalid_startups:
                success = startup_service.delete_startup(startup['id'])
                if success:
                    removed_count += 1
                    print(f"   ✅ {startup['name']} removida")
                else:
                    print(f"   ❌ Erro ao remover {startup['name']}")

            print(f"\n✅ Limpeza concluída! {removed_count} startups removidas.")
        else:
            print("   Limpeza cancelada.")
    else:
        print(f"\n✅ Nenhuma startup inválida encontrada!")

    db.close()

if __name__ == "__main__":
    cleanup_database()