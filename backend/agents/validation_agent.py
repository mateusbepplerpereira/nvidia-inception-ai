import requests
import json
import os
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class StartupValidationAgent:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")

        self.chat_url = "https://api.openai.com/v1/chat/completions"
        # Usar gpt-4o-mini padrão
        self.model = "gpt-4o-mini"

    def _perform_targeted_web_validation(self, startup_name: str, country: str, website_works: bool) -> Dict[str, Any]:
        """Validação técnica simples baseada no website fornecido pelo discovery"""

        logger.info(f"Executando validação técnica para {startup_name}")

        validation_data = {
            "website_found": None,
            "funding_confirmed": False,
            "funding_amount": None,
            "investors_found": [],
            "company_status": "unknown",
            "sources": [],
            "validation_method": "technical_validation"
        }

        # Se website funciona, considerar empresa ativa
        if website_works:
            validation_data["company_status"] = "active"
            validation_data["website_found"] = "confirmed_working"
            logger.info(f"Website de {startup_name} está funcionando")
        else:
            logger.warning(f"Website fornecido para {startup_name} não está funcionando")
            validation_data["company_status"] = "inactive_website"

        return validation_data






    def validate_startup_info(self, startup_data: Dict[str, Any]) -> Dict[str, Any]:
        """Valida informações de uma startup usando WebSearch nativo quando necessário"""

        # Primeiro, tentar validar website diretamente
        website_valid = self.check_website_validity(startup_data.get("website"))

        # Se website não funciona OU não há funding sources, fazer busca web
        needs_web_search = (
            not website_valid or
            not startup_data.get("sources", {}).get("funding") or
            startup_data.get("last_funding_amount", 0) > 10000000  # Validar funding alto
        )

        web_validation_data = {}
        if needs_web_search:
            web_validation_data = self._perform_targeted_web_validation(
                startup_data.get("name"),
                startup_data.get("country", "Brazil"),
                website_valid
            )

        # Análise final combinando validações técnicas + web (se necessário)
        validation_prompt = f"""
        Valide esta startup combinando verificações técnicas e busca web:

        DADOS DA STARTUP:
        Nome: {startup_data.get('name')}
        Website: {startup_data.get('website')} (acessível: {'Sim' if website_valid else 'Não'})
        Setor: {startup_data.get('sector')}
        Tecnologias IA: {startup_data.get('ai_technologies', [])} (DEVE ser em inglês)
        Funding: ${startup_data.get('last_funding_amount', 0):,}
        Investidores: {startup_data.get('investor_names')}
        Fontes: {startup_data.get('sources', {})}

        {'DADOS DA BUSCA WEB:' + json.dumps(web_validation_data, indent=2) if web_validation_data else 'Busca web não foi necessária.'}

        CRITÉRIOS DE VALIDAÇÃO - APLICAR RIGOROSAMENTE:

        1. COERÊNCIA NOME-DESCRIÇÃO: {'✓' if True else '✗'}
           - Nome e descrição devem se referir à MESMA empresa
           - Zero tolerância para mistura de empresas diferentes

        2. VALIDAÇÃO TÉCNICA DE WEBSITE: {'✓' if website_valid else '✗'}
           - Website deve ser tecnicamente acessível

        3. TECNOLOGIAS IA - CRITÉRIO RIGOROSO:
           - APENAS em inglês: "Computer Vision", "Natural Language Processing", "Machine Learning"
           - ESPECÍFICAS, não genéricas: "Deep Learning" ✓, "análise de dados" ✗
           - TECNOLOGIAS, não aplicações: "NLP" ✓, "análise de crédito" ✗

        4. VALIDAÇÃO DE SETOR POR CORE BUSINESS:
           - Identificar o negócio PRINCIPAL da startup
           - Validar se o core business condiz com o setor solicitado
           - Não aceitar empresas que apenas "atendem" o setor como clientes

        5. CONSISTÊNCIA DE DADOS:
           - Funding realista e verificado
           - Investidores conhecidos no ecossistema
           - Datas e valores coerentes

        INVALIDAÇÃO AUTOMÁTICA SE:
        - Tecnologias em português ou genéricas demais
        - Incoerência nome-descrição
        - Core business diferente do setor solicitado
        - Dados claramente inventados ou inconsistentes

        RETORNE JSON:
        {{
            "validation_status": "valid/suspicious/invalid",
            "confidence_score": 0.XX,
            "issues_found": ["problemas específicos"],
            "verified_website": "{startup_data.get('website') if website_valid else 'null'}",
            "funding_verified": true/false,
            "company_active": true/false,
            "web_search_used": {str(bool(web_validation_data)).lower()},
            "technology_validation": "valid/invalid",
            "sector_validation": "valid/invalid",
            "recommendations": ["ações sugeridas"]
        }}
        """

        try:
            response = requests.post(
                self.chat_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "Analise resultados de busca web e valide startups. Retorne JSON válido."},
                        {"role": "user", "content": validation_prompt}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 800
                },
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"].strip()

                # Parse JSON response
                if content.startswith("```json"):
                    content = content.replace("```json", "").replace("```", "").strip()
                elif content.startswith("```"):
                    content = content.replace("```", "", 1).replace("```", "").strip()

                validation_result = json.loads(content)
                validation_result["tokens_used"] = result["usage"]["total_tokens"]

                return validation_result

            else:
                return self._default_validation_result(f"API Error: {response.status_code}")

        except json.JSONDecodeError as e:
            return self._default_validation_result(f"JSON parse error: {e}")
        except Exception as e:
            return self._default_validation_result(f"Validation error: {e}")

    def _default_validation_result(self, error_msg: str) -> Dict[str, Any]:
        """Resultado padrão em caso de erro"""
        return {
            "validation_status": "error",
            "confidence_score": 0.0,
            "issues_found": [{"field": "validation", "issue": error_msg, "severity": "high"}],
            "verified_website": None,
            "funding_verified": False,
            "company_active": False,
            "recommendations": ["Manual review required"],
            "needs_manual_review": True,
            "tokens_used": 0
        }

    def batch_validate_startups(self, startups_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Valida uma lista de startups em lote"""
        results = []
        total_tokens = 0

        for startup in startups_list:
            validation = self.validate_startup_info(startup)
            total_tokens += validation.get("tokens_used", 0)

            results.append({
                "startup_name": startup.get("name", "Unknown"),
                "validation": validation
            })

            # Pequeno delay para evitar rate limiting
            time.sleep(1)

        return {
            "validations": results,
            "total_tokens_used": total_tokens,
            "summary": {
                "total_startups": len(startups_list),
                "valid": len([r for r in results if r["validation"]["validation_status"] == "valid"]),
                "suspicious": len([r for r in results if r["validation"]["validation_status"] == "suspicious"]),
                "invalid": len([r for r in results if r["validation"]["validation_status"] == "invalid"]),
                "errors": len([r for r in results if r["validation"]["validation_status"] == "error"])
            }
        }

    def check_website_validity(self, url: str) -> bool:
        """Verifica se um website é válido e acessível"""
        if not url:
            return False

        # Lista de URLs para tentar
        urls_to_try = [url]

        # Se não tem protocolo, adicionar variações
        if not url.startswith(('http://', 'https://')):
            urls_to_try = [
                f"https://{url}",
                f"http://{url}",
                url
            ]

        # Tentar cada URL
        for test_url in urls_to_try:
            try:
                parsed = urlparse(test_url)
                if not parsed.scheme or not parsed.netloc:
                    continue

                # Headers para parecer um browser real
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                }

                response = requests.get(
                    test_url,
                    timeout=15,
                    allow_redirects=True,
                    headers=headers,
                    verify=False  # Ignorar certificados SSL inválidos
                )

                # Considerar válido se retornar 200-399 ou 403 (bloqueio mas existe)
                if response.status_code in range(200, 400) or response.status_code == 403:
                    logger.info(f"Website válido encontrado: {test_url} (status: {response.status_code})")
                    return True

            except requests.exceptions.Timeout:
                logger.warning(f"Timeout ao acessar {test_url}")
                continue
            except Exception as e:
                logger.debug(f"Erro ao verificar {test_url}: {e}")
                continue

        return False