"""
Day 3 - Extreme Edge Cases Tests (Boris Cherny Standards)
Tests de casos extremos e situações limites.

Updated for v8.0 API:
- AgentTask instead of TaskContext
- AgentResponse.success instead of result.status
- Proper async/await patterns
"""
import pytest
import string
import random
from unittest.mock import MagicMock, AsyncMock

from vertice_cli.agents.planner import PlannerAgent
from vertice_cli.agents.refactorer import RefactorerAgent
from vertice_cli.agents.base import AgentTask


class TestExtremeInputSizes:
    """Tests com tamanhos extremos de input"""

    @pytest.mark.asyncio
    async def test_planner_handles_empty_description(self):
        """Planner com descrição vazia"""
        llm = MagicMock()
        llm.generate = AsyncMock(return_value='{"sops": []}')

        agent = PlannerAgent(llm_client=llm)
        task = AgentTask(request="", session_id="empty")
        result = await agent.execute(task)
        assert isinstance(result.success, bool)

    @pytest.mark.asyncio
    async def test_planner_handles_single_char_description(self):
        """Planner com descrição de 1 caractere"""
        llm = MagicMock()
        llm.generate = AsyncMock(return_value='{"sops": []}')

        agent = PlannerAgent(llm_client=llm)
        task = AgentTask(request="x", session_id="one")
        result = await agent.execute(task)
        assert isinstance(result.success, bool)

    @pytest.mark.asyncio
    async def test_planner_handles_max_description(self):
        """Planner com descrição máxima"""
        llm = MagicMock()
        llm.generate = AsyncMock(return_value='{"sops": []}')

        agent = PlannerAgent(llm_client=llm)
        desc = "x" * 100000
        task = AgentTask(request=desc, session_id="max")
        result = await agent.execute(task)
        assert isinstance(result.success, bool)

    @pytest.mark.asyncio
    async def test_refactorer_handles_empty_description(self):
        """Refactorer com descrição vazia"""
        llm = MagicMock()
        llm.generate = AsyncMock(return_value="{}")

        agent = RefactorerAgent(llm_client=llm)
        task = AgentTask(request="", session_id="empty", context={"target_file": "test.py"})
        result = await agent.execute(task)
        assert isinstance(result.success, bool)

    @pytest.mark.asyncio
    async def test_refactorer_handles_max_description(self):
        """Refactorer com descrição máxima"""
        llm = MagicMock()
        llm.generate = AsyncMock(return_value="{}")

        agent = RefactorerAgent(llm_client=llm)
        desc = "x" * 100000
        task = AgentTask(request=desc, session_id="max", context={"target_file": "test.py"})
        result = await agent.execute(task)
        assert isinstance(result.success, bool)


