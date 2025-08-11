from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class AgentConfig(BaseModel):
    """Modelo para configuração de agente"""
    name: str = Field(..., description="Nome do agente")
    description: str = Field(..., description="Descrição do agente")
    instructions: str = Field(..., description="Instruções do agente")
    plugins: Optional[List[str]] = Field(default=None, description="Plugins do agente")
    functions: Optional[List[str]] = Field(default=None, description="Funções do agente")
    settings: Optional[Dict[str, Any]] = Field(default=None, description="Configurações adicionais")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "ExampleAgent",
                "description": "Agente de exemplo",
                "instructions": "Você é um agente de exemplo que ajuda com tarefas básicas.",
                "plugins": [],
                "functions": [],
                "settings": {}
            }
        }


class AgentResponse(BaseModel):
    """Resposta padrão para operações com agentes"""
    success: bool = Field(..., description="Se a operação foi bem-sucedida")
    message: str = Field(..., description="Mensagem de resposta")
    data: Optional[Any] = Field(default=None, description="Dados retornados")


class MessageRequest(BaseModel):
    """Requisição para enviar mensagem"""
    message: str = Field(..., description="Mensagem a ser enviada", min_length=1)
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Olá, preciso de ajuda com investimentos"
            }
        }


class MessageResponse(BaseModel):
    """Resposta de mensagem processada"""
    success: bool = Field(..., description="Se a mensagem foi processada")
    response: str = Field(..., description="Resposta do agente")
    agent_name: str = Field(..., description="Nome do agente que respondeu")
    timestamp: datetime = Field(..., description="Timestamp da resposta")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "response": "Olá! Posso ajudá-lo com questões de investimentos...",
                "agent_name": "FinanceAgent",
                "timestamp": "2025-08-06T10:00:00Z"
            }
        }


class ChatMessage(BaseModel):
    """Modelo para mensagem do chat"""
    role: str = Field(..., description="Papel (user, assistant, tool)")
    name: Optional[str] = Field(default=None, description="Nome do agente")
    content: str = Field(..., description="Conteúdo da mensagem")
    timestamp: Optional[datetime] = Field(default=None, description="Timestamp da mensagem")
    ai_model_id: Optional[str] = Field(default=None, description="ID do modelo de IA")


class ChatHistoryResponse(BaseModel):
    """Resposta com histórico de chat"""
    success: bool = Field(..., description="Se a operação foi bem-sucedida")
    total_messages: int = Field(..., description="Total de mensagens")
    messages: List[ChatMessage] = Field(..., description="Lista de mensagens")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "total_messages": 5,
                "messages": [
                    {
                        "role": "user",
                        "name": None,
                        "content": "Olá!",
                        "timestamp": "2025-08-06T10:00:00Z"
                    },
                    {
                        "role": "assistant",
                        "name": "TriageAgent",
                        "content": "Olá! Como posso ajudá-lo?",
                        "timestamp": "2025-08-06T10:00:01Z"
                    }
                ]
            }
        }


class SystemStatus(BaseModel):
    """Status do sistema"""
    status: str = Field(..., description="Status do sistema")
    total_agents: int = Field(..., description="Total de agentes configurados")
    active_runtime: bool = Field(..., description="Se o runtime está ativo")
    last_message_time: Optional[datetime] = Field(default=None, description="Último timestamp de mensagem")


class GuardrailConfig(BaseModel):
    """Modelo para configuração de guardrail"""
    name: str = Field(..., description="Nome do guardrail")
    description: str = Field(..., description="Descrição do guardrail")
    keywords: Optional[List[str]] = Field(default=None, description="Palavras-chave para bloqueio")
    enabled: bool = Field(default=True, description="Se o guardrail está ativo")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "ProfanityGuardrail",
                "description": "Bloqueia conteúdo com palavrões e linguagem ofensiva",
                "keywords": ["palavra1", "palavra2", "palavra3"],
                "enabled": True
            }
        }


class GuardrailResponse(BaseModel):
    """Resposta padrão para operações com guardrails"""
    success: bool = Field(..., description="Se a operação foi bem-sucedida")
    message: str = Field(..., description="Mensagem de resposta")
    data: Optional[Any] = Field(default=None, description="Dados retornados")
