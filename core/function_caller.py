from semantic_kernel.functions import kernel_function
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel import Kernel
from typing import Dict, Any, List, Callable
import inspect
import logging

logger = logging.getLogger(__name__)


class FunctionRegistry:
    """
    Registro central de funções que podem ser chamadas pelos agentes.
    Permite adicionar funções dinamicamente e organizá-las em plugins.
    """
    
    def __init__(self):
        self.functions: Dict[str, Dict[str, Callable]] = {}
        self.plugins: Dict[str, object] = {}
    
    def register_function(self, plugin_name: str, function_name: str, function: Callable, description: str = ""):
        """Registra uma função em um plugin específico"""
        if plugin_name not in self.functions:
            self.functions[plugin_name] = {}
        
        # Adicionar decorador kernel_function se não estiver presente
        if not hasattr(function, '__kernel_function__'):
            function = kernel_function(
                name=function_name,
                description=description or f"Função {function_name} do plugin {plugin_name}"
            )(function)
        
        self.functions[plugin_name][function_name] = function
        logger.info(f"Função {function_name} registrada no plugin {plugin_name}")
    
    def register_plugin(self, plugin_name: str, plugin_instance: object):
        """Registra um plugin completo"""
        self.plugins[plugin_name] = plugin_instance
        
        # Auto-descobrir funções com decorador @kernel_function
        for attr_name in dir(plugin_instance):
            attr = getattr(plugin_instance, attr_name)
            if callable(attr) and hasattr(attr, '__kernel_function__'):
                self.register_function(plugin_name, attr_name, attr)
    
    def get_plugin_functions(self, plugin_name: str) -> Dict[str, Callable]:
        """Retorna todas as funções de um plugin"""
        return self.functions.get(plugin_name, {})
    
    def get_all_functions(self) -> Dict[str, Dict[str, Callable]]:
        """Retorna todas as funções registradas"""
        return self.functions
    
    def list_functions(self) -> List[str]:
        """Lista todas as funções disponíveis"""
        functions = []
        for plugin_name, plugin_functions in self.functions.items():
            for function_name in plugin_functions.keys():
                functions.append(f"{plugin_name}.{function_name}")
        return functions


