# Arquivo de configuração da API
import os
from pathlib import Path

# Configurações básicas
API_TITLE = "Sistema de Agentes Especialistas"
API_DESCRIPTION = "API REST para gerenciar agentes com arquitetura Handoff Orchestration usando Semantic Kernel"
API_VERSION = "1.0.0"

# Configurações do servidor
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8000

# Caminhos dos arquivos
BASE_DIR = Path(__file__).parent.parent
CONFIG_DIR = BASE_DIR / "config"
AGENTS_CONFIG_FILE = CONFIG_DIR / "agents_config.json"
GUARDRAILS_CONFIG_FILE = CONFIG_DIR / "guardrails_config.json"
CHAT_HISTORY_FILE = BASE_DIR / "chat_history.json"

# Configurações de logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Configurações OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = "gpt-4"

# Configurações do sistema
MAX_HISTORY_MESSAGES = 1000
DEFAULT_HISTORY_LIMIT = 50

# Mensagens constantes
SYSTEM_NOT_INITIALIZED = "Sistema não inicializado"
SYSTEM_INITIALIZED_SUCCESS = "Sistema inicializado com sucesso"
SYSTEM_SHUTDOWN_SUCCESS = "Sistema encerrado com sucesso"
