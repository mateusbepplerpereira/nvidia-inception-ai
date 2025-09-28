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

        # Usar Responses API para web search com gpt-4o-mini padrão
        self.chat_url = "https://api.openai.com/v1/chat/completions"
        self.responses_url = "https://api.openai.com/v1/responses"
        self.model = "gpt-4o-mini"  # Modelo padrão, mais estável que search-preview
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
        logger.info(f"*** DISCOVERY AGENT CHAMADO *** - Limite: {state['limit']}")
        logger.info(f"Estado atual: country={state.get('country')}, sector={state.get('sector')}, strategy={state.get('search_strategy')}")
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
            search_query = f"AI startups most demanded sectors {state.get('country', 'Latin America')} market trends venture capital"
            sector_constraint = f"""
        ESTRATÉGIA: BUSCAR SETORES EMERGENTES E DE DEMANDA CRESCENTE EM {state.get('country', 'AMÉRICA LATINA')}
        - Identifique os 3-5 setores de IA com MAIOR demanda/investimento em {state.get('country', 'América Latina')}
        - Foque em setores emergentes e de alto crescimento específicos da região
        - Explore setores de IA de alta demanda global
        - Diversifique entre diferentes setores promissores para a região
        - NÃO se limite a um setor específico - explore a demanda regional do mercado
        """

        elif search_strategy == 'global_market_demand':
            # Busca global por setores com alta demanda de mercado
            search_query = "AI startups most demanded sectors global market trends venture capital Latin America"
            sector_constraint = """
        ESTRATÉGIA: BUSCA GLOBAL POR SETORES EMERGENTES E DE ALTA DEMANDA
        - Identifique os setores de IA com MAIOR demanda/investimento GLOBALMENTE
        - Foque em setores emergentes e de alto crescimento mundial
        - Explore setores de IA de alta demanda global
        - Diversifique entre diferentes setores promissores globalmente
        - Aceite startups de qualquer país, mas priorize América Latina quando possível
        - NÃO se limite a um setor específico - explore a demanda GLOBAL do mercado
        """

        elif search_strategy == 'global':
            # Busca global sem limitação geográfica
            if state.get('country') and state.get('country') != '':
                search_query = f"AI startups {state.get('country', '')} {state.get('sector', '')} global market venture capital funding".strip()
            else:
                search_query = f"AI startups {state.get('sector', '')} global market Latin America venture capital funding".strip()

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
                # Query muito específica para país e setor
                country = state.get('country', 'Brazil')
                # Query específica para o setor
                sector_keywords = self._get_sector_keywords(state.get('sector', ''))

                if country.lower() in ['brazil', 'brasil']:
                    search_query = f"startups brasileiras {state['sector']} {sector_keywords} Brasil sede AI venture capital funding healthtech medtech"
                else:
                    search_query = f"startups {state['sector']} {sector_keywords} {country} AI venture capital funding founded {country}"

                sector_constraint = f"""
        RESTRIÇÕES ABSOLUTA DE PAÍS E SETOR - CUMPRIMENTO OBRIGATÓRIO:

        PAÍS: EXCLUSIVAMENTE startups do país "{state.get('country', 'Brazil')}"
        - Se busca "Brazil" → APENAS startups BRASILEIRAS fundadas no Brasil
        - Se encontrar startup da Argentina, Chile, México, etc. → REJEITÁ-LA COMPLETAMENTE
        - VALIDAR na WebSearch: "startup [nome] brasil sede fundada"
        - NO CAMPO "country" usar EXATAMENTE: "{state.get('country', 'Brazil')}"

        SETOR: EXCLUSIVAMENTE startups do setor "{state['sector']}"
        - ZERO TOLERÂNCIA para outros setores
        - Core business DEVE ser 100% {state['sector']}
        - NÃO aceitar startups que apenas "atendem" o setor como clientes
        - Se uma startup é de outro setor → REJEITÁ-LA COMPLETAMENTE
        - VALIDAR: o core business deve ser 100% "{state['sector']}"
        - NO CAMPO "sector" usar EXATAMENTE: "{state['sector']}"
        """
            else:
                search_query = f"AI startups {state.get('country', 'Brazil')} venture capital funding"
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

        # Sistema de exclusão inteligente - apenas impedir redescoberta de startups idênticas
        existing_startups = self._get_context_exclusions(state)
        exclusion_text = self._format_exclusion_list(existing_startups, state.get('sector'))

        # Prompt otimizado para DESCOBRIR APENAS STARTUPS COM VC CONFIRMADO
        prompt = f"""
        Use a ferramenta WebSearch para descobrir EXATAMENTE {state['limit']} startups de IA reais {geographic_context} que COMPROVADAMENTE receberam funding de VC.

        METODOLOGIA OBRIGATÓRIA PARA CADA STARTUP:
        1º) Encontre startups de IA do setor/região
        2º) Para CADA startup, busque especificamente: "[nome] venture capital funding investors"
        3º) Confirme em fontes confiáveis: Crunchbase, TechCrunch, sites de VC
        4º) SE NÃO ACHAR VC CONFIRMADO = DESCARTE e busque outra
        5º) APENAS inclua na lista se VC estiver 100% confirmado

        REGRA FUNDAMENTAL - VENTURE CAPITAL OBRIGATÓRIO:
        TODAS as startups descobertas DEVEM ter recebido funding de Venture Capital confirmado.
        NÃO incluir startups que só receberam:
        - Funding governamental, subsídios ou editais públicos
        - Bootstrapping ou autofinanciamento
        - Crowdfunding ou financiamento coletivo
        - Apenas angel investment sem VC follow-up
        - Aceleradoras sem VC confirmado

        APENAS incluir startups com:
        - Rounds de VC confirmados (Seed, Series A, B, C...)
        - Fundos de Venture Capital conhecidos como investidores
        - Investment comprovado em bases como Crunchbase/Distrito
        - Nomes específicos de fundos VC (não genéricos)

        QUERIES ESPECÍFICAS POR SETOR (OBRIGATORIAMENTE usar o setor {state.get('sector', '')}):
        1. "{search_query} {state.get('sector', '')} venture capital funding"
        2. "startups {state.get('sector', '')} Brasil VC healthtech medtech"
        3. "AI {state.get('sector', '')} Brasil artificial intelligence venture capital"
        4. "healthtech medical AI startups Brasil crunchbase funding"

        {exclusion_text}

        FONTES CONFIÁVEIS PARA CONFIRMAR VC (use para validar CADA startup):
        1. BASES OFICIAIS: crunchbase.com, pitchbook.com, dealroom.co
        2. VC BRASILEIROS: distrito.me, neofeed.com.br, brasiljorney.com.br
        3. MÍDIA TECH: techcrunch.com, venturebeat.com, valor.globo.com
        4. SITES DE VC: sites oficiais dos fundos VC brasileiros

        FUNDOS VC BRASILEIROS CONHECIDOS (para referência):
        Monashees, Kaszek, Canary, Redpoint e.ventures, Valor Capital, SP Ventures

        {sector_constraint}
        {exclusion_context}

        REGRA DE QUALIDADE - PREFERÊNCIA POR MENOS COM VC:
        - Melhor descobrir 1-2 startups COM VC confirmado
        - Do que descobrir 5 startups SEM VC confirmado
        - SE não encontrar {state['limit']} com VC, retorne menos
        - JAMAIS "inventar" ou "assumir" que uma startup tem VC

        OBRIGATÓRIO - WEBSITE OFICIAL REAL VIA WEBSEARCH:
        - Use WebSearch para encontrar o website OFICIAL de cada startup
        - Busque especificamente: "[nome da startup] site oficial website"
        - JAMAIS INVENTAR URLs ou adicionar .com.br/.com automaticamente
        - Se não encontrar website via busca, deixar campo "website" como null
        - APENAS usar websites que você encontrou através de busca web
        - USAR WebSearch para buscar: "[nome_startup] site oficial website url"
        - VERIFICAR em múltiplas fontes: matérias, perfis LinkedIn, diretórios
        - CONFIRMAR URL exato encontrado nas buscas
        - Exemplos REAIS encontrados via busca:
          * "Creditec" → site REAL é "https://soucreditec.com.br" (não creditec.com.br)
          * "Crop Sense AI" → site REAL é "https://crop-sense-ai.vercel.app/" (não cropsenseai.com.br)
        - Se WebSearch não encontrar URL oficial → usar "Não encontrado"
        - ZERO TOLERÂNCIA para URLs inventadas ou chutadas

        Após a busca web, extraia APENAS startups reais com:
        1. Nome confirmado em fonte confiável
        2. Website OFICIAL encontrado na busca (não inventado)
        3. Funding verificado em fontes CONFIÁVEIS (Neofeed, BrasilJourney, etc.)
        4. Tecnologias AI específicas e detalhadas

        REGRAS ANTI-ALUCINAÇÃO CRÍTICAS - SEGUIR RIGOROSAMENTE:

        1. COERÊNCIA ABSOLUTA NOME-DESCRIÇÃO:
           - CONFIRMAR que o nome no campo "name" é EXATAMENTE a mesma empresa da "description"
           - Se o nome é "Magie", toda a descrição deve falar APENAS da "Magie"
           - JAMAIS misturar: nome "TechStartup" com descrição da "OutraEmpresa"
           - VERIFICAR múltiplas vezes essa correspondência antes de incluir

        2. VALIDAÇÃO RIGOROSA DE SETOR/CORE BUSINESS:
           - Identificar o CORE BUSINESS real da startup pela descrição
           - Se busca "{state.get('sector', '')}", incluir APENAS startups cujo negócio principal é 100% desse setor
           - Analise o core business real da startup
           - Não confunda empresas que apenas "atendem" um setor com empresas "do" setor
           - Empresa que vende para agro ≠ empresa de agro (a menos que seja seu core business)
           - ANALISAR o negócio principal, não apenas o mercado alvo

        3. VERIFICAÇÃO OBRIGATÓRIA DE WEBSITES:
           - TODO startup DEVE ter um website funcional e verificado
           - Use busca web para confirmar que o site existe e funciona
           - Teste múltiplas variações: https://startup.com, https://www.startup.com, etc.
           - Se o site não funcionar ou não existir, DESCARTAR a startup completamente
           - NUNCA inventar URLs ou incluir startups sem sites funcionais verificados
           - Priorizar startups com sites ativos e responsivos

        OBRIGATÓRIO - TECNOLOGIAS EM INGLÊS:
        - ai_technologies SEMPRE em inglês: ["Computer Vision", "Natural Language Processing", "Machine Learning"]
        - NÃO usar português: "Visão Computacional", "Processamento de Linguagem Natural"
        - Tecnologias específicas, não mercados: "Computer Vision" não "análise de dados financeiros"

        FORMATO DE RESPOSTA OBRIGATÓRIO - APENAS JSON VÁLIDO:

        RESPONDA APENAS COM JSON ARRAY VÁLIDO (sem explicações, sem markdown, sem texto adicional):

        [
          {{
            "name": "Nome Exato da Startup",
            "website": "https://site-oficial-verificado.com.br",
            "sector": "{state.get('sector', 'AI/Technology')}",
            "ai_technologies": ["Computer Vision", "Natural Language Processing"],
            "founded_year": 2021,
            "last_funding_amount": 5000000,
            "investor_names": ["Nome do Investidor"],
            "country": "{state.get('country', 'Global')}",
            "city": "Cidade",
            "description": "Descrição verificada da startup",
            "has_venture_capital": true,
            "funding_round": "Series A",
            "funding_date": "2023",
            "sources": {{
              "funding": ["URL fonte de funding"],
              "validation": ["URL de validação"]
            }}
          }}
        ]

        IMPORTANTE:
        - NÃO adicione texto antes ou depois do JSON
        - NÃO use markdown (```json)
        - NÃO explique nada
        - APENAS o array JSON válido

        PROCESSO DE VALIDAÇÃO FINAL OBRIGATÓRIO:
        ETAPA 1 - Revisão Individual por Startup:
        Para CADA startup encontrada, perguntar-se:
        ✓ O nome no campo "name" é exatamente a mesma empresa da "description"?
        ✓ O core business principal é 100% do setor "{state.get('sector', 'AI/Technology')}"?
        ✓ O website foi verificado e funciona (acessível via busca web)?
        ✓ As tecnologias AI são específicas e em inglês?
        ✓ Os dados de funding são consistentes e verificados?

        VERIFICAÇÃO CRÍTICA DE WEBSITE:
        - TESTAR o website na busca web antes de incluir
        - Se o site retornar erro 404, não funcionar ou não existir → EXCLUIR startup
        - Apenas incluir startups cujo website está comprovadamente ativo
        - Website válido é OBRIGATÓRIO para inclusão

        ETAPA 2 - Filtro Rigoroso:
        - REMOVER startups que falhem em qualquer critério acima
        - REMOVER startups cujo negócio principal não seja 100% do setor solicitado
        - REMOVER startups com incoerência nome-descrição
        - Se todas as startups foram removidas, retornar array vazio []

        ETAPA 3 - Formatação Final:
        - Campo 'sector': usar EXATAMENTE "{state.get('sector', 'AI/Technology')}"
        - Campo 'description': SEMPRE em português brasileiro (pt-BR), descrever APENAS a startup mencionada no campo 'name'
        - Campo 'ai_technologies': APENAS em inglês, tecnologias específicas
        """

        try:
            logger.info(f"=== INICIANDO DISCOVERY AGENT === - Limite: {state['limit']}")
            logger.info(f"Prompt enviado (primeiros 300 chars): {prompt[:300]}...")
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

            # Extrair JSON do conteúdo mais agressivamente
            original_content = content

            # Remover markdown se existir
            if "```json" in content:
                json_start = content.find("```json") + len("```json")
                json_end = content.find("```", json_start)
                if json_end != -1:
                    content = content[json_start:json_end].strip()
                else:
                    content = content[json_start:].strip()
            elif "```" in content:
                json_start = content.find("```") + 3
                json_end = content.find("```", json_start)
                if json_end != -1:
                    content = content[json_start:json_end].strip()
                else:
                    content = content[json_start:].strip()

            # Se ainda não é JSON, tentar encontrar array no texto
            if not content.strip().startswith('['):
                # Procurar por array JSON no meio do texto
                import re
                json_match = re.search(r'\[.*?\]', content, re.DOTALL)
                if json_match:
                    content = json_match.group(0)
                else:
                    logger.error(f"Nenhum JSON array encontrado no conteúdo")
                    logger.error(f"Conteúdo original completo: {original_content}")
                    # Se não encontrar JSON, retornar array vazio
                    state["discovered_startups"] = []
                    state["errors"].append("Modelo retornou formato inválido - não JSON")
                    return state

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

            # FILTRO DUPLO: Remover startups SEM VC e SETOR ERRADO
            original_count = len(startups)
            filtered_startups = []
            expected_sector = state.get('sector', '')

            for startup in startups:
                startup_name = startup.get('name', 'N/A')
                startup_sector = startup.get('sector', '')
                has_vc = startup.get('has_venture_capital', False)
                investor_names = startup.get('investor_names', '')
                funding_amount = startup.get('last_funding_amount', 0)
                description = startup.get('description', '')

                # FILTRO 1: Verificar SETOR (primeira validação básica)
                sector_ok = True
                if expected_sector:
                    # Verificar se o setor bate (comparação simples)
                    sector_match = (
                        startup_sector.lower().strip() == expected_sector.lower().strip() or
                        expected_sector.lower() in startup_sector.lower()
                    )

                    if not sector_match:
                        sector_ok = False
                        logger.warning(f"SETOR ERRADO: {startup_name} ({startup_sector}) descartada - esperado {expected_sector}")
                    else:
                        logger.info(f"SETOR OK: {startup_name} ({startup_sector}) aprovado para {expected_sector}")

                # FILTRO 2: Verificar apenas VC (setor fica para o validation_agent)
                vc_ok = (
                    has_vc and
                    investor_names and
                    investor_names not in ['N/A', 'n/a', 'unknown', 'none', ''] and
                    funding_amount and funding_amount >= 100000
                )

                # APENAS incluir se passou nos dois filtros (setor + VC)
                if sector_ok and vc_ok:
                    filtered_startups.append(startup)
                    logger.info(f"APROVADA: {startup_name} - Setor: {startup_sector} - VC: {investor_names} - ${funding_amount:,}")
                elif not sector_ok:
                    logger.warning(f"REJEITADA POR SETOR: {startup_name}")
                else:
                    logger.warning(f"REJEITADA SEM VC: {startup_name}")

            startups = filtered_startups
            logger.info(f"=== FILTRO DUPLO: {original_count} -> {len(startups)} startups (setor + VC, validation_agent fará segunda validação) ===")

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
        """Fazer requisição OpenAI usando Chat Completions API com gpt-4o-mini padrão"""

        # Usar Responses API corretamente com gpt-4o-mini + web_search_preview
        payload = {
            "model": self.model,  # gpt-4o-mini padrão
            "input": [
                {"role": "system", "content": """ESPECIALISTA EM IDENTIFICAÇÃO RIGOROSA DE STARTUPS POR SETOR E PAÍS

REGRA CRÍTICA - ZERO TOLERÂNCIA:
- Se busca setor "Agro" → APENAS empresas cujo CORE BUSINESS é agricultura, pecuária, biotecnologia agrícola
- Se encontrar Magie (fintech) → REJEITAR (é fintech, não agro)
- Se encontrar Capim (fintech odontológico) → REJEITAR (é fintech health, não agro)
- Se encontrar qualquer fintech/healthtech → REJEITAR COMPLETAMENTE

DEFINIÇÕES ESPECÍFICAS:
- AGRO = agricultura, pecuária, agrotecnologia, biotecnologia agrícola, equipamentos agrícolas
- FINTECH = pagamentos, crédito, empréstimos, cartões, PIX (NUNCA é agro)
- HEALTHTECH = saúde, medicina, odontologia (NUNCA é agro)

OBRIGATÓRIO:
1. Use web search para identificar CORE BUSINESS real
2. Se a empresa faz pagamentos/crédito → É FINTECH (rejeitar se busca agro)
3. Se a empresa faz saúde/odonto → É HEALTHTECH (rejeitar se busca agro)
4. APENAS incluir se for 100% do setor solicitado

RESPOSTA: JSON array apenas."""},
                {"role": "user", "content": prompt}
            ],
            "tools": [
                {
                    "type": "web_search_preview"
                }
            ],
            "temperature": 0.1,  # Baixa temperatura para menos alucinações
            "max_output_tokens": max_tokens
        }

        try:
            logger.info(f"Fazendo requisição WebSearch com modelo: {self.model}")
            logger.info(f"Payload enviado: {json.dumps(payload, indent=2)}")

            response = requests.post(
                self.responses_url,  # Usar Responses API corretamente
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

                # Log detalhado da estrutura da resposta
                logger.info(f"=== ESTRUTURA COMPLETA DA RESPOSTA ===")
                logger.info(f"Keys disponíveis: {list(result.keys())}")
                logger.info(f"Resposta completa (primeiros 500 chars): {str(result)[:500]}")

                if "choices" in result and result["choices"]:
                    logger.info(f"Choices disponíveis: {len(result['choices'])}")
                    message_content = result["choices"][0]["message"]["content"]
                    logger.info(f"Conteúdo da mensagem (primeiros 200 chars): {message_content[:200] if message_content else 'VAZIO'}")
                elif "output" in result:
                    logger.info(f"Output encontrado - tipo: {type(result['output'])}")
                    logger.info(f"Output (primeiros 200 chars): {str(result['output'])[:200]}")
                else:
                    logger.error("Nem choices nem output encontrados na resposta!")
                    logger.error(f"Estrutura recebida: {result}")

                # DEBUG: Estrutura básica para confirmar recebimento
                logger.info(f"Status da resposta: {result.get('status')}")
                logger.info(f"Outputs recebidos: {len(result.get('output', []))}")

                # Responses API - estrutura real baseada nos logs
                content = ""
                annotations = []

                try:
                    # O conteúdo está em result['output'][1]['content'][0]['text']
                    if result.get("output") and len(result["output"]) > 1:
                        message_output = result["output"][1]  # Segundo item é a mensagem
                        if message_output.get("content") and len(message_output["content"]) > 0:
                            content = message_output["content"][0].get("text", "")
                            annotations = message_output["content"][0].get("annotations", [])
                except Exception as e:
                    logger.error(f"Erro ao extrair da estrutura real: {e}")
                    content = ""

                logger.info(f"Content extraído via output_text: {content[:200] if content else 'VAZIO'}...")
                logger.info(f"Annotations encontradas: {len(annotations)}")

                return {
                    "content": content,
                    "annotations": annotations,
                    "tokens_used": result.get("usage", {}).get("total_tokens", 0)
                }
            else:
                error_text = response.text[:500]
                logger.error(f"Erro WebSearch {response.status_code}: {error_text}")
                return {"error": f"WebSearch API Error: {response.status_code} - {error_text}"}

        except Exception as e:
            logger.error(f"Exceção na requisição WebSearch: {str(e)}")
            return {"error": f"WebSearch Request error: {str(e)}"}

    def _get_sector_keywords(self, sector: str) -> str:
        """Retorna keywords específicas para cada setor"""
        sector_map = {
            "Saúde": "medical healthcare medtech health hospital clínica medicina telemedicine diagnosis",
            "Health": "medical healthcare medtech health hospital clinic medicine telemedicine diagnosis",
            "Fintech": "financial banking payments credit card fintech finance digital wallet",
            "Agro": "agriculture farming agtech rural crops livestock precision agriculture",
            "Educação": "education edtech learning school university online courses e-learning",
            "Logística": "logistics transportation delivery supply chain shipping freight",
            "Energia": "energy renewable solar wind electricity power grid smart energy",
            "Varejo": "retail e-commerce marketplace shopping consumer goods fashion"
        }
        return sector_map.get(sector, "technology AI artificial intelligence")

    def _get_context_exclusions(self, state: OrchestrationState) -> list:
        """ISOLAMENTO DE CONTEXTO: Usa APENAS startups do contexto passado, nunca do banco"""
        exclusions = []

        # Adicionar startups válidas do contexto (já filtradas por setor no agent_service)
        for startup in state.get('valid_startups', []):
            if isinstance(startup, dict) and startup.get('name'):
                exclusions.append((startup['name'], state.get('sector', 'Unknown')))

        # Adicionar startups inválidas do contexto
        for startup in state.get('invalid_startups', []):
            if isinstance(startup, dict) and startup.get('name'):
                exclusions.append((startup['name'], state.get('sector', 'Unknown')))

        logger.info(f"EXCLUSION CONTEXT: {len(exclusions)} startups para excluir do setor {state.get('sector')}")
        return exclusions

    def _get_existing_startups(self, state: OrchestrationState) -> list:
        """MÉTODO DEPRECIADO - NÃO USAR PARA EVITAR CONTAMINAÇÃO DE CONTEXTO"""
        logger.warning(f"Método _get_existing_startups foi chamado para setor {state.get('sector')} - ISSO PODE CAUSAR CONTAMINAÇÃO!")
        return []

    def _format_exclusion_list(self, existing_startups: list, sector: str = None) -> str:
        """Formata lista de exclusão para o prompt - APENAS para evitar redescoberta"""
        if not existing_startups:
            return ""

        if sector:
            # Filtrar apenas startups do mesmo setor por NOME EXATO
            sector_startups = [name for name, startup_sector in existing_startups
                             if startup_sector and startup_sector.lower() == sector.lower()]

            if sector_startups:
                startup_list = "\n".join([f"- {name}" for name in sector_startups[:10]])  # Limitar a 10
                return f"""
        EVITAR REDESCOBERTA - STARTUPS JÁ CADASTRADAS NO SETOR {sector.upper()}:
        As seguintes startups JÁ ESTÃO no banco de dados:
        {startup_list}

        IMPORTANTE: NÃO descobrir novamente essas startups que já existem.
        Busque APENAS startups DIFERENTES e NOVAS que não estão nesta lista.
        Foque em encontrar outras startups do setor que ainda não foram descobertas.
        """
        else:
            # Para busca sem setor específico, mostrar todas por setor
            by_sector = {}
            for name, startup_sector in existing_startups:
                sector_key = startup_sector or "Outros"
                if sector_key not in by_sector:
                    by_sector[sector_key] = []
                by_sector[sector_key].append(name)

            exclusion_text = "EXCLUSÃO OBRIGATÓRIA - STARTUPS JÁ CADASTRADAS:\n"
            for sector_name, names in by_sector.items():
                limited_names = names[:10]  # Limitar a 10 por setor
                startup_list = "\n".join([f"  - {name}" for name in limited_names])
                exclusion_text += f"\n{sector_name}:\n{startup_list}\n"

            exclusion_text += "\nIMPORTANTE: NÃO BUSCAR nenhuma dessas startups. Busque APENAS startups NOVAS."
            return exclusion_text

        return ""


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

        # Verificação de tipo para evitar erro quando startup vem como string
        if isinstance(startup, str):
            logger.error(f"Startup veio como string ao invés de dict: {startup}")
            return {
                "is_reliable": False,
                "reliability_score": 0,
                "issues": ["Formato de dados inválido"]
            }

        sources = startup.get("sources", {})

        # PROTEÇÃO: Verificar se sources é dict (pode vir como lista por erro)
        if isinstance(sources, list):
            logger.warning(f"Sources veio como lista para {startup.get('name')}: {sources}")
            sources = {}  # Converter para dict vazio se vier como lista
        elif not isinstance(sources, dict):
            logger.warning(f"Sources tem tipo incorreto para {startup.get('name')}: {type(sources)}")
            sources = {}

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
            "setortech": 12, "industrytech": 10, "sectorbusiness": 10,

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
            validation_result = self._validate_startup_thoroughly(startup, state)

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

    def _validate_startup_thoroughly(self, startup: Dict[str, Any], state: OrchestrationState) -> Dict[str, Any]:
        """Validação rigorosa de startup com scoring detalhado E VERIFICAÇÃO DE CONTEXTO"""
        issues = []
        validation_scores = {}

        # VALIDAÇÃO CRÍTICA DE SETOR - REJEITAR SE INCORRETO
        expected_sector = state.get('sector', '')
        startup_sector = startup.get('sector', '')
        startup_name = startup.get('name', 'N/A')
        startup_description = startup.get('description', '')

        if expected_sector:
            # Verificar se o setor da startup corresponde ao esperado
            sector_match = (
                startup_sector.lower() == expected_sector.lower() or
                expected_sector.lower() in startup_sector.lower()
            )

            # Validar pela descrição se o core business é realmente do setor
            sector_keywords = self._get_sector_keywords(expected_sector).split()
            description_lower = startup_description.lower()
            keyword_matches = sum(1 for keyword in sector_keywords if keyword.lower() in description_lower)

            if not sector_match:
                issues.append(f"REJEITADA: Setor incorreto - esperado {expected_sector}, encontrado {startup_sector}")
                validation_scores['sector_match_score'] = 0
                logger.warning(f"SETOR INCORRETO: {startup_name} é {startup_sector}, mas busca era para {expected_sector}")
            elif keyword_matches < 2:  # Mínimo 2 keywords do setor na descrição
                issues.append(f"REJEITADA: Descrição não condiz com setor {expected_sector}")
                validation_scores['sector_match_score'] = 0
                logger.warning(f"DESCRIÇÃO INCOMPATÍVEL: {startup_name} - apenas {keyword_matches} keywords de {expected_sector}")
            else:
                validation_scores['sector_match_score'] = 100
                logger.info(f"SETOR OK: {startup_name} - {expected_sector}")

        # Deixar o agente de IA fazer a validação de setor

        # Validar website
        website_valid = self._validate_website(startup.get("website"))
        validation_scores["website_score"] = 100 if website_valid else 0
        if not website_valid:
            issues.append("Website inacessível ou inválido")

        # VALIDAÇÃO CRÍTICA DE VENTURE CAPITAL
        funding_sources = startup.get("sources", {}).get("funding", [])
        investor_names = startup.get("investor_names", "")
        funding_amount = startup.get("last_funding_amount", 0)
        has_vc = startup.get("has_venture_capital", False)

        # Normalizar investor_names (pode ser string ou lista)
        if isinstance(investor_names, list):
            investor_names_str = ", ".join(investor_names) if investor_names else ""
        else:
            investor_names_str = str(investor_names) if investor_names else ""

        # Verificar se tem VC confirmado
        if not has_vc:
            issues.append("REJEITADA: Startup sem Venture Capital confirmado")
            validation_scores["vc_funding_score"] = 0
        elif not investor_names_str or investor_names_str.lower() in ['n/a', 'unknown', 'none', '']:
            issues.append("REJEITADA: Sem nomes de investidores VC específicos")
            validation_scores["vc_funding_score"] = 0
        elif not funding_amount or funding_amount < 100000:  # Mínimo 100k
            issues.append("REJEITADA: Funding amount muito baixo ou inexistente")
            validation_scores["vc_funding_score"] = 0
        elif not funding_sources:
            issues.append("REJEITADA: Sem fontes que comprovem o VC funding")
            validation_scores["vc_funding_score"] = 0
        else:
            validation_scores["vc_funding_score"] = 100

        # Validar fontes de funding
        if not funding_sources:
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

        # Startup é válida se tem dados básicos (agente de IA já fez a validação de setor)
        is_valid = has_basic_data

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
        # Garantir que valores não sejam None para evitar erro de formatação
        name = startup.get('name') or 'N/A'
        sector = startup.get('sector') or 'N/A'
        ai_technologies = startup.get('ai_technologies') or []
        funding_amount = startup.get('last_funding_amount') or 0
        investor_names = startup.get('investor_names') or 'N/A'
        country = startup.get('country') or 'N/A'

        prompt = f"""
        Analise esta startup validada e calcule scores de 0-100 para as métricas. Seja criterioso e realista.

        STARTUP: {name}
        Setor: {sector}
        Tecnologias IA: {ai_technologies}
        Funding: ${funding_amount:,}
        Investidores: {investor_names}
        País: {country}
        Cidade: {startup.get('city') or 'N/A'}

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
                self.chat_url,  # Usar chat_url em vez de base_url
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
        """Executar orquestração completa com ISOLAMENTO TOTAL DE CONTEXTO"""

        # Inicialização da orquestração
        logger.info(f"Iniciando orquestração: {country} - {sector} - Limite: {limit}")

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
            # Executando LangGraph
            logger.info(f"Executando pipeline - limite: {limit}, setor: {initial_state.get('sector')}")

            try:
                final_state = self.graph.invoke(initial_state)
                logger.info(f"Pipeline concluído com sucesso")
            except Exception as graph_error:
                logger.error(f"Erro no pipeline: {str(graph_error)}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                raise graph_error

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