#!/usr/bin/env python3
"""
Script Simples para Avaliação dos Agentes
"""
import os
import sys
import asyncio
import json
from pathlib import Path

def check_api():
    """Verifica se a API está funcionando"""
    try:
        import requests
        response = requests.get("http://localhost:8000/status", timeout=5)
        return response.status_code == 200
    except:
        return False

def check_openai():
    """Verifica se a chave OpenAI está configurada"""
    key = os.getenv("OPENAI_API_KEY")
    return key and key.startswith("sk-")

async def test_single_case():
    """Testa um único caso para verificar se tudo está funcionando"""
    try:
        import requests
        
        # Enviar uma mensagem simples
        response = requests.post(
            "http://localhost:8000/chat/send",
            json={"message": "Quero informações sobre investimentos"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Teste básico funcionou!")
            print(f"📝 Resposta: {data.get('message', 'N/A')[:100]}...")
            return True
        else:
            print(f"❌ API retornou status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

async def run_basic_evaluation():
    """Executa avaliação básica"""
    print("🚀 Iniciando avaliação básica...")
    
    # Verificações
    print("\n🔍 Verificando requisitos...")
    
    if not check_api():
        print("❌ API não está rodando")
        return False
    print("✅ API está funcionando")
    
    if not check_openai():
        print("❌ OPENAI_API_KEY não configurada")
        return False
    print("✅ OpenAI configurado")
    
    # Teste simples
    print("\n🧪 Executando teste básico...")
    success = await test_single_case()
    
    if success:
        print("\n✅ Sistema está funcionando!")
        print("🎯 Agora você pode executar a avaliação completa")
    else:
        print("\n❌ Sistema não está funcionando corretamente")
    
    return success

def main():
    """Função principal"""
    print("🤖 Teste Simples do Sistema de Agentes")
    print("=" * 50)
    
    try:
        # Executar teste
        success = asyncio.run(run_basic_evaluation())
        
        if success:
            print("\n🎉 Teste concluído com sucesso!")
        else:
            print("\n⚠️ Teste falhou")
            
    except Exception as e:
        print(f"\n💥 Erro: {e}")
        return False

if __name__ == "__main__":
    main()
