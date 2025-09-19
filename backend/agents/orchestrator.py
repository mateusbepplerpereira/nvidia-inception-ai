from typing import Dict, Any, List, TypedDict
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor
import requests
import json
import os
from urllib.parse import urlparse
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class OrchestrationState(TypedDict):
    """Estado compartilhado entre todos os agentes"""
    # Dados de entrada
    country: str
    sector: str
    limit: int

    # Contexto de startups já processadas
    valid_startups: List[Dict[str, Any]]
    invalid_startups: List[Dict[str, Any]]

    # Resultados de cada agente
    discovered_startups: List[Dict[str, Any]]
    validated_startups: List[Dict[str, Any]]
    startup_metrics: List[Dict[str, Any]]

    # Metadados
    total_tokens: int
    processing_time: float
    current_step: str
    errors: List[str]


class StartupOrchestrator:
    """Orquestrador LangGraph para pipeline de agentes"""

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

        # Construir grafo
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Constrói o grafo de orquestração"""
        workflow = StateGraph(OrchestrationState)

        # Adicionar nodes
        workflow.add_node("discovery", self._discovery_agent)
        workflow.add_node("validation", self._validation_agent)
        workflow.add_node("metrics", self._metrics_agent)
        workflow.add_node("finalize", self._finalize_results)

        # Definir fluxo
        workflow.set_entry_point("discovery")
        workflow.add_edge("discovery", "validation")
        workflow.add_edge("validation", "metrics")
        workflow.add_edge("metrics", "finalize")
        workflow.add_edge("finalize", END)

        return workflow.compile()

    def _discovery_agent(self, state: OrchestrationState) -> OrchestrationState:
        """Agente de descoberta com contexto de startups já processadas"""
        state["current_step"] = "discovery"

        # Criar contexto de exclusão
        exclusion_context = ""
        if state.get("valid_startups"):
            valid_names = [s["name"] for s in state["valid_startups"]]
            exclusion_context += f"\nNÃO incluir estas startups válidas já encontradas: {valid_names}"

        if state.get("invalid_startups"):
            invalid_names = [s["name"] for s in state["invalid_startups"]]
            exclusion_context += f"\nNÃO incluir estas startups inválidas: {invalid_names}"

        prompt = f"""Como especialista no ecossistema de startups da América Latina, liste EXATAMENTE {state['limit']} startups de IA em {state['country']} que receberam investimento de Venture Capital.

{f'Setor específico: {state["sector"]}' if state.get("sector") else 'Todos os setores de IA'}

{exclusion_context}

IMPORTANTE:
- Retorne EXATAMENTE {state['limit']} startups, nem mais nem menos
- Busque startups DIFERENTES das já listadas no contexto
- Priorize startups reais e verificáveis

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
    "country": "{state['country']}",
    "city": "Cidade principal",
    "description": "Breve descrição da startup e sua solução de IA",
    "has_venture_capital": true
  }}
]

