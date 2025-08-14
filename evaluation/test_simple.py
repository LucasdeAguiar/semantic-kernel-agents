#!/usr/bin/env python3
"""
Script de Teste Simples para um Caso - Debug
"""
import os
import sys
import asyncio
import json
import requests
from pathlib import Path
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

def check_api():
    """Verifica se a API está funcionando"""
    try:
        response = requests.get("http://localhost:8000/status", timeout=5)
        return response.status_code == 200
    except:
        return False

def send_message(message: str):
    """Envia uma mensagem para a API"""
    try:
        response = requests.post(
            "http://localhost:8000/chat/send",
            json={"message": message},
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ API retornou status: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Erro ao enviar mensagem: {e}")
        return None

def clear_history():
    """Limpa o histórico"""
    try:
        response = requests.delete("http://localhost:8000/chat/history")
        return response.status_code == 200
    except:
        return False

def test_single_case():
    """Testa apenas um caso simples"""
    print("🚀 Testando caso específico do bolo de chocolate...")
    
    # Verificar API
    if not check_api():
        print("❌ API não está funcionando")
        return False
    
    # Limpar histórico
    clear_history()
    
    # Testar a mensagem problemática
    test_message = "Como fazer bolo de chocolate?"
    print(f"📤 Enviando: {test_message}")
    
    result = send_message(test_message)
    
    if result:
        print("✅ Sucesso!")
        print(f"🤖 Agente: {result.get('agent', 'N/A')}")
        print(f"📝 Resposta: {result.get('message', 'N/A')[:200]}...")
        
        # Verificar se foi roteado corretamente
        agent = result.get('agent', '')
        if 'triage' in agent.lower():
            print("✅ Roteamento correto para TriageAgent")
        elif agent.lower() == 'sistema':
            print("❌ Bloqueado pelo sistema (guardrails?)")
        else:
            print(f"⚠️ Roteamento inesperado para: {agent}")
        
        return True
    else:
        print("❌ Falha no teste")
        return False

def main():
    """Função principal"""
    print("🧪 Teste Simples do Sistema")
    print("=" * 40)
    
    # Verificar chave OpenAI
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY não configurada")
        return
    
    success = test_single_case()
    
    if success:
        print("\n🎉 Teste básico funcionou!")
        print("💡 O sistema está operacional")
    else:
        print("\n💥 Teste falhou")

if __name__ == "__main__":
    main()
