# 🚀 API do Sistema de Agentes - Quick Start

## Configuração Rápida

1. **Setup inicial:**
```bash
python setup_api.py
```

2. **Instalar dependências:**
```bash
pip install -r requirements.txt
```

3. **Configurar .env:**
```
OPENAI_API_KEY=sua_chave_openai_aqui
```

4. **Iniciar servidor:**
```bash
python run_api.py
```

5. **Testar API:**
```bash
python test_api.py
```

## 📋 Endpoints Essenciais

### 💬 Enviar Mensagem
```bash
curl -X POST "http://localhost:8000/chat/send" \
     -H "Content-Type: application/json" \
     -d '{"message": "Preciso de ajuda com investimentos"}'
```

### 👥 Listar Agentes
```bash
curl "http://localhost:8000/agents"
```

### 🛡️ Listar Guardrails
```bash
curl "http://localhost:8000/guardrails"
```

### 📊 Status do Sistema
```bash
curl "http://localhost:8000/status"
```

### 📝 Histórico de Chat
```bash
curl "http://localhost:8000/chat/history?limit=10"
```

## 🆕 Criar Novo Agente
```bash
curl -X POST "http://localhost:8000/agents" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "CustomerServiceAgent",
       "description": "Especialista em atendimento ao cliente",
       "instructions": "Você é um especialista em atendimento. Ajude com reclamações e dúvidas."
     }'
```

## 🛡️ Criar Novo Guardrail
```bash
curl -X POST "http://localhost:8000/guardrails" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "PoliticsGuardrail",
       "description": "Bloqueia discussões políticas",
       "keywords": ["política", "eleição", "governo"],
       "enabled": true
     }'
```

## 📖 Documentação Completa
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## 🏗️ Arquitetura Mantida
- ✅ **Handoff Orchestration** (Semantic Kernel)
- ✅ **TriageAgent** (Roteamento inteligente)
- ✅ **Agentes Especialistas** (Dinâmicos)
- ✅ **Guardrails & Moderação**
- ✅ **Histórico Persistente**
