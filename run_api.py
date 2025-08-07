#!/usr/bin/env python3
"""
Servidor da API do Sistema de Agentes Especialistas
"""

import uvicorn
from api.config import DEFAULT_HOST, DEFAULT_PORT

if __name__ == "__main__":
    print("🚀 Iniciando servidor da API...")
    print(f"📍 Acesse: http://{DEFAULT_HOST}:{DEFAULT_PORT}/docs")
    
    uvicorn.run(
        "api.main:app",  # Import string para permitir reload
        host=DEFAULT_HOST,
        port=DEFAULT_PORT,
        reload=True,  # Para desenvolvimento
        log_level="info"
    )
