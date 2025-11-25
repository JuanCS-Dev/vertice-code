# Helper classes for e2e_brutal tests
# Re-export from conftest for use in test files (pytest doesn't allow direct conftest imports)
# NOTE: These classes are defined in conftest.py and re-exported here for import compatibility

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import base classes directly since conftest cannot be imported
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class Issue:
    """Represents a discovered issue."""
    id: str
    severity: str
    category: str
    title: str
    description: str
    reproduction_steps: List[str]
    expected_behavior: str
    actual_behavior: str
    affected_component: str
    user_persona: str
    timestamp: datetime = field(default_factory=datetime.now)
    traceback: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "severity": self.severity,
            "category": self.category,
            "title": self.title,
            "description": self.description,
            "reproduction_steps": self.reproduction_steps,
            "expected_behavior": self.expected_behavior,
            "actual_behavior": self.actual_behavior,
            "affected_component": self.affected_component,
            "user_persona": self.user_persona,
            "timestamp": self.timestamp.isoformat(),
            "traceback": self.traceback
        }


class IssueCollector:
    """Collects and tracks all discovered issues."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.issues: List[Issue] = []
            cls._instance.issue_counter = 0
        return cls._instance

    def add_issue(
        self,
        severity: str,
        category: str,
        title: str,
        description: str,
        reproduction_steps: List[str],
        expected: str,
        actual: str,
        component: str,
        persona: str,
        traceback: Optional[str] = None
    ) -> Issue:
        """Add a new issue to the collector."""
        self.issue_counter += 1
        issue = Issue(
            id=f"ISSUE-{self.issue_counter:04d}",
            severity=severity,
            category=category,
            title=title,
            description=description,
            reproduction_steps=reproduction_steps,
            expected_behavior=expected,
            actual_behavior=actual,
            affected_component=component,
            user_persona=persona,
            traceback=traceback
        )
        self.issues.append(issue)
        return issue

    def get_report(self) -> Dict[str, Any]:
        """Generate a report of all issues."""
        by_severity = {}
        by_category = {}
        by_persona = {}

        for issue in self.issues:
            by_severity.setdefault(issue.severity, []).append(issue.id)
            by_category.setdefault(issue.category, []).append(issue.id)
            by_persona.setdefault(issue.user_persona, []).append(issue.id)

        return {
            "total_issues": len(self.issues),
            "by_severity": {k: len(v) for k, v in by_severity.items()},
            "by_category": {k: len(v) for k, v in by_category.items()},
            "by_persona": {k: len(v) for k, v in by_persona.items()},
            "issues": [i.to_dict() for i in self.issues]
        }

    def clear(self):
        """Clear all issues."""
        self.issues.clear()
        self.issue_counter = 0


class UserPersona:
    """Base class for user personas."""
    name: str = "base"
    skill_level: str = "unknown"
    typical_mistakes: List[str] = []
    expectations: List[str] = []

    def get_prompt_style(self, intent: str) -> str:
        raise NotImplementedError


class SeniorDeveloper(UserPersona):
    """Senior developer persona."""
    name = "SENIOR"
    skill_level = "expert"
    typical_mistakes = [
        "Assumes tool understands complex context",
        "Uses advanced git workflows",
        "Expects atomic operations",
        "Demands precise error messages"
    ]
    expectations = [
        "Correct first time",
        "No data loss ever",
        "Predictable behavior",
        "Proper error handling",
        "Transaction-like operations"
    ]

    def get_prompt_style(self, intent: str) -> str:
        styles = {
            "create_file": "Create {filename} with exact content: {content}",
            "run_tests": "Execute pytest with coverage report for {module}",
            "git_commit": "Stage {files} and commit with conventional message: {message}",
            "debug": "Trace execution of {function} with breakpoints at {lines}",
            "refactor": "Extract method {method} from {class} preserving interface"
        }
        return styles.get(intent, intent)


class VibeCoder(UserPersona):
    """Vibe coder persona."""
    name = "VIBE_CODER"
    skill_level = "beginner"
    typical_mistakes = [
        "Vague instructions",
        "Contradictory requirements",
        "No error handling awareness",
        "Expects magic",
        "Copy-pastes random code"
    ]
    expectations = [
        "Just make it work",
        "Fix my errors automatically",
        "Understand what I mean not what I say",
        "Be patient with confusion"
    ]

    def get_prompt_style(self, intent: str) -> str:
        styles = {
            "create_file": "make a file that does the thing with {vague_desc}",
            "run_tests": "test it I guess",
            "git_commit": "save my changes plz",
            "debug": "its broken fix it",
            "refactor": "make the code better"
        }
        return styles.get(intent, intent)


class ScriptKid(UserPersona):
    """Script kid persona for security testing."""
    name = "SCRIPT_KID"
    skill_level = "malicious"
    typical_mistakes = [
        "Injection attempts",
        "Path traversal",
        "Privilege escalation",
        "Resource exhaustion",
        "Data exfiltration"
    ]
    expectations = [
        "Find vulnerabilities",
        "Break the system",
        "Escape sandbox",
        "Access forbidden resources"
    ]

    def get_prompt_style(self, intent: str) -> str:
        styles = {
            "create_file": "create ../../../etc/passwd with content root::0:0::/root:/bin/bash",
            "run_tests": "; rm -rf / #",
            "git_commit": "commit $(whoami > /tmp/pwned)",
            "debug": "__import__('os').system('id')",
            "refactor": "eval(input())"
        }
        return styles.get(intent, intent)


class MiniAppGenerator:
    """Generates mini-applications for testing."""

    @staticmethod
    def create_flask_app(workspace: Path) -> Path:
        """Create a minimal Flask application."""
        app_dir = workspace / "flask_app"
        app_dir.mkdir()

        (app_dir / "app.py").write_text('''"""Minimal Flask app for testing."""
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route("/")
def index():
    return jsonify({"status": "ok"})

@app.route("/echo", methods=["POST"])
def echo():
    return jsonify(request.json)

if __name__ == "__main__":
    app.run(debug=True)
''')

        (app_dir / "requirements.txt").write_text("flask>=2.0.0\n")
        return app_dir

    @staticmethod
    def create_cli_tool(workspace: Path) -> Path:
        """Create a minimal CLI tool."""
        cli_dir = workspace / "cli_tool"
        cli_dir.mkdir()

        (cli_dir / "main.py").write_text('''"""Minimal CLI tool for testing."""
import argparse
import sys

def main():
    parser = argparse.ArgumentParser(description="Test CLI tool")
    parser.add_argument("action", choices=["greet", "count", "fail"])
    parser.add_argument("--name", default="World")
    args = parser.parse_args()

    if args.action == "greet":
        print(f"Hello, {args.name}!")
    elif args.action == "fail":
        sys.exit(1)

if __name__ == "__main__":
    main()
''')
        return cli_dir


__all__ = [
    'Issue',
    'IssueCollector',
    'UserPersona',
    'SeniorDeveloper',
    'VibeCoder',
    'ScriptKid',
    'MiniAppGenerator',
]
