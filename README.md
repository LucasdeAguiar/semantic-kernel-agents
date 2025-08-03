# Sistema de Agentes Especialistas com Semantic Kernel

🤖 **Sistema escalável de criação de agentes especialistas dinâmicos usando Microsoft Semantic Kernel com arquitetura de handoff orchestration.**

## 🎯 Visão Geral

Este projeto implementa um sistema completo de agentes especializados que podem ser configurados dinamicamente através de arquivos JSON. O sistema utiliza a **arquitetura de handoff** do Semantic Kernel, permitindo que um agente orquestrador (triage) direcione automaticamente as solicitações para os agentes especialistas mais adequados.

### ✨ Características Principais

- **🔄 Handoff Orchestration**: Transferência inteligente entre agentes usando as funções nativas do Semantic Kernel
- **⚙️ Configuração Dinâmica**: Agentes definidos via JSON, permitindo fácil customização sem alteração de código
- **🧠 Function Calling**: Integração com chamadas de função para executar tarefas específicas
- **💾 Histórico Persistente**: Salvamento automático de conversas com recuperação de sessões
- **🎛️ Human-in-the-Loop**: Capacidade de interação humana durante o fluxo de orquestração
- **📊 Logging Avançado**: Sistema completo de logs para debugging e monitoramento
- **🔌 Extensível**: Arquitetura clean que permite fácil adição de novos agentes e funcionalidades

## 🏗️ Arquitetura

```
semantic-kernel-agents/
├── main.py                 # Ponto de entrada principal
├── requirements.txt        # Dependências do projeto
├── README.md              # Este arquivo
├── agents/                # Agentes especialistas
│   ├── __init__.py
│   ├── agent_loader.py    # Carregamento dinâmico de agentes
│   └── specialist_agent.py # Classes base dos agentes
├── config/                # Configurações
│   └── agents_config.json # Definições dos agentes
├── core/                  # Funcionalidades centrais
│   ├── __init__.py
│   ├── function_caller.py # Sistema de function calling
│   └── memory_manager.py  # Gerenciamento de memória/histórico
└── orchestrator/          # Orquestração
    ├── __init__.py
    └── triage_agent.py    # Agente orquestrador principal
```

## 🚀 Como Usar

### 1. Instalação

```bash
# Clone o repositório
git clone <seu-repositorio>
cd semantic-kernel-agents

# Instale as dependências
pip install -r requirements.txt
```

### 2. Configuração

1. **Configure sua chave OpenAI** no arquivo `main.py`:
```python
OPENAI_API_KEY = "sua-chave-openai-aqui"
```

2. **Personalize os agentes** editando `config/agents_config.json`:
```json
[
  {
    "name": "MeuAgentePersonalizado",
    "description": "Descrição do que o agente faz",
    "instructions": "Instruções detalhadas para o comportamento do agente"
  }
]
```

### 3. Execução

```bash
python main.py
```

## 🎮 Comandos Disponíveis

Durante a execução, você pode usar os seguintes comandos:

- **Conversa normal**: Digite sua pergunta normalmente
- `historico`: Mostra as últimas 10 mensagens
- `limpar`: Limpa o histórico da conversa
- `help`: Mostra ajuda com comandos
- `sair`/`exit`/`quit`: Encerra o sistema

## 🤖 Agentes Padrão

O sistema vem com 4 agentes pré-configurados:

### 🎯 TriageAgent (Orquestrador)
- **Função**: Analisa solicitações e direciona para especialistas
- **Comportamento**: Usa handoff functions para transferir conversas

### 💰 FinanceAgent
- **Especialidade**: Finanças pessoais, investimentos, orçamento
- **Funções**: Cálculo de juros, simulação de financiamentos

### 🛠️ TechSupportAgent  
- **Especialidade**: Suporte técnico, troubleshooting, TI
- **Funções**: Verificação de status de sistemas, restart de serviços

### 🤝 CustomerServiceAgent
- **Especialidade**: Atendimento ao cliente, reclamações
- **Funções**: Gerenciamento de tickets, criação de ocorrências

## 🔧 Function Calling

O sistema inclui funções predefinidas organizadas em plugins:

### UtilityFunctions
- `get_current_time()`: Data e hora atual
- `calculate(expression)`: Cálculos matemáticos
- `format_text(text, format_type)`: Formatação de texto

### CustomerServiceFunctions
- `check_ticket_status(ticket_id)`: Verificar status de ticket
- `create_ticket(tipo, descricao, prioridade)`: Criar novo ticket

### TechSupportFunctions
- `check_system_status(system_name)`: Status de sistemas
- `restart_service(service_name)`: Reiniciar serviços

### FinanceFunctions
- `calculate_interest(principal, rate, time)`: Juros compostos
- `loan_simulation(amount, rate, months)`: Simulação de financiamento

## 📝 Configuração de Agentes

### Estrutura do JSON

