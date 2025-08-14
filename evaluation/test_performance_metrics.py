#!/usr/bin/env python3
"""
Script para testar as métricas de performance implementadas.
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

class PerformanceTester:
    def __init__(self):
        self.api_key = OPENAI_API_KEY
        if not self.api_key:
            # Tentar pegar da variável de ambiente
            self.api_key = os.getenv("OPENAI_API_KEY")
            if not self.api_key:
                print("⚠️ OPENAI_API_KEY não encontrada. Usando chave dummy para teste de estrutura.")
                self.api_key = "sk-dummy-key-for-testing"
        
        self.agent_service = AgentService(self.api_key)
    
    async def test_performance_metrics(self):
        """Testa as métricas de performance implementadas"""
        
        print("🚀 TESTE DE MÉTRICAS DE PERFORMANCE")
        print("=" * 50)
        
        test_messages = [
            "Quero trocar meu assento no voo JJ1234 para o assento 12A",
            "Qual é o status do voo JJ1234?",
            "Preciso cancelar meu voo",
            "Quantas malas posso levar?",
        ]
        
        results = []
        
        for i, message in enumerate(test_messages, 1):
            print(f"\n🗣️ TESTE {i}: {message}")
            print("-" * 40)
            
            try:
                # Processar mensagem com métricas
                result = await self.agent_service.process_message(message)
                
                # Extrair métricas
                success = result.get('success', False)
                response = result.get('response', 'Sem resposta')
                agent_name = result.get('agent_name', 'Unknown')
                response_time = result.get('response_time_seconds', 0)
                performance_metrics = result.get('performance_metrics', {})
                
                print(f"✅ Sucesso: {success}")
                print(f"🤖 Agente: {agent_name}")
                print(f"⏱️ Tempo: {response_time}s")
                print(f"📊 Métricas: {json.dumps(performance_metrics, indent=2, ensure_ascii=False)}")
                print(f"💬 Resposta: {response[:100]}...")
                
                # Análise de performance
                self._analyze_performance(response_time, agent_name, len(message))
                
                results.append({
                    'test_number': i,
                    'message': message,
                    'success': success,
                    'agent_name': agent_name,
                    'response_time': response_time,
                    'performance_metrics': performance_metrics,
                    'response_preview': response[:100]
                })
                
            except Exception as e:
                print(f"❌ Erro no teste {i}: {e}")
                results.append({
                    'test_number': i,
                    'message': message,
                    'error': str(e)
                })
            
            # Pequena pausa entre testes
            await asyncio.sleep(1)
        
        # Análise final
        print("\n📈 ANÁLISE FINAL")
        print("=" * 50)
        self._final_performance_analysis(results)
        
        return results
    
    def _analyze_performance(self, response_time: float, agent_name: str, message_length: int):
        """Analisa a performance individual de uma resposta"""
        
        if response_time < 2.0:
            print(f"🟢 Performance EXCELENTE ({response_time}s)")
        elif response_time < 5.0:
            print(f"🟡 Performance BOA ({response_time}s)")
        elif response_time < 10.0:
            print(f"🟠 Performance MODERADA ({response_time}s)")
        else:
            print(f"🔴 Performance LENTA ({response_time}s)")
        
        # Análise por agente
        if "Agent" in agent_name and response_time > 8.0:
            print(f"⚠️ {agent_name} pode precisar de otimização")
        
        # Análise por tamanho da mensagem
        if message_length > 100 and response_time > 6.0:
            print(f"📝 Mensagem longa ({message_length} chars) pode estar afetando performance")
    
    def _final_performance_analysis(self, results):
        """Análise final de todas as métricas"""
        
        successful_tests = [r for r in results if r.get('success', False)]
        failed_tests = [r for r in results if not r.get('success', False)]
        
        if not successful_tests:
            print("❌ Nenhum teste bem-sucedido para analisar")
            return
        
        # Estatísticas de tempo
        response_times = [r['response_time'] for r in successful_tests]
        avg_time = sum(response_times) / len(response_times)
        max_time = max(response_times)
        min_time = min(response_times)
        
        print("⏱️ TEMPO DE RESPOSTA:")
        print(f"   - Média: {avg_time:.3f}s")
        print(f"   - Máximo: {max_time:.3f}s")
        print(f"   - Mínimo: {min_time:.3f}s")
        
        # Estatísticas por agente
        agents_used = {}
        for r in successful_tests:
            agent = r['agent_name']
            if agent in agents_used:
                agents_used[agent].append(r['response_time'])
            else:
                agents_used[agent] = [r['response_time']]
        
        print("\n🤖 PERFORMANCE POR AGENTE:")
        for agent, times in agents_used.items():
            avg_agent_time = sum(times) / len(times)
            print(f"   - {agent}: {avg_agent_time:.3f}s (média de {len(times)} teste(s))")
        
        # Análise de erros
        if failed_tests:
            print(f"\n❌ ERROS ({len(failed_tests)} teste(s)):")
            for r in failed_tests:
                print(f"   - Teste {r['test_number']}: {r.get('error', 'Erro desconhecido')}")
        
        # Recomendações
        print("\n💡 RECOMENDAÇÕES:")
        if avg_time > 8.0:
            print("   - Considerar otimização geral do sistema (tempo médio > 8s)")
        if max_time > 15.0:
            print("   - Investigar gargalos específicos (tempo máximo > 15s)")
        if len(failed_tests) > 0:
            print("   - Melhorar tratamento de erros e robustez")
        
        print(f"\n✅ Teste concluído! {len(successful_tests)}/{len(results)} testes bem-sucedidos")

async def main():
    """Função principal"""
    try:
        tester = PerformanceTester()
        await tester.test_performance_metrics()
        
    except Exception as e:
        print(f"❌ Erro durante os testes: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