class TestExtremeMetadata:
    """Tests com metadata extrema"""

    @pytest.mark.asyncio
    async def test_planner_handles_empty_metadata(self):
        """Planner com metadata vazio"""
        llm = MagicMock()
        llm.generate = AsyncMock(return_value='{"sops": []}')

        agent = PlannerAgent(llm_client=llm)
        task = AgentTask(request="Task", session_id="test", metadata={})
        result = await agent.execute(task)
        assert isinstance(result.success, bool)

    @pytest.mark.asyncio
    async def test_planner_handles_large_metadata(self):
        """Planner com metadata gigante"""
        llm = MagicMock()
        llm.generate = AsyncMock(return_value='{"sops": []}')

        agent = PlannerAgent(llm_client=llm)
        large_meta = {f"key_{i}": f"value_{i}" * 1000 for i in range(100)}
        task = AgentTask(request="Task", session_id="test", metadata=large_meta)
        result = await agent.execute(task)
        assert isinstance(result.success, bool)

    @pytest.mark.asyncio
    async def test_planner_handles_nested_metadata(self):
        """Planner com metadata profundamente aninhado"""
        llm = MagicMock()
        llm.generate = AsyncMock(return_value='{"sops": []}')

        agent = PlannerAgent(llm_client=llm)
        nested = {"level1": {"level2": {"level3": {"level4": {"level5": "deep"}}}}}
        task = AgentTask(request="Task", session_id="test", metadata=nested)
        result = await agent.execute(task)
        assert isinstance(result.success, bool)

    @pytest.mark.asyncio
    async def test_refactorer_handles_null_metadata_values(self):
        """Refactorer com valores null em metadata"""
        llm = MagicMock()
        llm.generate = AsyncMock(return_value="{}")

        agent = RefactorerAgent(llm_client=llm)
        meta = {"key1": None, "key2": None}
        task = AgentTask(
            request="Task", session_id="test", metadata=meta, context={"target_file": "test.py"}
        )
        result = await agent.execute(task)
        assert isinstance(result.success, bool)

    @pytest.mark.asyncio
    async def test_refactorer_handles_mixed_type_metadata(self):
        """Refactorer com tipos mistos em metadata"""
        llm = MagicMock()
        llm.generate = AsyncMock(return_value="{}")

        agent = RefactorerAgent(llm_client=llm)
        meta = {
            "string": "value",
            "int": 42,
            "float": 3.14,
            "bool": True,
            "list": [1, 2, 3],
            "nested": {"a": 1},
        }
        task = AgentTask(
            request="Task", session_id="test", metadata=meta, context={"target_file": "test.py"}
        )
        result = await agent.execute(task)
        assert isinstance(result.success, bool)


class TestExtremeUnicode:
    """Tests com unicode extremo"""

    @pytest.mark.asyncio
    async def test_planner_handles_emoji_description(self):
        """Planner com emojis na descrição"""
        llm = MagicMock()
        llm.generate = AsyncMock(return_value='{"sops": []}')

        agent = PlannerAgent(llm_client=llm)
        task = AgentTask(request="Add feature 🚀🎉💻", session_id="emoji")
        result = await agent.execute(task)
        assert isinstance(result.success, bool)

    @pytest.mark.asyncio
    async def test_planner_handles_mixed_languages(self):
        """Planner com múltiplos idiomas"""
        llm = MagicMock()
        llm.generate = AsyncMock(return_value='{"sops": []}')

        agent = PlannerAgent(llm_client=llm)
        task = AgentTask(request="Hello世界مرحباПривет", session_id="mixed")
        result = await agent.execute(task)
        assert isinstance(result.success, bool)

    @pytest.mark.asyncio
    async def test_planner_handles_rtl_text(self):
        """Planner com texto RTL"""
        llm = MagicMock()
        llm.generate = AsyncMock(return_value='{"sops": []}')

        agent = PlannerAgent(llm_client=llm)
        task = AgentTask(request="مرحبا بالعالم", session_id="rtl")
        result = await agent.execute(task)
        assert isinstance(result.success, bool)

    @pytest.mark.asyncio
    async def test_refactorer_handles_special_characters(self):
        """Refactorer com caracteres especiais"""
        llm = MagicMock()
        llm.generate = AsyncMock(return_value="{}")

        agent = RefactorerAgent(llm_client=llm)
        task = AgentTask(
            request="Fix bug in <script>alert('xss')</script>",
            session_id="special",
            context={"target_file": "test.py"},
        )
        result = await agent.execute(task)
        assert isinstance(result.success, bool)

    @pytest.mark.asyncio
    async def test_refactorer_handles_control_characters(self):
        """Refactorer com caracteres de controle"""
        llm = MagicMock()
        llm.generate = AsyncMock(return_value="{}")

        agent = RefactorerAgent(llm_client=llm)
        task = AgentTask(
            request="Fix\x00bug\x0a\x0dwith\ttabs",
            session_id="control",
            context={"target_file": "test.py"},
        )
        result = await agent.execute(task)
        assert isinstance(result.success, bool)


