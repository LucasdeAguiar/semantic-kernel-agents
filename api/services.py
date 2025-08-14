import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.agent_loader import carregar_agentes_dinamicamente, salvar_configuracao_agentes, validar_configuracao_agente
from orchestrator.triage_agent import TriageAgent
from semantic_kernel.contents import ChatMessageContent
import logging

logger = logging.getLogger(__name__)

SYSTEM_NOT_INITIALIZED = "Sistema não inicializado"

class AgentService:
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.triage_agent: Optional[TriageAgent] = None
        self._initialize_system()
    
    def _initialize_system(self):
        try:
            agentes_config = carregar_agentes_dinamicamente()
            self.triage_agent = TriageAgent(agentes_config, self.api_key)
            self.triage_agent.iniciar_runtime()
            logger.info("Sistema de agentes inicializado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao inicializar sistema: {e}")
            raise
    
    def get_all_agents(self) -> List[Dict[str, Any]]:
        try:
            return carregar_agentes_dinamicamente()
        except Exception as e:
            logger.error(f"Erro ao carregar agentes: {e}")
            raise
    
    def get_agent_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        try:
            agentes = carregar_agentes_dinamicamente()
            for agente in agentes:
                if agente["name"] == name:
                    return agente
            return None
        except Exception as e:
            logger.error(f"Erro ao buscar agente {name}: {e}")
            raise
    
    def create_agent(self, agent_config: Dict[str, Any]) -> Dict[str, Any]:
        try:
            validar_configuracao_agente(agent_config)
            
            if not agent_config.get("name", "").strip():
                raise ValueError("Nome do agente não pode ser vazio")
            
            if len(agent_config.get("name", "")) > 50:
                raise ValueError("Nome do agente muito longo (máximo 50 caracteres)")
            
            agentes = carregar_agentes_dinamicamente()
            
            for agente in agentes:
                if agente["name"] == agent_config["name"]:
                    raise ValueError(f"Agente com nome '{agent_config['name']}' já existe")
            
            if len(agentes) >= 10:
                raise ValueError("Número máximo de agentes atingido (10)")
            
            agentes.append(agent_config)
            
            salvar_configuracao_agentes(agentes)
            
            self._reinitialize_system()
            
            logger.info(f"Agente '{agent_config['name']}' criado com sucesso")
            return agent_config
            
        except Exception as e:
            logger.error(f"Erro ao criar agente: {e}")
            raise
    
    def update_agent(self, name: str, agent_config: Dict[str, Any]) -> Dict[str, Any]:
        try:
            validar_configuracao_agente(agent_config)
            
            agentes = carregar_agentes_dinamicamente()
            
            found = False
            for i, agente in enumerate(agentes):
                if agente["name"] == name:
                    agentes[i] = agent_config
                    found = True
                    break
            
            if not found:
                raise ValueError(f"Agente '{name}' não encontrado")
            
            salvar_configuracao_agentes(agentes)
            
            self._reinitialize_system()
            
            logger.info(f"Agente '{name}' atualizado com sucesso")
            return agent_config
            
        except Exception as e:
            logger.error(f"Erro ao atualizar agente {name}: {e}")
            raise
    
    def delete_agent(self, name: str) -> bool:
        """Remove um agente"""
        try:
            if name == "TriageAgent":
                raise ValueError("Não é possível remover o TriageAgent")
            
            agentes = carregar_agentes_dinamicamente()
            
            agentes_filtrados = [agente for agente in agentes if agente["name"] != name]
            
            if len(agentes_filtrados) == len(agentes):
                raise ValueError(f"Agente '{name}' não encontrado")
            
            salvar_configuracao_agentes(agentes_filtrados)
            
            self._reinitialize_system()
            
            logger.info(f"Agente '{name}' removido com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao remover agente {name}: {e}")
            raise
    
    async def process_message(self, message: str) -> Dict[str, Any]:
        import time
        start_time = time.time()
        
        try:
            if not self.triage_agent:
                raise RuntimeError(SYSTEM_NOT_INITIALIZED)
            
            response = await self.triage_agent.processar_mensagem(message)
            
            # Calcular tempo de resposta
            end_time = time.time()
            response_time = round(end_time - start_time, 3)
            
            # Verificar se a resposta é de bloqueio por guardrails ou moderação
            is_blocked_message = (
                "bloqueada por regras de segurança" in response or
                "Conteúdo sensível detectado" in response or
                "⛔" in response or
                "⚠️" in response
            )
            
            if is_blocked_message:
                # Para mensagens bloqueadas, usar a resposta diretamente sem buscar no histórico
                agent_name = "Sistema"
                agent_response = response
            else:
                # Para mensagens normais, buscar o agente que respondeu no histórico
                historico = self.triage_agent.obter_historico()
                
                agent_name = "Sistema"
                agent_response = response  
                
                for msg in reversed(historico):
                    if (hasattr(msg, 'role') and 
                        msg.role.value == "assistant" and 
                        msg.name and 
                        msg.name != "Sistema" and
                        hasattr(msg, 'content') and 
                        msg.content):
                        
                        agent_name = msg.name
                        agent_response = msg.content
                        break
            
            # Log da performance
            logger.info(f"⏱️ Tempo de resposta: {response_time}s | Agente: {agent_name} | Mensagem: {message[:50]}...")
            
            return {
                "success": True,
                "response": agent_response,
                "agent_name": agent_name,
                "timestamp": datetime.now(),
                "response_time_seconds": response_time,
                "performance_metrics": {
                    "total_time": response_time,
                    "agent_used": agent_name,
                    "message_length": len(message)
                }
            }
            
        except Exception as e:
            end_time = time.time()
            response_time = round(end_time - start_time, 3)
            
            logger.error(f"⏱️ Erro após {response_time}s | Mensagem: {message[:50]}... | Erro: {e}")
            return {
                "success": False,
                "response": f"Erro ao processar mensagem: {str(e)}",
                "agent_name": "Sistema",
                "timestamp": datetime.now(),
                "response_time_seconds": response_time,
                "performance_metrics": {
                    "total_time": response_time,
                    "agent_used": "Sistema",
                    "error": str(e),
                    "message_length": len(message)
                }
            }
    
    def get_chat_history(self, limit: Optional[int] = None) -> Dict[str, Any]:
        try:
            if not self.triage_agent:
                raise RuntimeError(SYSTEM_NOT_INITIALIZED)
            
            historico = self.triage_agent.obter_historico()
            
            messages = []
            for msg in historico:
                if hasattr(msg, 'content') and msg.content:
                    messages.append({
                        "role": msg.role.value if hasattr(msg.role, 'value') else str(msg.role),
                        "name": msg.name,
                        "content": msg.content,
                        "timestamp": datetime.now(), 
                        "ai_model_id": getattr(msg, 'ai_model_id', None)
                    })
            
            if limit:
                messages = messages[-limit:]
            
            return {
                "success": True,
                "total_messages": len(messages),
                "messages": messages
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter histórico: {e}")
            return {
                "success": False,
                "total_messages": 0,
                "messages": []
            }
    
    def clear_history(self) -> bool:
        try:
            if not self.triage_agent:
                raise RuntimeError(SYSTEM_NOT_INITIALIZED)
            
            self.triage_agent.limpar_historico()
            logger.info("Histórico limpo com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao limpar histórico: {e}")
            return False
    
    def get_system_status(self) -> Dict[str, Any]:
        try:
            agentes = carregar_agentes_dinamicamente()
            
            last_message_time = None
            if self.triage_agent:
                historico = self.triage_agent.obter_historico()
                if historico:
                    last_message_time = datetime.now()  # Simplificado
            
            return {
                "status": "active" if self.triage_agent and self.triage_agent.runtime else "inactive",
                "total_agents": len(agentes),
                "active_runtime": bool(self.triage_agent and self.triage_agent.runtime),
                "last_message_time": last_message_time
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter status: {e}")
            return {
                "status": "error",
                "total_agents": 0,
                "active_runtime": False,
                "last_message_time": None
            }
    
    def _reinitialize_system(self):
        try:
            if self.triage_agent and self.triage_agent.runtime:
                import asyncio
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    task = asyncio.create_task(self.triage_agent.parar_runtime())
             
                    self._cleanup_task = task
                else:
                    asyncio.run(self.triage_agent.parar_runtime())
            
            self._initialize_system()
            
        except Exception as e:
            logger.error(f"Erro ao reinicializar sistema: {e}")
            raise
    
    async def cleanup(self):
        try:
            if self.triage_agent and self.triage_agent.runtime:
                await self.triage_agent.parar_runtime()
            logger.info("Sistema limpo com sucesso")
        except Exception as e:
            logger.error(f"Erro durante cleanup: {e}")
    
    # ==================== MÉTODOS PARA GUARDRAILS ====================
    
    def get_all_guardrails(self) -> List[Dict[str, Any]]:
        try:
            import json
            from pathlib import Path
            
            guardrails_file = Path("config/guardrails_config.json")
            if not guardrails_file.exists():
                return []
            
            with open(guardrails_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Erro ao carregar guardrails: {e}")
            raise
    
    def get_guardrail_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        try:
            guardrails = self.get_all_guardrails()
            for guardrail in guardrails:
                if guardrail["name"] == name:
                    return guardrail
            return None
        except Exception as e:
            logger.error(f"Erro ao buscar guardrail {name}: {e}")
            raise
    
    def create_guardrail(self, guardrail_config: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if not guardrail_config.get("name", "").strip():
                raise ValueError("Nome do guardrail não pode ser vazio")
            
            if len(guardrail_config.get("name", "")) > 50:
                raise ValueError("Nome do guardrail muito longo (máximo 50 caracteres)")
            
            guardrails = self.get_all_guardrails()
            
            for guardrail in guardrails:
                if guardrail["name"] == guardrail_config["name"]:
                    raise ValueError(f"Guardrail com nome '{guardrail_config['name']}' já existe")
            
            # Limitar número máximo de guardrails
            if len(guardrails) >= 20:
                raise ValueError("Número máximo de guardrails atingido (20)")
            
            if "enabled" not in guardrail_config:
                guardrail_config["enabled"] = True
            
            guardrails.append(guardrail_config)
            
            self._save_guardrails_config(guardrails)
            
            self._reinitialize_system()
            
            logger.info(f"Guardrail '{guardrail_config['name']}' criado com sucesso")
            return guardrail_config
            
        except Exception as e:
            logger.error(f"Erro ao criar guardrail: {e}")
            raise
    
    def update_guardrail(self, name: str, guardrail_config: Dict[str, Any]) -> Dict[str, Any]:
        try:
            guardrails = self.get_all_guardrails()
            
            found = False
            for i, guardrail in enumerate(guardrails):
                if guardrail["name"] == name:
                    if "name" not in guardrail_config:
                        guardrail_config["name"] = name
                    guardrails[i] = guardrail_config
                    found = True
                    break
            
            if not found:
                raise ValueError(f"Guardrail '{name}' não encontrado")
        
            self._save_guardrails_config(guardrails)
            
            self._reinitialize_system()
            
            logger.info(f"Guardrail '{name}' atualizado com sucesso")
            return guardrail_config
            
        except Exception as e:
            logger.error(f"Erro ao atualizar guardrail {name}: {e}")
            raise
    
    def delete_guardrail(self, name: str) -> bool:
        try:
            guardrails = self.get_all_guardrails()
            
            guardrails_filtrados = [g for g in guardrails if g["name"] != name]
            
            if len(guardrails_filtrados) == len(guardrails):
                raise ValueError(f"Guardrail '{name}' não encontrado")
            
            self._save_guardrails_config(guardrails_filtrados)
            
            self._reinitialize_system()
            
            logger.info(f"Guardrail '{name}' removido com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao remover guardrail {name}: {e}")
            raise
    
    def _save_guardrails_config(self, guardrails: List[Dict[str, Any]]) -> None:
        try:
            import json
            from pathlib import Path
            
            config_path = Path("config/guardrails_config.json")
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(guardrails, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Configuração de {len(guardrails)} guardrails salva")
            
        except Exception as e:
            logger.error(f"Erro ao salvar configuração de guardrails: {e}")
            raise
