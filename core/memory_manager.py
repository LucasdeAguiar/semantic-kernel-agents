from semantic_kernel.contents import ChatHistory, ChatMessageContent
from typing import List
import json
from pathlib import Path


def criar_memoria_volatil():
    """
    Cria uma memória volátil para o kernel.
    Na versão atual do Semantic Kernel, usamos ChatHistory diretamente.
    """
    return ChatHistory()


class ChatHistoryManager:
    """
    Gerenciador de histórico de conversas com persistência.
    Mantém histórico em memória e permite salvar/carregar de arquivo.
    """
    
    def __init__(self, persist_file: str = "chat_history.json"):
        self.chat_history = ChatHistory()
        self.persist_file = Path(persist_file)
        self._load_history_if_exists()
    
    def add_message(self, message: ChatMessageContent):
        """Adiciona uma mensagem ao histórico"""
        self.chat_history.add_message(message)
    
    def get_history(self) -> List[ChatMessageContent]:
        """Retorna o histórico completo"""
        return list(self.chat_history.messages)
    
    def get_chat_history(self) -> ChatHistory:
        """Retorna o objeto ChatHistory do Semantic Kernel"""
        return self.chat_history
    
    def clear_history(self):
        """Limpa todo o histórico"""
        self.chat_history.clear()
    
    def _load_history_if_exists(self):
        """Carrega histórico do arquivo se existir"""
        if self.persist_file.exists() and self.persist_file.stat().st_size > 0:
            try:
                with open(self.persist_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for msg_data in data:
                        try:
                            message = ChatMessageContent.model_validate(msg_data)
                            self.chat_history.add_message(message)
                        except Exception:
                            # Pular mensagens com formato inválido
                            continue
            except Exception as e:
                print(f"Erro ao carregar histórico: {e}")
    
    def save_history(self):
        """Salva o histórico atual em arquivo de forma síncrona"""
        self.save_history_sync()
    
    def save_history_sync(self):
        """Salva o histórico atual em arquivo de forma síncrona"""
        try:
            data = []
            for message in self.chat_history.messages:
                try:
                    data.append(message.model_dump())
                except Exception:
                    # Pular mensagens que não podem ser serializadas
                    continue
            
            with open(self.persist_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Erro ao salvar histórico: {e}")
    
    def get_recent_messages_by_agent(self, agent_name: str, count: int = 5) -> List[ChatMessageContent]:
        """Retorna as últimas N mensagens de um agente específico"""
        agent_messages = [msg for msg in self.chat_history.messages 
                         if hasattr(msg, 'name') and msg.name == agent_name]
        return agent_messages[-count:] if len(agent_messages) > count else agent_messages
    
    def get_context_for_agent(self, current_agent: str, user_message: ChatMessageContent, max_messages: int = 5) -> List[ChatMessageContent]:
        """
        Cria contexto otimizado para um agente específico:
        - Mensagem atual do usuário
        - Últimas 5 mensagens do agente atual
        - Últimas 2 mensagens de outros agentes (para contexto de handoff)
        """
        context_messages = []
        
        # 1. Adicionar mensagens recentes do agente atual
        agent_messages = self.get_recent_messages_by_agent(current_agent, max_messages)
        context_messages.extend(agent_messages)
        
        # 2. Adicionar últimas mensagens de outros agentes para contexto de handoff
        other_agents_messages = []
        for msg in reversed(list(self.chat_history.messages)):
            if (hasattr(msg, 'name') and msg.name and msg.name != current_agent and 
                msg.role.value == "assistant" and len(other_agents_messages) < 2):
                other_agents_messages.append(msg)
        
        # Adicionar na ordem correta (mais antigas primeiro)
        context_messages.extend(reversed(other_agents_messages))
        
        # 3. Adicionar mensagem atual do usuário
        context_messages.append(user_message)
        
        # Ordenar por ordem cronológica e remover duplicatas
        unique_messages = []
        seen_contents = set()
        for msg in sorted(context_messages, key=lambda x: getattr(x, 'timestamp', 0)):
            content_key = f"{msg.role.value}:{msg.content[:50]}"
            if content_key not in seen_contents:
                unique_messages.append(msg)
                seen_contents.add(content_key)
        
        return unique_messages[-10:]  # Máximo 10 mensagens no contexto total

    def get_recent_messages(self, count: int = 10) -> List[ChatMessageContent]:
        """Retorna as últimas N mensagens"""
        messages = list(self.chat_history.messages)
        return messages[-count:] if len(messages) > count else messages
    
    def get_messages_by_role(self, role: str) -> List[ChatMessageContent]:
        """Retorna mensagens filtradas por role (user, assistant, system, tool)"""
        return [msg for msg in self.chat_history.messages if msg.role.value == role]
    
    def message_count(self) -> int:
        """Retorna o número total de mensagens no histórico"""
        return len(self.chat_history.messages)


class ConversationMemoryManager:
    """
    Gerenciador avançado de memória de conversas com múltiplas sessões
    """
    
    def __init__(self, base_dir: str = "conversations"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        self.current_session = None
        self.sessions = {}
    
    def create_session(self, session_id: str) -> ChatHistoryManager:
        """Cria uma nova sessão de conversa"""
        session_file = self.base_dir / f"{session_id}.json"
        manager = ChatHistoryManager(str(session_file))
        self.sessions[session_id] = manager
        self.current_session = session_id
        return manager
    
    def get_session(self, session_id: str) -> ChatHistoryManager:
        """Obtém uma sessão existente"""
        if session_id not in self.sessions:
            return self.create_session(session_id)
        return self.sessions[session_id]
    
    def list_sessions(self) -> List[str]:
        """Lista todas as sessões disponíveis"""
        return [f.stem for f in self.base_dir.glob("*.json")]
    
    def delete_session(self, session_id: str):
        """Remove uma sessão"""
        if session_id in self.sessions:
            del self.sessions[session_id]
        
        session_file = self.base_dir / f"{session_id}.json"
        if session_file.exists():
            session_file.unlink()
    
    def get_current_session(self) -> ChatHistoryManager:
        """Retorna a sessão atual"""
        if self.current_session and self.current_session in self.sessions:
            return self.sessions[self.current_session]
        
        # Criar sessão padrão se não houver
        return self.create_session("default")
