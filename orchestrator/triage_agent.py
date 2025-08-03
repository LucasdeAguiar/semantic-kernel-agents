import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent, HandoffOrchestration, OrchestrationHandoffs
from semantic_kernel.agents.runtime import InProcessRuntime
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.contents import ChatMessageContent, AuthorRole
from core.memory_manager import ChatHistoryManager
import logging

logger = logging.getLogger(__name__)


class TriageAgent:
    """
    Agente orquestrador que implementa handoff architecture
    para roteamento dinâmico entre agentes especialistas.
    """
    
    def __init__(self, agentes_config: list[dict], api_key: str):
        self.agentes_config = agentes_config
        self.api_key = api_key
        self.specialist_agents = {}
        self.handoff_orchestration = None
        self.runtime = None
        self.memory_manager = ChatHistoryManager()
        self._setup_agents()
        self._setup_handoff_orchestration()
    
    def _setup_agents(self):
        """Configura todos os agentes (triage + especialistas)"""
        
        # Criar o serviço OpenAI
        service = OpenAIChatCompletion(
            service_id="openai-triage",
            ai_model_id="gpt-4",
            api_key=self.api_key
        )
        
        kernel = Kernel()
        kernel.add_service(service)
        
        # Gerar dinamicamente a lista de agentes especialistas disponíveis
        specialists_info = []
        for config in self.agentes_config:
            if config["name"] != "TriageAgent":
                specialists_info.append(f"- {config['name']}: {config['description']}")
        
        # Criar instruções mais simples para evitar conflitos
        dynamic_instructions = f"""Você é o agente de triagem. Direcione usuários para especialistas.

ESPECIALISTAS:
{chr(10).join(specialists_info)}

Use as funções transfer_to_* para direcionar. Seja breve."""
        
        # Criar o agente de triagem principal
        self.triage_agent = ChatCompletionAgent(
            name="TriageAgent",
            description="Agente orquestrador que direciona usuários para especialistas adequados",
            instructions=dynamic_instructions,
            service=service
        )
        
        # Criar agentes especialistas dinamicamente
        for config in self.agentes_config:
            if config["name"] != "TriageAgent":  # Pular o triage agent
                from agents.specialist_agent import criar_agente_especialista
                specialist_agent = criar_agente_especialista(config, self.api_key)
                self.specialist_agents[config["name"]] = specialist_agent
    
    def _setup_handoff_orchestration(self):
        """Configura a orquestração de handoff entre agentes - seguindo a documentação oficial"""
        
        # Criar handoffs usando o padrão da documentação
        handoffs = (
            OrchestrationHandoffs()
            .add_many(
                source_agent=self.triage_agent.name,
                target_agents={
                    agent_name: f"Transfer to this agent if the issue is related to {agent.description.lower()}"
                    for agent_name, agent in self.specialist_agents.items()
                }
            )
        )
        
        # Adicionar handoffs de volta para o triage (cada especialista pode voltar)
        for agent_name in self.specialist_agents.keys():
            handoffs.add(
                source_agent=agent_name,
                target_agent=self.triage_agent.name,
                description="Transfer back to triage if the issue is not related to my expertise"
            )
        
        # Criar lista de todos os agentes
        all_agents = [self.triage_agent] + list(self.specialist_agents.values())
        
        # Configurar orquestração seguindo exatamente a documentação
        self.handoff_orchestration = HandoffOrchestration(
            members=all_agents,
            handoffs=handoffs,
            agent_response_callback=self._agent_response_callback,
            human_response_function=self._human_response_function
        )
    
    def _agent_response_callback(self, message: ChatMessageContent) -> None:
        """Callback para capturar respostas dos agentes"""
        # Salvar na memória
        self.memory_manager.add_message(message)
        
        # Log limpo - mostrar mensagem completa sem truncar
        agent_name = message.name or "Sistema"
        content = message.content
        
        # Só truncar se for extremamente longo (mais de 1000 chars)
        if len(content) > 1000:
            content = content[:1000] + "...\n[Mensagem truncada - muito longa]"
        
        print(f"🤖 {agent_name}: {content}")
    
    def _human_response_function(self) -> ChatMessageContent:
        """Função para obter input do usuário (human-in-the-loop)"""
        # Para modo automatizado, retornar mensagem vazia
        message = ChatMessageContent(
            role=AuthorRole.USER,
            content=""
        )
        return message
    
    def iniciar_runtime(self):
        """Inicia o runtime de orquestração"""
        self.runtime = InProcessRuntime()
        self.runtime.start()
    
    async def parar_runtime(self):
        """Para o runtime de orquestração"""
        if self.runtime:
            await self.runtime.stop_when_idle()
    
    async def processar_mensagem(self, mensagem: str) -> str:
        """
        Método principal para processar mensagens usando handoff orchestration com contexto otimizado
        """
        try:
            if not self.runtime:
                self.iniciar_runtime()
            
            # Criar mensagem do usuário
            user_message = ChatMessageContent(
                role=AuthorRole.USER,
                content=mensagem
            )
            
            # IMPORTANTE: Salvar SEMPRE no histórico completo (nunca deletar)
            self.memory_manager.add_message(user_message)
            
            # Verificar se temos muitas mensagens (só avisar, não deletar)
            history_count = len(self.memory_manager.get_history())
            if history_count > 50:
                print(f"📊 Histórico tem {history_count} mensagens (contexto será otimizado automaticamente)")
            
            # Executar orquestração
            orchestration_result = await asyncio.wait_for(
                self.handoff_orchestration.invoke(
                    task=user_message,
                    runtime=self.runtime
                ),
                timeout=25.0
            )
            
            result = await orchestration_result.get()
            return str(result) if result else "Conversa finalizada."
            
        except asyncio.TimeoutError:
            error_msg = "⏰ Timeout: O processamento demorou muito. Tente novamente."
            logger.error(error_msg)
            return error_msg
            
        except Exception as e:
            error_str = str(e)
            error_msg = f"❌ Erro ao processar mensagem: {error_str[:100]}..."
            logger.error(error_msg)
            
            # Se for erro do modelo, só avisar (não deletar histórico)
            if "model_error" in error_str or "invalid content" in error_str:
                logger.info("🔄 Erro de modelo detectado. Sistema otimizará contexto automaticamente.")
                return "🔄 Sistema detectou sobrecarga. Tente reformular sua pergunta de forma mais simples."
            
            return error_msg
    
    def obter_historico(self) -> list[ChatMessageContent]:
        """Retorna o histórico completo da conversa"""
        return self.memory_manager.get_history()
    
    def limpar_historico(self):
        """Limpa o histórico da conversa"""
        self.memory_manager.clear_history()