```json
{
  "name": "NomeDoAgente",
  "description": "Breve descrição do agente",
  "instructions": "Instruções detalhadas sobre como o agente deve se comportar"
}
```

### Campos Obrigatórios

- **name**: Nome único do agente (usado para handoffs)
- **description**: Descrição clara da especialidade
- **instructions**: Prompt detalhado com comportamento esperado

### Exemplo de Novo Agente

```json
{
  "name": "LegalAgent",
  "description": "Especialista em questões jurídicas e compliance",
  "instructions": "Você é um especialista em direito empresarial. Ajude com dúvidas sobre contratos, compliance, legislação trabalhista e questões jurídicas gerais. IMPORTANTE: Sempre deixe claro que suas respostas são orientações gerais e que casos específicos devem ser analisados por um advogado."
}
```

## 🔄 Fluxo de Handoff

1. **Usuário envia mensagem** → TriageAgent recebe
2. **TriageAgent analisa** a solicitação usando IA
3. **Decisão de roteamento** baseada no conteúdo
4. **Transfer function** é chamada automaticamente
5. **Agente especialista** processa a solicitação
6. **Resposta** é enviada de volta ao usuário
7. **Histórico** é salvo automaticamente

## 💾 Persistência de Dados

- **Histórico de conversas**: Salvo em `chat_history.json`
- **Sessões múltiplas**: Suporte a múltiplas conversas
- **Auto-save**: Salvamento automático após cada interação
- **Recuperação**: Carregamento automático do histórico na inicialização

## 🛠️ Extensibilidade

### Adicionando Novos Agentes

1. Adicione configuração em `agents_config.json`
2. O sistema criará automaticamente o agente
3. Configure handoffs no `TriageAgent` se necessário

### Adicionando Novas Funções

1. Crie uma nova classe de plugin em `core/function_caller.py`
2. Use o decorador `@kernel_function`
3. Registre o plugin no `setup_default_functions()`

### Personalizando Comportamento

- Modifique as instruções dos agentes no JSON
- Adicione novos plugins de função
- Customize callbacks de resposta
- Implemente novos tipos de memória

## 🐛 Debugging

O sistema inclui logging detalhado:

```python
import logging
logging.getLogger().setLevel(logging.DEBUG)  # Para debug verboso
```

Logs importantes:
- **Handoff decisions**: Quando e por que transferências acontecem
- **Function calls**: Quais funções são chamadas
- **Agent responses**: Respostas de cada agente
- **Memory operations**: Salvamento e carregamento de histórico

## 📚 Documentação Técnica

### Baseado na Documentação Oficial Microsoft

- [Semantic Kernel Quick Start](https://learn.microsoft.com/en-us/semantic-kernel/get-started/quick-start-guide?pivots=programming-language-python)
- [Handoff Orchestration](https://learn.microsoft.com/en-us/semantic-kernel/frameworks/agent/agent-orchestration/handoff?pivots=programming-language-python)
- [Agent Framework](https://learn.microsoft.com/en-us/semantic-kernel/frameworks/agent/)

### Principais Classes Utilizadas

- `ChatCompletionAgent`: Agentes baseados em chat completion
- `HandoffOrchestration`: Orquestração de transferências
- `OrchestrationHandoffs`: Configuração de handoffs
- `InProcessRuntime`: Runtime para execução de agentes
- `ChatHistory`: Gerenciamento de histórico

## 🎯 Casos de Uso

### Atendimento ao Cliente
- Triagem automática de solicitações
- Roteamento para departamentos específicos
- Escalação para agentes humanos quando necessário

### Suporte Técnico
- Diagnóstico inicial automatizado
- Direcionamento por especialidade técnica
- Resolução de problemas comum vs. complexos

### Consultoria Financeira
- Categorização de dúvidas financeiras
- Calculadoras especializadas
- Planejamento personalizado

### Help Desk Interno
- Suporte a múltiplos departamentos
- Conhecimento especializado por área
- Histórico de interações

## 🔒 Segurança e Considerações

- **API Keys**: Nunca commit chaves de API no código
- **Input Validation**: Validação de entradas para function calling
- **Rate Limiting**: Considere implementar limits de uso
- **Data Privacy**: Histórico pode conter informações sensíveis
- **Error Handling**: Sistema robusto de tratamento de erros

## 🚧 Próximos Passos

- [ ] Interface web com Streamlit/Gradio
- [ ] Integração com Azure OpenAI Service  
- [ ] Metrics e analytics de performance
- [ ] Testes automatizados
- [ ] Deploy em containers
- [ ] API REST para integração externa
- [ ] Suporte a múltiplos modelos de IA
- [ ] Cache inteligente de respostas

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 💡 Suporte

Para dúvidas ou suporte:
- Abra uma issue no GitHub
- Consulte a [documentação oficial do Semantic Kernel](https://learn.microsoft.com/en-us/semantic-kernel/)
- Verifique os logs do sistema para debugging

---

**Desenvolvido com ❤️ usando Microsoft Semantic Kernel**