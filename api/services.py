import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Adicionar path para imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.agent_loader import carregar_agentes_dinamicamente, salvar_configuracao_agentes, validar_configuracao_agente
from orchestrator.triage_agent import TriageAgent
from semantic_kernel.contents import ChatMessageContent
import logging

logger = logging.getLogger(__name__)

# Constantes
SYSTEM_NOT_INITIALIZED = "Sistema não inicializado"


class AgentService:
    """Serviço para gerenciar agentes"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.triage_agent: Optional[TriageAgent] = None
        self._initialize_system()
    
    def _initialize_system(self):
        """Inicializa o sistema de agentes"""
        try:
            agentes_config = carregar_agentes_dinamicamente()
            self.triage_agent = TriageAgent(agentes_config, self.api_key)
            self.triage_agent.iniciar_runtime()
            logger.info("Sistema de agentes inicializado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao inicializar sistema: {e}")
            raise
    
    def get_all_agents(self) -> List[Dict[str, Any]]:
        """Retorna todos os agentes configurados"""
        try:
            return carregar_agentes_dinamicamente()
        except Exception as e:
            logger.error(f"Erro ao carregar agentes: {e}")
            raise
    
    def get_agent_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Retorna um agente específico pelo nome"""
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
        """Cria um novo agente"""
        try:
            # Validar configuração
            validar_configuracao_agente(agent_config)
            
            # Verificações adicionais de segurança
            if not agent_config.get("name", "").strip():
                raise ValueError("Nome do agente não pode ser vazio")
            
            if len(agent_config.get("name", "")) > 50:
                raise ValueError("Nome do agente muito longo (máximo 50 caracteres)")
            
            # Carregar agentes existentes
            agentes = carregar_agentes_dinamicamente()
            
            # Verificar se já existe
            for agente in agentes:
                if agente["name"] == agent_config["name"]:
                    raise ValueError(f"Agente com nome '{agent_config['name']}' já existe")
            
            # Limitar número máximo de agentes
            if len(agentes) >= 10:
                raise ValueError("Número máximo de agentes atingido (10)")
            
            # Adicionar novo agente
            agentes.append(agent_config)
            
            # Salvar configuração
            salvar_configuracao_agentes(agentes)
            
            # Reinicializar sistema
            self._reinitialize_system()
            
            logger.info(f"Agente '{agent_config['name']}' criado com sucesso")
            return agent_config
            
        except Exception as e:
            logger.error(f"Erro ao criar agente: {e}")
            raise
    
    def update_agent(self, name: str, agent_config: Dict[str, Any]) -> Dict[str, Any]:
        """Atualiza um agente existente"""
        try:
            # Validar configuração
            validar_configuracao_agente(agent_config)
            
            # Carregar agentes existentes
            agentes = carregar_agentes_dinamicamente()
            
            # Encontrar e atualizar agente
            found = False
            for i, agente in enumerate(agentes):
                if agente["name"] == name:
                    agentes[i] = agent_config
                    found = True
                    break
            
            if not found:
                raise ValueError(f"Agente '{name}' não encontrado")
            
            # Salvar configuração
            salvar_configuracao_agentes(agentes)
            
            # Reinicializar sistema
            self._reinitialize_system()
            
            logger.info(f"Agente '{name}' atualizado com sucesso")
            return agent_config
            
        except Exception as e:
            logger.error(f"Erro ao atualizar agente {name}: {e}")
            raise
    
    def delete_agent(self, name: str) -> bool:
        """Remove um agente"""
        try:
            # Não permitir remover TriageAgent
            if name == "TriageAgent":
                raise ValueError("Não é possível remover o TriageAgent")
            
            # Carregar agentes existentes
            agentes = carregar_agentes_dinamicamente()
            
            # Remover agente
            agentes_filtrados = [agente for agente in agentes if agente["name"] != name]
            
            if len(agentes_filtrados) == len(agentes):
                raise ValueError(f"Agente '{name}' não encontrado")
            
            # Salvar configuração
            salvar_configuracao_agentes(agentes_filtrados)
            
            # Reinicializar sistema
            self._reinitialize_system()
            
            logger.info(f"Agente '{name}' removido com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao remover agente {name}: {e}")
            raise
    
    async def process_message(self, message: str) -> Dict[str, Any]:
        """Processa uma mensagem através do sistema de agentes"""
        try:
            if not self.triage_agent:
                raise RuntimeError(SYSTEM_NOT_INITIALIZED)
            
            # Processar mensagem
            response = await self.triage_agent.processar_mensagem(message)
            
            # Pegar a última resposta do histórico para identificar o agente e a resposta real
            historico = self.triage_agent.obter_historico()
            
            # Procurar pela última mensagem de assistente (não de usuário)
            agent_name = "Sistema"
            agent_response = response  # fallback para a resposta do sistema
            
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
            
            return {
                "success": True,
                "response": agent_response,
                "agent_name": agent_name,
                "timestamp": datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Erro ao processar mensagem: {e}")
            return {
                "success": False,
                "response": f"Erro ao processar mensagem: {str(e)}",
                "agent_name": "Sistema",
                "timestamp": datetime.now()
            }
    
    def get_chat_history(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """Retorna o histórico de chat"""
        try:
            if not self.triage_agent:
                raise RuntimeError(SYSTEM_NOT_INITIALIZED)
            
            # Pegar histórico do memory manager
            historico = self.triage_agent.obter_historico()
            
            # Converter para formato da API
            messages = []
            for msg in historico:
                if hasattr(msg, 'content') and msg.content:
                    messages.append({
                        "role": msg.role.value if hasattr(msg.role, 'value') else str(msg.role),
                        "name": msg.name,
                        "content": msg.content,
                        "timestamp": datetime.now(),  # Poderia ser extraído do metadata se disponível
                        "ai_model_id": getattr(msg, 'ai_model_id', None)
                    })
            
            # Aplicar limite se especificado
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
        """Limpa o histórico de chat"""
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
        """Retorna status do sistema"""
        try:
            agentes = carregar_agentes_dinamicamente()
            
            # Pegar timestamp da última mensagem se disponível
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
        """Reinicializa o sistema após mudanças na configuração"""
        try:
            # Parar runtime atual se existir
            if self.triage_agent and self.triage_agent.runtime:
                import asyncio
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Se já estamos em um loop assíncrono, não podemos usar run_until_complete
                    # Agendar para parar mais tarde
                    task = asyncio.create_task(self.triage_agent.parar_runtime())
                    # Salvar referência da task para evitar garbage collection
                    self._cleanup_task = task
                else:
                    asyncio.run(self.triage_agent.parar_runtime())
            
            # Reinicializar
            self._initialize_system()
            
        except Exception as e:
            logger.error(f"Erro ao reinicializar sistema: {e}")
            raise
    
    async def cleanup(self):
        """Limpa recursos do sistema"""
        try:
            if self.triage_agent and self.triage_agent.runtime:
                await self.triage_agent.parar_runtime()
            logger.info("Sistema limpo com sucesso")
        except Exception as e:
            logger.error(f"Erro durante cleanup: {e}")