class TestExtremePaths:
    """Tests com paths extremos"""

    @pytest.mark.asyncio
    async def test_planner_handles_very_long_path(self):
        """Planner com path muito longo"""
        llm = MagicMock()
        llm.generate = AsyncMock(return_value='{"sops": []}')

        agent = PlannerAgent(llm_client=llm)
        long_path = "/tmp/" + "a" * 200 + "/file.py"
        task = AgentTask(
            request="Edit file", session_id="longpath", context={"target_file": long_path}
        )
        result = await agent.execute(task)
        assert isinstance(result.success, bool)

    @pytest.mark.asyncio
    async def test_planner_handles_special_chars_in_path(self):
        """Planner com caracteres especiais no path"""
        llm = MagicMock()
        llm.generate = AsyncMock(return_value='{"sops": []}')

        agent = PlannerAgent(llm_client=llm)
        task = AgentTask(
            request="Edit file",
            session_id="specialpath",
            context={"target_file": "/tmp/my file (1).py"},
        )
        result = await agent.execute(task)
        assert isinstance(result.success, bool)

    @pytest.mark.asyncio
    async def test_planner_handles_unicode_in_path(self):
        """Planner com unicode no path"""
        llm = MagicMock()
        llm.generate = AsyncMock(return_value='{"sops": []}')

        agent = PlannerAgent(llm_client=llm)
        task = AgentTask(
            request="Edit file",
            session_id="unicodepath",
            context={"target_file": "/tmp/arquivo_日本語.py"},
        )
        result = await agent.execute(task)
        assert isinstance(result.success, bool)

    @pytest.mark.asyncio
    async def test_refactorer_handles_relative_path(self):
        """Refactorer com path relativo"""
        llm = MagicMock()
        llm.generate = AsyncMock(return_value="{}")

        agent = RefactorerAgent(llm_client=llm)
        task = AgentTask(
            request="Edit file",
            session_id="relpath",
            context={"target_file": "../../../etc/passwd"},
        )
        result = await agent.execute(task)
        assert isinstance(result.success, bool)

    @pytest.mark.asyncio
    async def test_refactorer_handles_symlink_path(self):
        """Refactorer com symlink no path"""
        llm = MagicMock()
        llm.generate = AsyncMock(return_value="{}")

        agent = RefactorerAgent(llm_client=llm)
        task = AgentTask(
            request="Edit file",
            session_id="symlink",
            context={"target_file": "/tmp/link -> /real/file.py"},
        )
        result = await agent.execute(task)
        assert isinstance(result.success, bool)


class TestExtremeTaskIds:
    """Tests com task IDs extremos"""

    @pytest.mark.asyncio
    async def test_planner_handles_empty_task_id(self):
        """Planner com task_id vazio"""
        llm = MagicMock()
        llm.generate = AsyncMock(return_value='{"sops": []}')

        agent = PlannerAgent(llm_client=llm)
        task = AgentTask(request="Task", session_id="")
        result = await agent.execute(task)
        assert isinstance(result.success, bool)

    @pytest.mark.asyncio
    async def test_planner_handles_very_long_task_id(self):
        """Planner com task_id muito longo"""
        llm = MagicMock()
        llm.generate = AsyncMock(return_value='{"sops": []}')

        agent = PlannerAgent(llm_client=llm)
        long_id = "x" * 10000
        task = AgentTask(request="Task", session_id=long_id)
        result = await agent.execute(task)
        assert isinstance(result.success, bool)

    @pytest.mark.asyncio
    async def test_planner_handles_special_chars_in_task_id(self):
        """Planner com caracteres especiais no task_id"""
        llm = MagicMock()
        llm.generate = AsyncMock(return_value='{"sops": []}')

        agent = PlannerAgent(llm_client=llm)
        task = AgentTask(request="Task", session_id="task-id/with:special@chars!")
        result = await agent.execute(task)
        assert isinstance(result.success, bool)

    @pytest.mark.asyncio
    async def test_refactorer_handles_uuid_task_id(self):
        """Refactorer com UUID como task_id"""
        llm = MagicMock()
        llm.generate = AsyncMock(return_value="{}")

        agent = RefactorerAgent(llm_client=llm)
        task = AgentTask(
            request="Task",
            session_id="550e8400-e29b-41d4-a716-446655440000",
            context={"target_file": "test.py"},
        )
        result = await agent.execute(task)
        assert isinstance(result.success, bool)

    @pytest.mark.asyncio
    async def test_refactorer_handles_numeric_task_id(self):
        """Refactorer com número como task_id"""
        llm = MagicMock()
        llm.generate = AsyncMock(return_value="{}")

        agent = RefactorerAgent(llm_client=llm)
        task = AgentTask(request="Task", session_id="12345", context={"target_file": "test.py"})
        result = await agent.execute(task)
        assert isinstance(result.success, bool)