class UtilityFunctions:
    """
    Plugin com funções utilitárias básicas para os agentes
    """
    
    @kernel_function(
        name="get_current_time",
        description="Obtém a data e hora atual"
    )
    def get_current_time(self) -> str:
        """Retorna a data e hora atual"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    @kernel_function(
        name="calculate",
        description="Realiza cálculos matemáticos básicos"
    )
    def calculate(self, expression: str) -> str:
        """Calcula uma expressão matemática simples"""
        try:
            # Apenas operações básicas por segurança
            allowed_chars = "0123456789+-*/.() "
            if all(c in allowed_chars for c in expression):
                result = eval(expression)
                return str(result)
            else:
                return "Erro: Expressão contém caracteres não permitidos"
        except Exception as e:
            return f"Erro no cálculo: {str(e)}"
    
    @kernel_function(
        name="format_text",
        description="Formata texto (maiúscula, minúscula, título)"
    )
    def format_text(self, text: str, format_type: str = "title") -> str:
        """Formata texto de acordo com o tipo especificado"""
        format_type = format_type.lower()
        
        if format_type == "upper":
            return text.upper()
        elif format_type == "lower":
            return text.lower()
        elif format_type == "title":
            return text.title()
        elif format_type == "capitalize":
            return text.capitalize()
        else:
            return text


class CustomerServiceFunctions:
    """
    Plugin com funções específicas para atendimento ao cliente
    """
    
    def __init__(self):
        # Simular banco de dados de tickets
        self.tickets = {
            "12345": {"status": "aberto", "tipo": "reclamação", "prioridade": "alta"},
            "67890": {"status": "em_andamento", "tipo": "dúvida", "prioridade": "média"},
            "11111": {"status": "fechado", "tipo": "elogio", "prioridade": "baixa"}
        }
    
    @kernel_function(
        name="check_ticket_status",
        description="Verifica o status de um ticket de atendimento"
    )
    def check_ticket_status(self, ticket_id: str) -> str:
        """Verifica o status de um ticket"""
        ticket = self.tickets.get(ticket_id)
        if ticket:
            return f"Ticket {ticket_id}: Status={ticket['status']}, Tipo={ticket['tipo']}, Prioridade={ticket['prioridade']}"
        else:
            return f"Ticket {ticket_id} não encontrado"
    
    @kernel_function(
        name="create_ticket",
        description="Cria um novo ticket de atendimento"
    )
    def create_ticket(self, tipo: str, descricao: str, prioridade: str = "média") -> str:
        """Cria um novo ticket"""
        import random
        ticket_id = str(random.randint(100000, 999999))
        self.tickets[ticket_id] = {
            "status": "aberto",
            "tipo": tipo,
            "prioridade": prioridade,
            "descricao": descricao
        }
        return f"Ticket {ticket_id} criado com sucesso"


class TechSupportFunctions:
    """
    Plugin com funções para suporte técnico
    """
    
    @kernel_function(
        name="check_system_status",
        description="Verifica o status de um sistema ou serviço"
    )
    def check_system_status(self, system_name: str) -> str:
        """Simula verificação de status de sistema"""
        # Simular alguns sistemas
        systems = {
            "email": "operacional",
            "website": "operacional", 
            "database": "manutenção programada",
            "api": "operacional",
            "vpn": "instável"
        }
        
        status = systems.get(system_name.lower(), "desconhecido")
        return f"Sistema {system_name}: {status}"
    
    @kernel_function(
        name="restart_service",
        description="Simula o restart de um serviço"
    )
    def restart_service(self, service_name: str) -> str:
        """Simula restart de serviço"""
        return f"Serviço {service_name} foi reiniciado com sucesso"


class FinanceFunctions:
    """
    Plugin com funções para área financeira
    """
    
    @kernel_function(
        name="calculate_interest",
        description="Calcula juros compostos"
    )
    def calculate_interest(self, principal: float, rate: float, time: float) -> str:
        """Calcula juros compostos"""
        try:
            # Fórmula: A = P(1 + r)^t
            amount = principal * ((1 + rate/100) ** time)
            interest = amount - principal
            return f"Capital inicial: R$ {principal:.2f}, Montante final: R$ {amount:.2f}, Juros: R$ {interest:.2f}"
        except Exception as e:
            return f"Erro no cálculo: {str(e)}"
    
    @kernel_function(
        name="loan_simulation",
        description="Simula financiamento com prestações fixas"
    )
    def loan_simulation(self, amount: float, rate: float, months: int) -> str:
        """Simula financiamento"""
        try:
            # Fórmula da prestação fixa
            monthly_rate = rate / 100 / 12
            if monthly_rate == 0:
                installment = amount / months
            else:
                installment = amount * (monthly_rate * (1 + monthly_rate)**months) / ((1 + monthly_rate)**months - 1)
            
            total = installment * months
            interest = total - amount
            
            return f"Valor financiado: R$ {amount:.2f}, Prestação: R$ {installment:.2f}, Total a pagar: R$ {total:.2f}, Juros totais: R$ {interest:.2f}"
        except Exception as e:
            return f"Erro na simulação: {str(e)}"


def setup_default_functions(kernel: Kernel) -> FunctionRegistry:
    """
    Configura as funções padrão do sistema e retorna o registry
    """
    registry = FunctionRegistry()
    
    # Registrar plugins padrão
    registry.register_plugin("UtilityFunctions", UtilityFunctions())
    registry.register_plugin("CustomerServiceFunctions", CustomerServiceFunctions())
    registry.register_plugin("TechSupportFunctions", TechSupportFunctions())
    registry.register_plugin("FinanceFunctions", FinanceFunctions())
    
    # Adicionar plugins ao kernel
    for plugin_name, plugin_instance in registry.plugins.items():
        kernel.add_plugin(plugin_instance, plugin_name=plugin_name)
    
    logger.info(f"Configurados {len(registry.plugins)} plugins com {len(registry.list_functions())} funções")
    
    return registry