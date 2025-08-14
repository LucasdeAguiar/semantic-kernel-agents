#!/usr/bin/env python3
"""
Script para verificar a estrutura da resposta da API
"""
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def test_api_response():
    """Testa e mostra a estrutura completa da resposta da API"""
    try:
        # Limpar histórico
        requests.delete("http://localhost:8000/chat/history")
        
        # Enviar mensagem
        response = requests.post(
            "http://localhost:8000/chat/send",
            json={"message": "Quero investir em renda fixa"},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n📋 Estrutura completa da resposta:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(f"❌ Erro: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    print("🔍 Verificando estrutura da resposta da API")
    print("=" * 50)
    test_api_response()
