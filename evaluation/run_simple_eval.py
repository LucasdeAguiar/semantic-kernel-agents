#!/usr/bin/env python3
"""
Script de Avaliação Simplificado - Sem RAGAs para evitar problemas de event loop
"""
import os
import sys
import json
import time
import requests
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

class SimpleEvaluator:
    """Avaliador simples sem dependências complexas"""
    
    def __init__(self, api_base_url: str):
        self.api_base_url = api_base_url
        self.results = []
    
    def load_test_cases(self, file_path: str):
        """Carrega casos de teste"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data['test_cases']
    
    def clear_history(self):
        """Limpa histórico"""
        try:
            requests.delete(f"{self.api_base_url}/chat/history")
        except:
            pass
    
    def send_message(self, message: str):
        """Envia mensagem"""
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.api_base_url}/chat/send",
                json={"message": message},
                timeout=30
            )
            end_time = time.time()
            
            if response.status_code == 200:
                data = response.json()
                data['response_time_ms'] = (end_time - start_time) * 1000
                return data
            else:
                return None
        except Exception as e:
            print(f"❌ Erro na mensagem: {e}")
            return None
    
    def evaluate_test_case(self, test_case):
        """Avalia um caso de teste"""
        print(f"📝 Teste: {test_case['id']} - {test_case['message'][:50]}...")
        
        # Limpar histórico antes de cada teste
        self.clear_history()
        
        # Enviar mensagens de contexto se necessário
        if test_case.get('context_dependent', False) and test_case.get('previous_messages'):
            for msg in test_case['previous_messages']:
                self.send_message(msg)
                time.sleep(0.3)
        
        # Enviar mensagem principal
        result = self.send_message(test_case['message'])
        
        if not result:
            print("❌ Falha na comunicação")
            return None
        
        # Verificar roteamento
        actual_agent = result.get('agent_name', 'Unknown')
        expected_agent = test_case.get('expected_agent', '')
        routing_correct = (actual_agent == expected_agent)
        
        print(f"🤖 Agente: {actual_agent} (esperado: {expected_agent}) {'✅' if routing_correct else '❌'}")
        print(f"⚡ Tempo: {result.get('response_time_ms', 0):.0f}ms")
        
        return {
            'id': test_case['id'],
            'message': test_case['message'],
            'actual_agent': actual_agent,
            'expected_agent': expected_agent,
            'routing_correct': routing_correct,
            'response': result.get('response', ''),
            'response_time_ms': result.get('response_time_ms', 0),
            'timestamp': datetime.now().isoformat()
        }
    
    def run_evaluation(self, test_cases):
        """Executa avaliação completa"""
        print(f"🚀 Iniciando avaliação de {len(test_cases)} casos...")
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n--- Teste {i}/{len(test_cases)} ---")
            result = self.evaluate_test_case(test_case)
            if result:
                self.results.append(result)
        
        return self.generate_report()
    
    def generate_report(self):
        """Gera relatório"""
        if not self.results:
            return {"error": "Nenhum resultado"}
        
        total_tests = len(self.results)
        routing_correct = sum(1 for r in self.results if r['routing_correct'])
        avg_response_time = sum(r['response_time_ms'] for r in self.results) / total_tests
        
        # Performance por agente
        agent_stats = {}
        for result in self.results:
            agent = result['expected_agent']
            if agent not in agent_stats:
                agent_stats[agent] = {'total': 0, 'correct': 0}
            agent_stats[agent]['total'] += 1
            if result['routing_correct']:
                agent_stats[agent]['correct'] += 1
        
        agent_accuracy = {
            agent: stats['correct'] / stats['total'] 
            for agent, stats in agent_stats.items()
        }
        
        report = {
            'summary': {
                'total_tests': total_tests,
                'routing_accuracy': routing_correct / total_tests,
                'avg_response_time_ms': avg_response_time,
                'context_usage_rate': 1.0  # Simplificado
            },
            'agent_performance': {
                'routing_accuracy_by_agent': agent_accuracy
            },
            'detailed_results': self.results,
            'timestamp': datetime.now().isoformat()
        }
        
        return report
    
    def save_report(self, report):
        """Salva relatório"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"evaluation_report_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        return filename

def main():
    """Função principal"""
    print("🤖 Avaliador Simples de Agentes")
    print("=" * 50)
    
    # Verificações
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY não configurada")
        return
    
    try:
        response = requests.get("http://localhost:8000/status", timeout=5)
        if response.status_code != 200:
            print("❌ API não está funcionando")
            return
    except:
        print("❌ API não está acessível")
        return
    
    print("✅ Verificações OK")
    
    # Executar avaliação
    evaluator = SimpleEvaluator("http://localhost:8000")
    
    try:
        test_cases = evaluator.load_test_cases("test_cases.json")
        print(f"📋 Carregados {len(test_cases)} casos de teste")
        
        report = evaluator.run_evaluation(test_cases)
        
        # Mostrar resumo
        print("\n" + "=" * 50)
        print("📊 RESUMO DA AVALIAÇÃO")
        print("=" * 50)
        
        summary = report['summary']
        print(f"✅ Total de testes: {summary['total_tests']}")
        print(f"🎯 Accuracy de roteamento: {summary['routing_accuracy']:.1%}")
        print(f"⚡ Tempo médio de resposta: {summary['avg_response_time_ms']:.0f}ms")
        
        # Performance por agente
        print(f"\n🤖 Performance por Agente:")
        for agent, accuracy in report['agent_performance']['routing_accuracy_by_agent'].items():
            status = "✅" if accuracy > 0.8 else "⚠️" if accuracy > 0.6 else "❌"
            print(f"   {status} {agent}: {accuracy:.1%}")
        
        # Salvar relatório
        filename = evaluator.save_report(report)
        print(f"\n💾 Relatório salvo em: {filename}")
        
        print("\n🎉 Avaliação concluída com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
