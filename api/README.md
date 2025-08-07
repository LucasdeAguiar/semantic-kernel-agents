# API do Sistema de Agentes Especialistas

API REST construída com FastAPI para gerenciar agentes com arquitetura Handoff Orchestration usando Semantic Kernel.

## 🚀 Como Executar

1. **Instalar dependências:**
```bash
pip install -r requirements.txt
```

2. **Configurar variáveis de ambiente:**
Criar arquivo `.env` na raiz do projeto:
```
OPENAI_API_KEY=sua_chave_openai_aqui
```

3. **Executar o servidor:**
```bash
python run_api.py
```

4. **Acessar documentação:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 📋 Endpoints Disponíveis

### Sistema
- `GET /` - Informações básicas da API
- `GET /status` - Status atual do sistema

### Gerenciamento de Agentes
- `GET /agents` - Lista todos os agentes
- `GET /agents/{name}` - Detalhes de um agente específico
- `POST /agents` - Cria um novo agente
- `PUT /agents/{name}` - Atualiza um agente existente
- `DELETE /agents/{name}` - Remove um agente

### Chat
- `POST /chat/send` - Envia mensagem para o sistema
- `GET /chat/history` - Histórico de conversas
- `DELETE /chat/history` - Limpa o histórico

## 💬 Exemplos de Uso

### Criar um novo agente
```json
POST /agents
{
  "name": "CustomerServiceAgent",
  "description": "Especialista em atendimento ao cliente",
  "instructions": "Você é um especialista em atendimento ao cliente. Ajude com reclamações, dúvidas e suporte geral."
}
```

### Enviar mensagem
```json
POST /chat/send
{
  "message": "Preciso de ajuda com investimentos"
}
```

### Resposta do sistema
```json
{
  "success": true,
  "response": "Olá! Sou especialista em investimentos. Como posso ajudá-lo?",
  "agent_name": "FinanceAgent",
  "timestamp": "2025-08-06T10:00:00Z"
}
```

## 🔧 Arquitetura

A API mantém a arquitetura **Handoff Orchestration** do Semantic Kernel:

1. **TriageAgent** - Agente orquestrador que roteia mensagens
2. **Agentes Especialistas** - Criados dinamicamente da configuração
3. **HandoffOrchestration** - Gerencia transferências entre agentes
4. **InProcessRuntime** - Runtime para execução

## 🛡️ Recursos de Segurança

- **Moderação de Conteúdo** - Via OpenAI Moderation API
- **Guardrails** - Regras customizáveis de conteúdo
- **Validação de Input** - Pydantic models
- **Error Handling** - Tratamento robusto de erros

## 📁 Estrutura dos Arquivos

```
api/
├── __init__.py          # Inicialização do módulo
├── main.py             # Aplicação FastAPI principal
├── models.py           # Modelos Pydantic (DTOs)
├── services.py         # Lógica de negócio
└── config.py           # Configurações da API

run_api.py              # Script para executar servidor
```

## 🔄 Fluxo de Funcionamento

1. **Inicialização** - Sistema carrega agentes da configuração JSON
2. **Handoff Setup** - Configura orquestração entre agentes
3. **Runtime Start** - Inicia runtime do Semantic Kernel
4. **Message Processing** - Processa mensagens via handoff
5. **Response** - Retorna resposta do agente adequado

## 📊 Monitoramento

- Logs estruturados com timestamps
- Status do sistema via endpoint `/status`
- Histórico de conversas persistido
- Error tracking e reporting