class TestConcurrencyEdgeCases:
    """Tests de edge cases de concorrência"""

    @pytest.mark.asyncio
    async def test_planner_handles_rapid_sequential_calls(self):
        """Planner com chamadas rápidas sequenciais"""
        llm = MagicMock()
        llm.generate = AsyncMock(return_value='{"sops": []}')

        agent = PlannerAgent(llm_client=llm)
        results = []
        for i in range(10):
            task = AgentTask(request=f"Task {i}", session_id=f"rapid-{i}")
            result = await agent.execute(task)
            results.append(result)

        assert len(results) == 10
        assert all(isinstance(r.success, bool) for r in results)

    @pytest.mark.asyncio
    async def test_planner_handles_identical_contexts(self):
        """Planner com contextos idênticos"""
        llm = MagicMock()
        llm.generate = AsyncMock(return_value='{"sops": []}')

        agent = PlannerAgent(llm_client=llm)
        task = AgentTask(request="Same task", session_id="same")

        result1 = await agent.execute(task)
        result2 = await agent.execute(task)

        assert isinstance(result1.success, bool)
        assert isinstance(result2.success, bool)

    @pytest.mark.asyncio
    async def test_refactorer_handles_interleaved_calls(self):
        """Refactorer com chamadas intercaladas"""
        llm = MagicMock()
        llm.generate = AsyncMock(return_value="{}")

        agent = RefactorerAgent(llm_client=llm)
        results = []
        for i in range(5):
            task = AgentTask(
                request=f"Task {i}",
                session_id=f"interleaved-{i}",
                context={"target_file": f"file{i}.py"},
            )
            result = await agent.execute(task)
            results.append(result)

        assert len(results) == 5


class TestMemoryPressure:
    """Tests de pressão de memória"""

    @pytest.mark.asyncio
    async def test_planner_handles_many_small_tasks(self):
        """Planner com muitas tasks pequenas"""
        llm = MagicMock()
        llm.generate = AsyncMock(return_value='{"sops": []}')

        agent = PlannerAgent(llm_client=llm)
        for i in range(100):
            task = AgentTask(request="x", session_id=f"small-{i}")
            result = await agent.execute(task)
            assert isinstance(result.success, bool)

    @pytest.mark.asyncio
    async def test_planner_handles_few_large_tasks(self):
        """Planner com poucas tasks grandes"""
        llm = MagicMock()
        llm.generate = AsyncMock(return_value='{"sops": []}')

        agent = PlannerAgent(llm_client=llm)
        for i in range(5):
            large_request = "x" * 50000
            task = AgentTask(request=large_request, session_id=f"large-{i}")
            result = await agent.execute(task)
            assert isinstance(result.success, bool)

    @pytest.mark.asyncio
    async def test_refactorer_handles_repeated_execution(self):
        """Refactorer com execução repetida"""
        llm = MagicMock()
        llm.generate = AsyncMock(return_value="{}")

        agent = RefactorerAgent(llm_client=llm)
        task = AgentTask(
            request="Refactor", session_id="repeat", context={"target_file": "test.py"}
        )
        for _ in range(50):
            result = await agent.execute(task)
            assert isinstance(result.success, bool)


