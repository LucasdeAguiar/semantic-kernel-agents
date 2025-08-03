# Core funcionalidades
from .memory_manager import ChatHistoryManager, criar_memoria_volatil
from .function_caller import FunctionRegistry, setup_default_functions

__all__ = ['ChatHistoryManager', 'criar_memoria_volatil', 'FunctionRegistry', 'setup_default_functions']
