"""
Security Agent.

SCALE & SUSTAIN Phase 3.1 - Semantic Modularization.

Specialized agent for security analysis using AST.
NO MORE STRING MATCHING - Surgical AST-based detection!

Author: Vertice Team
Date: 2026-01-02
"""

import ast
from typing import List

from .types import CodeIssue, IssueCategory, IssueSeverity


class SecurityAgent(ast.NodeVisitor):
    """
    Specialized agent for security analysis using AST.
    NO MORE STRING MATCHING - Surgical AST-based detection!
    """

    DANGEROUS_CALLS = {
        "eval": {
            "severity": IssueSeverity.CRITICAL,
            "message": "Use of eval() is a critical security risk",
            "explanation": "eval() can execute arbitrary code and is a common attack vector",
            "fix": "Replace with ast.literal_eval() for literals or json.loads() for JSON",
        },
        "exec": {
            "severity": IssueSeverity.CRITICAL,
            "message": "Use of exec() is a critical security risk",
            "explanation": "exec() executes arbitrary Python code",
            "fix": "Refactor to avoid dynamic code execution",
        },
        "__import__": {
            "severity": IssueSeverity.HIGH,
            "message": "Dynamic import with __import__() can be dangerous",
            "explanation": "Can be used to import arbitrary modules",
            "fix": "Use standard import statements or importlib.import_module() with validation",
        },
    }

    DANGEROUS_METHODS = {
        ("pickle", "loads"): {
            "severity": IssueSeverity.HIGH,
            "message": "pickle.loads() can execute arbitrary code",
            "explanation": "Unpickling untrusted data is dangerous",
            "fix": "Use JSON or other safe serialization formats",
        },
        ("subprocess", "call"): {
            "severity": IssueSeverity.HIGH,
            "message": "subprocess.call() without shell=False is risky",
            "explanation": "Can lead to command injection if user input is used",
            "fix": "Use subprocess.run() with explicit args list and shell=False",
        },
        ("os", "system"): {
            "severity": IssueSeverity.CRITICAL,
            "message": "os.system() is vulnerable to command injection",
            "explanation": "Executes shell commands directly",
            "fix": "Use subprocess.run() with explicit args list",
        },
        ("hashlib", "md5"): {
            "severity": IssueSeverity.HIGH,
            "message": "MD5 is cryptographically broken, do not use for security",
            "explanation": "MD5 is vulnerable to collision attacks",
            "fix": "Use bcrypt, argon2, or scrypt for passwords; SHA-256+ for integrity",
        },
        ("hashlib", "sha1"): {
            "severity": IssueSeverity.MEDIUM,
            "message": "SHA-1 is deprecated for security purposes",
            "explanation": "SHA-1 has known vulnerabilities",
            "fix": "Use SHA-256 or SHA-3 for cryptographic purposes",
        },
    }

    SQL_KEYWORDS = {"select", "insert", "update", "delete", "drop", "execute", "exec"}

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.issues: List[CodeIssue] = []

    async def analyze(self, code: str, tree: ast.AST) -> List[CodeIssue]:
        """AST-based security analysis - no false positives from comments/strings."""
        self.issues = []
        self.visit(tree)
        return self.issues

    def visit_Call(self, node: ast.Call):
        """Visit function calls - the surgical approach."""
        # Case 1: Direct dangerous function call (eval, exec, etc.)
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name in self.DANGEROUS_CALLS:
                danger = self.DANGEROUS_CALLS[func_name]
                self.issues.append(
                    CodeIssue(
                        file=self.file_path,
                        line=node.lineno,
                        end_line=node.end_lineno,
                        severity=danger["severity"],
                        category=IssueCategory.SECURITY,
                        message=danger["message"],
                        explanation=danger["explanation"],
                        fix_suggestion=danger["fix"],
                        auto_fixable=False,
                        confidence=1.0,
                    )
                )

        # Case 2: Method calls on modules (pickle.loads, os.system, etc.)
        elif isinstance(node.func, ast.Attribute):
            module_chain = self._get_attribute_chain(node.func)

            if len(module_chain) >= 2:
                module_method = (module_chain[-2], module_chain[-1])
                if module_method in self.DANGEROUS_METHODS:
                    danger = self.DANGEROUS_METHODS[module_method]

                    # Extra check for subprocess - warn only if shell=True
                    if module_method[0] == "subprocess":
                        has_shell_true = any(
                            isinstance(kw, ast.keyword)
                            and kw.arg == "shell"
                            and isinstance(kw.value, ast.Constant)
                            and kw.value.value is True
                            for kw in node.keywords
                        )
                        if not has_shell_true:
                            self.generic_visit(node)
                            return

                    self.issues.append(
                        CodeIssue(
                            file=self.file_path,
                            line=node.lineno,
                            end_line=node.end_lineno,
                            severity=danger["severity"],
                            category=IssueCategory.SECURITY,
                            message=danger["message"],
                            explanation=danger["explanation"],
                            fix_suggestion=danger["fix"],
                            auto_fixable=False,
                            confidence=0.95,
                        )
                    )

        self.generic_visit(node)

    def visit_JoinedStr(self, node: ast.JoinedStr):
        """Detect SQL injection via f-strings."""
        string_parts = []
        has_variable = False

        for value in node.values:
            if isinstance(value, ast.Constant):
                string_parts.append(str(value.value).lower())
            elif isinstance(value, ast.FormattedValue):
                has_variable = True

        full_string = "".join(string_parts)
        if has_variable and any(kw in full_string for kw in self.SQL_KEYWORDS):
            self.issues.append(
                CodeIssue(
                    file=self.file_path,
                    line=node.lineno,
                    end_line=getattr(node, "end_lineno", node.lineno),
                    severity=IssueSeverity.CRITICAL,
                    category=IssueCategory.SECURITY,
                    message="Potential SQL injection via f-string interpolation",
                    explanation="F-strings with user input in SQL queries allow attackers to inject malicious SQL",
                    fix_suggestion="Use parameterized queries with placeholders (?, %s) instead of f-strings",
                    auto_fixable=False,
                    confidence=0.9,
                )
            )

        self.generic_visit(node)

    def visit_BinOp(self, node: ast.BinOp):
        """Detect SQL injection via string concatenation."""
        if isinstance(node.op, ast.Add):
            string_parts = []
            has_name = False

            def extract_strings(n):
                nonlocal has_name
                if isinstance(n, ast.Constant) and isinstance(n.value, str):
                    string_parts.append(n.value.lower())
                elif isinstance(n, ast.Name):
                    has_name = True
                elif isinstance(n, ast.BinOp) and isinstance(n.op, ast.Add):
                    extract_strings(n.left)
                    extract_strings(n.right)

            extract_strings(node.left)
            extract_strings(node.right)

            full_string = "".join(string_parts)
            if has_name and any(kw in full_string for kw in self.SQL_KEYWORDS):
                self.issues.append(
                    CodeIssue(
                        file=self.file_path,
                        line=node.lineno,
                        end_line=getattr(node, "end_lineno", node.lineno),
                        severity=IssueSeverity.CRITICAL,
                        category=IssueCategory.SECURITY,
                        message="Potential SQL injection via string concatenation",
                        explanation="Concatenating user input into SQL queries allows attackers to inject malicious SQL",
                        fix_suggestion="Use parameterized queries with placeholders (?, %s) instead of concatenation",
                        auto_fixable=False,
                        confidence=0.85,
                    )
                )

        self.generic_visit(node)

    def _get_attribute_chain(self, node: ast.Attribute) -> List[str]:
        """Extract attribute chain: a.b.c -> ['a', 'b', 'c']."""
        chain = [node.attr]
        current = node.value

        while isinstance(current, ast.Attribute):
            chain.insert(0, current.attr)
            current = current.value

        if isinstance(current, ast.Name):
            chain.insert(0, current.id)

        return chain


__all__ = ["SecurityAgent"]