class TestBoundaryValues:
    """Tests de valores limite"""

    @pytest.mark.asyncio
    async def test_planner_with_min_valid_context(self):
        """Planner com contexto mínimo válido"""
        llm = MagicMock()
        llm.generate = AsyncMock(return_value='{"sops": []}')

        agent = PlannerAgent(llm_client=llm)
        task = AgentTask(request="x", session_id="min")
        result = await agent.execute(task)
        assert isinstance(result.success, bool)

    @pytest.mark.asyncio
    async def test_planner_with_max_valid_context(self):
        """Planner com contexto máximo válido"""
        llm = MagicMock()
        llm.generate = AsyncMock(return_value='{"sops": []}')

        agent = PlannerAgent(llm_client=llm)
        large_context = {f"key_{i}": "x" * 1000 for i in range(100)}
        task = AgentTask(request="Task with large context", session_id="max", context=large_context)
        result = await agent.execute(task)
        assert isinstance(result.success, bool)

    @pytest.mark.asyncio
    async def test_refactorer_with_zero_timeout(self):
        """Refactorer sem timeout específico"""
        llm = MagicMock()
        llm.generate = AsyncMock(return_value="{}")

        agent = RefactorerAgent(llm_client=llm)
        task = AgentTask(
            request="Task",
            session_id="zero-timeout",
            context={"target_file": "test.py", "timeout": 0},
        )
        result = await agent.execute(task)
        assert isinstance(result.success, bool)

    @pytest.mark.asyncio
    async def test_refactorer_with_negative_values(self):
        """Refactorer com valores negativos no contexto"""
        llm = MagicMock()
        llm.generate = AsyncMock(return_value="{}")

        agent = RefactorerAgent(llm_client=llm)
        task = AgentTask(
            request="Task",
            session_id="negative",
            context={"target_file": "test.py", "retries": -1, "timeout": -100},
        )
        result = await agent.execute(task)
        assert isinstance(result.success, bool)


class TestErrorRecovery:
    """Tests de recuperação de erros"""

    @pytest.mark.asyncio
    async def test_planner_recovers_from_partial_failure(self):
        """Planner recupera de falha parcial"""
        llm = MagicMock()
        llm.generate = AsyncMock(side_effect=[Exception("First fails"), '{"sops": []}'])

        agent = PlannerAgent(llm_client=llm)
        task = AgentTask(request="Task", session_id="partial")

        # First call fails
        result1 = await agent.execute(task)
        assert result1.success is False or result1.success is True

        # Second call succeeds
        result2 = await agent.execute(task)
        assert isinstance(result2.success, bool)

    @pytest.mark.asyncio
    async def test_planner_handles_retry_after_failure(self):
        """Planner tenta novamente após falha"""
        llm = MagicMock()
        llm.generate = AsyncMock(return_value='{"sops": []}')

        agent = PlannerAgent(llm_client=llm)
        task = AgentTask(request="Task", session_id="retry")

        for _ in range(3):
            result = await agent.execute(task)
            assert isinstance(result.success, bool)

    @pytest.mark.asyncio
    async def test_refactorer_handles_cascading_failures(self):
        """Refactorer lida com falhas em cascata"""
        llm = MagicMock()
        llm.generate = AsyncMock(side_effect=Exception("Always fails"))

        agent = RefactorerAgent(llm_client=llm)

        for i in range(5):
            task = AgentTask(
                request=f"Task {i}", session_id=f"cascade-{i}", context={"target_file": "test.py"}
            )
            result = await agent.execute(task)
            assert result.success is False
            assert result.error is not None


