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
from core.moderation import ContentModerator
from core.guardrails import GuardrailsManager

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
        self.moderator = ContentModerator(api_key=self.api_key)
        self.guardrails = GuardrailsManager(api_key=self.api_key)

        self._setup_agents()
        self._setup_handoff_orchestration()
    
    def _setup_agents(self):
        
        service = OpenAIChatCompletion(
            service_id="openai-triage",
            ai_model_id="gpt-4.1",  
            api_key=self.api_key
        )
        
        kernel = Kernel()
        kernel.add_service(service)
        
        specialists_info = []
        for config in self.agentes_config:
            if config["name"] != "TriageAgent":
                specialists_info.append(f"- {config['name']}: {config['description']}")

        RECOMMENDED_PROMPT_PREFIX = (
            "# System context\n"
            "You are part of a multi-agent system called the Agents SDK, designed to make agent "
            "coordination and execution easy. Agents uses two primary abstraction: **Agents** and "
            "**Handoffs**. An agent encompasses instructions and tools and can hand off a "
            "conversation to another agent when appropriate. "
            "Handoffs are achieved by calling a handoff function, generally named "
            "`transfer_to_<agent_name>`. Transfers between agents are handled seamlessly in the background;"
            " do not mention or draw attention to these transfers in your conversation with the user.\n"
        )

        dynamic_instructions = (
            f"{RECOMMENDED_PROMPT_PREFIX} "
            "You are an Orchestrator agent. Analyze the user's question and:\n"
            "1. If the question relates to any available specialist (flights, HR, tech support), immediately hand off to the appropriate agent\n" 
            "2. If the question is completely outside our scope (general knowledge, unrelated topics), respond politely explaining our limitations\n"
            "3. If the question is ambiguous, ask for clarification to properly route\n"
            "NEVER respond with specialist domain content - only handle routing, out-of-scope cases, and clarifications."
        )
        
        self.triage_agent = ChatCompletionAgent(
            name="TriageAgent",
            description="An Orchestrator agent that can delegate a customer's request to the appropriate agent.",
            instructions=dynamic_instructions,
            service=service
        )
        
        for config in self.agentes_config:
            if config["name"] != "TriageAgent": 
                from agents.specialist_agent import criar_agente_especialista
                specialist_agent = criar_agente_especialista(config, self.api_key)
                self.specialist_agents[config["name"]] = specialist_agent
    
    def _setup_handoff_orchestration(self):
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
        
        for agent_name in self.specialist_agents.keys():
            handoffs.add(
                source_agent=agent_name,
                target_agent=self.triage_agent.name,
                description="Transfer back to triage if the issue is not related to my expertise"
            )
        
        all_agents = [self.triage_agent] + list(self.specialist_agents.values())
        
        self.handoff_orchestration = HandoffOrchestration(
            members=all_agents,
            handoffs=handoffs,
            agent_response_callback=self._agent_response_callback
        )
    
    def _agent_response_callback(self, message: ChatMessageContent) -> None:
        # Adicionar mensagem ao histórico principal
        self.memory_manager.add_message(message)
        
        # Salvar histórico automaticamente após cada mensagem
        try:
            self.memory_manager.save_history()
            logger.debug(f"💾 Histórico salvo automaticamente após mensagem de {message.name}")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao salvar histórico: {e}")
        
        # Atualizar o histórico na orquestração para o próximo handoff
        if hasattr(self.handoff_orchestration, '_history'):
            self.handoff_orchestration._history = self.memory_manager.get_chat_history()
        
        message_key = f"{message.name}:{message.content[:100]}"
        if not hasattr(self, '_displayed_messages'):
            self._displayed_messages = set()
        
        # Capturar respostas de agentes
        if (hasattr(message, 'role') and 
            message.role.value == "assistant" and 
            message.name and 
            message.name != "Sistema"):
            
            if message.name == "TriageAgent":
                # TriageAgent só deve responder para OOS ou clarificações
                # Detectar se está tentando fazer handoff textualmente
                handoff_indicators = [
                    'vou encaminhar', 'direcionando', 'transferindo', 'redirecionando',
                    'aguarde um instante', 'setor responsável', 'especialista', 'departamento'
                ]
                
                if (any(keyword in message.content.lower() for keyword in ['transfer', 'handoff', 'delegate', 'routing']) or
                    any(indicator in message.content.lower() for indicator in handoff_indicators)):
                    logger.warning(f"🚫 TriageAgent tentou responder com handoff textual (ignorado): {message.content[:50]}...")
                    return
                
                # Resposta válida do TriageAgent (OOS ou clarificação)
                self._last_agent_response = {
                    "name": message.name,
                    "content": message.content
                }
                logger.info(f"🎯 TriageAgent respondeu validamente: {message.content[:50]}...")
                
            else:
                # Agente especialista
                # Verificar se é resposta OOS (fora de escopo)
                if self._is_out_of_scope_response(message.content):
                    logger.warning(f"🚫 {message.name} respondeu OOS: {message.content[:50]}...")
                    # NÃO capturar respostas OOS - deixar o TriageAgent gerenciar
                    return
                
                # Resposta válida de agente especialista
                self._last_agent_response = {
                    "name": message.name,
                    "content": message.content
                }
                logger.info(f"✅ Resposta capturada de {message.name}: {message.content[:50]}...")
        
        if message_key not in self._displayed_messages:
            self._displayed_messages.add(message_key)
            
            agent_name = message.name or "Sistema"
            content = message.content
            
            if len(content) > 1000:
                content = content[:1000] + "...\n[Mensagem truncada - muito longa]"
            
            # Só mostrar no console se não for resposta indevida do TriageAgent
            if message.name != "TriageAgent" or "transfer" in content.lower():
                print(f"🤖 {agent_name}: {content}")
        
        if len(self._displayed_messages) > 100:
            self._displayed_messages.clear()
    
    def iniciar_runtime(self):
        self.runtime = InProcessRuntime()
        self.runtime.start()
    
    async def parar_runtime(self):
        if self.runtime:
            await self.runtime.stop_when_idle()
    
    async def processar_mensagem(self, mensagem: str) -> str:
        import time
        start_time = time.time()
        
        try:
            if not self.runtime:
                self.iniciar_runtime()

            self._last_agent_response = None

            # Tempo de análise de guardrails
            guardrail_start = time.time()
            guardrail_result = self.guardrails.analisar_mensagem(mensagem)
            guardrail_time = round(time.time() - guardrail_start, 3)
            
            if guardrail_result.blocked:
                total_time = round(time.time() - start_time, 3)
                logger.info(f"⏱️ Guardrails: {guardrail_time}s | Total: {total_time}s (BLOQUEADO)")
                
                blocked_message = ChatMessageContent(
                    role=AuthorRole.ASSISTANT,
                    content=f"⛔ Sua mensagem foi bloqueada por regras de segurança ({guardrail_result.guardrail_name}): {guardrail_result.reason}",
                    name="Sistema"
                )
                self.memory_manager.add_message(blocked_message)
                print(f"🤖 Sistema: {blocked_message.content}")
                return blocked_message.content

            # Tempo de análise de moderação
            moderation_start = time.time()
            moderation_result = self.moderator.analisar_mensagem(mensagem)
            moderation_time = round(time.time() - moderation_start, 3)
            
            if moderation_result.flagged:
                total_time = round(time.time() - start_time, 3)
                logger.warning(f"⏱️ Moderação: {moderation_time}s | Total: {total_time}s | 🛑 Mensagem bloqueada por moderação")
                
                categorias = [k for k, v in moderation_result.categories.items() if v]
                
                blocked_message = ChatMessageContent(
                    role=AuthorRole.ASSISTANT,
                    content=f"⚠️ Conteúdo sensível detectado ({', '.join(categorias)}). A mensagem foi bloqueada.",
                    name="Sistema"
                )
                self.memory_manager.add_message(blocked_message)
                print(f"🤖 Sistema: {blocked_message.content}")
                
                return blocked_message.content
            
            user_message = ChatMessageContent(
                role=AuthorRole.USER,
                content=mensagem
            )
            
            self.memory_manager.add_message(user_message)
            
            # Tempo de criação de contexto
            context_start = time.time()
            context_summary = self._create_context_summary()
            enhanced_message = f"{context_summary}\n\nUsuário atual: {mensagem}"
            context_time = round(time.time() - context_start, 3)
            
            print(f"📋 Processando com contexto resumido ({len(self.memory_manager.get_history())} mensagens no histórico)")
            print(f"🔍 Contexto enviado: {len(context_summary)} caracteres")
            
            # Detectar palavras-chave para forçar handoff direto (evitar TriageAgent responder)
            tech_keywords = ['senha', 'email', 'e-mail', 'login', 'acesso', 'cadastrado', 'redefinir']
            hr_keywords = ['benefício', 'férias', 'licença', 'rh', 'recursos humanos']
            flight_keywords = ['voo', 'assento', 'reserva', 'cancelar', 'status']
            
            mensagem_lower = mensagem.lower()
            
            # Forçar handoff direto baseado em palavras-chave
            if any(keyword in mensagem_lower for keyword in tech_keywords):
                logger.info("🎯 Detectado problema técnico - forçando handoff direto para TechSupportAgent")
                fallback_result = await self._force_handoff_to_agent("TechSupportAgent", mensagem)
                if fallback_result:
                    total_time = round(time.time() - start_time, 3)
                    logger.info(f"⏱️ DIRETO TECH - Total: {total_time}s")
                    return fallback_result
                    
            elif any(keyword in mensagem_lower for keyword in hr_keywords):
                logger.info("🎯 Detectado consulta RH - forçando handoff direto para HRAgent")
                fallback_result = await self._force_handoff_to_agent("HRAgent", mensagem)
                if fallback_result:
                    total_time = round(time.time() - start_time, 3)
                    logger.info(f"⏱️ DIRETO HR - Total: {total_time}s")
                    return fallback_result
                    
            elif any(keyword in mensagem_lower for keyword in flight_keywords):
                # Determinar se é SeatBooking ou FlightStatus
                if any(word in mensagem_lower for word in ['assento', 'trocar', 'alterar']):
                    logger.info("🎯 Detectado troca de assento - forçando handoff direto para SeatBookingAgent")
                    fallback_result = await self._force_handoff_to_agent("SeatBookingAgent", mensagem)
                else:
                    logger.info("🎯 Detectado consulta voo - forçando handoff direto para FlightStatusAgent")
                    fallback_result = await self._force_handoff_to_agent("FlightStatusAgent", mensagem)
                    
                if fallback_result:
                    total_time = round(time.time() - start_time, 3)
                    logger.info(f"⏱️ DIRETO FLIGHT - Total: {total_time}s")
                    return fallback_result
            
            # Verificar se deve manter continuidade com agente atual
            stick_with_agent = self._should_stick_with_current_agent()
            if stick_with_agent:
                logger.info(f"🔗 Forçando continuidade com {stick_with_agent}")
                # Usar apenas a mensagem atual, não o enhanced_message
                # O agente receberá seu contexto específico das últimas mensagens
                fallback_result = await self._force_handoff_to_agent(stick_with_agent, mensagem)
                if fallback_result:
                    total_time = round(time.time() - start_time, 3)
                    logger.info(f"⏱️ CONTINUIDADE - Total: {total_time}s | Agent: {stick_with_agent}")
                    return fallback_result
            
            # Tempo de processamento do agente
            agent_start = time.time()
            
            # Tentar passar contexto completo para a orquestração
            try:
                chat_history = self.memory_manager.get_chat_history()
                orchestration_result = await asyncio.wait_for(
                    self.handoff_orchestration.invoke(
                        task=enhanced_message,
                        runtime=self.runtime,
                        history=chat_history  # Tentar passar histórico completo
                    ),
                    timeout=25.0
                )
            except TypeError:
                # Se history não for suportado, usar apenas a mensagem enhanced
                orchestration_result = await asyncio.wait_for(
                    self.handoff_orchestration.invoke(
                        task=enhanced_message,
                        runtime=self.runtime
                    ),
                    timeout=25.0
                )
            agent_time = round(time.time() - agent_start, 3)
            
            result = await orchestration_result.get()
            
            # Calcular tempo total
            total_time = round(time.time() - start_time, 3)
            
            # Log detalhado de performance
            agent_used = getattr(self, '_last_agent_response', {}).get('name', 'Unknown')
            logger.info(f"⏱️ PERFORMANCE - Total: {total_time}s | Guardrails: {guardrail_time}s | Moderação: {moderation_time}s | Contexto: {context_time}s | Agente: {agent_time}s | Agent: {agent_used}")
            
            # Verificar se houve resposta de agente especialista
            if hasattr(self, '_last_agent_response') and self._last_agent_response:
                response_agent = self._last_agent_response['name']
                response_content = self._last_agent_response['content']
                
                if response_agent != "TriageAgent":
                    # Verificar se é resposta OOS de agente especialista e interceptar
                    if self._is_out_of_scope_response(response_content):
                        logger.warning(f"🚫 Interceptando resposta OOS de {response_agent}")
                        # TriageAgent deve gerar resposta própria para OOS
                        oos_response = "Desculpe, não consegui encontrar informações sobre isso. Posso ajudá-lo com questões relacionadas a voos, suporte técnico, recursos humanos ou outras áreas disponíveis."
                        
                        # Adicionar ao histórico como resposta do TriageAgent
                        triage_message = ChatMessageContent(
                            role=AuthorRole.ASSISTANT,
                            content=oos_response,
                            name="TriageAgent"
                        )
                        self.memory_manager.add_message(triage_message)
                        
                        return oos_response
                    
                    # Resposta válida de agente especialista
                    return response_content
                else:
                    # TriageAgent respondeu - verificar se é apropriado
                    logger.info(f"🎯 TriageAgent respondeu: {response_content[:100]}...")
                    
                    # Detectar se o TriageAgent está tentando responder algo que deveria ser handoff
                    handoff_indicators = [
                        'vou encaminhar',
                        'direcionando',
                        'transferindo',
                        'redirecionando',
                        'aguarde um instante',
                        'setor responsável',
                        'suporte técnico',
                        'especialista',
                        'departamento'
                    ]
                    
                    # Se contém indicadores de handoff OU palavras técnicas de handoff
                    if (any(keyword in response_content.lower() for keyword in ['transfer', 'handoff', 'delegate', 'routing']) or
                        any(indicator in response_content.lower() for indicator in handoff_indicators)):
                        logger.warning(f"🚫 TriageAgent tentou responder em vez de fazer handoff (ignorado): {response_content[:50]}...")
                        
                        # Forçar handoff para TechSupportAgent se menciona problemas técnicos
                        if any(tech_word in response_content.lower() for tech_word in ['senha', 'email', 'acesso', 'login', 'suporte técnico']):
                            logger.info("🔄 Forçando handoff para TechSupportAgent...")
                            fallback_result = await self._force_handoff_to_agent("TechSupportAgent", mensagem)
                            if fallback_result:
                                return fallback_result
                        
                        return "Desculpe, houve um problema no roteamento. Tente reformular sua pergunta."
                    
                    # Resposta válida do TriageAgent (apenas OOS verdadeiro)
                    return response_content
            
            # Se chegou até aqui, sem resposta capturada - usar result
            result_str = str(result) if result else ""
            
            # Se result contém palavras de handoff, é falha na orquestração
            if result_str and any(keyword in result_str.lower() for keyword in ['transfer', 'handoff', 'delegate']):
                logger.warning(f"🚫 TriageAgent tentou responder (ignorado): {result_str[:50]}...")
                return "Desculpe, não consegui encontrar informações sobre isso. Posso ajudá-lo com questões relacionadas a voos, suporte técnico, recursos humanos ou outras áreas disponíveis."
            
            # Resultado válido ou vazio
            result_final = result_str if result_str else "Conversa finalizada."
            
            # Salvar histórico antes de retornar
            try:
                self.memory_manager.save_history()
                logger.info(f"💾 Histórico salvo com sucesso ({self.memory_manager.message_count()} mensagens)")
            except Exception as e:
                logger.warning(f"⚠️ Erro ao salvar histórico final: {e}")
            
            return result_final
            
        except asyncio.TimeoutError:
            total_time = round(time.time() - start_time, 3)
            error_msg = f"⏰ Timeout após {total_time}s: O processamento demorou muito. Tente novamente."   
            logger.error(error_msg)
            return error_msg
            
        except Exception as e:
            total_time = round(time.time() - start_time, 3)
            return self._handle_processing_error(e, total_time)
    
    def _handle_processing_error(self, error: Exception, total_time: float) -> str:
        """Trata erros de processamento de mensagem"""
        error_str = str(error)
        
        # Log completo do erro para debugging
        logger.error(f"❌ Erro completo após {total_time}s: {error_str}")
        
        # Tratamento específico para erros conhecidos
        if "api_key" in error_str.lower():
            error_msg = f"🔑 Erro de API Key após {total_time}s: Verifique se a OPENAI_API_KEY está configurada corretamente"
        elif "gpt-4.1" in error_str or "model" in error_str.lower():
            error_msg = f"🤖 Erro de modelo após {total_time}s: Modelo não encontrado. Usando fallback."
        elif "quota" in error_str.lower() or "rate" in error_str.lower():
            error_msg = f"📊 Limite de API após {total_time}s: Cota excedida ou rate limit atingido"
        else:
            error_msg = f"❌ Erro após {total_time}s ao processar mensagem: {error_str[:200]}..."
        
        logger.error(error_msg)
        
        if "model_error" in error_str or "invalid content" in error_str:
            logger.info("🔄 Erro de modelo detectado. Sistema otimizará contexto automaticamente.")
            return "🔄 Sistema detectou sobrecarga. Tente reformular sua pergunta de forma mais simples."
        
        return error_msg
    
    def _create_context_summary(self) -> str:
        recent_messages = self.memory_manager.get_recent_messages(count=15)  # Aumentado de 6 para 15 mensagens
        
        if len(recent_messages) <= 1:
            return "[CONTEXTO: Primeira interação]"
        
        # Extrair informações importantes já mencionadas na conversa
        important_info = self._extract_important_context(recent_messages)
        
        context_parts = []
        for msg in recent_messages[-12:]:  # Aumentado de 5 para 12 mensagens
            role = "Usuário" if msg.role.value == "user" else f"Assistente({msg.name or 'Sistema'})"
            # Aumentado limite de caracteres de 100 para 300 para preservar mais contexto
            content = str(msg.content)[:300] + "..." if len(str(msg.content)) > 300 else str(msg.content)
            context_parts.append(f"- {role}: {content}")
        
        context = "\n".join(context_parts)
        
        # Adicionar informações importantes extraídas
        final_context = f"[CONTEXTO DA CONVERSA:\n{context}\n"
        if important_info:
            final_context += f"\nINFORMAÇÕES IMPORTANTES JÁ FORNECIDAS:\n{important_info}\n"
        final_context += "]"
        
        return final_context
    
    def _extract_important_context(self, messages) -> str:
        """Extrai informações importantes que já foram mencionadas na conversa"""
        important_data = []
        
        for msg in messages:
            content_upper = str(msg.content).upper()
            content_lower = str(msg.content).lower()
            
            # Detectar números de voo
            import re
            flight_numbers = re.findall(r'\b[A-Z]{2}\d{3,4}\b', content_upper)
            important_data.extend(f"Voo: {flight}" for flight in flight_numbers if f"Voo: {flight}" not in important_data)
            
            # Detectar assentos
            seats = re.findall(r'\b\d{1,2}[A-F]\b', content_upper)
            important_data.extend(f"Assento: {seat}" for seat in seats if f"Assento: {seat}" not in important_data)
            
            # Detectar tipos de solicitação
            if any(word in content_lower for word in ['cancelar', 'cancelamento']) and "Solicitação: Cancelamento" not in important_data:
                important_data.append("Solicitação: Cancelamento")
            
            if any(word in content_lower for word in ['trocar', 'mudar', 'alterar']) and 'assento' in content_lower and "Solicitação: Troca de assento" not in important_data:
                important_data.append("Solicitação: Troca de assento")
        
        return "\n".join(f"- {info}" for info in important_data)
    
    def obter_historico(self) -> list[ChatMessageContent]:
        """Retorna o histórico completo da conversa"""
        return self.memory_manager.get_history()
    
    def limpar_historico(self):
        """Limpa o histórico da conversa"""
        self.memory_manager.clear_history()
    
    async def _force_handoff_to_agent(self, agent_name: str, message: str) -> str:
        """Força handoff para um agente específico usando contexto das últimas mensagens dele"""
        try:
            if agent_name in self.specialist_agents:
                agent = self.specialist_agents[agent_name]
                
                # Obter últimas 5 mensagens deste agente específico usando memory manager
                recent_agent_messages = self.memory_manager.get_recent_messages_by_agent(agent_name, count=5)
                
                # Montar contexto simples: últimas mensagens do agente + mensagem atual
                context_parts = []
                
                if recent_agent_messages:
                    context_parts.append(f"[SUAS ÚLTIMAS {len(recent_agent_messages)} MENSAGENS:]")
                    for msg in recent_agent_messages:
                        context_parts.append(f"Você disse: {msg.content}")
                    context_parts.append("")
                
                context_parts.append("[MENSAGEM ATUAL DO USUÁRIO:]")
                context_parts.append(message)
                
                full_context = "\n".join(context_parts)
                
                # Processar com contexto específico do agente
                logger.info(f"🎯 Handoff para {agent_name} com {len(recent_agent_messages)} mensagens de contexto")
                response = await agent.invoke(full_context)
                
                # Adicionar resposta ao histórico
                response_message = ChatMessageContent(
                    role=AuthorRole.ASSISTANT,
                    content=str(response),
                    name=agent_name
                )
                self.memory_manager.add_message(response_message)
                
                # Salvar histórico no arquivo JSON
                self.memory_manager.save_history()
                logger.info(f"💾 Histórico salvo em {self.memory_manager.persist_file}")
                
                return str(response)
        except Exception as e:
            logger.error(f"Erro no handoff forçado para {agent_name}: {e}")
        return ""
    
    def _is_out_of_scope_response(self, content: str) -> bool:
        """Detecta se uma resposta é fora de escopo (OOS)"""
        content_lower = content.lower()
        
        # Padrões que indicam resposta OOS de agentes especialistas
        oos_patterns = [
            "desculpe, não posso ajudar com essa pergunta",
            "não posso ajudar com isso",
            "não é da minha área",
            "fora do meu escopo",
            "não é do meu tema",
            "não posso responder sobre",
            "não tenho informações sobre",
            "estou disponível para responder dúvidas sobre",
            "se precisar de informações sobre esses temas"
        ]
        
        return any(pattern in content_lower for pattern in oos_patterns)
    
    def _identify_active_agent(self) -> str:
        """Identifica qual agente está ativo com base nas mensagens recentes"""
        recent_messages = self.memory_manager.get_recent_messages(count=3)
        
        # Procurar pelo último agente especialista que respondeu
        for msg in reversed(recent_messages):
            if (hasattr(msg, 'role') and 
                msg.role.value == "assistant" and 
                msg.name and 
                msg.name != "TriageAgent" and
                msg.name != "Sistema"):
                return msg.name
        
        return ""
    
    def _should_stick_with_current_agent(self) -> str:
        """Determina se deve continuar com o agente atual baseado no contexto"""
        # Identificar agente ativo
        active_agent = self._identify_active_agent()
        
        if not active_agent:
            return ""
        
        # Usar get_recent_messages_by_agent para obter contexto específico
        recent_agent_messages = self.memory_manager.get_recent_messages_by_agent(active_agent, count=2)
        
        # Verificar se o último agente fez uma pergunta que precisa de resposta
        for msg in recent_agent_messages:
            content = str(msg.content).lower()
            # Se o agente fez uma pergunta específica, manter com ele
            if any(question in content for question in [
                "qual é o número do seu voo",
                "qual assento", 
                "qual é o seu e-mail",
                "confirme",
                "por favor",
                "informe",
                "preciso",
                "pode me informar",
                "?"  # Qualquer pergunta
            ]):
                logger.info(f"🔗 Mantendo continuidade com {active_agent} (fez pergunta)")
                return active_agent
        
        return ""
