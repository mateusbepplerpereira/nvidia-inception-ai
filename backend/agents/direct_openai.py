import requests
import json
import os
from typing import Dict, Any

class DirectOpenAIAgent:
    """Agente usando requests direto para OpenAI API"""

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY não encontrada")

        self.base_url = "https://api.openai.com/v1/chat/completions"
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def _make_request(self, prompt: str, max_tokens: int = 3000) -> Dict[str, Any]:
        """Faz requisição direta para OpenAI"""
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.3
        }

        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                tokens_used = result["usage"]["total_tokens"]
                return {"content": content, "tokens_used": tokens_used}
            else:
                return {"error": f"OpenAI API error: {response.status_code} - {response.text}"}

        except Exception as e:
            return {"error": f"Request error: {str(e)}"}

    def discover_startups(self, country: str = "Brazil", sector: str = None, limit: int = 5) -> Dict[str, Any]:
        """Descobre startups usando OpenAI"""

        prompt = f"""Como especialista no ecossistema de startups da América Latina, liste {limit} startups de IA em {country} que receberam investimento de Venture Capital.

{f'Setor específico: {sector}' if sector else 'Todos os setores de IA'}

Para cada startup, retorne APENAS um JSON válido com este formato:
[
  {{
    "name": "Nome da Startup",
    "website": "https://website.com",
    "sector": "Setor",
    "ai_technologies": ["Computer Vision", "NLP"],
    "founded_year": 2020,
    "last_funding_amount": 50000000,
    "investor_names": ["Investidor 1", "Investidor 2"],
    "ceo_name": "Nome do CEO",
    "ceo_linkedin": "https://linkedin.com/in/ceo",
    "cto_name": "Nome do CTO",
    "cto_linkedin": "https://linkedin.com/in/cto",
    "country": "{country}",
    "city": "Cidade principal",
    "description": "Breve descrição da startup e sua solução de IA",
    "has_venture_capital": true
  }}
]

IMPORTANTE:
- Priorize SEMPRE LinkedIn sobre GitHub ou outros perfis
- Inclua CEO e CTO quando disponíveis
- Seja preciso com valores de funding (em USD)
- Verifique se realmente usam IA
- Apenas startups que receberam VC

Retorne apenas o array JSON, sem texto adicional."""

        result = self._make_request(prompt)

        if "error" in result:
            return {"status": "error", "error": result["error"]}

        try:
            # Tenta extrair JSON da resposta
            content = result["content"].strip()

            # Remove markdown se existir
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            elif content.startswith("```"):
                content = content.replace("```", "", 1).replace("```", "").strip()

            startups = json.loads(content)

            return {
                "status": "success",
                "country": country,
                "sector": sector,
                "startups": startups,
                "count": len(startups),
                "tokens_used": result["tokens_used"]
            }

        except json.JSONDecodeError as e:
            return {
                "status": "error",
                "error": f"JSON parse error: {str(e)}",
                "raw_response": result.get("content", "")
            }

    def analyze_startup(self, startup_data: Dict) -> Dict[str, Any]:
        """Analisa uma startup específica"""

        prompt = f"""Analise esta startup para o programa NVIDIA Inception:

{json.dumps(startup_data, indent=2)}

Critérios (0-100):
1. Alinhamento com NVIDIA (GPU/AI)
2. Oportunidade de mercado
3. Força da equipe técnica
4. Prioridade geral

Retorne apenas este JSON:
{{
  "technology_alignment": 85,
  "market_opportunity": 78,
  "team_strength": 82,
  "overall_priority": 81,
  "insights": ["insight 1", "insight 2", "insight 3"],
  "recommendation": "Recomendação em 1-2 frases"
}}"""

        result = self._make_request(prompt, max_tokens=800)

        if "error" in result:
            return {"error": result["error"]}

        try:
            content = result["content"].strip()
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            elif content.startswith("```"):
                content = content.replace("```", "", 1).replace("```", "").strip()

            analysis = json.loads(content)
            analysis["tokens_used"] = result["tokens_used"]
            return analysis

        except json.JSONDecodeError as e:
            return {
                "error": f"JSON parse error: {str(e)}",
                "raw_response": result.get("content", "")
            }

    def get_market_insights(self, country: str = "Brazil") -> Dict[str, Any]:
        """Análise geral do mercado"""

        prompt = f"""Como analista do ecossistema de startups de IA em {country}, forneça insights sobre:

1. Principais setores com startups de IA
2. Tecnologias de IA mais usadas
3. Principais investidores ativos
4. Tendências e oportunidades

Retorne apenas este JSON:
{{
  "top_sectors": ["Fintech", "Healthtech", "Agtech"],
  "ai_technologies": ["Machine Learning", "Computer Vision", "NLP"],
  "active_investors": ["Investor 1", "Investor 2", "Investor 3"],
  "market_trends": ["Trend 1", "Trend 2", "Trend 3"],
  "opportunities": ["Oportunidade 1", "Oportunidade 2"]
}}"""

        result = self._make_request(prompt, max_tokens=1000)

        if "error" in result:
            return {"error": result["error"]}

        try:
            content = result["content"].strip()
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            elif content.startswith("```"):
                content = content.replace("```", "", 1).replace("```", "").strip()

            insights = json.loads(content)
            insights["country"] = country
            insights["tokens_used"] = result["tokens_used"]
            return insights

        except json.JSONDecodeError as e:
            return {
                "error": f"JSON parse error: {str(e)}",
                "raw_response": result.get("content", "")
            }