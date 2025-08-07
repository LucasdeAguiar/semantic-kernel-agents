from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from typing import List, Optional
import os
import logging
from dotenv import load_dotenv

from .models import (
    AgentConfig, AgentResponse, MessageRequest, MessageResponse,
    ChatHistoryResponse, SystemStatus
)
from .services import AgentService

# Carregar variáveis de ambiente
load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Instância global do serviço
agent_service: Optional[AgentService] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerenciamento do ciclo de vida da aplicação"""
    global agent_service
    
    # Startup
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY não encontrada. Alguns recursos podem não funcionar.")
            api_key = "dummy-key"  # Para permitir inicialização mesmo sem chave
        
        agent_service = AgentService(api_key)
        logger.info("🚀 Sistema de Agentes inicializado com sucesso")
        yield
        
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar sistema: {e}")
        raise
    
    # Shutdown
    finally:
        if agent_service:
            try:
                await agent_service.cleanup()
                logger.info("✅ Sistema encerrado com sucesso")
            except Exception as e:
                logger.error(f"⚠️ Erro durante cleanup: {e}")


# Criar aplicação FastAPI
app = FastAPI(
    title="Sistema de Agentes Especialistas",
    description="API REST para gerenciar agentes usando Semantic Kernel",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)


def get_agent_service() -> AgentService:
    """Dependency para obter o serviço de agentes"""
    if not agent_service:
        raise HTTPException(status_code=503, detail="Sistema não inicializado")
    return agent_service


@app.get("/", tags=["Sistema"])
async def root():
    """Endpoint raiz com informações básicas"""
    return {
        "message": "🤖 Sistema de Agentes Especialistas",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "active"
    }


@app.get("/status", response_model=SystemStatus, tags=["Sistema"])
async def get_system_status(service: AgentService = Depends(get_agent_service)):
    """Retorna o status atual do sistema"""
    try:
        status = service.get_system_status()
        return SystemStatus(**status)
    except Exception as e:
        logger.error(f"Erro ao obter status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ENDPOINTS DE AGENTES ====================

@app.get("/agents", response_model=List[AgentConfig], tags=["Agentes"])
async def get_agents(service: AgentService = Depends(get_agent_service)):
    """Lista todos os agentes configurados"""
    try:
        agents = service.get_all_agents()
        return [AgentConfig(**agent) for agent in agents]
    except Exception as e:
        logger.error(f"Erro ao listar agentes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agents/{agent_name}", response_model=AgentConfig, tags=["Agentes"])
async def get_agent(agent_name: str, service: AgentService = Depends(get_agent_service)):
    """Retorna um agente específico"""
    try:
        agent = service.get_agent_by_name(agent_name)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agente '{agent_name}' não encontrado")
        return AgentConfig(**agent)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar agente {agent_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agents", response_model=AgentResponse, tags=["Agentes"])
async def create_agent(agent: AgentConfig, service: AgentService = Depends(get_agent_service)):
    """Cria um novo agente"""
    try:
        created_agent = service.create_agent(agent.model_dump())
        return AgentResponse(
            success=True,
            message=f"Agente '{agent.name}' criado com sucesso",
            data=created_agent
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Erro ao criar agente: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/agents/{agent_name}", response_model=AgentResponse, tags=["Agentes"])
async def update_agent(
    agent_name: str, 
    agent: AgentConfig, 
    service: AgentService = Depends(get_agent_service)
):
    """Atualiza um agente existente"""
    try:
        # Garantir que o nome na URL seja usado
        agent_data = agent.model_dump()
        agent_data["name"] = agent_name
        
        updated_agent = service.update_agent(agent_name, agent_data)
        return AgentResponse(
            success=True,
            message=f"Agente '{agent_name}' atualizado com sucesso",
            data=updated_agent
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Erro ao atualizar agente {agent_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/agents/{agent_name}", response_model=AgentResponse, tags=["Agentes"])
async def delete_agent(agent_name: str, service: AgentService = Depends(get_agent_service)):
    """Remove um agente"""
    try:
        success = service.delete_agent(agent_name)
        if success:
            return AgentResponse(
                success=True,
                message=f"Agente '{agent_name}' removido com sucesso"
            )
        else:
            raise HTTPException(status_code=400, detail="Falha ao remover agente")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Erro ao remover agente {agent_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ENDPOINTS DE CHAT ====================

@app.post("/chat/send", response_model=MessageResponse, tags=["Chat"])
async def send_message(
    message: MessageRequest, 
    service: AgentService = Depends(get_agent_service)
):
    """Envia uma mensagem para o sistema de agentes"""
    try:
        result = await service.process_message(message.message)
        return MessageResponse(**result)
    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {e}")
        from datetime import datetime
        return MessageResponse(
            success=False,
            response=f"Erro ao processar mensagem: {str(e)}",
            agent_name="Sistema",
            timestamp=datetime.now()
        )


@app.get("/chat/history", response_model=ChatHistoryResponse, tags=["Chat"])
async def get_chat_history(
    limit: Optional[int] = None,
    service: AgentService = Depends(get_agent_service)
):
    """Retorna o histórico de conversas"""
    try:
        history = service.get_chat_history(limit)
        return ChatHistoryResponse(**history)
    except Exception as e:
        logger.error(f"Erro ao obter histórico: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/chat/history", response_model=AgentResponse, tags=["Chat"])
async def clear_chat_history(service: AgentService = Depends(get_agent_service)):
    """Limpa o histórico de conversas"""
    try:
        success = service.clear_history()
        if success:
            return AgentResponse(
                success=True,
                message="Histórico limpo com sucesso"
            )
        else:
            raise HTTPException(status_code=500, detail="Falha ao limpar histórico")
    except Exception as e:
        logger.error(f"Erro ao limpar histórico: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== HANDLER DE ERROS ====================

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handler geral para exceções não tratadas"""
    logger.error(f"Erro não tratado: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Erro interno do servidor"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
