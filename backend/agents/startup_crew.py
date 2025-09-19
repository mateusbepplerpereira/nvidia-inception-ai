# Importa o agente que funciona
from .direct_openai import DirectOpenAIAgent
from typing import Dict, Any

class StartupDiscoveryCrew:
    """Wrapper para compatibilidade - agora usa agente direto"""

    def __init__(self):
        self.agent = DirectOpenAIAgent()

    # Métodos de compatibilidade removidos - agora usa agente simples

    def discover_startups(self, country: str = "Brazil", sector: str = None, limit: int = 10) -> Dict[str, Any]:
        """Usa o agente simples para descobrir startups"""
        return self.agent.discover_startups(country, sector, limit)

    def analyze_single_startup(self, startup_data: Dict) -> Dict[str, Any]:
        """Usa o agente simples para analisar startup"""
        return self.agent.analyze_startup(startup_data)

    def get_market_insights(self, country: str = "Brazil") -> Dict[str, Any]:
        """Obter insights de mercado"""
        return self.agent.get_market_insights(country)