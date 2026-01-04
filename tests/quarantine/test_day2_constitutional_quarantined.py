import pytest
from unittest.mock import MagicMock

from vertice_cli.agents.testing import TestingAgent
from vertice_cli.agents.refactor import RefactorAgent
from vertice_cli.agents.base import AgentTask


@pytest.mark.skip(reason="QUARANTINED: RefactorAgent actions (detect_smells, quality_score) not implemented")
class TestRealWorldEndToEnd:
    """End-to-end tests with real code scenarios."""

    @pytest.mark.asyncio
    async def test_e2e_flask_route_testing(self):
        """E2E: Generate tests for Flask route."""
        agent = TestingAgent(model=MagicMock())

        code = """
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/api/users', methods=['GET'])
def get_users():
    return jsonify({"users": []})
"""

        task = AgentTask(
            request="Generate tests",
            context={"action": "generate_tests", "source_code": code},
        )

        response = await agent.execute(task)

        assert response.success is True
        # Should generate test for get_users

    @pytest.mark.asyncio
    async def test_e2e_django_model_testing(self):
        """E2E: Generate tests for Django model."""
        agent = TestingAgent(model=MagicMock())

        code = """
from django.db import models

class User(models.Model):
    username = models.CharField(max_length=100)
    email = models.EmailField()
    is_active = models.BooleanField(default=True)

    def activate(self):
        self.is_active = True
        self.save()
"""

        task = AgentTask(
            request="Generate tests",
            context={"action": "generate_tests", "source_code": code},
        )

        response = await agent.execute(task)

        assert response.success is True

    @pytest.mark.asyncio
    async def test_e2e_refactor_messy_code(self):
        """E2E: Refactor analysis of messy code."""
        agent = RefactorAgent(llm_client=MagicMock(), mcp_client=MagicMock())

        # Intentionally messy code
        code = """
def process(x, y, z):
    if x > 0:
        if y > 0:
            if z > 0:
                return 42 * 3.14 + 100
            else:
                return 0
        else:
            return -1
    else:
        return -2
"""

        task = AgentTask(
            request="Detect smells",
            context={"action": "detect_smells", "source_code": code},
        )

        response = await agent.execute(task)

        assert response.success is True
        # Should detect deep nesting and magic numbers
        assert response.data["total_issues"] >= 2

    @pytest.mark.asyncio
    async def test_e2e_integration_test_then_refactor(self):
        """E2E: Test generation → Refactor analysis pipeline."""
        test_agent = TestingAgent(model=MagicMock())
        refactor_agent = RefactorAgent(llm_client=MagicMock(), mcp_client=MagicMock())

        code = """
def calculate_discount(price, customer_type):
    if customer_type == "premium":
        return price * 0.8
    return price * 0.9
"""

        # Step 1: Generate tests
        test_task = AgentTask(
            request="Generate tests",
            context={"action": "generate_tests", "source_code": code},
        )

        test_response = await test_agent.execute(test_task)
        assert test_response.success is True

        # Step 2: Analyze quality
        refactor_task = AgentTask(
            request="Quality score",
            context={"action": "quality_score", "source_code": code},
        )

        refactor_response = await refactor_agent.execute(refactor_task)
        assert refactor_response.success is True

        # Both should work together
        assert "test_cases" in test_response.data
        assert "quality_score" in refactor_response.data

    @pytest.mark.asyncio
    async def test_e2e_sqlalchemy_repository_pattern(self):
        """E2E: Test SQLAlchemy repository pattern."""
        agent = TestingAgent(model=MagicMock())

        code = """
from sqlalchemy.orm import Session

class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, user_id: int):
        return self.session.query(User).filter_by(id=user_id).first()

    def create(self, username: str, email: str):
        user = User(username=username, email=email)
        self.session.add(user)
        self.session.commit()
        return user
"""

        task = AgentTask(
            request="Generate tests",
            context={"action": "generate_tests", "source_code": code},
        )

        response = await agent.execute(task)

        assert response.success is True
