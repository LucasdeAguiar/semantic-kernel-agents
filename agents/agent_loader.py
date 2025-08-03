import json
from pathlib import Path
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


def carregar_agentes_dinamicamente(path: str = "config/agents_config.json") -> List[Dict[str, Any]]:
    """
    Carrega a configuração dos agentes dinamicamente a partir de um arquivo JSON.
    
    Args:
        path: Caminho para o arquivo de configuração JSON
        
    Returns:
        Lista de dicionários com as configurações dos agentes
        
    Raises:
        FileNotFoundError: Se o arquivo não for encontrado
        json.JSONDecodeError: Se o arquivo JSON for inválido
    """
    try:
        config_path = Path(path)
        
        if not config_path.exists():
            logger.error(f"Arquivo de configuração não encontrado: {config_path.absolute()}")
            raise FileNotFoundError(f"Arquivo de configuração não encontrado: {config_path.absolute()}")
        
        with open(config_path, "r", encoding="utf-8") as file:
            config_data = json.load(file)
            
        if not isinstance(config_data, list):
            raise ValueError("O arquivo de configuração deve conter uma lista de agentes")
        
        # Validar estrutura básica de cada agente
        required_fields = ["name", "description", "instructions"]
        for i, agent_config in enumerate(config_data):
            for field in required_fields:
                if field not in agent_config:
                    raise ValueError(f"Agente {i}: campo obrigatório '{field}' não encontrado")
        
        logger.info(f"Carregados {len(config_data)} agentes da configuração")
        return config_data
        
    except json.JSONDecodeError as e:
        logger.error(f"Erro ao decodificar JSON: {e}")
        raise json.JSONDecodeError(f"Arquivo JSON inválido: {e}", e.doc, e.pos)
    except Exception as e:
        logger.error(f"Erro ao carregar configuração dos agentes: {e}")
        raise


def validar_configuracao_agente(config: Dict[str, Any]) -> bool:
    """
    Valida se a configuração de um agente está correta.
    
    Args:
        config: Dicionário com a configuração do agente
        
    Returns:
        True se a configuração for válida
        
    Raises:
        ValueError: Se a configuração for inválida
    """
    required_fields = ["name", "description", "instructions"]
    optional_fields = ["plugins", "functions", "settings"]
    
    # Verificar campos obrigatórios
    for field in required_fields:
        if field not in config:
            raise ValueError(f"Campo obrigatório '{field}' não encontrado")
        if not isinstance(config[field], str) or not config[field].strip():
            raise ValueError(f"Campo '{field}' deve ser uma string não vazia")
    
    # Verificar se há campos desconhecidos
    all_known_fields = required_fields + optional_fields
    for field in config.keys():
        if field not in all_known_fields:
            logger.warning(f"Campo desconhecido '{field}' ignorado na configuração do agente {config.get('name', 'desconhecido')}")
    
    return True


def salvar_configuracao_agentes(agentes: List[Dict[str, Any]], path: str = "config/agents_config.json") -> None:
    """
    Salva a configuração dos agentes em um arquivo JSON.
    
    Args:
        agentes: Lista de configurações dos agentes
        path: Caminho onde salvar o arquivo
    """
    try:
        # Validar todas as configurações antes de salvar
        for i, agente in enumerate(agentes):
            try:
                validar_configuracao_agente(agente)
            except ValueError as e:
                raise ValueError(f"Agente {i} ({agente.get('name', 'desconhecido')}): {e}")
        
        config_path = Path(path)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, "w", encoding="utf-8") as file:
            json.dump(agentes, file, ensure_ascii=False, indent=2)
        
        logger.info(f"Configuração de {len(agentes)} agentes salva em {config_path.absolute()}")
        
    except Exception as e:
        logger.error(f"Erro ao salvar configuração dos agentes: {e}")
        raise
