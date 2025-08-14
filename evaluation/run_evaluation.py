#!/usr/bin/env python3
"""
Script para executar avaliação dos agentes usando RAGAs
Baseado na documentação oficial: https://docs.ragas.io/en/stable/getstarted/evals/
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

def check_dependencies():
    """Verifica se as dependências estão instaladas"""
    try:
        import ragas
        import requests
        import pandas as pd
        import matplotlib.pyplot as plt
        print("✅ Dependências verificadas")
        return True
    except ImportError as e:
        print(f"❌ Dependência faltando: {e}")
        print("💡 Execute: pip install -r requirements.txt")
        return False

def check_api_connection():
    """Verifica se a API está rodando"""
    try:
        response = requests.get("http://localhost:8000/status", timeout=5)
        if response.status_code == 200:
            print("✅ API está rodando")
            return True
        else:
            print(f"❌ API retornou status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Não foi possível conectar à API: {e}")
        print("💡 Certifique-se que a API está rodando em http://localhost:8000")
        return False

def check_openai_key():
    """Verifica se a chave OpenAI está configurada"""
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key and api_key.startswith("sk-"):
        print("✅ OPENAI_API_KEY configurada")
        return True
    else:
        print("❌ OPENAI_API_KEY não configurada ou inválida")
        print("💡 Configure no arquivo .env: OPENAI_API_KEY=sua_chave")
        return False

async def run_evaluation():
    """Executa a avaliação completa"""
    print("\n" + "="*60)
    print("🚀 INICIANDO AVALIAÇÃO DO SISTEMA DE AGENTES")
    print("="*60)
    
    # Verificações preliminares
    checks = [
        ("Dependências", check_dependencies()),
        ("API Connection", check_api_connection()),
        ("OpenAI Key", check_openai_key())
    ]
    
    if not all(check[1] for check in checks):
        print("\n❌ Falha nas verificações preliminares")
        return False
    
    print("\n✅ Todas as verificações passaram!")
    print("\n📝 Iniciando avaliação...")
    
    try:
        # Importar avaliador
        from agent_evaluator import AgentEvaluator
        
        # Configurar
        api_base_url = "http://localhost:8000"
        openai_api_key = os.getenv("OPENAI_API_KEY")
        
        # Inicializar avaliador
        evaluator = AgentEvaluator(api_base_url, openai_api_key)
        
        # Carregar casos de teste
        test_cases = evaluator.load_test_cases("test_cases.json")
        
        # Executar avaliação usando o método correto
        print(f"📊 Executando {len(test_cases)} casos de teste...")
        results = await evaluator.evaluate_system(test_cases)
        
        if not results:
            print("❌ Nenhum resultado foi retornado")
            return False
        
        # Exibir resumo
        print("\n" + "="*60)
        print("📊 RESUMO DA AVALIAÇÃO")
        print("="*60)
        
        summary = results.get('summary', {})
        print(f"✅ Total de testes: {summary.get('total_tests', 0)}")
        print(f"🎯 Accuracy de roteamento: {summary.get('routing_accuracy', 0):.1%}")
        print(f"🧠 Taxa de uso de contexto: {summary.get('context_usage_rate', 0):.1%}")
        print(f"⚡ Tempo médio de resposta: {summary.get('avg_response_time_ms', 0):.0f}ms")
        
        # Métricas RAGAs
        ragas_means = summary.get('ragas_means', {})
        if ragas_means:
            print("\n📈 Métricas RAGAs (0-1, maior é melhor):")
            for metric, value in ragas_means.items():
                if isinstance(value, (int, float)):
                    if value > 0.7:
                        status = "✅"
                    elif value > 0.5:
                        status = "⚠️"
                    else:
                        status = "❌"
                    print(f"   {status} {metric}: {value:.3f}")
        
        # Análise por agente
        agent_performance = results.get('agent_performance', {})
        routing_by_agent = agent_performance.get('routing_accuracy_by_agent', {})
        if routing_by_agent:
            print("\n🤖 Performance por Agente:")
            for agent, accuracy in routing_by_agent.items():
                if accuracy > 0.8:
                    status = "✅"
                elif accuracy > 0.6:
                    status = "⚠️"
                else:
                    status = "❌"
                print(f"   {status} {agent}: {accuracy:.1%}")
        
        # Salvar relatório
        output_file = evaluator.save_report(results)
        print(f"\n💾 Relatório completo salvo em: {output_file}")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"❌ Erro durante avaliação: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Função principal"""
    print("🤖 Sistema de Avaliação de Agentes de IA")
    print("Versão: 1.0.0 - RAGAs Integration")
    print("="*60)
    
    # Verificar se estamos no diretório correto
    if not Path("test_cases.json").exists():
        print("❌ Arquivo test_cases.json não encontrado")
        print("💡 Execute este script na pasta evaluation/")
        return
    
    try:
        # Executar avaliação
        success = asyncio.run(run_evaluation())
        
        if success:
            print("\n🎉 Avaliação concluída com sucesso!")
            print("💡 Verifique os gráficos e relatórios gerados")
        else:
            print("\n💥 Avaliação falhou!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️ Avaliação interrompida pelo usuário")
    except Exception as e:
        print(f"\n💥 Erro crítico: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
