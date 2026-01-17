"""
AutoAudit Export - Exportação de Relatórios.

Suporta:
- JSON (via BlackBoxLogger)
- HTML (template leve)
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from .service import AuditReport


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AutoAudit Report - {timestamp}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #0a0a0a; color: #e0e0e0; padding: 2rem;
        }}
        .container {{ max-width: 800px; margin: 0 auto; }}
        h1 {{ color: #00d9ff; margin-bottom: 1rem; }}
        .summary {{
            display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem;
            margin-bottom: 2rem;
        }}
        .card {{
            background: #1a1a1a; border-radius: 8px; padding: 1rem;
            text-align: center; border: 1px solid #333;
        }}
        .card.success {{ border-color: #22c55e; }}
        .card.fail {{ border-color: #ef4444; }}
        .card .value {{ font-size: 2rem; font-weight: bold; }}
        .card.success .value {{ color: #22c55e; }}
        .card.fail .value {{ color: #ef4444; }}
        .score {{
            font-size: 3rem; color: {score_color}; text-align: center;
            padding: 2rem; background: #1a1a1a; border-radius: 8px;
            margin-bottom: 2rem;
        }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 1rem; }}
        th, td {{ padding: 0.75rem; text-align: left; border-bottom: 1px solid #333; }}
        th {{ color: #00d9ff; }}
        .status-ok {{ color: #22c55e; }}
        .status-fail {{ color: #ef4444; }}
        .timestamp {{ color: #666; font-size: 0.875rem; margin-top: 2rem; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔬 AutoAudit Report</h1>

        <div class="score">{score:.1f}%</div>

        <div class="summary">
            <div class="card success">
                <div class="value">{passed}</div>
                <div>Passou</div>
            </div>
            <div class="card fail">
                <div class="value">{failed}</div>
                <div>Falhou</div>
            </div>
            <div class="card">
                <div class="value">{skipped}</div>
                <div>Pulado</div>
            </div>
            <div class="card fail">
                <div class="value">{critical}</div>
                <div>Crítico</div>
            </div>
        </div>

        <h2>Resultados</h2>
        <table>
            <thead>
                <tr>
                    <th>Cenário</th>
                    <th>Status</th>
                    <th>Latência</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>

        <p class="timestamp">
            Gerado em {timestamp}<br>
            Início: {started_at} | Fim: {ended_at}
        </p>
    </div>
</body>
</html>"""


def export_html(report: AuditReport, output_path: Optional[Path] = None) -> str:
    """
    Exporta relatório para HTML.

    Returns:
        Caminho do arquivo gerado
    """
    rows = []
    for r in report.results:
        status_class = "status-ok" if r.status == "SUCCESS" else "status-fail"
        status_icon = "✅" if r.status == "SUCCESS" else "❌"
        rows.append(
            f"<tr><td>{r.scenario_id}</td>"
            f'<td class="{status_class}">{status_icon} {r.status}</td>'
            f"<td>{r.latency_ms:.0f}ms</td></tr>"
        )

    score_color = "#22c55e" if report.success_rate >= 80 else "#ef4444"

    html = HTML_TEMPLATE.format(
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        score=report.success_rate,
        score_color=score_color,
        passed=report.passed,
        failed=report.failed,
        skipped=report.skipped,
        critical=report.critical_errors,
        rows="\n".join(rows),
        started_at=report.started_at,
        ended_at=report.ended_at,
    )

    if output_path is None:
        output_path = Path(
            "logs/autoaudit"
        ) / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")

    return str(output_path)


def export_json(report: AuditReport, output_path: Optional[Path] = None) -> str:
    """
    Exporta relatório para JSON.

    Returns:
        Caminho do arquivo gerado
    """
    import json

    if output_path is None:
        output_path = Path(
            "logs/autoaudit"
        ) / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)

    return str(output_path)


__all__ = ["export_html", "export_json"]
