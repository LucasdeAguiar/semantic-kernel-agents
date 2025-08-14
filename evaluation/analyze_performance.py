#!/usr/bin/env python3
"""
Análise de Performance do Sistema de Agentes
"""
import json

def analyze_performance():
    # Carregar o relatório
    with open('evaluation_report_20250812_173030.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Analisar tempos de resposta
    response_times = []
    agent_times = {}

    for result in data['detailed_results']:
        time_ms = result['response_time_ms']
        agent = result['actual_agent']
        
        response_times.append(time_ms)
        
        if agent not in agent_times:
            agent_times[agent] = []
        agent_times[agent].append(time_ms)

    # Estatísticas gerais
    response_times.sort()
    print('📊 ANÁLISE DE PERFORMANCE')
    print('=' * 40)
    print(f'⚡ Tempo médio: {sum(response_times)/len(response_times):.0f}ms')
    print(f'🏃 Mais rápido: {min(response_times):.0f}ms')
    print(f'🐌 Mais lento: {max(response_times):.0f}ms')
    print(f'📈 Mediana: {response_times[len(response_times)//2]:.0f}ms')
    print()

    # Por agente
    print('🤖 TEMPO MÉDIO POR AGENTE:')
    for agent, times in agent_times.items():
        avg_time = sum(times) / len(times)
        print(f'   {agent}: {avg_time:.0f}ms ({len(times)} casos)')

    print()
    print('🔥 CASOS MAIS LENTOS:')
    slow_cases = [(r['id'], r['response_time_ms'], r['actual_agent']) for r in data['detailed_results']]
    slow_cases.sort(key=lambda x: x[1], reverse=True)
    for case_id, time_ms, agent in slow_cases[:5]:
        print(f'   {case_id}: {time_ms:.0f}ms ({agent})')

    print()
    print('🎯 RECOMENDAÇÕES:')
    if max(response_times) > 20000:
        print('   ⚠️  Respostas muito longas detectadas (>20s)')
    if sum(response_times)/len(response_times) > 10000:
        print('   ⚠️  Tempo médio alto (>10s) - considerar otimizações')
    
    # Identificar padrões
    finance_avg = sum(agent_times.get('FinanceAgent', [0])) / len(agent_times.get('FinanceAgent', [1]))
    triage_avg = sum(agent_times.get('TriageAgent', [0])) / len(agent_times.get('TriageAgent', [1]))
    
    if finance_avg > triage_avg * 2:
        print('   💡 FinanceAgent é 2x+ mais lento que TriageAgent - revisar prompts')

if __name__ == "__main__":
    analyze_performance()
