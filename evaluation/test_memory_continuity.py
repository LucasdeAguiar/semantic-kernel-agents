#!/usr/bin/env python3
"""
Script para testar a continuidade de memória/contexto entre mensagens.
Analisa se os agentes especialistas mantêm contexto de conversas anteriores.
"""

import asyncio
import os
import sys
import json
from datetime import datetime

# Adiciona o diretório raiz ao path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)

from api.services import AgentService
from api.config import OPENAI_API_KEY

class MemoryContinuityTester:
    def __init__(self):
        self.api_key = OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY não encontrada nas configurações")
        
        self.agent_service = AgentService(self.api_key)
    
    async def run_memory_test(self):
        """Executa teste de continuidade de memória baseado no caso reportado"""
        
        print("🧠 TESTE DE CONTINUIDADE DE MEMÓRIA")
        print("=" * 50)
        
        # Teste baseado na conversa reportada pelo usuário
        test_messages = [
            "Quero trocar meu assento.",
            "JJ1234",  # Número do voo
            "12A",     # Primeiro assento
            "12A",     # Repetindo o assento (simula dupla entrada)
            "Voo JJ1234",  # Reiterar o voo
            "12A"      # Assento final
        ]
        
        print("📝 Simulando a conversa problemática:")
        print("User: Quero trocar meu assento.")
        print("Expected: SeatBookingAgent pergunta o número do voo")
        print()
        
        results = []
        
        for i, message in enumerate(test_messages, 1):
            print(f"🗣️  MENSAGEM {i}: {message}")
            
            # Processar mensagem
            result = await self.agent_service.process_message(message)
            
            # Capturar resposta
            agent_name = result.get('agent_name', 'Unknown')
            response = result.get('response', 'No response')
            
            print(f"🤖 {agent_name}: {response}")
            print()
            
            # Analisar se há problema de continuidade
            memory_issue = self._analyze_memory_issue(i, message, response, agent_name)
            if memory_issue:
                print(f"⚠️  PROBLEMA DE MEMÓRIA: {memory_issue}")
                print()
            
            results.append({
                'step': i,
                'user_message': message,
                'agent_name': agent_name,
                'agent_response': response,
                'memory_issue': memory_issue
            })
            
            # Pequena pausa entre mensagens
            await asyncio.sleep(1)
        
        # Análise final
        print("📊 ANÁLISE FINAL:")
        print("-" * 30)
        self._final_analysis(results)
        
        # Verificar histórico completo
        print("\n📋 HISTÓRICO COMPLETO:")
        print("-" * 30)
        history = self.agent_service.get_chat_history()
        if history.get('success'):
            for i, msg in enumerate(history['messages'], 1):
                role = msg['role']
                name = msg.get('name', 'N/A')
                content = msg['content'][:100] + "..." if len(msg['content']) > 100 else msg['content']
                print(f"{i:2d}. [{role}] {name}: {content}")
        
        return results
    
    def _analyze_memory_issue(self, step, user_message, agent_response, agent_name):
        """Analisa se há problemas de continuidade de memória"""
        
        # Detectar problemas específicos baseados na conversa reportada
        if step == 4 and "número do seu voo" in agent_response.lower():
            return "Agente esqueceu que o voo JJ1234 já foi informado no passo 2"
        
        if step == 5 and "qual é o assento" in agent_response.lower():
            return "Agente esqueceu que o assento 12A já foi mencionado nos passos 3 e 4"
        
        if step == 6 and "qual é o assento" in agent_response.lower():
            return "Agente continua perguntando o assento mesmo após múltiplas menções"
        
        # Verificar se agente está perguntando informações já fornecidas
        if "número do voo" in agent_response.lower() and step > 2:
            return f"Agente pergunta número do voo novamente no passo {step}"
        
        if "qual.*assento" in agent_response.lower() and step > 3:
            return f"Agente pergunta assento novamente no passo {step}"
        
        return None
    
    def _final_analysis(self, results):
        """Análise final dos resultados"""
        
        memory_issues = [r for r in results if r['memory_issue']]
        
        if not memory_issues:
            print("✅ Nenhum problema de continuidade detectado!")
            return
        
        print(f"❌ {len(memory_issues)} problemas de continuidade encontrados:")
        for issue in memory_issues:
            print(f"   - Passo {issue['step']}: {issue['memory_issue']}")
        
        print("\n🔍 POSSÍVEIS CAUSAS:")
        print("1. Agentes especialistas não recebem histórico completo")
        print("2. Contexto sendo resumido demais na função _create_context_summary()")
        print("3. Agentes não processando adequadamente o contexto fornecido")
        print("4. Problema na implementação do ChatHistory no Semantic Kernel")
        
        print("\n💡 RECOMENDAÇÕES:")
        print("1. Modificar _create_context_summary() para incluir mais contexto")
        print("2. Passar histórico completo para agentes especialistas")
        print("3. Adicionar instruções específicas sobre manutenção de contexto")
        print("4. Implementar validação de contexto antes das respostas")

async def main():
    """Função principal"""
    try:
        tester = MemoryContinuityTester()
        await tester.run_memory_test()
        
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
