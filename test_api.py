"""
Testes básicos para a API do Sistema de Agentes
"""

import requests
import json
from time import sleep

# Configurações
BASE_URL = "http://localhost:8000"
headers = {"Content-Type": "application/json"}

def test_basic_endpoints():
    """Testa endpoints básicos"""
    print("🧪 Testando endpoints básicos...")
    
    # Teste 1: Root endpoint
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"✅ Root: {response.status_code} - {response.json().get('message', '')}")
    except Exception as e:
        print(f"❌ Root: Erro - {e}")
    
    # Teste 2: Status
    try:
        response = requests.get(f"{BASE_URL}/status")
        if response.status_code == 200:
            status = response.json()
            print(f"✅ Status: {status.get('status', 'unknown')} - {status.get('total_agents', 0)} agentes")
        else:
            print(f"❌ Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Status: Erro - {e}")

def test_agents():
    """Testa gerenciamento de agentes"""
    print("\n🧪 Testando gerenciamento de agentes...")
    
    # Teste 1: Listar agentes
    try:
        response = requests.get(f"{BASE_URL}/agents")
        if response.status_code == 200:
            agents = response.json()
            print(f"✅ Listar agentes: {len(agents)} agentes encontrados")
            for agent in agents[:3]:  # Mostrar apenas os 3 primeiros
                print(f"   - {agent.get('name', 'N/A')}: {agent.get('description', 'N/A')}")
        else:
            print(f"❌ Listar agentes: {response.status_code}")
    except Exception as e:
        print(f"❌ Listar agentes: Erro - {e}")
    
    # Teste 2: Buscar agente específico
    try:
        response = requests.get(f"{BASE_URL}/agents/FinanceAgent")
        if response.status_code == 200:
            agent = response.json()
            print(f"✅ Buscar FinanceAgent: {agent.get('name', 'N/A')}")
        elif response.status_code == 404:
            print("⚠️ FinanceAgent não encontrado")
        else:
            print(f"❌ Buscar FinanceAgent: {response.status_code}")
    except Exception as e:
        print(f"❌ Buscar FinanceAgent: Erro - {e}")

def test_chat():
    """Testa funcionalidades de chat"""
    print("\n🧪 Testando chat...")
    
    # Teste 1: Enviar mensagem
    try:
        message_data = {
            "message": "Olá, este é um teste da API"
        }
        response = requests.post(f"{BASE_URL}/chat/send", 
                               json=message_data, 
                               headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Enviar mensagem: {result.get('agent_name', 'N/A')} respondeu")
            print(f"   Resposta: {result.get('response', 'N/A')[:100]}...")
        else:
            print(f"❌ Enviar mensagem: {response.status_code}")
            print(f"   Erro: {response.text}")
    except Exception as e:
        print(f"❌ Enviar mensagem: Erro - {e}")
    
    sleep(1)  # Aguardar um pouco
    
    # Teste 2: Histórico
    try:
        response = requests.get(f"{BASE_URL}/chat/history?limit=5")
        if response.status_code == 200:
            history = response.json()
            print(f"✅ Histórico: {history.get('total_messages', 0)} mensagens")
            for msg in history.get('messages', [])[-2:]:  # Últimas 2
                print(f"   {msg.get('role', 'N/A')}: {msg.get('content', 'N/A')[:50]}...")
        else:
            print(f"❌ Histórico: {response.status_code}")
    except Exception as e:
        print(f"❌ Histórico: Erro - {e}")

def main():
    """Função principal de testes"""
    print("🚀 Iniciando testes da API do Sistema de Agentes")
    print("=" * 60)
    
    # Verificar se servidor está rodando
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code != 200:
            print("❌ Servidor não está respondendo corretamente")
            return
    except requests.exceptions.RequestException:
        print("❌ Servidor não está rodando ou não acessível")
        print("💡 Execute: python run_api.py")
        return
    
    # Executar testes
    test_basic_endpoints()
    test_agents()
    test_chat()
    
    print("\n" + "=" * 60)
    print("🏁 Testes concluídos!")
    print("📖 Para mais detalhes, acesse: http://localhost:8000/docs")

if __name__ == "__main__":
    main()
