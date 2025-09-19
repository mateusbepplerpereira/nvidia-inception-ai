import requests
import json
import os
from typing import Dict, Any, List
from urllib.parse import urlparse
import time

class StartupValidationAgent:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")

        self.base_url = "https://api.openai.com/v1/chat/completions"
        self.model = "gpt-4o-mini"

    def validate_startup_info(self, startup_data: Dict[str, Any]) -> Dict[str, Any]:
        """Valida informações de uma startup usando verificação cruzada e análise de consistência"""

        # Primeiro, fazer verificações técnicas
        website_status = self.check_website_validity(startup_data.get("website"))
        linkedin_checks = self.verify_linkedin_profiles(startup_data)

        prompt = f"""
        Você é um especialista em validação de startups reais. Analise CRITICAMENTE se esta startup realmente existe.

        DADOS DA STARTUP:
        {json.dumps(startup_data, indent=2, ensure_ascii=False)}

        VERIFICAÇÕES TÉCNICAS JÁ REALIZADAS:
        - Website funciona: {website_status}
        - LinkedIn CEO válido: {linkedin_checks.get('ceo_valid', False)}
        - LinkedIn CTO válido: {linkedin_checks.get('cto_valid', False)}

        VALIDAÇÃO CRÍTICA NECESSÁRIA:
        1. Esta empresa REALMENTE EXISTE? (conhecida no mercado brasileiro/latino)
        2. Os nomes CEO/CTO são REAIS? (não genéricos como "João Silva")
        3. O funding é REALISTA para o setor e período?
        4. A empresa está ATIVA ou foi fechada/adquirida?
        5. As tecnologias AI fazem sentido para o negócio?

        IMPORTANTE: Seja RIGOROSO. Muitas dessas podem ser empresas inventadas.

        RETORNE APENAS JSON:
        {{
            "validation_status": "valid/suspicious/invalid",
            "confidence_score": 0.XX,
            "issues_found": ["lista de problemas específicos"],
            "recommendations": ["ações para corrigir"],
            "verified_fields": ["campos verificados"],
            "needs_manual_review": true/false,
            "company_exists": true/false,
            "executives_verified": true/false
        }}
        """

        try:
            response = requests.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "Você é um especialista em validação de dados de startups. Sempre retorne JSON válido."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 1000
                },
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"].strip()

                # Parse JSON response
                try:
                    validation_result = json.loads(content)
                    validation_result["tokens_used"] = result["usage"]["total_tokens"]
                    return validation_result
                except json.JSONDecodeError:
                    return {
                        "validation_status": "error",
                        "confidence_score": 0.0,
                        "issues_found": [{"field": "validation", "issue": "Failed to parse validation response", "severity": "high"}],
                        "recommendations": ["Manual review required"],
                        "verified_fields": [],
                        "needs_manual_review": True,
                        "tokens_used": result["usage"]["total_tokens"]
                    }
            else:
                return {
                    "validation_status": "error",
                    "confidence_score": 0.0,
                    "issues_found": [{"field": "api", "issue": f"API Error: {response.status_code}", "severity": "high"}],
                    "recommendations": ["Retry validation"],
                    "verified_fields": [],
                    "needs_manual_review": True,
                    "tokens_used": 0
                }

        except Exception as e:
            return {
                "validation_status": "error",
                "confidence_score": 0.0,
                "issues_found": [{"field": "system", "issue": str(e), "severity": "high"}],
                "recommendations": ["System check required"],
                "verified_fields": [],
                "needs_manual_review": True,
                "tokens_used": 0
            }

    def batch_validate_startups(self, startups_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
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

        try:
            # Parse URL
            parsed = urlparse(str(url))
            if not parsed.scheme or not parsed.netloc:
                return False

            # Fazer request HTTP real para verificar se existe
            response = requests.get(str(url), timeout=10, allow_redirects=True)
            return response.status_code == 200

        except (requests.RequestException, Exception):
            return False

    def verify_linkedin_profiles(self, startup_data: Dict[str, Any]) -> Dict[str, bool]:
        """Verifica se os perfis do LinkedIn são válidos"""
        results = {
            "ceo_valid": False,
            "cto_valid": False
        }

        # Verificar CEO LinkedIn
        ceo_linkedin = startup_data.get("ceo_linkedin")
        if ceo_linkedin and self._is_valid_linkedin_url(ceo_linkedin):
            results["ceo_valid"] = True

        # Verificar CTO LinkedIn
        cto_linkedin = startup_data.get("cto_linkedin")
        if cto_linkedin and self._is_valid_linkedin_url(cto_linkedin):
            results["cto_valid"] = True

        return results

    def _is_valid_linkedin_url(self, url: str) -> bool:
        """Verifica se a URL do LinkedIn é válida"""
        if not url:
            return False

        try:
            parsed = urlparse(str(url))

            # Verificar se é domínio LinkedIn
            if "linkedin.com" not in parsed.netloc:
                return False

            # Verificar se tem formato correto /in/username
            if "/in/" not in parsed.path:
                return False

            # Fazer request básico (LinkedIn pode bloquear, mas tentamos)
            try:
                response = requests.get(str(url), timeout=5, allow_redirects=True)
                # LinkedIn retorna 999 para bots, mas isso indica que a URL existe
                return response.status_code in [200, 999]
            except:
                # Se não conseguir acessar, considera válido baseado no formato
                return True

        except Exception:
            return False