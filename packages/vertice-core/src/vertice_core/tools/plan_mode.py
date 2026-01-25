from .base import Tool, ToolResult, ToolCategory


class EnterNoesisModeTool(Tool):
    """Entra no Modo Noesis para consciência estratégica."""

    def __init__(self):
        super().__init__()
        self.name = "enter_noesis_mode"
        self.category = ToolCategory.CONTEXT
        self.description = "Ativa Modo Noesis para qualidade absoluta em momentos estratégicos"

    async def execute(self, **kwargs) -> ToolResult:
        """Ativa Modo Noesis."""
        try:
            # Placeholder para integração futura
            return ToolResult(
                success=True,
                data="🧠 Modo Noesis ativado (placeholder)\n⚖️ Tribunal Ético: VERITAS | SOPHIA | DIKÉ\n🎯 Qualidade Absoluta: Engajada",
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Erro: {e}")


class ExitNoesisModeTool(Tool):
    """Sai do Modo Noesis."""

    def __init__(self):
        super().__init__()
        self.name = "exit_noesis_mode"
        self.category = ToolCategory.CONTEXT
        self.description = "Desativa Modo Noesis"

    async def execute(self, **kwargs) -> ToolResult:
        """Desativa Modo Noesis."""
        try:
            return ToolResult(
                success=True, data="✅ Modo Noesis desativado\n🔄 Retornando ao modo normal"
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Erro: {e}")


class GetNoesisStatusTool(Tool):
    """Obtém status do Modo Noesis."""

    def __init__(self):
        super().__init__()
        self.name = "get_noesis_status"
        self.category = ToolCategory.CONTEXT
        self.description = "Verifica status atual do Modo Noesis"

    async def execute(self, **kwargs) -> ToolResult:
        """Retorna status do Modo Noesis."""
        try:
            return ToolResult(
                success=True,
                data="🔄 Modo Noesis: IMPLEMENTAÇÃO BASE\n💡 Status: Placeholder ativo\n⚖️ Tribunal: Pronto para integração",
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Erro: {e}")


class EnterPlanModeTool(Tool):
    """Entra no Modo Planejamento para execução estruturada."""

    def __init__(self):
        super().__init__()
        self.name = "enter_plan_mode"
        self.category = ToolCategory.CONTEXT
        self.description = "Ativa Modo Planejamento para execução estruturada e controlada"

    async def execute(self, **kwargs) -> ToolResult:
        """Ativa Modo Planejamento."""
        try:
            _plan_state["active"] = True
            _plan_state["start_time"] = None  # Could set actual time
            return ToolResult(
                success=True,
                data="📋 Modo Planejamento ativado\n🎯 Execução Estruturada: Engajada\n📊 Controle de Progresso: Ativo\n⚡ Otimização Tática: Habilitada",
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Erro: {e}")


class ExitPlanModeTool(Tool):
    """Sai do Modo Planejamento."""

    def __init__(self):
        super().__init__()
        self.name = "exit_plan_mode"
        self.category = ToolCategory.CONTEXT
        self.description = "Desativa Modo Planejamento"

    async def execute(self, **kwargs) -> ToolResult:
        """Desativa Modo Planejamento."""
        try:
            if not _plan_state.get("active", False):
                return ToolResult(success=False, error="Not currently in plan mode")

            _plan_state["active"] = False
            return ToolResult(
                success=True, data="✅ Modo Planejamento desativado\n🔄 Retornando ao modo normal"
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Erro: {e}")


class AddPlanNoteTool(Tool):
    """Adiciona uma nota ao plano atual."""

    def __init__(self):
        super().__init__()
        self.name = "add_plan_note"
        self.category = ToolCategory.CONTEXT
        self.description = "Adiciona uma observação ao plano de execução atual"

    async def execute(self, note: str, **kwargs) -> ToolResult:
        """Adiciona nota ao plano."""
        try:
            return ToolResult(
                success=True,
                data=f"📝 Nota adicionada ao plano\n💭 '{note}'\n📋 Registro: Salvo no contexto de execução",
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Erro: {e}")


class GetPlanStatusTool(Tool):
    """Obtém status atual do plano de execução."""

    def __init__(self):
        super().__init__()
        self.name = "get_plan_status"
        self.category = ToolCategory.CONTEXT
        self.description = "Verifica status atual do plano de execução"

    async def execute(self, **kwargs) -> ToolResult:
        """Retorna status do plano."""
        try:
            return ToolResult(
                success=True,
                data="📊 Status do Plano: IMPLEMENTAÇÃO BASE\n📈 Progresso: Placeholder ativo\n🎯 Objetivos: Sistema de planejamento pronto\n⚡ Execução: Aguardando tarefas",
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Erro: {e}")


def get_noesis_mode_tools():
    """Retorna lista de ferramentas do noesis mode."""
    return [
        EnterNoesisModeTool(),
        ExitNoesisModeTool(),
        GetNoesisStatusTool(),
    ]


def get_plan_mode_tools():
    """Retorna lista de ferramentas do planning mode."""
    return [
        EnterPlanModeTool(),
        ExitPlanModeTool(),
        AddPlanNoteTool(),
        GetPlanStatusTool(),
    ]


# Global state for plan mode
_plan_state = {
    "active": False,
    "notes": [],
    "start_time": None,
}


def get_plan_state():
    """Get current plan state."""
    return _plan_state.copy()


def reset_plan_state():
    """Reset plan state to initial values."""
    global _plan_state
    _plan_state = {
        "active": False,
        "notes": [],
        "start_time": None,
    }
