import asyncio
import logging
from pathlib import Path

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from orchestrator.triage_agent import TriageAgent
from agents.agent_loader import carregar_agentes_dinamicamente
from core.memory_manager import ChatHistoryManager
from core.function_caller import setup_default_functions

# Configurar logging mais limpo
logging.basicConfig(
    level=logging.WARNING,  # Só mostra warnings e erros por padrão
    format='%(levelname)s: %(message)s'
)

# Configurar loggers específicos para mostrar apenas o essencial
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Silenciar logs verbosos do runtime e httpx
logging.getLogger('in_process_runtime').setLevel(logging.WARNING)
logging.getLogger('in_process_runtime.events').setLevel(logging.WARNING) 
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('semantic_kernel').setLevel(logging.WARNING)

# Manter logs importantes dos agentes
logging.getLogger('orchestrator.triage_agent').setLevel(logging.INFO)
logging.getLogger('agents.agent_loader').setLevel(logging.INFO)

# SUA CHAVE API OPENAI
OPENAI_API_KEY = "openaikey"


async def main():
    """
    Função principal do sistema de agentes especialistas com handoff orchestration
    """
    try:
        print("🤖 Sistema de Agentes Especialistas com Semantic Kernel")
        print("=" * 60)
        
        # Carregar configurações dos agentes
        agentes_config = carregar_agentes_dinamicamente()
        
        # Criar o agente orquestrador (Triage Agent)
        orquestrador = TriageAgent(agentes_config, OPENAI_API_KEY)
        
        # Inicializar runtime
        orquestrador.iniciar_runtime()
        
        print(f"\n✅ Sistema iniciado com {len(agentes_config)} agentes!")
        print("\nAgentes disponíveis:")
        for agente in agentes_config:
            print(f"  • {agente['name']}: {agente['description']}")
        
        print("\n" + "="*60)
        print("💬 Comece sua conversa (digite 'sair', 'exit' ou 'quit' para encerrar)")
        print("💾 O histórico será salvo automaticamente")
        print("🔄 O sistema usa handoff orchestration para rotear automaticamente")
        print("=" * 60)
        
        # Loop principal de conversa
        while True:
            try:
                user_input = input("\n👤 Você: ").strip()
                
                if not user_input:
                    continue
                    
                if user_input.lower() in ["sair", "exit", "quit", "q"]:
                    print("\n👋 Encerrando sistema...")
                    break
                
                # Comandos especiais
                if user_input.lower() == "historico":
                    print("\n📋 Histórico da conversa:")
                    historico = orquestrador.obter_historico()
                    for i, msg in enumerate(historico[-10:], 1):  # Últimas 10 mensagens
                        role_icon = "👤" if msg.role.value == "user" else "🤖"
                        print(f"  {i}. {role_icon} {msg.name or msg.role.value}: {msg.content}")
                    continue
                
                if user_input.lower() == "limpar":
                    orquestrador.limpar_historico()
                    print("🗑️ Histórico limpo!")
                    continue
                
                if user_input.lower() == "help":
                    print("\n📖 Comandos disponíveis:")
                    print("  • historico - mostra últimas 10 mensagens")
                    print("  • limpar - limpa o histórico")
                    print("  • help - mostra esta ajuda")
                    print("  • sair/exit/quit - encerra o sistema")
                    continue
                
                # Processar mensagem através do orquestrador
                print("🔄 Processando...")
                resposta = await orquestrador.processar_mensagem(user_input)
                
                # A resposta já é exibida pelo callback do agente
                if resposta and not resposta.startswith("🤖"):
                    print(f"📋 Status: {resposta}")
                
                # Salvar histórico automaticamente
                orquestrador.memory_manager.save_history()
                
            except KeyboardInterrupt:
                print("\n\n⚠️ Interrupção detectada. Encerrando...")
                break
            except Exception as e:
                print(f"❌ Erro: {str(e)}")
                print("🔄 Tentando continuar...")
    
    except Exception as e:
        print(f"💥 Erro crítico: {str(e)}")
        return
    
    finally:
        # Cleanup
        try:
            if 'orquestrador' in locals() and orquestrador.runtime:
                await orquestrador.parar_runtime()
            
            # Salvar histórico final
            if 'orquestrador' in locals():
                orquestrador.memory_manager.save_history()
        except Exception as e:
            print(f"⚠️ Erro durante cleanup: {e}")
        
        print("\n✅ Sistema encerrado com sucesso!")


def verificar_dependencias():
    """Verifica se as dependências estão instaladas"""
    try:
        import semantic_kernel
        import openai
        return True
    except ImportError as e:
        print(f"❌ Dependência faltando: {e}")
        print("📦 Execute: pip install -r requirements.txt")
        return False


if __name__ == "__main__":
    print("🚀 Inicializando Sistema de Agentes Especialistas...")
    
    # Verificar dependências
    if not verificar_dependencias():
        exit(1)
    
    # Verificar se a chave API está configurada
    if not OPENAI_API_KEY or OPENAI_API_KEY == "SUA_OPENAI_API_KEY":
        print("⚠️ ATENÇÃO: Configure sua chave OpenAI API no arquivo main.py")
        print("🔑 Substitua OPENAI_API_KEY pela sua chave real")
        
        # Permitir continuar mesmo sem chave para teste da estrutura
        resposta = input("Continuar mesmo assim? (s/N): ")
        if resposta.lower() != 's':
            exit(1)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Sistema encerrado pelo usuário")
    except Exception as e:
        print(f"💥 Erro fatal: {str(e)}")