Retorne apenas o array JSON, sem texto adicional."""

        try:
            result = self._make_openai_request(prompt)
            if "error" in result:
                state["errors"].append(f"Discovery error: {result['error']}")
                state["discovered_startups"] = []
                return state

            # Parse JSON response
            content = result["content"].strip()
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            elif content.startswith("```"):
                content = content.replace("```", "", 1).replace("```", "").strip()

            startups = json.loads(content)

            # Garantir que temos exatamente o limite especificado
            if len(startups) > state['limit']:
                startups = startups[:state['limit']]

            state["discovered_startups"] = startups
            state["total_tokens"] += result.get("tokens_used", 0)

            logger.info(f"Discovery agent encontrou {len(startups)} startups")

        except json.JSONDecodeError as e:
            error_msg = f"JSON parse error in discovery: {str(e)}"
            state["errors"].append(error_msg)
            state["discovered_startups"] = []
            logger.error(error_msg)
        except Exception as e:
            error_msg = f"Discovery agent error: {str(e)}"
            state["errors"].append(error_msg)
            state["discovered_startups"] = []
            logger.error(error_msg)

        return state

    def _validation_agent(self, state: OrchestrationState) -> OrchestrationState:
        """Agente de validação com insights detalhados"""
        state["current_step"] = "validation"
        validated_startups = []

        for startup in state.get("discovered_startups", []):
            validation_result = self._validate_startup_thoroughly(startup)

            # SEMPRE salvar startup, mas marcar se é válida ou inválida
            startup["validation"] = validation_result
            startup["is_valid"] = validation_result["is_valid"]

            if validation_result["is_valid"]:
                validated_startups.append(startup)
            else:
                # Gerar insight detalhado do porque é inválida
                validation_insight = self._generate_validation_insight(startup, validation_result)

                invalid_startup = {
                    "name": startup["name"],
                    "website": startup.get("website"),
                    "sector": startup.get("sector"),
                    "ceo_name": startup.get("ceo_name"),
                    "cto_name": startup.get("cto_name"),
                    "ceo_linkedin": startup.get("ceo_linkedin"),
                    "cto_linkedin": startup.get("cto_linkedin"),
                    "reason": validation_result.get("reason", "Validation failed"),
                    "issues": validation_result.get("issues", []),
                    "validation_insight": validation_insight["insight"],
                    "confidence_level": validation_insight["confidence"],
                    "recommendation": validation_insight["recommendation"],
                    "full_validation_data": validation_result
                }

                if "invalid_startups" not in state:
                    state["invalid_startups"] = []
                state["invalid_startups"].append(invalid_startup)

                # Adicionar tokens usados na geração do insight
                state["total_tokens"] += validation_insight.get("tokens_used", 0)

        state["validated_startups"] = validated_startups
        state["total_tokens"] += sum([s.get("validation", {}).get("tokens_used", 0) for s in validated_startups])

        logger.info(f"Validation agent: {len(validated_startups)} válidas, {len(state.get('invalid_startups', []))} inválidas")

        return state

    def _metrics_agent(self, state: OrchestrationState) -> OrchestrationState:
        """Agente de métricas e scoring"""
        state["current_step"] = "metrics"
        startup_metrics = []

        for startup in state.get("validated_startups", []):
            metrics = self._calculate_startup_metrics(startup)
            startup["metrics"] = metrics
            startup_metrics.append({
                "startup": startup,
                "metrics": metrics
            })
            state["total_tokens"] += metrics.get("tokens_used", 0)

        # Ordenar por score total
        startup_metrics.sort(key=lambda x: x["metrics"]["total_score"], reverse=True)

        state["startup_metrics"] = startup_metrics

        logger.info(f"Metrics agent processou {len(startup_metrics)} startups")

        return state

    def _finalize_results(self, state: OrchestrationState) -> OrchestrationState:
        """Finalizar e estruturar resultados"""
        state["current_step"] = "completed"

        # Calcular tempo de processamento se não foi definido
        if "processing_time" not in state:
            state["processing_time"] = 0.0

        logger.info(f"Orquestração finalizada: {len(state.get('startup_metrics', []))} startups processadas")

        return state

    def _validate_startup_thoroughly(self, startup: Dict[str, Any]) -> Dict[str, Any]:
        """Validação rigorosa de startup com scoring detalhado"""
        issues = []
        validation_scores = {}

        # Validar website
        website_valid = self._validate_website(startup.get("website"))
        validation_scores["website_score"] = 100 if website_valid else 0
        if not website_valid:
            issues.append("Website inacessível ou inválido")

        # Validar LinkedIn profiles
        ceo_linkedin_valid = self._validate_linkedin_profile(
            startup.get("ceo_linkedin"),
            startup.get("ceo_name")
        )
        cto_linkedin_valid = self._validate_linkedin_profile(
            startup.get("cto_linkedin"),
            startup.get("cto_name")
        )

        validation_scores["ceo_linkedin_score"] = 100 if ceo_linkedin_valid else 0
        validation_scores["cto_linkedin_score"] = 100 if cto_linkedin_valid else 0

        if not ceo_linkedin_valid:
            issues.append("LinkedIn do CEO inválido ou não encontrado")
        if not cto_linkedin_valid:
            issues.append("LinkedIn do CTO inválido ou não encontrado")

        # Calcular score total de validação (sem validação de existência por IA)
        total_validation_score = sum(validation_scores.values()) / len(validation_scores)

        # Determinar se é válida (critérios mais flexíveis)
        is_valid = (
            total_validation_score >= 60 and  # Score mínimo reduzido para 60%
            (website_valid or (ceo_linkedin_valid and cto_linkedin_valid))  # Website OU LinkedIn válidos
        )

        return {
            "is_valid": is_valid,
            "total_validation_score": total_validation_score,
            "website_valid": website_valid,
            "ceo_linkedin_valid": ceo_linkedin_valid,
            "cto_linkedin_valid": cto_linkedin_valid,
            "validation_scores": validation_scores,
            "issues": issues,
            "reason": "; ".join(issues) if issues else "Valid",
            "tokens_used": 0
        }

    def _generate_validation_insight(self, startup: Dict[str, Any], validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Gera insight detalhado sobre porque a startup foi invalidada"""
        prompt = f"""
        Analise porque esta startup foi marcada como INVÁLIDA e forneça insights acionáveis:

        STARTUP: {startup.get('name')}
        Website: {startup.get('website')}
        CEO: {startup.get('ceo_name')} - LinkedIn: {startup.get('ceo_linkedin')}
        CTO: {startup.get('cto_name')} - LinkedIn: {startup.get('cto_linkedin')}
        Setor: {startup.get('sector')}

        RESULTADOS DA VALIDAÇÃO:
        - Website funcionando: {'✅' if validation_result.get('website_valid') else '❌'}
        - LinkedIn CEO válido: {'✅' if validation_result.get('ceo_linkedin_valid') else '❌'}
        - LinkedIn CTO válido: {'✅' if validation_result.get('cto_linkedin_valid') else '❌'}
        - Score total: {validation_result.get('total_validation_score', 0):.1f}%
        - Issues encontrados: {validation_result.get('issues', [])}

        Forneça uma análise DETALHADA em JSON:
        {{
            "insight": "Explicação clara e detalhada dos problemas encontrados",
            "confidence": 0.XX,
            "main_issues": ["issue1", "issue2"],
            "potential_fixes": ["como corrigir issue1", "como corrigir issue2"],
            "recommendation": "REJECT/INVESTIGATE/MANUAL_REVIEW",
            "analysis": {{
                "website_analysis": "análise específica do website",
                "linkedin_analysis": "análise dos perfis LinkedIn",
                "existence_analysis": "análise da existência da empresa",
                "data_quality": "qualidade geral dos dados fornecidos"
            }}
        }}
        """

        try:
            result = self._make_openai_request(prompt, max_tokens=800)
            if "error" in result:
                return self._default_validation_insight(validation_result)

            insight_data = json.loads(result["content"].strip())
            insight_data["tokens_used"] = result.get("tokens_used", 0)
            return insight_data

        except Exception as e:
            logger.error(f"Erro ao gerar insight de validação: {e}")
            return self._default_validation_insight(validation_result)

    def _default_validation_insight(self, validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Insight padrão quando a IA falha"""
        return {
            "insight": f"Startup invalidada devido a: {validation_result.get('reason', 'Problemas de validação')}",
            "confidence": 0.5,
            "main_issues": validation_result.get("issues", ["Validação falharam"]),
            "potential_fixes": ["Verificar dados manualmente", "Validar fontes de informação"],
            "recommendation": "MANUAL_REVIEW",
            "analysis": {
                "website_analysis": "Website não acessível ou URL incorreta",
                "linkedin_analysis": "Perfis LinkedIn não validados ou URLs incorretas",
                "data_quality": "Dados podem conter URLs incorretas ou informações desatualizadas"
            },
            "tokens_used": 0
        }

    def _normalize_url(self, url: str) -> str:
        """Normaliza URL removendo acentos e caracteres especiais"""
        if not url:
            return url

        # Remover acentos comuns
        url = url.replace('ê', 'e').replace('é', 'e').replace('ã', 'a').replace('ç', 'c')
        url = url.replace('á', 'a').replace('à', 'a').replace('ó', 'o').replace('í', 'i')
        url = url.replace('ú', 'u').replace('ô', 'o').replace('â', 'a').replace('õ', 'o')

        return url

    def _validate_website(self, url: str) -> bool:
        """Validar se website existe e é acessível com URLs normalizadas"""
        if not url:
            return False

        urls_to_try = [
            url,  # URL original
            self._normalize_url(url),  # URL normalizada
        ]

        # Se não tem protocolo, adicionar https
        if not url.startswith(('http://', 'https://')):
            urls_to_try.extend([
                f"https://{url}",
                f"https://{self._normalize_url(url)}",
                f"http://{url}",
                f"http://{self._normalize_url(url)}"
            ])

        for test_url in urls_to_try:
            try:
                response = requests.get(test_url, timeout=8, allow_redirects=True)
                if response.status_code in [200, 301, 302]:
                    return True
            except:
                continue

        return False

    def _validate_linkedin_profile(self, linkedin_url: str, person_name: str) -> bool:
        """Validar perfil LinkedIn"""
        if not linkedin_url or not person_name:
            return False

        try:
            parsed = urlparse(str(linkedin_url))
            if "linkedin.com" not in parsed.netloc:
                return False

            if "/in/" not in parsed.path:
                return False

            # Fazer request básico
            response = requests.get(str(linkedin_url), timeout=5, allow_redirects=True)
            return response.status_code in [200, 999]  # 999 = LinkedIn bot detection

        except:
            return False


    def _calculate_startup_metrics(self, startup: Dict[str, Any]) -> Dict[str, Any]:
        """Calcular métricas de score para a startup"""
        prompt = f"""
        Analise esta startup validada e calcule scores de 0-100 para as métricas:

        STARTUP: {startup.get('name')}
        Setor: {startup.get('sector')}
        Tecnologias IA: {startup.get('ai_technologies')}
        CEO: {startup.get('ceo_name')}
        CTO: {startup.get('cto_name')}
        Funding: ${startup.get('last_funding_amount', 0):,}
        Investidores: {startup.get('investor_names')}

        CALCULE SCORES (0-100):
        1. MARKET_DEMAND: Demanda do mercado (setor em alta, tecnologias relevantes)
        2. TECHNICAL_LEVEL: Nível técnico (baseado em CTO e tecnologias)
        3. PARTNERSHIP_POTENTIAL: Potencial de parceria (funding, investidores, tração)

        RETORNE APENAS JSON:
        {{
            "market_demand_score": XX,
            "technical_level_score": XX,
            "partnership_potential_score": XX,
            "total_score": XX,
            "reasoning": {{
                "market": "justificativa",
                "technical": "justificativa",
                "partnership": "justificativa"
            }}
        }}
        """

        try:
            result = self._make_openai_request(prompt, max_tokens=500)
            if "error" in result:
                return self._default_metrics()

            metrics = json.loads(result["content"].strip())

            # Calcular total_score se não foi fornecido
            if "total_score" not in metrics:
                metrics["total_score"] = (
                    metrics.get("market_demand_score", 0) * 0.4 +
                    metrics.get("technical_level_score", 0) * 0.3 +
                    metrics.get("partnership_potential_score", 0) * 0.3
                )

            metrics["tokens_used"] = result.get("tokens_used", 0)
            return metrics

        except:
            return self._default_metrics()

    def _default_metrics(self) -> Dict[str, Any]:
        """Métricas padrão em caso de erro"""
        return {
            "market_demand_score": 50,
            "technical_level_score": 50,
            "partnership_potential_score": 50,
            "total_score": 50,
            "reasoning": {"error": "Failed to calculate metrics"},
            "tokens_used": 0
        }

    def _make_openai_request(self, prompt: str, max_tokens: int = 3000) -> Dict[str, Any]:
        """Fazer requisição para OpenAI"""
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.1
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
                return {
                    "content": result["choices"][0]["message"]["content"],
                    "tokens_used": result["usage"]["total_tokens"]
                }
            else:
                return {"error": f"API Error: {response.status_code}"}

        except Exception as e:
            return {"error": f"Request error: {str(e)}"}

    def run_orchestration(self, country: str, sector: str = None, limit: int = 5,
                         existing_valid: List = None, existing_invalid: List = None) -> Dict[str, Any]:
        """Executar orquestração completa"""

        initial_state = OrchestrationState(
            country=country,
            sector=sector,
            limit=limit,
            valid_startups=existing_valid or [],
            invalid_startups=existing_invalid or [],
            discovered_startups=[],
            validated_startups=[],
            startup_metrics=[],
            total_tokens=0,
            processing_time=0.0,
            current_step="starting",
            errors=[]
        )

        start_time = datetime.now()

        try:
            # Executar grafo
            final_state = self.graph.invoke(initial_state)

            end_time = datetime.now()
            final_state["processing_time"] = (end_time - start_time).total_seconds()

            return {
                "status": "success",
                "country": country,
                "sector": sector,
                "limit": limit,
                "results": {
                    "discovered_count": len(final_state.get("discovered_startups", [])),
                    "validated_count": len(final_state.get("validated_startups", [])),
                    "invalid_count": len(final_state.get("invalid_startups", [])),
                    "startup_metrics": final_state.get("startup_metrics", []),
                    "invalid_startups": final_state.get("invalid_startups", [])
                },
                "tokens_used": final_state.get("total_tokens", 0),
                "processing_time": final_state.get("processing_time", 0),
                "errors": final_state.get("errors", [])
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "tokens_used": initial_state.get("total_tokens", 0),
                "processing_time": (datetime.now() - start_time).total_seconds()
            }