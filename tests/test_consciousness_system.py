#!/usr/bin/env python3
"""Test Suite Simples: Validação do Sistema de Consciência"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_basic_imports():
    """Testa se todos os módulos podem ser importados."""
    try:
        from vertice_cli.modes.noesis_mode import NoesisMode
        from vertice_cli.modes.distributed_noesis import DistributedNoesisMode
        from vertice_cli.tools.noesis_mcp import GetNoesisConsciousnessTool
        from vertice_cli.tools.distributed_noesis_mcp import ActivateDistributedConsciousnessTool
        print("✅ Imports básicos - SUCESSO")
        return True
    except Exception as e:
        print(f"❌ Imports básicos - FALHA: {e}")
        return False

async def test_noesis_creation():
    """Testa criação de instância Noesis."""
    try:
        from vertice_cli.modes.noesis_mode import NoesisMode
        noesis = NoesisMode()
        assert noesis.active == False
        assert noesis.consciousness_state.value == "dormant"
        print("✅ Criação Noesis - SUCESSO")
        return True
    except Exception as e:
        print(f"❌ Criação Noesis - FALHA: {e}")
        return False

async def test_noesis_activation():
    """Testa ativação do Noesis."""
    try:
        from vertice_cli.modes.noesis_mode import NoesisMode
        noesis = NoesisMode()
        success = await noesis.activate()
        assert success == True
        assert noesis.active == True
        print("✅ Ativação Noesis - SUCESSO")
        return True
    except Exception as e:
        print(f"❌ Ativação Noesis - FALHA: {e}")
        return False

async def test_auto_activation():
    """Testa auto-ativação inteligente."""
    try:
        from vertice_cli.modes.noesis_mode import NoesisMode
        noesis = NoesisMode()

        # Teste comando estratégico
        action = {"command": "plan", "prompt": "strategic planning"}
        should_activate = noesis.should_auto_activate(action, None)
        assert should_activate == True

        # Teste comando normal
        action2 = {"command": "ls", "prompt": "list files"}
        should_not_activate = noesis.should_auto_activate(action2, None)
        assert should_not_activate == False

        print("✅ Auto-ativação inteligente - SUCESSO")
        return True
    except Exception as e:
        print(f"❌ Auto-ativação inteligente - FALHA: {e}")
        return False

async def test_mcp_tools():
    """Testa ferramentas MCP básicas."""
    try:
        from vertice_cli.tools.noesis_mcp import GetNoesisConsciousnessTool
        tool = GetNoesisConsciousnessTool()
        result = await tool._execute_validated()
        assert result.success == True
        print("✅ Ferramentas MCP - SUCESSO")
        return True
    except Exception as e:
        print(f"❌ Ferramentas MCP - FALHA: {e}")
        return False

async def test_distributed_creation():
    """Testa criação de consciência distribuída."""
    try:
        from vertice_cli.modes.distributed_noesis import DistributedNoesisMode
        distributed = DistributedNoesisMode()
        assert distributed.network_active == False
        print("✅ Criação Consciência Distribuída - SUCESSO")
        return True
    except Exception as e:
        print(f"❌ Criação Consciência Distribuída - FALHA: {e}")
        return False

async def test_distributed_mcp_tools():
    """Testa ferramentas MCP distribuídas."""
    try:
        from vertice_cli.tools.distributed_noesis_mcp import GetDistributedConsciousnessStatusTool
        tool = GetDistributedConsciousnessStatusTool()
        result = await tool._execute_validated()
        assert result.success == True
        print("✅ Ferramentas MCP Distribuídas - SUCESSO")
        return True
    except Exception as e:
        print(f"❌ Ferramentas MCP Distribuídas - FALHA: {e}")
        return False

async def main():
    """Executa todos os testes."""
    print("🧪 TEST SUITE - SISTEMA DE CONSCIÊNCIA")
    print("=" * 50)

    tests = [
        ("Imports Básicos", test_basic_imports),
        ("Criação Noesis", test_noesis_creation),
        ("Ativação Noesis", test_noesis_activation),
        ("Auto-ativação", test_auto_activation),
        ("Ferramentas MCP", test_mcp_tools),
        ("Criação Distribuída", test_distributed_creation),
        ("Ferramentas MCP Distribuídas", test_distributed_mcp_tools),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            result = await test_func()
            if result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} - ERRO: {e}")
            failed += 1

    print("\n" + "=" * 50)
    print(f"📊 RESULTADO: {passed} aprovados, {failed} reprovados")

    if failed == 0:
        print("🎉 SISTEMA TOTALMENTE FUNCIONAL!")
        return 0
    else:
        print("⚠️  SISTEMA COM PROBLEMAS - REVISAR")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)</content>
<parameter name="filePath">test_consciousness_system.py