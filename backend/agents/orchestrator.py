from typing import Dict, Any, List, TypedDict
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor
import requests
import json
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class OrchestrationState(TypedDict):
    """Estado compartilhado entre todos os agentes"""
    # Dados de entrada
    country: str
    sector: str
    limit: int
    search_strategy: str

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
        # Sempre usar modelo do env - deve ser gpt-4o-mini-search-preview para WebSearch
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini-search-preview")
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
        workflow.add_node("source_validation", self._source_validation_agent)
        workflow.add_node("validation", self._validation_agent)
        workflow.add_node("metrics", self._metrics_agent)
        workflow.add_node("finalize", self._finalize_results)

        # Definir fluxo
        workflow.set_entry_point("discovery")
        workflow.add_edge("discovery", "source_validation")
        workflow.add_edge("source_validation", "validation")
        workflow.add_edge("validation", "metrics")
        workflow.add_edge("metrics", "finalize")
        workflow.add_edge("finalize", END)

        return workflow.compile()

    def _discovery_agent(self, state: OrchestrationState) -> OrchestrationState:
        """Agente de descoberta usando WebSearch nativo"""
        logger.info("*** DISCOVERY AGENT CHAMADO ***")
        state["current_step"] = "discovery"

        # Criar contexto de exclusão
        exclusion_context = ""
        if state.get("valid_startups"):
            valid_names = [s["name"] for s in state["valid_startups"]]
            exclusion_context += f"\nNÃO incluir estas startups já encontradas: {valid_names}"

        if state.get("invalid_startups"):
            invalid_names = [s["name"] for s in state["invalid_startups"]]
            exclusion_context += f"\nNÃO incluir estas startups inválidas: {invalid_names}"

        # Definir query e restrições baseadas na estratégia de busca
        search_strategy = state.get('search_strategy', 'specific')

        if search_strategy == 'market_demand':
            # Busca por setores com alta demanda de mercado em país específico
            search_query = f"AI startups most demanded sectors {state.get('country', 'Latin America')} market trends venture capital 2024"
            sector_constraint = f"""
        ESTRATÉGIA: BUSCAR SETORES EMERGENTES E DE DEMANDA CRESCENTE EM {state.get('country', 'AMÉRICA LATINA')}
        - Identifique os 3-5 setores de IA com MAIOR demanda/investimento em {state.get('country', 'América Latina')}
        - Foque em setores emergentes e de alto crescimento específicos da região
        - Priorize startups em setores como: FinTech, AI, Educação, Agro
        - Diversifique entre diferentes setores promissores para a região
        - NÃO se limite a um setor específico - explore a demanda regional do mercado
        """

        elif search_strategy == 'global_market_demand':
            # Busca global por setores com alta demanda de mercado
            search_query = "AI startups most demanded sectors global market trends venture capital Latin America 2024"
            sector_constraint = """
        ESTRATÉGIA: BUSCA GLOBAL POR SETORES EMERGENTES E DE ALTA DEMANDA
        - Identifique os setores de IA com MAIOR demanda/investimento GLOBALMENTE
        - Foque em setores emergentes e de alto crescimento mundial
        - Priorize startups em setores como: FinTech, AI, Educação, Agro
        - Diversifique entre diferentes setores promissores globalmente
        - Aceite startups de qualquer país, mas priorize América Latina quando possível
        - NÃO se limite a um setor específico - explore a demanda GLOBAL do mercado
        """

        elif search_strategy == 'global':
            # Busca global sem limitação geográfica
            if state.get('country') and state.get('country') != '':
                search_query = f"AI startups {state.get('country', '')} {state.get('sector', '')} global market venture capital funding 2024".strip()
            else:
                search_query = f"AI startups {state.get('sector', '')} global market Latin America venture capital funding 2024".strip()

            sector_constraint = f"""
        ESTRATÉGIA: BUSCA GLOBAL SEM LIMITAÇÃO GEOGRÁFICA
        - Busque startups de IA em qualquer país, priorizando América Latina se aplicável
        - Aceite startups do mundo todo que tenham presença ou interesse na América Latina
        - Foque em startups com potencial de expansão global
        {f'- Setor específico: {state.get("sector")}' if state.get('sector') else '- Explore diversos setores de IA'}
        """

        else:  # search_strategy == 'specific'
            # Busca específica original
            if state.get('sector'):
                search_query = f"AI startups {state['sector']} {state.get('country', 'Brazil')} venture capital funding 2024"
                sector_constraint = f"""
        RESTRIÇÃO OBRIGATÓRIA DE SETOR:
        - APENAS startups do setor "{state['sector']}"
        - NÃO incluir startups de outros setores
        - Se for "fintech", APENAS fintechs
        - Se for "healthtech", APENAS healthtechs
        - Se for "agtech", APENAS agtechs
        - REJEITAR qualquer startup fora do setor especificado
        """
            else:
                search_query = f"AI startups {state.get('country', 'Brazil')} venture capital funding 2024"
                sector_constraint = ""

        # Contexto geográfico baseado na estratégia
        geographic_context = ""
        if search_strategy == 'global_market_demand':
            geographic_context = "globalmente por setores de alta demanda (priorizando América Latina)"
        elif search_strategy == 'global':
            geographic_context = "globalmente (priorizando América Latina quando aplicável)"
        elif search_strategy == 'market_demand':
            geographic_context = f"em {state.get('country', 'América Latina')} por setores emergentes"
        elif state.get('country'):
            geographic_context = f"em {state['country']}"
        else:
            geographic_context = "na América Latina"

        # Prompt otimizado para usar WebSearch
        prompt = f"""
        Use a ferramenta WebSearch para encontrar EXATAMENTE {state['limit']} startups de IA reais {geographic_context} que receberam funding de VC.

        QUERY PARA BUSCAR: "{search_query}"

        PRIORIDADE DE BUSCA (busque primeiro nessas fontes CONFIÁVEIS):
        1. FONTES PRIMÁRIAS: neofeed.com.br, brasiljorney.com.br, startup.com.br, crunchbase.com, techcrunch.com
        2. MÍDIA BRASILEIRA: valor.globo.com, exame.com, abstartups.com.br
        3. BASES DE DADOS: pitchbook.com, angellist.com
        4. Apenas se não encontrar suficientes, use outras fontes

        {sector_constraint}
        {exclusion_context}

        OBRIGATÓRIO - WEBSITE OFICIAL CORRETO:
        - BUSQUE na web: "nome_startup site oficial" ou "nome_startup website"
        - CONFIRME o domínio correto nas matérias e fontes confiáveis
        - Exemplos reais: "Creditec" → site é "https://soucreditec.com.br" (não creditec.com.br)
        - Exemplo: "Juvo" → site é "https://www.juvocredito.com.br" (não juvo.com.br)
        - SEMPRE verifique múltiplas fontes para confirmar o domínio correto
        - Se não encontrar o site oficial exato, NÃO INCLUA a startup

        Após a busca web, extraia APENAS startups reais com:
        1. Nome confirmado em fonte confiável
        2. Website OFICIAL encontrado na busca (não inventado)
        3. Funding verificado em fontes CONFIÁVEIS (Neofeed, BrasilJourney, etc.)
        4. Tecnologias AI específicas e detalhadas

        OBRIGATÓRIO - TECNOLOGIAS EM INGLÊS:
        - ai_technologies SEMPRE em inglês: ["Computer Vision", "Natural Language Processing", "Machine Learning"]
        - NÃO usar português: "Visão Computacional", "Processamento de Linguagem Natural"
        - Tecnologias específicas, não mercados: "Computer Vision" não "análise de dados financeiros"

        RETORNE JSON:
        [
          {{
            "name": "Nome Exato da Startup",
            "website": "https://site-oficial-confirmado-na-busca.com.br",
            "sector": "{state.get('sector') if state.get('sector') else 'AI/Technology'}",
            "ai_technologies": ["Computer Vision", "Natural Language Processing"],
            "founded_year": 2021,
            "last_funding_amount": 5000000,
            "investor_names": ["Nome do Investidor"],
            "country": "{state.get('country', 'Global')}",
            "city": "Cidade",
            "description": "Descrição da startup",
            "has_venture_capital": true,
            "sources": {{
              "funding": ["URL da fonte"],
              "validation": ["URL de confirmação"]
            }}
          }}
        ]
        """

        try:
            logger.info("=== INICIANDO DISCOVERY AGENT ===")
            result = self._make_openai_request_with_websearch(prompt)
            logger.info(f"=== RESULTADO RECEBIDO: {result} ===")

            if "error" in result:
                logger.error(f"Erro encontrado no resultado: {result['error']}")
                state["errors"].append(f"Discovery error: {result['error']}")
                state["discovered_startups"] = []
                return state

            # Parse JSON response
            logger.info(f"=== INICIANDO PARSE JSON ===")
            content = result.get("content", "")
            logger.info(f"=== CONTENT ORIGINAL: '{content}' ===")
            content = content.strip() if content else ""
            logger.info(f"Conteúdo bruto recebido: {content[:200]}...")
            logger.info(f"Tamanho do conteúdo: {len(content)}")

            if not content:
                logger.error("Conteúdo vazio recebido da API!")
                state["errors"].append("Conteúdo vazio recebido da OpenAI API")
                state["discovered_startups"] = []
                return state

            # Extrair JSON do conteúdo (pode ter texto antes e depois)
            if "```json" in content:
                # Encontrar o início do JSON
                json_start = content.find("```json") + len("```json")
                # Encontrar o fim do JSON
                json_end = content.find("```", json_start)
                if json_end != -1:
                    content = content[json_start:json_end].strip()
                else:
                    # Se não encontrar o fim, pegar tudo após ```json
                    content = content[json_start:].strip()
            elif "```" in content:
                # Tratar caso genérico de markdown
                json_start = content.find("```") + 3
                json_end = content.find("```", json_start)
                if json_end != -1:
                    content = content[json_start:json_end].strip()
                else:
                    content = content[json_start:].strip()

            logger.info(f"JSON extraído: {content[:200]}...")

            if not content:
                logger.error("Conteúdo vazio após limpeza de markdown!")
                state["errors"].append("Conteúdo vazio após limpeza")
                state["discovered_startups"] = []
                return state

            # Corrigir underscores em números para evitar erro de JSON
            import re
            content = re.sub(r'"last_funding_amount":\s*(\d+)_(\d+)', r'"last_funding_amount": \1\2', content)
            content = re.sub(r':(\s*)(\d+)_(\d+)', r':\1\2\3', content)
            logger.info(f"JSON corrigido (primeiros 200 chars): {content[:200]}...")

            startups = json.loads(content)

            # Garantir limite
            if len(startups) > state['limit']:
                startups = startups[:state['limit']]

            state["discovered_startups"] = startups
            state["total_tokens"] += result.get("tokens_used", 0)

            logger.info(f"Discovery agent encontrou {len(startups)} startups via WebSearch")

        except json.JSONDecodeError as e:
            error_msg = f"JSON parse error in discovery: {str(e)}"
            logger.error(f"=== JSON DECODE ERROR ===")
            logger.error(f"Erro: {str(e)}")
            logger.error(f"Content que causou erro: '{content if 'content' in locals() else 'CONTENT_NAO_DEFINIDO'}'")
            logger.error(f"Result completo: {result if 'result' in locals() else 'RESULT_NAO_DEFINIDO'}")
            state["errors"].append(error_msg)
            state["discovered_startups"] = []
        except Exception as e:
            error_msg = f"Discovery agent error: {str(e)}"
            logger.error(f"=== EXCEPTION GERAL ===")
            logger.error(f"Erro: {str(e)}")
            logger.error(f"Tipo do erro: {type(e)}")
            state["errors"].append(error_msg)
            state["discovered_startups"] = []

        return state

    def _make_openai_request_with_websearch(self, prompt: str, max_tokens: int = 2500) -> Dict[str, Any]:
        """Fazer requisição OpenAI com WebSearch usando estrutura correta"""

        # Usar sempre modelo do env (deve ser gpt-4o-mini-search-preview)
        payload = {
            "model": self.model,  # Modelo do env
            "web_search_options": {},  # Estrutura simples conforme OpenAI
            "messages": [
                {"role": "system", "content": "Você é um especialista em descobrir startups reais. Use busca web para encontrar informações atualizadas e precisas."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens
        }

        try:
            logger.info(f"Fazendo requisição WebSearch com modelo: {self.model}")
            logger.info(f"Payload enviado: {json.dumps(payload, indent=2)}")

            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=120  # Timeout maior para WebSearch
            )

            logger.info(f"Status da resposta: {response.status_code}")
            logger.info(f"Headers da resposta: {dict(response.headers)}")

            # Log da resposta bruta para debug
            response_text = response.text
            logger.info(f"Resposta bruta (primeiros 500 chars): {response_text[:500]}")

            if response.status_code == 200:
                result = response.json()
                logger.info(f"WebSearch concluído com sucesso usando {self.model}")

                # Log da estrutura da resposta
                logger.info(f"Estrutura da resposta: {list(result.keys())}")
                if "choices" in result and result["choices"]:
                    logger.info(f"Choices disponíveis: {len(result['choices'])}")
                    message_content = result["choices"][0]["message"]["content"]
                    logger.info(f"Conteúdo da mensagem (primeiros 200 chars): {message_content[:200] if message_content else 'VAZIO'}")
                else:
                    logger.error("Estrutura de choices não encontrada na resposta!")

                return {
                    "content": result["choices"][0]["message"]["content"] if result.get("choices") and result["choices"][0].get("message") else "",
                    "tokens_used": result.get("usage", {}).get("total_tokens", 0)
                }
            else:
                error_text = response.text[:500]
                logger.error(f"Erro WebSearch {response.status_code}: {error_text}")
                return {"error": f"WebSearch API Error: {response.status_code} - {error_text}"}

        except Exception as e:
            logger.error(f"Exceção na requisição WebSearch: {str(e)}")
            return {"error": f"WebSearch Request error: {str(e)}"}



    def _source_validation_agent(self, state: OrchestrationState) -> OrchestrationState:
        """Agente para validar fontes confiáveis de funding e investidores"""
        state["current_step"] = "source_validation"
        all_startups = []

        for startup in state.get("discovered_startups", []):
            source_validation = self._validate_startup_sources(startup)
            startup["source_validation"] = source_validation

            # SEMPRE manter a startup, independente da confiabilidade das fontes
            all_startups.append(startup)

            if source_validation["is_reliable"]:
                logger.info(f"Fontes validadas para {startup['name']}: {source_validation['reliability_score']:.1f}%")
            else:
                logger.info(f"Fontes não confiáveis para {startup['name']}: {source_validation['issues']} - mantendo startup")

        state["discovered_startups"] = all_startups
        reliable_count = len([s for s in all_startups if s.get("source_validation", {}).get("is_reliable", False)])
        logger.info(f"Source validation: {len(all_startups)} startups processadas ({reliable_count} com fontes confiáveis)")

        return state

    def _validate_startup_sources(self, startup: Dict[str, Any]) -> Dict[str, Any]:
        """Validar se as fontes fornecidas são confiáveis"""

        sources = startup.get("sources", {})
        reliability_score = 0
        issues = []
        validated_sources = {}

        # Fontes confiáveis conhecidas com weights (hierarquia de confiabilidade)
        trusted_sources = {
            # Bases de dados profissionais (peso máximo)
            "crunchbase": 30, "pitchbook": 30, "angellist": 25,

            # Mídia especializada internacional (peso alto)
            "techcrunch": 20, "venturebeat": 18, "bloomberg": 18, "forbes": 18,

            # Mídia brasileira confiável (peso alto)
            "neofeed": 25, "brasiljorney": 22, "startup.com.br": 20,
            "valor econômico": 18, "exame": 15, "folha": 15, "estadão": 15,

            # Organizações e hubs de startups brasileiros (peso médio-alto)
            "abstartups": 15, "distrito": 15, "startupi": 12, "baguete": 12,
            "startse": 12, "ecommercebrasil": 10, "tecmundo": 10,

            # Fontes setoriais especializadas (peso médio)
            "fintechbrasil": 12, "saúdebusiness": 10, "agtech": 10,

            # Sites oficiais e comunicados (peso médio)
            "site oficial": 12, "press release": 10, "linkedin company": 10,
            "comunicado oficial": 12, "portal da transparência": 15
        }

        # Validar funding sources
        funding_sources = sources.get("funding", [])
        funding_score = 0

        for source in funding_sources:
            source_lower = source.lower()
            for trusted, weight in trusted_sources.items():
                if trusted in source_lower:
                    funding_score += weight
                    break
            else:
                issues.append(f"Fonte de funding não reconhecida: {source}")

        validated_sources["funding"] = funding_sources
        funding_score = min(funding_score, 50)  # Máximo 50 pontos para funding

        # Validar investor sources
        investor_sources = sources.get("investors", [])
        investor_score = 0

        for source in investor_sources:
            source_lower = source.lower()
            for trusted, weight in trusted_sources.items():
                if trusted in source_lower:
                    investor_score += weight
                    break
            else:
                issues.append(f"Fonte de investidores não reconhecida: {source}")

        validated_sources["investors"] = investor_sources
        investor_score = min(investor_score, 30)  # Máximo 30 pontos para investors

        # Validar validation sources
        validation_sources = sources.get("validation", [])
        validation_score = 0

        for source in validation_sources:
            source_lower = source.lower()
            for trusted, weight in trusted_sources.items():
                if trusted in source_lower:
                    validation_score += weight
                    break

        validated_sources["validation"] = validation_sources
        validation_score = min(validation_score, 20)  # Máximo 20 pontos para validation

        # Score final
        reliability_score = funding_score + investor_score + validation_score

        # Critérios para ser considerado confiável
        is_reliable = (
            reliability_score >= 40 and  # Score mínimo de 40%
            len(funding_sources) >= 1 and  # Pelo menos 1 fonte de funding
            funding_score >= 15  # Pelo menos 15 pontos em funding sources
        )

        return {
            "is_reliable": is_reliable,
            "reliability_score": reliability_score,
            "funding_score": funding_score,
            "investor_score": investor_score,
            "validation_score": validation_score,
            "validated_sources": validated_sources,
            "issues": issues,
            "recommendation": "ACCEPT" if is_reliable else "INVESTIGATE_SOURCES"
        }

    def _validation_agent(self, state: OrchestrationState) -> OrchestrationState:
        """Agente de validação com insights detalhados"""
        state["current_step"] = "validation"
        validated_startups = []

        for startup in state.get("discovered_startups", []):
            validation_result = self._validate_startup_thoroughly(startup)

            # Se website não é válido, marcar como "Não encontrado"
            if not validation_result.get("website_valid", True):
                startup["website"] = "Não encontrado"

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

        # Validar fontes de funding
        funding_sources = startup.get("sources", {}).get("funding", [])
        if not funding_sources:
            issues.append("Sem fontes confiáveis para funding")
            validation_scores["funding_sources_score"] = 0
        else:
            validation_scores["funding_sources_score"] = 100

        # Calcular score total de validação
        total_validation_score = sum(validation_scores.values()) / len(validation_scores) if validation_scores else 0

        # Determinar se é válida (não invalidar apenas por website inacessível)
        # Startup é válida se tem dados básicos consistentes
        has_basic_data = (
            startup.get("name") and
            startup.get("sector") and
            startup.get("ai_technologies")
        )

        is_valid = has_basic_data  # Website inacessível não invalida a startup

        return {
            "is_valid": is_valid,
            "total_validation_score": total_validation_score,
            "website_valid": website_valid,
            "validation_scores": validation_scores,
            "issues": issues,
            "reason": "; ".join(issues) if issues else "Valid",
            "tokens_used": 0
        }

    def _generate_validation_insight(self, startup: Dict[str, Any], validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Gera insight detalhado sobre porque a startup foi invalidada"""

        # Otimização: Para casos simples de website inválido, usar insight padrão sem API
        issues = validation_result.get("issues", [])
        if len(issues) == 1 and any("Website" in issue or "website" in issue for issue in issues):
            logger.info(f"Usando insight padrão para {startup.get('name')} - problema simples de website")
            return self._default_validation_insight(validation_result)

        # Para casos mais complexos, usar IA
        prompt = f"""
        Analise porque esta startup foi marcada como INVÁLIDA e forneça insights acionáveis:

        STARTUP: {startup.get('name')}
        Website: {startup.get('website')}
        Setor: {startup.get('sector')}
        Tecnologias: {startup.get('ai_technologies')}
        Funding: ${startup.get('last_funding_amount', 0):,}
        Investidores: {startup.get('investor_names')}

        RESULTADOS DA VALIDAÇÃO:
        - Website funcionando: {'SIM' if validation_result.get('website_valid') else 'NÃO'}
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
                "funding_analysis": "análise das fontes de funding",
                "existence_analysis": "análise da existência da empresa",
                "data_quality": "qualidade geral dos dados fornecidos"
            }}
        }}
        """

        try:
            result = self._make_openai_request(prompt, max_tokens=800)
            if "error" in result:
                logger.warning(f"API error no insight de validação: {result['error']}")
                return self._default_validation_insight(validation_result)

            content = result.get("content", "").strip()
            if not content:
                logger.warning("Conteúdo vazio recebido para insight de validação")
                return self._default_validation_insight(validation_result)

            # Limpar markdown se presente
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            elif content.startswith("```"):
                content = content.replace("```", "", 1).replace("```", "").strip()

            if not content:
                logger.warning("Conteúdo vazio após limpeza de markdown")
                return self._default_validation_insight(validation_result)

            insight_data = json.loads(content)
            insight_data["tokens_used"] = result.get("tokens_used", 0)
            return insight_data

        except json.JSONDecodeError as e:
            logger.warning(f"JSON parsing falhou no insight de validação: {e}")
            logger.warning(f"Content recebido: '{content if 'content' in locals() else 'CONTENT_NAO_DEFINIDO'}'")
            return self._default_validation_insight(validation_result)
        except Exception as e:
            logger.warning(f"Não foi possível gerar insight de validação: {e}")
            return self._default_validation_insight(validation_result)

    def _default_validation_insight(self, validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Insight padrão quando não é possível gerar insight detalhado"""
        issues = validation_result.get("issues", [])
        reason = validation_result.get('reason', 'Problemas de validação')

        return {
            "insight": f"Não encontrado - Startup invalidada devido a: {reason}",
            "confidence": 0.5,
            "main_issues": issues if issues else ["Problemas de validação não especificados"],
            "potential_fixes": ["Verificar dados manualmente", "Validar fontes de informação"],
            "recommendation": "MANUAL_REVIEW",
            "analysis": {
                "website_analysis": "Não encontrado - Website pode não estar acessível",
                "funding_analysis": "Não encontrado - Fontes de funding não verificadas",
                "data_quality": "Não encontrado - Análise detalhada indisponível"
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



    def _calculate_startup_metrics(self, startup: Dict[str, Any]) -> Dict[str, Any]:
        """Calcular métricas de score para a startup"""
        prompt = f"""
        Analise esta startup validada e calcule scores de 0-100 para as métricas. Seja criterioso e realista.

        STARTUP: {startup.get('name')}
        Setor: {startup.get('sector')}
        Tecnologias IA: {startup.get('ai_technologies')}
        Funding: ${startup.get('last_funding_amount', 0):,}
        Investidores: {startup.get('investor_names')}
        País: {startup.get('country')}
        Cidade: {startup.get('city')}

        CRITÉRIOS DE ANÁLISE (baseado nas tecnologias ESPECÍFICAS da startup):
        1. MARKET_DEMAND (0-100): Demanda do mercado
           - Baseado nas tecnologias IA ESPECÍFICAS: Computer Vision (85-95), NLP (80-90), Machine Learning (70-85)
           - Tecnologias relevantes para NVIDIA GPU (Deep Learning, Computer Vision: +20 pontos)
           - Aplicação prática no setor específico (B2B enterprise: +15 pontos)
           - NÃO criar análises genéricas como "análise de dados financeiros"

        2. TECHNICAL_LEVEL (0-100): Nível técnico
           - Baseado nas tecnologias IA LISTADAS: Deep Learning (80-100), Machine Learning (60-80), Computer Vision (70-90)
           - Complexidade técnica real: Multi-modal AI (90-100), Single technology (60-80)
           - Avaliar apenas as tecnologias mencionadas na lista ai_technologies

        3. PARTNERSHIP_POTENTIAL (0-100): Potencial de parceria
           - Funding recente e significativo (>$10M: 80-100, $1-10M: 60-80, <$1M: 30-60)
           - Investidores conhecidos (+20 pontos)
           - Setor alinhado com NVIDIA (AI/GPU intensive: +15 pontos)

        RETORNE APENAS JSON válido (sem markdown):
        {{
            "market_demand_score": XX,
            "technical_level_score": XX,
            "partnership_potential_score": XX,
            "total_score": XX,
            "reasoning": {{
                "market": "justificativa detalhada",
                "technical": "justificativa detalhada",
                "partnership": "justificativa detalhada"
            }}
        }}
        """

        try:
            result = self._make_openai_request(prompt, max_tokens=700)
            if "error" in result:
                logger.error(f"OpenAI API error para metrics: {result['error']}")
                return self._default_metrics(startup, f"API Error: {result['error']}")

            content = result["content"].strip()

            # Remover markdown se presente
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            elif content.startswith("```"):
                content = content.replace("```", "", 1).replace("```", "").strip()

            metrics = json.loads(content)

            # Validar que todos os scores estão presentes
            required_scores = ["market_demand_score", "technical_level_score", "partnership_potential_score"]
            for score_key in required_scores:
                if score_key not in metrics or not isinstance(metrics[score_key], (int, float)):
                    logger.error(f"Score inválido ou ausente: {score_key}")
                    return self._default_metrics(startup, f"Score inválido: {score_key}")

            # Calcular total_score se não foi fornecido ou está inválido
            if "total_score" not in metrics or not isinstance(metrics["total_score"], (int, float)):
                metrics["total_score"] = round(
                    metrics.get("market_demand_score", 0) * 0.4 +
                    metrics.get("technical_level_score", 0) * 0.3 +
                    metrics.get("partnership_potential_score", 0) * 0.3,
                    2
                )

            # Validar reasoning
            if "reasoning" not in metrics:
                metrics["reasoning"] = {
                    "market": "Análise padrão de mercado",
                    "technical": "Análise padrão técnica",
                    "partnership": "Análise padrão de parceria"
                }

            metrics["tokens_used"] = result.get("tokens_used", 0)

            logger.info(f"Métricas calculadas para {startup.get('name')}: Total Score = {metrics['total_score']}")
            return metrics

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error para startup {startup.get('name')}: {e}")
            return self._default_metrics(startup, f"JSON parse error: {str(e)}")
        except Exception as e:
            logger.error(f"Erro inesperado ao calcular métricas para {startup.get('name')}: {e}")
            return self._default_metrics(startup, f"Erro inesperado: {str(e)}")

    def _default_metrics(self, startup: Dict[str, Any] = None, error_msg: str = "Failed to calculate metrics") -> Dict[str, Any]:
        """Métricas padrão em caso de erro com análise básica"""

        # Fazer uma análise básica sem IA em caso de erro
        market_score = 40
        technical_score = 40
        partnership_score = 40

        if startup:
            # Análise simples baseada em dados disponíveis

            # Market demand baseado em tecnologias
            ai_techs = startup.get('ai_technologies', [])
            if any(tech.lower() in ['computer vision', 'cv', 'vision'] for tech in ai_techs):
                market_score += 15
            if any(tech.lower() in ['nlp', 'natural language', 'language model'] for tech in ai_techs):
                market_score += 10
            if any(tech.lower() in ['deep learning', 'neural network'] for tech in ai_techs):
                market_score += 10

            # Technical level baseado em tecnologias
            if len(ai_techs) >= 2:
                technical_score += 10
            if any(tech.lower() in ['deep learning', 'machine learning'] for tech in ai_techs):
                technical_score += 15

            # Partnership potential baseado em funding
            funding = startup.get('last_funding_amount', 0)
            if funding >= 10000000:  # $10M+
                partnership_score += 25
            elif funding >= 1000000:  # $1M+
                partnership_score += 15
            elif funding > 0:
                partnership_score += 5

            # Investidores
            investors = startup.get('investor_names', [])
            if len(investors) >= 2:
                partnership_score += 10

        # Garantir que scores não excedam 100
        market_score = min(market_score, 100)
        technical_score = min(technical_score, 100)
        partnership_score = min(partnership_score, 100)

        total_score = round(market_score * 0.4 + technical_score * 0.3 + partnership_score * 0.3, 2)

        return {
            "market_demand_score": market_score,
            "technical_level_score": technical_score,
            "partnership_potential_score": partnership_score,
            "total_score": total_score,
            "reasoning": {
                "error": error_msg,
                "market": f"Análise básica sem IA: Score {market_score} baseado em tecnologias",
                "technical": f"Análise básica sem IA: Score {technical_score} baseado em CTO e tecnologias",
                "partnership": f"Análise básica sem IA: Score {partnership_score} baseado em funding e investidores"
            },
            "tokens_used": 0
        }

    def _make_openai_request(self, prompt: str, max_tokens: int = 3000) -> Dict[str, Any]:
        """Fazer requisição para OpenAI sem WebSearch (para métricas, validação, etc.)"""
        # Para operações que não precisam de WebSearch, usar gpt-4o-mini padrão
        model_without_search = "gpt-4o-mini"

        payload = {
            "model": model_without_search,
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
                         existing_valid: List = None, existing_invalid: List = None,
                         search_strategy: str = "specific") -> Dict[str, Any]:
        """Executar orquestração completa"""

        initial_state = OrchestrationState(
            country=country,
            sector=sector,
            limit=limit,
            search_strategy=search_strategy,
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