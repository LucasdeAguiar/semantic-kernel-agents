#!/usr/bin/env python3
"""
Script de instalação e configuração do Sistema de Agentes Especialistas
"""

import subprocess
import sys
import os
from pathlib import Path


def check_python_version():
    """Verifica se a versão do Python é compatível"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ é necessário")
        print(f"   Versão atual: {version.major}.{version.minor}.{version.micro}")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} - compatível")
    return True


def install_dependencies():
    """Instala as dependências necessárias"""
    print("📦 Instalando dependências...")
    
    try:
        # Atualizar pip
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
                      check=True, capture_output=True)
        print("  ✅ pip atualizado")
        
        # Instalar dependências do requirements.txt
        if Path("requirements.txt").exists():
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                          check=True, capture_output=True)
            print("  ✅ Dependências instaladas do requirements.txt")
        else:
            # Instalar manualmente se não houver requirements.txt
            dependencies = [
                "semantic-kernel>=1.14.0",
                "openai>=1.45.0"
            ]
            
            for dep in dependencies:
                subprocess.run([sys.executable, "-m", "pip", "install", dep], 
                              check=True, capture_output=True)
                print(f"  ✅ {dep} instalado")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"  ❌ Erro na instalação: {e}")
        return False


def create_config_if_needed():
    """Cria arquivo de configuração se não existir"""
    config_dir = Path("config")
    config_file = config_dir / "agents_config.json"
    
    if not config_file.exists():
        print("📝 Criando arquivo de configuração padrão...")
        
        config_dir.mkdir(exist_ok=True)
        
        from agents.agent_loader import criar_configuracao_exemplo, salvar_configuracao_agentes
        
        config_exemplo = criar_configuracao_exemplo()
        salvar_configuracao_agentes(config_exemplo, str(config_file))
        
        print(f"  ✅ Configuração criada em: {config_file}")
    else:
        print("  ✅ Arquivo de configuração já existe")


def setup_api_key():
    """Orienta sobre configuração da chave API"""
    print("🔑 Configuração da Chave API")
    print("=" * 40)
    
    print("Para usar o sistema completo, você precisa:")
    print("1. Ter uma conta OpenAI (https://platform.openai.com)")
    print("2. Criar uma chave API")
    print("3. Configurar a chave no arquivo main.py")
    print()
    
    api_key = input("Digite sua chave OpenAI (ou Enter para pular): ").strip()
    
    if api_key:
        # Atualizar main.py com a chave
        main_file = Path("main.py")
        if main_file.exists():
            content = main_file.read_text(encoding='utf-8')
            
            # Substituir a linha da chave API
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if 'OPENAI_API_KEY = ' in line and line.strip().startswith('OPENAI_API_KEY'):
                    lines[i] = f'OPENAI_API_KEY = "{api_key}"'
                    break
            
            main_file.write_text('\n'.join(lines), encoding='utf-8')
            print("  ✅ Chave API configurada no main.py")
        else:
            print("  ⚠️ Arquivo main.py não encontrado")
    else:
        print("  ⚠️ Chave API não configurada - você pode fazer isso mais tarde editando main.py")


def run_tests():
    """Executa os testes do sistema"""
    print("🧪 Executando testes do sistema...")
    
    try:
        result = subprocess.run([sys.executable, "test_system.py"], 
                               capture_output=True, text=True)
        
        if result.returncode == 0:
            print("  ✅ Todos os testes passaram!")
            return True
        else:
            print("  ❌ Alguns testes falharam:")
            print(result.stdout)
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"  ❌ Erro ao executar testes: {e}")
        return False


def show_next_steps():
    """Mostra os próximos passos"""
    print("\n🎉 Instalação concluída!")
    print("=" * 50)
    print("📋 Próximos passos:")
    print()
    print("1. 🔧 Configure sua chave OpenAI (se ainda não fez):")
    print("   - Edite o arquivo main.py")
    print("   - Substitua 'SUA_OPENAI_API_KEY' pela sua chave real")
    print()
    print("2. ⚙️ Personalize os agentes (opcional):")
    print("   - Edite config/agents_config.json")
    print("   - Adicione novos agentes ou modifique existentes")
    print()
    print("3. 🚀 Execute o sistema:")
    print("   - python main.py (sistema completo)")
    print("   - python demo.py (demonstração sem API)")
    print("   - python test_system.py (executar testes)")
    print()
    print("4. 📚 Leia a documentação:")
    print("   - README.md contém informações detalhadas")
    print("   - Exemplos de uso e personalização")
    print()
    print("🎯 O sistema está pronto para uso!")


def main():
    """Função principal de instalação"""
    print("🚀 Instalador do Sistema de Agentes Especialistas")
    print("=" * 60)
    print("Este script irá configurar seu ambiente para usar o sistema.")
    print("=" * 60)
    print()
    
    steps = [
        ("Verificando versão do Python", check_python_version),
        ("Instalando dependências", install_dependencies),
        ("Criando configuração padrão", create_config_if_needed),
        ("Executando testes", run_tests),
    ]
    
    success_count = 0
    
    for step_name, step_func in steps:
        print(f"⏳ {step_name}...")
        try:
            if step_func():
                success_count += 1
            else:
                print(f"❌ Falha em: {step_name}")
        except Exception as e:
            print(f"❌ Erro em {step_name}: {e}")
    
    print(f"\n📊 Resultado: {success_count}/{len(steps)} etapas concluídas")
    
    if success_count == len(steps):
        print("\n🔑 Configuração da Chave API (opcional)")
        try:
            setup_api_key()
        except Exception as e:
            print(f"⚠️ Erro na configuração da API: {e}")
        
        show_next_steps()
    else:
        print("\n⚠️ Instalação incompleta. Verifique os erros acima.")
        print("💡 Você pode tentar executar novamente ou configurar manualmente.")


if __name__ == "__main__":
    main()
