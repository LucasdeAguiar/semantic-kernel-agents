from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion


def criar_agente_especialista(config: dict, api_key: str) -> ChatCompletionAgent:
    """
    Factory function para criar agentes especialistas dinamicamente
    seguindo o padrão da documentação oficial do Semantic Kernel.
    """
    
    # Criar serviço OpenAI para o agente
    service = OpenAIChatCompletion(
        service_id=f"openai-{config['name'].lower()}",
        ai_model_id="gpt-4",
        api_key=api_key
    )
    
    # Criar e retornar o agente diretamente
    return ChatCompletionAgent(
        name=config["name"],
        description=config["description"],
        instructions=config["instructions"],
        service=service
    )