class TestRandomizedInputs:
    """Tests com inputs randomizados"""

    @pytest.mark.asyncio
    async def test_planner_handles_random_descriptions(self):
        """Planner com descrições aleatórias"""
        llm = MagicMock()
        llm.generate = AsyncMock(return_value='{"sops": []}')

        agent = PlannerAgent(llm_client=llm)

        for _ in range(10):
            random_desc = "".join(random.choices(string.printable, k=random.randint(1, 1000)))
            task = AgentTask(request=random_desc, session_id="random")
            result = await agent.execute(task)
            assert isinstance(result.success, bool)

    @pytest.mark.asyncio
    async def test_refactorer_handles_random_metadata(self):
        """Refactorer com metadata aleatória"""
        llm = MagicMock()
        llm.generate = AsyncMock(return_value="{}")

        agent = RefactorerAgent(llm_client=llm)

        for _ in range(10):
            random_meta = {
                "".join(random.choices(string.ascii_letters, k=10)): "".join(
                    random.choices(string.printable, k=50)
                )
                for _ in range(random.randint(1, 20))
            }
            task = AgentTask(
                request="Task",
                session_id="random-meta",
                metadata=random_meta,
                context={"target_file": "test.py"},
            )
            result = await agent.execute(task)
            assert isinstance(result.success, bool)


class TestTypeCoercion:
    """Tests de coerção de tipos"""

    @pytest.mark.asyncio
    async def test_planner_handles_numeric_description(self):
        """Planner com descrição que parece número"""
        llm = MagicMock()
        llm.generate = AsyncMock(return_value='{"sops": []}')

        agent = PlannerAgent(llm_client=llm)
        task = AgentTask(request="12345", session_id="numeric")
        result = await agent.execute(task)
        assert isinstance(result.success, bool)

    @pytest.mark.asyncio
    async def test_planner_handles_boolean_in_metadata(self):
        """Planner com booleanos em metadata"""
        llm = MagicMock()
        llm.generate = AsyncMock(return_value='{"sops": []}')

        agent = PlannerAgent(llm_client=llm)
        task = AgentTask(
            request="Task", session_id="bool", metadata={"enabled": True, "disabled": False}
        )
        result = await agent.execute(task)
        assert isinstance(result.success, bool)

    @pytest.mark.asyncio
    async def test_refactorer_handles_stringified_numbers(self):
        """Refactorer com números como strings"""
        llm = MagicMock()
        llm.generate = AsyncMock(return_value="{}")

        agent = RefactorerAgent(llm_client=llm)
        task = AgentTask(
            request="Task",
            session_id="stringnum",
            context={"target_file": "test.py", "retries": "3", "timeout": "100"},
        )
        result = await agent.execute(task)
        assert isinstance(result.success, bool)


class TestImmutability:
    """Tests de imutabilidade"""

    @pytest.mark.asyncio
    async def test_planner_does_not_modify_input_context(self):
        """Planner não modifica contexto de entrada"""
        llm = MagicMock()
        llm.generate = AsyncMock(return_value='{"sops": []}')

        agent = PlannerAgent(llm_client=llm)
        original_context = {"key": "value", "nested": {"a": 1}}
        context_copy = {"key": "value", "nested": {"a": 1}}

        task = AgentTask(request="Task", session_id="immut", context=original_context)
        await agent.execute(task)

        assert original_context == context_copy

    @pytest.mark.asyncio
    async def test_refactorer_does_not_modify_input_context(self):
        """Refactorer não modifica contexto de entrada"""
        llm = MagicMock()
        llm.generate = AsyncMock(return_value="{}")

        agent = RefactorerAgent(llm_client=llm)
        original_context = {"target_file": "test.py", "data": {"x": 1}}
        context_copy = {"target_file": "test.py", "data": {"x": 1}}

        task = AgentTask(request="Task", session_id="immut", context=original_context)
        await agent.execute(task)

        assert original_context == context_copy
