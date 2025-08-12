from semantic_kernel.contents import ChatHistory, ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
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
        self.chat_history.add_message(message)
    
    def get_history(self) -> List[ChatMessageContent]:
        return list(self.chat_history.messages)
    
    def get_chat_history(self) -> ChatHistory:
        return self.chat_history
    
    def clear_history(self):
        self.chat_history.clear()
    
    def _load_history_if_exists(self):
        if self.persist_file.exists() and self.persist_file.stat().st_size > 0:
            try:
                with open(self.persist_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for msg_data in data:
                        try:
                            message = ChatMessageContent.model_validate(msg_data)
                            self.chat_history.add_message(message)
                        except Exception:
                            continue
            except Exception as e:
                print(f"Erro ao carregar histórico: {e}")
    
    def save_history(self):
        self.save_history_sync()
    
    def save_history_sync(self):
        try:
            data = []
            for message in self.chat_history.messages:
                try:
                    data.append(message.model_dump())
                except Exception:
                    continue
            
            with open(self.persist_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Erro ao salvar histórico: {e}")
    
    def get_recent_messages_by_agent(self, agent_name: str, count: int = 5) -> List[ChatMessageContent]:
        agent_messages = [msg for msg in self.chat_history.messages 
                         if hasattr(msg, 'name') and msg.name == agent_name]
        return agent_messages[-count:] if len(agent_messages) > count else agent_messages
    
    def get_context_for_agent(self, agent_name: str, max_interactions: int = 5) -> ChatHistory:
        context_history = ChatHistory()
        
        agent_messages = self.get_recent_messages_by_agent(agent_name, max_interactions)
        
        user_messages = [msg for msg in self.chat_history.messages 
                        if msg.role == AuthorRole.USER][-5:]  # Últimas 5 mensagens de usuários

        all_relevant = []
        
        all_relevant.extend(user_messages)
        
        all_relevant.extend(agent_messages)
        
        all_relevant.sort(key=lambda x: getattr(x, 'timestamp', 0))
        
        for msg in all_relevant[-10:]:
            context_history.add_message(msg)
        
        return context_history

    def get_recent_messages(self, count: int = 10) -> List[ChatMessageContent]:
        messages = list(self.chat_history.messages)
        return messages[-count:] if len(messages) > count else messages
    
    def get_messages_by_role(self, role: str) -> List[ChatMessageContent]:
        return [msg for msg in self.chat_history.messages if msg.role.value == role]
    
    def message_count(self) -> int:
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
        session_file = self.base_dir / f"{session_id}.json"
        manager = ChatHistoryManager(str(session_file))
        self.sessions[session_id] = manager
        self.current_session = session_id
        return manager
    
    def get_session(self, session_id: str) -> ChatHistoryManager:
        if session_id not in self.sessions:
            return self.create_session(session_id)
        return self.sessions[session_id]
    
    def list_sessions(self) -> List[str]:
        return [f.stem for f in self.base_dir.glob("*.json")]
    
    def delete_session(self, session_id: str):
        if session_id in self.sessions:
            del self.sessions[session_id]
        
        session_file = self.base_dir / f"{session_id}.json"
        if session_file.exists():
            session_file.unlink()
    
    def get_current_session(self) -> ChatHistoryManager:
        if self.current_session and self.current_session in self.sessions:
            return self.sessions[self.current_session]
        
        return self.create_session("default")
