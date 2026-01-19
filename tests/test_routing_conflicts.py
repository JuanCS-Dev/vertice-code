"""
Constitutional Audit: Routing Conflicts Test
============================================

Testa edge cases e conflitos no routing do MAESTRO.
"""

from scripts.maestro.orchestrator import Orchestrator


class MockLLM:
    async def generate(self, *args, **kwargs):
        return "mock"


def test_routing():
    print("=" * 80)
    print("CONSTITUTIONAL AUDIT: ROUTING CONFLICTS")
    print("=" * 80)
    print()

    llm = MockLLM()
    orchestrator = Orchestrator(llm, None)

    # Test cases: (prompt, expected_agent, category)
    test_cases = [
        # Executor tests
        ("run ls -la", "executor", "bash_command"),
        ("show me current directory", "executor", "directory"),
        ("kill process 1234", "executor", "process"),
        # DevOps tests
        ("deploy to kubernetes", "devops", "deploy"),
        ("generate dockerfile", "devops", "docker"),
        ("create ci/cd pipeline", "devops", "pipeline"),
        ("check infrastructure health", "devops", "health"),
        # Database tests
        ("analyze database schema", "data", "schema"),
        ("optimize this sql query", "data", "query"),
        ("plan database migration", "data", "migration"),
        # Reviewer tests
        ("review this code", "reviewer", "review"),
        ("audit security", "reviewer", "audit"),
        # Planner tests
        ("plan this feature", "planner", "plan"),
        ("break down this task", "planner", "decompose"),
        # Refactorer tests
        ("refactor this function", "refactorer", "refactor"),
        ("rename variable", "refactorer", "rename"),
        # Explorer tests
        ("explore the codebase", "explorer", "explore"),
        ("show dependencies", "explorer", "dependencies"),
        # Architect tests
        ("design system architecture", "architect", "architecture"),
        ("create uml diagram", "architect", "diagram"),
        # Security tests
        ("check for vulnerabilities", "security", "vulnerability"),
        ("find security issues", "security", "security"),
        # Performance tests
        ("optimize performance", "performance", "performance"),
        ("find bottlenecks", "performance", "bottleneck"),
        # Testing tests
        ("generate unit tests", "testing", "test"),
        ("write pytest fixtures", "testing", "pytest"),
        # Documentation tests
        ("write documentation", "documentation", "document"),
        ("generate docstrings", "documentation", "docstring"),
        # Edge cases - Overlaps/Conflicts (Domain-specific wins over generic)
        (
            "optimize database query",
            "data",
            "db_vs_performance",
        ),  # Data is more specific than performance
        (
            "audit security vulnerabilities",
            "reviewer",
            "review_vs_security",
        ),  # Reviewer (audit keyword)
        (
            "test security",
            "security",
            "test_vs_security",
        ),  # Security is domain-specific, test is generic
        ("document architecture", "architect", "doc_vs_architect"),  # Architect is domain-specific
        ("plan deployment", "devops", "plan_vs_devops"),  # Devops (deployment is domain-specific)
        # Edge cases - Empty/Ambiguous
        ("", "executor", "empty_string"),  # Default to executor
        ("do something", "executor", "ambiguous"),  # Default to executor
        ("help", "executor", "help_ambiguous"),  # Default to executor
    ]

    conflicts = []
    passed = 0
    failed = 0

    print("Testing {} routing scenarios...\n".format(len(test_cases)))

    for prompt, expected, category in test_cases:
        actual = orchestrator.route(prompt)
        status = "✅" if actual == expected else "❌"

        if actual != expected:
            conflicts.append(
                {"prompt": prompt, "expected": expected, "actual": actual, "category": category}
            )
            failed += 1
            print(f"{status} [{category}] '{prompt}'")
            print(f"    Expected: {expected}, Got: {actual}")
        else:
            passed += 1
            print(f"{status} [{category}] '{prompt}' → {actual}")

    print("\n" + "=" * 80)
    print(f"RESULTS: {passed}/{len(test_cases)} PASSED, {failed} FAILED")
    print("=" * 80)

    if conflicts:
        print("\n⚠️  ROUTING CONFLICTS FOUND:")
        for conflict in conflicts:
            print(f"  • [{conflict['category']}] '{conflict['prompt']}'")
            print(f"    Expected: {conflict['expected']}, Got: {conflict['actual']}")
        print()
        return False
    else:
        print("\n✅ NO ROUTING CONFLICTS - ALL TESTS PASSED!")
        return True


if __name__ == "__main__":
    success = test_routing()
    exit(0 if success else 1)
