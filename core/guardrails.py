import json
from pathlib import Path
from typing import List, Dict
from openai import OpenAI
import logging

logger = logging.getLogger(__name__)


class GuardrailResult:
    def __init__(self, blocked: bool, reason: str = "", guardrail_name: str = ""):
        self.blocked = blocked
        self.reason = reason
        self.guardrail_name = guardrail_name

    def __repr__(self):
        return f"<GuardrailResult blocked={self.blocked} reason='{self.reason}'>"


class GuardrailsManager:
    def __init__(self, config_path="config/guardrails_config.json", api_key=None):
        self.guardrails_config = self._load_config(config_path)
        self.client = OpenAI(api_key=api_key) if api_key else None

    def _load_config(self, path: str) -> List[Dict]:
        try:
            full_path = Path(path).resolve()
            logger.info(f"[GUARDRAIL] Lendo config de: {full_path}")
            with open(full_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                logger.info(f"[GUARDRAIL] Carregados {len(config)} guardrails")
                return config
        except Exception as e:
            logger.error(f"[GUARDRAIL] Erro ao carregar guardrails: {e}")
            return []

    def analisar_mensagem(self, texto: str) -> GuardrailResult:
        """
        Analisa mensagem aplicando guardrails definidos na configuração.
        Suporta tanto keyword quanto semantic guardrails.
        """
        logger.debug(f"[GUARDRAIL] Analisando mensagem: {texto[:50]}...")
        
        for rule in self.guardrails_config:
            if not rule.get("enabled", True):
                continue

            rule_name = rule.get("name", "Unknown")
            rule_type = rule.get("type", "keyword")
            
            logger.debug(f"[GUARDRAIL] Verificando regra: {rule_name} (tipo: {rule_type})")

            if rule_type == "keyword":
                result = self._check_keyword_guardrail(texto, rule)
                if result.blocked:
                    return result

            elif rule_type == "semantic" and self.client:
                result = self._check_semantic_guardrail(texto, rule)
                if result.blocked:
                    return result

        logger.debug(f"[GUARDRAIL] Nenhuma violação detectada para: {texto[:50]}...")
        return GuardrailResult(blocked=False)

    def _check_keyword_guardrail(self, texto: str, rule: Dict) -> GuardrailResult:
        """Verifica guardrails baseados em palavras-chave"""
        keywords = rule.get("keywords", [])
        
        for palavra in keywords:
            if palavra.lower() in texto.lower():
                logger.warning(f"[GUARDRAIL] 🚫 BLOQUEADO por palavra-chave: '{palavra}' na frase: {texto}")
                return GuardrailResult(
                    blocked=True,
                    reason=f"Contém palavra proibida: '{palavra}'",
                    guardrail_name=rule["name"]
                )
        
        return GuardrailResult(blocked=False)

    def _check_semantic_guardrail(self, texto: str, rule: Dict) -> GuardrailResult:
        """
        Verifica guardrails semânticos usando OpenAI.
        Implementação simples e robusta.
        """
        try:
            description = rule.get("description", "")
            name = rule.get("name", "SemanticGuardrail")
            
            prompt = f"""Analise se a seguinte mensagem viola a política: "{description}"

Mensagem: "{texto}"

Responda apenas com:
- "BLOCK" se a mensagem viola a política (mesmo que indiretamente)
- "ALLOW" se a mensagem não viola a política

Seguido de uma breve explicação em uma linha."""

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Você é um sistema de moderação que analisa se mensagens violam políticas específicas. Seja rigoroso mas justo."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.1
            )
            
            result_text = response.choices[0].message.content.strip()
            
            if result_text.startswith("BLOCK"):
                explanation = result_text.replace("BLOCK", "").strip()
                logger.warning(f"[GUARDRAIL] 🔥 BLOQUEADO por {name}: {explanation}")
                return GuardrailResult(
                    blocked=True,
                    reason=explanation or "Violação detectada por análise semântica",
                    guardrail_name=name
                )
            
            logger.debug(f"[GUARDRAIL] ✅ Aprovado por {name}")
            return GuardrailResult(blocked=False)
            
        except Exception as e:
            logger.error(f"[GUARDRAIL] Erro ao executar guardrail semântico ({rule.get('name', 'Unknown')}): {e}")
            return GuardrailResult(blocked=False)
