from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion


def criar_agente_especialista(config: dict, api_key: str) -> ChatCompletionAgent:
    # Criar serviço OpenAI para o agente
    service = OpenAIChatCompletion(
        service_id=f"openai-{config['name'].lower()}",
        ai_model_id="gpt-4",
        api_key=api_key
    )
    
    return ChatCompletionAgent(
        name=config["name"],
        description=config["description"],
        instructions=config["instructions"],
        service=service
    )
