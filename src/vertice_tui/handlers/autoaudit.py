"""
AutoAudit Handler - Handler de Comandos /autoaudit.

Comandos:
- /autoaudit           - Executa auditoria completa
- /autoaudit quick     - Apenas cenários rápidos
- /autoaudit list      - Lista cenários
- /autoaudit category  - Por categoria
- /autoaudit status    - Status da última auditoria
- /autoaudit scenario  - Executa cenário específico
- /autoaudit export    - Exporta último relatório (html/json)
- /autoaudit custom    - Carrega cenários de YAML
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from vertice_tui.app import VerticeApp
    from vertice_tui.widgets.response_view import ResponseView
    from vertice_tui.core.autoaudit import AutoAuditService, AuditReport


class AutoAuditHandler:
    """Handler para comandos /autoaudit."""

    def __init__(self, app: "VerticeApp") -> None:
        self.app = app
        self._service: "AutoAuditService | None" = None
        self._last_report: "AuditReport | None" = None

    async def handle(self, command: str, args: str, view: "ResponseView") -> None:
        """Roteamento de subcomandos."""
        parts = args.split(maxsplit=1)
        subcommand = parts[0].lower() if parts else "run"
        sub_args = parts[1] if len(parts) > 1 else ""

        handlers = {
            "run": self._run,
            "quick": self._quick,
            "list": self._list,
            "status": self._status,
            "category": self._category,
            "scenario": self._single,
            "export": self._export,
            "custom": self._custom,
            "help": self._help,
        }

        handler = handlers.get(subcommand, self._run)
        await handler(sub_args, view)

    async def _run(self, args: str, view: "ResponseView") -> None:
        """Executa auditoria completa."""
        from vertice_tui.core.autoaudit import AutoAuditService

        self._service = AutoAuditService(self.app, view)
        self._last_report = await self._service.run()

    async def _quick(self, args: str, view: "ResponseView") -> None:
        """Apenas cenários rápidos (<5s)."""
        from vertice_tui.core.autoaudit import AutoAuditService, SCENARIOS, Expectation

        quick = [s for s in SCENARIOS if Expectation.LATENCY_UNDER_5S in s.expectations]

        self._service = AutoAuditService(self.app, view, quick)
        self._last_report = await self._service.run()

    async def _list(self, args: str, view: "ResponseView") -> None:
        """Lista cenários."""
        from vertice_tui.core.autoaudit import SCENARIOS, ScenarioCategory

        lines = ["## 📋 Cenários de Auditoria\n"]

        for category in ScenarioCategory:
            cat_scenarios = [s for s in SCENARIOS if s.category == category]
            if cat_scenarios:
                lines.append(f"\n### {category.value.upper()}")
                for s in cat_scenarios:
                    lines.append(f"- `{s.id}`: {s.description}")

        lines.append(f"\n**Total:** {len(SCENARIOS)} cenários")
        view.add_system_message("\n".join(lines))

    async def _status(self, args: str, view: "ResponseView") -> None:
        """Status da última auditoria."""
        if self._last_report is None:
            view.add_system_message("Nenhuma auditoria executada.")
            return

        r = self._last_report
        view.add_system_message(
            f"## 📊 Última Auditoria\n\n"
            f"- **Score:** {r.success_rate:.1f}%\n"
            f"- ✅ Passou: {r.passed}\n"
            f"- ❌ Falhou: {r.failed}\n"
            f"- 💥 Crítico: {r.critical_errors}"
        )

    async def _category(self, args: str, view: "ResponseView") -> None:
        """Por categoria."""
        from vertice_tui.core.autoaudit import AutoAuditService, ScenarioCategory

        if not args:
            cats = ", ".join(c.value for c in ScenarioCategory)
            view.add_error(f"Uso: /autoaudit category <nome>\nCategorias: {cats}")
            return

        try:
            category = ScenarioCategory(args.lower())
        except ValueError:
            view.add_error(f"Categoria inválida: {args}")
            return

        self._service = AutoAuditService(self.app, view)
        self._last_report = await self._service.run(categories=[category])

    async def _single(self, args: str, view: "ResponseView") -> None:
        """Cenário específico."""
        from vertice_tui.core.autoaudit import AutoAuditService, get_scenario_by_id

        if not args:
            view.add_error("Uso: /autoaudit scenario <id>")
            return

        scenario = get_scenario_by_id(args)
        if not scenario:
            view.add_error(f"Cenário não encontrado: {args}")
            return

        self._service = AutoAuditService(self.app, view, [scenario])
        self._last_report = await self._service.run()

    async def _export(self, args: str, view: "ResponseView") -> None:
        """Exporta relatório (html/json)."""
        if self._last_report is None:
            view.add_error("Execute `/autoaudit run` primeiro.")
            return

        from vertice_tui.core.autoaudit.export import export_html, export_json

        fmt = args.lower() if args else "html"

        if fmt == "html":
            path = export_html(self._last_report)
            view.add_system_message(f"✅ Exportado: `{path}`")
        elif fmt == "json":
            path = export_json(self._last_report)
            view.add_system_message(f"✅ Exportado: `{path}`")
        else:
            view.add_error("Uso: /autoaudit export [html|json]")

    async def _custom(self, args: str, view: "ResponseView") -> None:
        """Carrega cenários de YAML."""
        from vertice_tui.core.autoaudit import AutoAuditService, load_custom_scenarios

        yaml_path = Path(args) if args else Path.home() / ".vertice" / "custom_scenarios.yaml"

        if not yaml_path.exists():
            view.add_error(f"Arquivo não encontrado: {yaml_path}")
            return

        custom = load_custom_scenarios(yaml_path)
        if not custom:
            view.add_error(f"Nenhum cenário válido em: {yaml_path}")
            return

        view.add_system_message(f"📂 Carregados {len(custom)} cenários de `{yaml_path}`")

        self._service = AutoAuditService(self.app, view, custom)
        self._last_report = await self._service.run()

    async def _help(self, args: str, view: "ResponseView") -> None:
        """Ajuda."""
        view.add_system_message(
            "## 🔍 AutoAudit - Comandos\n\n"
            "| Comando | Descrição |\n"
            "|---------|----------|\n"
            "| `/autoaudit` | Executa todos os cenários |\n"
            "| `/autoaudit quick` | Apenas cenários rápidos |\n"
            "| `/autoaudit list` | Lista cenários |\n"
            "| `/autoaudit category <cat>` | Por categoria |\n"
            "| `/autoaudit scenario <id>` | Cenário específico |\n"
            "| `/autoaudit export [html\\|json]` | Exporta relatório |\n"
            "| `/autoaudit custom [path]` | Cenários YAML |\n"
            "| `/autoaudit status` | Última auditoria |"
        )
