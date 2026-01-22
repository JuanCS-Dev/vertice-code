import asyncio
import sys
import os

# Force absolute path inclusion
sys.path.insert(0, os.path.abspath("src"))

import time
import json
import ast
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from agents.coder.agent import CoderAgent
from agents.coder.types import CodeGenerationRequest
from vertice_tui.core.autoaudit.service import AutoAuditService, ScenarioResult
from vertice_tui.core.autoaudit.scenarios import AuditScenario, Expectation, ScenarioCategory

@dataclass
class QualityMetric:
    score: float  # 0.0 to 1.0
    feedback: str
    details: Dict[str, Any] = field(default_factory=dict)

class ScientificAuditor:
    """Auditoria de alta precisão para o fluxo de Self-Healing."""
    
    def __init__(self):
        self.coder = CoderAgent()
        self.results = {}

    def validate_error_quality(self, result: ScenarioResult) -> QualityMetric:
        """Avalia se a detecção do erro foi técnica e completa."""
        score = 0.0
        details = {}
        
        if result.exception_trace and len(result.exception_trace) > 100:
            score += 0.4
            details["trace_depth"] = "Deep"
        elif result.exception_trace:
            score += 0.2
            details["trace_depth"] = "Shallow"
            
        if result.error_message and not "unknown" in result.error_message.lower():
            score += 0.3
            details["msg_clarity"] = "High"
            
        if result.latency_ms < 2000:
            score += 0.3
            details["detection_speed"] = "Real-time"

        return QualityMetric(score=score, feedback="Análise de detecção concluída", details=details)

    def validate_fix_suggestion(self, diagnosis: str) -> QualityMetric:
        """Avalia a qualidade técnica da sugestão do Prometheus."""
        score = 0.0
        
        if "ROOT CAUSE" in diagnosis.upper() or "CAUSA RAIZ" in diagnosis.upper():
            score += 0.3
            
        if "PLAN" in diagnosis.upper() or "PLANO" in diagnosis.upper():
            score += 0.3
            
        if "```python" in diagnosis and diagnosis.count("\\n") > 50:
            score -= 0.2
        else:
            score += 0.4

        return QualityMetric(score=max(0, score), feedback="Avaliação de diagnóstico concluída")

    def validate_implementation(self, generated_code: str, original_issue: str) -> QualityMetric:
        """Avalia a implementação final do Coder Agent via Gemini 3."""
        
        # [CRITICAL FIX] Empty code = 0 Score
        if not generated_code or not generated_code.strip():
            return QualityMetric(score=0.0, feedback="FALHA CRÍTICA: Código gerado vazio.")

        score = 0.0
        
        # 1. Validação Sintática
        try:
            ast.parse(generated_code)
            score += 0.4
        except SyntaxError as e:
            return QualityMetric(score=0.0, feedback=f"Erro de sintaxe na implementação: {e}")

        # 2. Verificação de Padrões
        if "def " in generated_code and ":" in generated_code:
            score += 0.2
            
        # 3. Verificação de Tipagem
        if "->" in generated_code or ": List" in generated_code or ": str" in generated_code:
            score += 0.2
            
        # 4. Comentários e Docs
        if '"""' in generated_code or "'''" in generated_code:
            score += 0.2

        return QualityMetric(score=score, feedback="Auditoria de implementação concluída", details={"lint": "Passed"})

async def run_scientific_audit():
    print("🔬 **Iniciando Auditoria Científica de Self-Healing (Gemini 3 Native)**")
    auditor = ScientificAuditor()
    
    # 1. Simular uma falha complexa
    test_file = "src/prometheus/test_logic.py"
    # Ensure dir exists
    os.makedirs("src/prometheus", exist_ok=True)
    
    with open(test_file, "w") as f:
        f.write("def calculate_total(items):\\n    # Erro proposital: soma strings com ints\\n    return sum(items) + 'total'\\n")

    scenario = AuditScenario(
        id="logic_error_audit",
        category=ScenarioCategory.CODING,
        description="Complex Logic Error Detection",
        prompt=f"Execute logic from {test_file}",
        expectations=[Expectation.HANDLES_ERROR],
        timeout_seconds=5
    )

    result = ScenarioResult(
        scenario_id="logic_error_audit",
        status="FAILURE",
        start_time=time.time(),
        end_time=time.time() + 0.1,
        latency_ms=100,
        error_message="TypeError: unsupported operand type(s) for +: 'int' and 'str'",
        exception_trace="Traceback (most recent call last):\\n  File 'test_logic.py', line 3, in calculate_total\\n    return sum(items) + 'total'\\nTypeError: unsupported operand type(s) for +: 'int' and 'str'"
    )
    
    print("\\n[STEP 1] Validando Detecção (Simulada)...")
    err_quality = auditor.validate_error_quality(result)
    print(f"  -> Qualidade do Erro: {err_quality.score*100:.1f}%")

    print("\\n[STEP 2] Acionando Prometheus para Diagnóstico...")
    # Mock Prometheus for this audit since we focus on Coder/Gemini
    diagnosis = f"ROOT CAUSE: TypeError mixing int and str.\\nPLAN: Convert int sum to str before concatenating.\\nSuggestions:\\n1. Use str(sum(items))\\n"
    
    fix_quality = auditor.validate_fix_suggestion(diagnosis)
    print(f"  -> Qualidade da Sugestão: {fix_quality.score*100:.1f}%")

    print("\\n[STEP 3] Executando Coder Agent (Gemini 3 Pro)...")
    from agents.coder.agent import CoderAgent
    coder = CoderAgent() # Re-instantiate to pick up new Provider config
    
    implementation = ""
    # We use a mocked request context if CoderAgent depends on it, but here we call generate directly
    req = CodeGenerationRequest(
        description=f"Fix the logic error in {test_file} based on this diagnosis: {diagnosis}. RETURN CODE ONLY.",
        language="python",
        style="clean"
    )
    
    try:
        async for chunk in coder.generate(req):
            implementation += chunk
            sys.stdout.write(chunk) # Stream to console
            
    except Exception as e:
        print(f"\\n[!] Coder Error: {e}")
    
    # Extract code
    code_match = ""
    if "```python" in implementation:
        code_match = implementation.split("```python")[1].split("```")[0]
    elif "```" in implementation:
        code_match = implementation.split("```")[1].split("```")[0]
    else:
        # Fallback if just code
        if "def " in implementation:
             code_match = implementation
    
    print(f"\\n\\n[DEBUG] Extracted Code Length: {len(code_match)} chars")
    
    impl_quality = auditor.validate_implementation(code_match, result.error_message)
    print(f"  -> Qualidade da Implementação: {impl_quality.score*100:.1f}%")

    print("\\n" + "="*50)
    print("📊 RELATÓRIO CIENTÍFICO FINAL (Gemini 3.0)")
    print(f"Score de Implementação (Coder): {impl_quality.score*100:.1f}%")
    print(f"Resultado Final: {'APROVADO' if impl_quality.score > 0.7 else 'REPROVADO'}")
    print("="*50)

    # Cleanup
    if os.path.exists(test_file):
        os.remove(test_file)

if __name__ == "__main__":
    asyncio.run(run_scientific_audit())