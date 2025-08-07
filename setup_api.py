#!/usr/bin/env python3
"""
Script de setup inicial para a API do Sistema de Agentes
"""

import os
import sys
from pathlib import Path

def check_dependencies():
    """Verifica se as dependências estão instaladas"""
    print("🔍 Verificando dependências...")
    
    required_packages = [
        'fastapi',
        'uvicorn',
        'semantic_kernel', 
        'openai',
        'pydantic'
    ]
    
    # Teste especial para python-dotenv
    try:
        import dotenv
        print("✅ python-dotenv")
    except ImportError:
        missing.append('python-dotenv')
        print("❌ python-dotenv")
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            missing.append(package)
            print(f"❌ {package}")
    
    if missing:
        print("\n📦 Instale as dependências faltantes:")
        print("pip install -r requirements.txt")
        return False
    
    return True

def check_env_file():
    """Verifica se o arquivo .env existe"""
    print("\n🔧 Verificando configuração...")
    
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ Arquivo .env não encontrado")
        print("\n📝 Criando arquivo .env de exemplo...")
        
        with open(".env", "w") as f:
            f.write("# Configuração da API do Sistema de Agentes\n")
            f.write("OPENAI_API_KEY=sua_chave_openai_aqui\n")
            f.write("\n# Configurações opcionais\n")
            f.write("LOG_LEVEL=INFO\n")
        
        print("✅ Arquivo .env criado!")
        print("⚠️ ATENÇÃO: Configure sua chave da OpenAI no arquivo .env")
        return False
    
    # Verificar se tem OPENAI_API_KEY
    with open(".env", "r") as f:
        content = f.read()
        if "sua_chave_openai_aqui" in content:
            print("⚠️ Configure sua chave da OpenAI no arquivo .env")
            return False
    
    print("✅ Arquivo .env configurado")
    return True

def check_config_files():
    """Verifica se os arquivos de configuração existem"""
    print("\n📁 Verificando arquivos de configuração...")
    
    config_dir = Path("config")
    if not config_dir.exists():
        print("❌ Diretório config não encontrado")
        return False
    
    agents_config = config_dir / "agents_config.json"
    if not agents_config.exists():
        print("❌ agents_config.json não encontrado")
        return False
    
    guardrails_config = config_dir / "guardrails_config.json"
    if not guardrails_config.exists():
        print("❌ guardrails_config.json não encontrado")
        return False
    
    print("✅ Arquivos de configuração OK")
    return True

def run_tests():
    """Executa testes básicos"""
    print("\n🧪 Executando testes básicos...")
    
    try:
        # Importar e testar módulos principais
        sys.path.append(".")
        
        from api.models import AgentConfig, MessageRequest
        print("✅ Modelos carregados")
        
        from agents.agent_loader import carregar_agentes_dinamicamente
        agents = carregar_agentes_dinamicamente()
        print(f"✅ Configuração carregada: {len(agents)} agentes")
        
        return True
    except Exception as e:
        print(f"❌ Erro nos testes: {e}")
        return False

def main():
    """Função principal"""
    print("🚀 Setup da API do Sistema de Agentes Especialistas")
    print("=" * 60)
    
    success = True
    
    # Verificações
    if not check_dependencies():
        success = False
    
    if not check_env_file():
        success = False
    
    if not check_config_files():
        success = False
    
    if success and not run_tests():
        success = False
    
    print("\n" + "=" * 60)
    
    if success:
        print("✅ Setup concluído com sucesso!")
        print("\n🚀 Para iniciar o servidor:")
        print("python run_api.py")
        print("\n📖 Documentação:")
        print("http://localhost:8000/docs")
    else:
        print("❌ Setup incompleto. Corrija os problemas acima.")
    
    return success

if __name__ == "__main__":
    if main():
        sys.exit(0)
    else:
        sys.exit(1)
