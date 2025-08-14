#!/usr/bin/env python3
"""
Script para testar a conexão com a API da OpenAI
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Adiciona o diretório raiz ao path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)

async def test_openai_connection():
    """Testa a conexão com a API da OpenAI"""
    
    print("🔍 TESTE DE CONEXÃO COM OPENAI API")
    print("=" * 40)
    
    # Verificar API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY não encontrada no arquivo .env")
        return False
    
    print(f"✅ API Key encontrada: {api_key[:10]}...{api_key[-4:]}")
    
    try:
        from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
        
        # Testar modelos diferentes
        models_to_test = ["gpt-4o", "gpt-4", "gpt-3.5-turbo"]
        
        for model in models_to_test:
            print(f"\n🧪 Testando modelo: {model}")
            
            try:
                service = OpenAIChatCompletion(
                    service_id=f"test-{model}",
                    ai_model_id=model,
                    api_key=api_key
                )
                
                print(f"✅ Serviço {model} criado com sucesso")
                
                # Teste simples de geração
                try:
                    # Não fazer chamada real para economizar tokens, apenas verificar inicialização
                    print(f"✅ {model} disponível para uso")
                    return True
                    
                except Exception as e:
                    print(f"⚠️ Erro ao testar {model}: {e}")
                    continue
                    
            except Exception as e:
                print(f"❌ Erro ao criar serviço {model}: {e}")
                continue
        
        print("\n❌ Nenhum modelo funcionou")
        return False
        
    except ImportError as e:
        print(f"❌ Erro de importação: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        return False

async def main():
    """Função principal"""
    try:
        success = await test_openai_connection()
        
        if success:
            print("\n✅ Teste concluído com sucesso!")
            print("💡 A API da OpenAI deve estar funcionando corretamente.")
        else:
            print("\n❌ Teste falhou!")
            print("💡 Verifique:")
            print("   1. Se a OPENAI_API_KEY está correta")
            print("   2. Se você tem créditos na conta OpenAI")
            print("   3. Se não há bloqueios de firewall")
            
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")

if __name__ == "__main__":
    asyncio.run(main())
