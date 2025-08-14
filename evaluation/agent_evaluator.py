"""
Sistema de Avaliação de Agentes de IA
=====================================

Framework reutilizável para avaliar sistemas multi-agentes usando RAGAs.

Métricas avaliadas:
- Roteamento correto para agentes especializados
- Uso de contexto/histórico conversacional  
- Qualidade das respostas (RAGAs)
- Performance e latência

Uso:
    python agent_evaluator.py --config config.json
"""

import os
import json
import time
import asyncio
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import requests
from dotenv import load_dotenv

# RAGAs imports
from ragas import evaluate
from ragas.metrics import (
    answer_relevancy,
    answer_correctness,
    answer_similarity,
    faithfulness
)
from datasets import Dataset

# Plotting
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# Configuração
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TestCase:
    """Caso de teste para avaliação"""
    id: str
    message: str
    expected_agent: str
    expected_response_type: str
    context_dependent: bool = False
    previous_messages: List[str] = None
    ground_truth: str = ""
    expected_keywords: List[str] = None


@dataclass 
class EvaluationResult:
    """Resultado de uma avaliação"""
    test_id: str
    message: str
    actual_agent: str
    expected_agent: str
    agent_routing_correct: bool
    response: str
    response_time_ms: float
    context_used: bool
    ragas_scores: Dict[str, float]
    timestamp: datetime


