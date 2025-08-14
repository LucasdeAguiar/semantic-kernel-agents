# 🔬 Sistema de Avaliação de Agentes de IA

Framework completo e **reutilizável** para avaliar sistemas multi-agentes usando métricas avançadas com RAGAs.

## 📋 O que este sistema avalia

### 🎯 **Roteamento de Agentes**
- Verifica se as mensagens são direcionadas para o agente correto
- Mede accuracy de roteamento por agente
- Identifica casos de roteamento incorreto

### 🧠 **Uso de Contexto**
- Avalia se agentes consideram mensagens anteriores
- Testa continuidade conversacional  
- Verifica referências a interações passadas

### 📊 **Qualidade das Respostas (RAGAs)**
- **Answer Relevancy**: Relevância da resposta
- **Answer Correctness**: Correção factual
- **Answer Similarity**: Similaridade semântica
- **Faithfulness**: Fidelidade ao contexto

### ⚡ **Performance**
- Tempo de resposta por teste
- Distribuição de latência
- Identificação de gargalos

## 🚀 Como usar

### **1. Instalação**

```bash
# Na pasta evaluation/
pip install -r requirements.txt
```

### **2. Configurar ambiente**

Crie arquivo `.env` na raiz do projeto:
```
OPENAI_API_KEY=sua_chave_openai_aqui
```

### **3. Executar avaliação**

```bash
# Método simples
python run_evaluation.py

# Método avançado  
python agent_evaluator.py
```

### **4. Ver resultados**

Os resultados são salvos em `results/` com:
- 📊 **Gráficos estáticos** (PNG)
- 🌐 **Dashboard interativo** (HTML)
- 📈 **Relatório completo** (JSON)
- 📋 **Dados tabulares** (CSV)

## 📁 Estrutura do projeto

```
evaluation/
├── agent_evaluator.py      # Motor principal de avaliação
├── run_evaluation.py       # Script de execução rápida  
├── test_cases.json         # Casos de teste
├── config.json            # Configurações
├── requirements.txt       # Dependências
├── README.md             # Este arquivo
└── results/              # Resultados gerados
    ├── evaluation_report_YYYYMMDD_HHMMSS.json
    ├── evaluation_results_YYYYMMDD_HHMMSS.csv
    ├── evaluation_charts_YYYYMMDD_HHMMSS.png
    └── interactive_dashboard_YYYYMMDD_HHMMSS.html
```

## 🧪 Casos de teste incluídos

### **Roteamento básico**
- ✅ Finanças → FinanceAgent
- ✅ Tecnologia → TechSupportAgent  
- ✅ Vendas → SalesAgent
- ✅ RH → HRAgent
- ✅ Fora de escopo → TriageAgent

### **Contexto conversacional**
- 💬 Perguntas dependentes de mensagens anteriores
- 🔄 Fluxos de conversa multi-turno
- 📝 Referências a interações passadas

### **Casos extremos**
- 🌐 Domínios mistos (finance + tech)
- 📏 Mensagens muito longas
- ❓ Perguntas ambíguas

## 📊 Métricas de sucesso

### **Thresholds esperados:**
- 🎯 **Routing Accuracy**: > 85%
- 🧠 **Context Usage**: > 75%  
- ⚡ **Response Time**: < 5000ms
- 📈 **RAGAs Score**: > 0.7

### **Interpretação RAGAs:**
- **0.8 - 1.0**: 🟢 Excelente
- **0.6 - 0.8**: 🟡 Bom
- **0.4 - 0.6**: 🟠 Regular  
- **< 0.4**: 🔴 Ruim

## 🔧 Personalização para outros projetos

### **1. Modificar casos de teste**

Edite `test_cases.json`:
```json
{
  "test_cases": [
    {
      "id": "seu_teste_01",
      "message": "Sua mensagem de teste",
      "expected_agent": "SeuAgentEsperado",
      "expected_response_type": "tipo_resposta",
      "context_dependent": false,
      "ground_truth": "Resposta esperada para comparação RAGAs"
    }
  ]
}
```

### **2. Configurar API endpoints**

Modifique `config.json`:
```json
{
  "api_config": {
    "base_url": "http://seu-servidor:porta",
    "endpoints": {
      "send_message": "/seu/endpoint/chat",
      "clear_history": "/seu/endpoint/limpar"
    }
  }
}
```

### **3. Adaptar mapeamento de agentes**

No `config.json`:
```json
{
  "agent_mapping": {
    "seu_dominio": ["SeuAgent", "palavra_chave1", "palavra_chave2"]
  }
}
```

## 📈 Relatórios gerados

### **JSON Completo**
```json
{
  "summary": {
    "total_tests": 18,
    "routing_accuracy": 0.944,
    "context_usage_rate": 0.833,
    "avg_response_time_ms": 1250.5
  },
  "ragas_metrics": {
    "answer_relevancy": 0.857,
    "answer_correctness": 0.789,
    "answer_similarity": 0.823,
    "faithfulness": 0.901
  },
  "agent_performance": {
    "routing_accuracy_by_agent": {
      "FinanceAgent": 0.900,
      "TechSupportAgent": 1.000,
      "SalesAgent": 0.950
    }
  }
}
```

### **Dashboard Interativo**
- 📊 Gráficos interativos com Plotly
- 🔍 Drill-down por agente
- 📈 Tendências temporais
- 🎯 Análise de performance

## 🚨 Troubleshooting

### **Erro: "RAGAs não encontrado"**
```bash
pip install ragas>=0.1.0
```

### **Erro: "API não conecta"**
1. Verifique se API está rodando
2. Confirme URL no config.json
3. Teste: `curl http://localhost:8000/status`

### **Erro: "OpenAI API Key inválida"**
1. Verifique `.env` com chave válida
2. Confirme formato: `sk-...`
3. Teste no OpenAI Playground

### **Resultados inconsistentes**
1. Limpe histórico entre execuções
2. Verifique casos de teste duplicados
3. Aguarde alguns segundos entre testes

## 🔄 Execução contínua

### **Para monitoramento contínuo:**

```bash
# Script para execução agendada
#!/bin/bash
cd /caminho/para/evaluation
python run_evaluation.py
# Enviar relatório por email/slack
```

### **Para CI/CD:**

```yaml
# .github/workflows/agent-evaluation.yml
name: Agent Evaluation
on: [push, schedule]
jobs:
  evaluate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - run: |
          cd evaluation
          pip install -r requirements.txt
          python run_evaluation.py
```

## 🎯 Próximos passos

Após executar a avaliação:

1. **Analise o relatório** gerado
2. **Identifique pontos fracos** no roteamento
3. **Compare métricas** entre versões
4. **Otimize prompts** dos agentes
5. **Execute novamente** para medir melhoria

---

**💡 Este framework é totalmente reutilizável para qualquer sistema multi-agentes!**

Basta adaptar os casos de teste e configurações para seu projeto específico.