class AgentEvaluator:
    """Avaliador principal de sistemas multi-agentes"""
    
    def __init__(self, api_base_url: str, openai_api_key: str):
        self.api_base_url = api_base_url.rstrip('/')
        self.openai_api_key = openai_api_key
        self.results: List[EvaluationResult] = []
        
        # Configurar RAGAs
        os.environ["OPENAI_API_KEY"] = openai_api_key
        
    def load_test_cases(self, test_file: str) -> List[TestCase]:
        """Carrega casos de teste do arquivo JSON"""
        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            test_cases = []
            for item in data['test_cases']:
                test_cases.append(TestCase(**item))
            
            logger.info(f"✅ Carregados {len(test_cases)} casos de teste")
            return test_cases
            
        except Exception as e:
            logger.error(f"❌ Erro ao carregar casos de teste: {e}")
            raise
    
    async def evaluate_system(self, test_cases: List[TestCase]) -> Dict[str, Any]:
        """Executa avaliação completa do sistema"""
        logger.info("🚀 Iniciando avaliação do sistema de agentes...")
        
        # Limpar histórico antes de começar
        self._clear_chat_history()
        
        # Executar casos de teste
        for i, test_case in enumerate(test_cases, 1):
            logger.info(f"📝 Executando teste {i}/{len(test_cases)}: {test_case.id}")
            
            try:
                result = await self._execute_test_case(test_case)
                self.results.append(result)
                
                # Pequena pausa entre testes
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"❌ Erro no teste {test_case.id}: {e}")
                continue
        
        # Gerar relatório
        report = self._generate_report()
        return report
    
    async def _execute_test_case(self, test_case: TestCase) -> EvaluationResult:
        """Executa um caso de teste individual"""
        
        # Se tem dependência de contexto, enviar mensagens anteriores
        if test_case.context_dependent and test_case.previous_messages:
            for msg in test_case.previous_messages:
                await self._send_message(msg)
                await asyncio.sleep(0.3)
        
        # Medir tempo de resposta
        start_time = time.time()
        response_data = await self._send_message(test_case.message)
        end_time = time.time()
        
        response_time_ms = (end_time - start_time) * 1000
        
        # Extrair informações da resposta
        actual_agent = response_data.get('agent_name', 'Unknown')
        response_text = response_data.get('response', '')
        
        # Verificar roteamento
        agent_routing_correct = (actual_agent == test_case.expected_agent)
        
        # Verificar uso de contexto (simplificado)
        context_used = self._check_context_usage(test_case, response_text)
        
        # Calcular métricas RAGAs
        ragas_scores = await self._calculate_ragas_metrics(
            test_case.message,
            response_text,
            test_case.ground_truth
        )
        
        return EvaluationResult(
            test_id=test_case.id,
            message=test_case.message,
            actual_agent=actual_agent,
            expected_agent=test_case.expected_agent,
            agent_routing_correct=agent_routing_correct,
            response=response_text,
            response_time_ms=response_time_ms,
            context_used=context_used,
            ragas_scores=ragas_scores,
            timestamp=datetime.now()
        )
    
    async def _send_message(self, message: str) -> Dict[str, Any]:
        """Envia mensagem para API"""
        try:
            response = requests.post(
                f"{self.api_base_url}/chat/send",
                json={"message": message},
                timeout=30
            )
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem: {e}")
            raise
    
    def _clear_chat_history(self):
        """Limpa histórico de conversas"""
        try:
            response = requests.delete(f"{self.api_base_url}/chat/history")
            response.raise_for_status()
            logger.info("🧹 Histórico limpo")
        except Exception as e:
            logger.warning(f"Aviso: Não foi possível limpar histórico: {e}")
    
    def _check_context_usage(self, test_case: TestCase, response: str) -> bool:
        """Verifica se o agente usou contexto da conversa"""
        if not test_case.context_dependent:
            return True  # Não precisa de contexto
        
        # Verificações simples de contexto
        if test_case.expected_keywords:
            for keyword in test_case.expected_keywords:
                if keyword.lower() in response.lower():
                    return True
        
        # Se tem mensagens anteriores, verificar referências
        if test_case.previous_messages:
            for prev_msg in test_case.previous_messages:
                # Procurar palavras-chave das mensagens anteriores na resposta
                words = prev_msg.split()
                key_words = [w for w in words if len(w) > 4 and w.isalpha()]
                for word in key_words[:3]:  # Primeiras 3 palavras significativas
                    if word.lower() in response.lower():
                        return True
        
        return False
    
    async def _calculate_ragas_metrics(self, question: str, answer: str, ground_truth: str) -> Dict[str, float]:
        """
        Calcula métricas RAGAs seguindo a documentação oficial
        https://docs.ragas.io/en/stable/getstarted/evals/
        """
        try:
            from ragas import evaluate, EvaluationDataset
            from ragas.metrics import AspectCritic
            from ragas.llms import LangchainLLMWrapper
            from langchain_openai import ChatOpenAI
            from datasets import Dataset
            
            if not ground_truth:
                return {"no_ground_truth": 0.0}
            
            # Configurar LLM para RAGAs
            evaluator_llm = LangchainLLMWrapper(ChatOpenAI(model="gpt-4", api_key=self.openai_api_key))
            
            # Criar dados para avaliação
            test_data = [{
                "user_input": question,
                "response": answer,
            }]
            
            # Converter para dataset RAGAs
            dataset = Dataset.from_list(test_data)
            eval_dataset = EvaluationDataset.from_hf_dataset(dataset)
            
            # Definir métricas
            metrics = [
                AspectCritic(
                    name="answer_relevancy",
                    llm=evaluator_llm, 
                    definition="Verify if the response is relevant to the user input."
                ),
                AspectCritic(
                    name="answer_correctness",
                    llm=evaluator_llm,
                    definition="Verify if the response is factually correct."
                ),
                AspectCritic(
                    name="answer_similarity",
                    llm=evaluator_llm,
                    definition="Verify if the response is comprehensive and helpful."
                ),
                AspectCritic(
                    name="faithfulness",
                    llm=evaluator_llm,
                    definition="Verify if the response is faithful and trustworthy."
                )
            ]
            
            # Executar avaliação
            results = evaluate(eval_dataset, metrics=metrics)
            
            # Converter resultados para dict
            ragas_scores = {}
            if hasattr(results, 'to_pandas'):
                df = results.to_pandas()
                for col in df.columns:
                    try:
                        value = df[col].iloc[0] if len(df) > 0 else 0.0
                        ragas_scores[col] = float(value) if pd.notna(value) else 0.0
                    except (ValueError, TypeError, IndexError):
                        ragas_scores[col] = 0.0
            else:
                # Se results for dict direto
                for metric_name in ["answer_relevancy", "answer_correctness", "answer_similarity", "faithfulness"]:
                    ragas_scores[metric_name] = float(results.get(metric_name, 0.0))
            
            return ragas_scores
            
        except Exception as e:
            logger.warning(f"Erro no cálculo RAGAs: {e}")
            return {
                "answer_relevancy": 0.0,
                "answer_correctness": 0.0,
                "answer_similarity": 0.0,
                "faithfulness": 0.0
            }
    
    def _generate_report(self) -> Dict[str, Any]:
        """Gera relatório completo da avaliação"""
        if not self.results:
            return {"error": "Nenhum resultado disponível"}
        
        # Converter para DataFrame
        df = pd.DataFrame([asdict(r) for r in self.results])
        
        # Métricas gerais
        total_tests = len(self.results)
        routing_accuracy = df['agent_routing_correct'].mean()
        context_usage = df['context_used'].mean()
        avg_response_time = df['response_time_ms'].mean()
        
        # Métricas RAGAs
        ragas_df = pd.json_normalize(df['ragas_scores'])
        ragas_means = {}
        
        # Calcular médias de forma segura
        for col in ragas_df.columns:
            try:
                # Filtrar valores numéricos válidos
                valid_values = pd.to_numeric(ragas_df[col], errors='coerce').dropna()
                if len(valid_values) > 0:
                    ragas_means[col] = valid_values.mean()
                else:
                    ragas_means[col] = 0.0
            except Exception as e:
                logger.warning(f"Erro ao calcular média para {col}: {e}")
                ragas_means[col] = 0.0
        
        # Distribuição por agente
        agent_distribution = df['actual_agent'].value_counts().to_dict()
        routing_by_agent = df.groupby('expected_agent')['agent_routing_correct'].mean().to_dict()
        
        report = {
            "summary": {
                "total_tests": total_tests,
                "routing_accuracy": round(routing_accuracy, 3),
                "context_usage_rate": round(context_usage, 3),
                "avg_response_time_ms": round(avg_response_time, 2),
                "evaluation_timestamp": datetime.now().isoformat()
            },
            "ragas_metrics": {k: round(v, 3) for k, v in ragas_means.items()},
            "agent_performance": {
                "distribution": agent_distribution,
                "routing_accuracy_by_agent": {k: round(v, 3) for k, v in routing_by_agent.items()}
            },
            "detailed_results": [asdict(r) for r in self.results]
        }
        
        return report
    
    def save_report(self, report: Dict[str, Any], output_dir: str = "results"):
        """Salva relatório em múltiplos formatos"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON completo
        json_file = output_path / f"evaluation_report_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        # CSV dos resultados
        csv_file = output_path / f"evaluation_results_{timestamp}.csv"
        df = pd.DataFrame(report["detailed_results"])
        df.to_csv(csv_file, index=False, encoding='utf-8')
        
        # Gráficos
        self._generate_plots(report, output_path, timestamp)
        
        logger.info(f"📊 Relatório salvo em: {output_path}")
        return json_file
    
    def _generate_plots(self, report: Dict[str, Any], output_path: Path, timestamp: str):
        """Gera visualizações dos resultados"""
        try:
            # Configurar estilo
            plt.style.use('seaborn-v0_8')
            sns.set_palette("husl")
            
            # 1. Accuracy por agente
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
            
            # Routing Accuracy
            agents = list(report["agent_performance"]["routing_accuracy_by_agent"].keys())
            accuracies = list(report["agent_performance"]["routing_accuracy_by_agent"].values())
            
            ax1.bar(agents, accuracies)
            ax1.set_title('Accuracy de Roteamento por Agente')
            ax1.set_ylabel('Accuracy')
            ax1.tick_params(axis='x', rotation=45)
            
            # Distribuição de agentes
            agent_counts = report["agent_performance"]["distribution"]
            ax2.pie(agent_counts.values(), labels=agent_counts.keys(), autopct='%1.1f%%')
            ax2.set_title('Distribuição de Testes por Agente')
            
            # Métricas RAGAs
            ragas_metrics = report["ragas_metrics"]
            if ragas_metrics:
                metrics = list(ragas_metrics.keys())
                values = list(ragas_metrics.values())
                
                ax3.bar(metrics, values)
                ax3.set_title('Métricas RAGAs')
                ax3.set_ylabel('Score')
                ax3.tick_params(axis='x', rotation=45)
            
            # Tempo de resposta
            df = pd.DataFrame(report["detailed_results"])
            ax4.hist(df['response_time_ms'], bins=20, alpha=0.7)
            ax4.set_title('Distribuição do Tempo de Resposta')
            ax4.set_xlabel('Tempo (ms)')
            ax4.set_ylabel('Frequência')
            
            plt.tight_layout()
            plt.savefig(output_path / f"evaluation_charts_{timestamp}.png", dpi=300, bbox_inches='tight')
            plt.close()
            
            # 2. Gráfico interativo com Plotly
            self._create_interactive_dashboard(report, output_path, timestamp)
            
        except Exception as e:
            logger.warning(f"Erro ao gerar gráficos: {e}")
    
    def _create_interactive_dashboard(self, report: Dict[str, Any], output_path: Path, timestamp: str):
        """Cria dashboard interativo"""
        try:
            df = pd.DataFrame(report["detailed_results"])
            
            # Criar subplots
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('Routing Accuracy', 'Response Time Distribution', 
                               'RAGAs Metrics', 'Agent Performance'),
                specs=[[{"type": "bar"}, {"type": "histogram"}],
                       [{"type": "bar"}, {"type": "bar"}]]
            )
            
            # Routing accuracy
            routing_data = report["agent_performance"]["routing_accuracy_by_agent"]
            fig.add_trace(
                go.Bar(x=list(routing_data.keys()), y=list(routing_data.values()), 
                       name="Routing Accuracy"),
                row=1, col=1
            )
            
            # Response time
            fig.add_trace(
                go.Histogram(x=df['response_time_ms'], name="Response Time"),
                row=1, col=2
            )
            
            # RAGAs metrics
            ragas_data = report["ragas_metrics"]
            if ragas_data:
                fig.add_trace(
                    go.Bar(x=list(ragas_data.keys()), y=list(ragas_data.values()),
                           name="RAGAs Scores"),
                    row=2, col=1
                )
            
            # Agent distribution
            agent_dist = report["agent_performance"]["distribution"]
            fig.add_trace(
                go.Bar(x=list(agent_dist.keys()), y=list(agent_dist.values()),
                       name="Test Distribution"),
                row=2, col=2
            )
            
            fig.update_layout(
                title="Sistema de Agentes - Relatório de Avaliação",
                showlegend=False,
                height=800
            )
            
            # Salvar
            html_file = output_path / f"interactive_dashboard_{timestamp}.html"
            fig.write_html(str(html_file))
            
        except Exception as e:
            logger.warning(f"Erro ao criar dashboard: {e}")


async def main():
    """Função principal"""
    # Configuração
    api_base_url = "http://localhost:8000"
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY não configurada")
    
    # Inicializar avaliador
    evaluator = AgentEvaluator(api_base_url, openai_api_key)
    
    # Carregar casos de teste
    test_cases = evaluator.load_test_cases("test_cases.json")
    
    # Executar avaliação
    report = await evaluator.evaluate_system(test_cases)
    
    # Salvar relatório
    output_file = evaluator.save_report(report)
    
    # Exibir resumo
    print("\n" + "="*60)
    print("📊 RELATÓRIO DE AVALIAÇÃO DO SISTEMA DE AGENTES")
    print("="*60)
    print(f"✅ Total de testes: {report['summary']['total_tests']}")
    print(f"🎯 Accuracy de roteamento: {report['summary']['routing_accuracy']:.1%}")
    print(f"🧠 Taxa de uso de contexto: {report['summary']['context_usage_rate']:.1%}")
    print(f"⚡ Tempo médio de resposta: {report['summary']['avg_response_time_ms']:.0f}ms")
    
    if report['ragas_metrics']:
        print(f"\n📈 Métricas RAGAs:")
        for metric, value in report['ragas_metrics'].items():
            print(f"   {metric}: {value:.3f}")
    
    print(f"\n💾 Relatório salvo: {output_file}")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
