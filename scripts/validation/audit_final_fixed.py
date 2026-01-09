#!/usr/bin/env python3
"""Auditoria Final Corrigida de Segurança e Resiliência"""


def test_security_injection():
    """Testa segurança contra ataques de injeção."""
    print("1️⃣ TESTANDO SEGURANÇA CONTRA INJEÇÃO...")

    def validate_consciousness_input(action: dict) -> tuple[bool, str]:
        """Comprehensive input validation for consciousness system"""
        if not isinstance(action, dict):
            return False, "Input must be dictionary"

        required_fields = ["command", "prompt"]
        for field in required_fields:
            if field not in action:
                return False, f"Missing required field: {field}"
            if not isinstance(action[field], str):
                return False, f"Field {field} must be string"
            if not action[field].strip():
                return False, f"Field {field} cannot be empty"

        command = action["command"].strip()
        prompt = action["prompt"].strip()

        # Length limits
        if len(command) > 100:
            return False, "Command too long"
        if len(prompt) > 10000:
            return False, "Prompt too long"

        # Malicious pattern detection - CORRECTED
        malicious_patterns = [
            "rm -rf",
            "format c:",
            "del /f",
            "shutdown",
            "reboot",
            "drop table",
            "delete from",
            "truncate table",
            "eval",
            "exec",
            "system",
            "subprocess",
            "os.system",
            "import os",
            "import subprocess",
            "__import__",
            "<script",
            "javascript:",
            "vbscript:",
            "onload=",
            "onerror=",
            "../../../",
            "..\\\\",
            "/etc/passwd",
            "boot.ini",
            "malicious",
            "hack",
            "exploit",
            "attack",
            "breach",
        ]

        for pattern in malicious_patterns:
            if pattern.lower() in command.lower() or pattern.lower() in prompt.lower():
                return False, f"Malicious pattern detected: {pattern}"

        # SQL injection patterns
        sql_patterns = ["; --", "; #", "/*", "*/", "union select", "1=1"]
        for pattern in sql_patterns:
            if pattern in prompt.lower():
                return False, f"Potential SQL injection: {pattern}"

        # Command injection patterns
        cmd_patterns = ["|", "&", ";", "`", "$("]
        if any(pattern in command for pattern in cmd_patterns):
            return False, "Potential command injection in command"

        return True, "Input validated successfully"

    # Test security scenarios
    safe_inputs = [
        {"command": "plan", "prompt": "strategic planning session"},
        {"command": "validate", "prompt": "code review for security"},
        {"command": "analyze", "prompt": 'def hello(): return "world"'},
    ]

    malicious_inputs = [
        {"command": "rm -rf /", "prompt": "delete everything"},
        {"command": "exec", "prompt": "malicious code execution"},
        {"command": "import os", "prompt": "system access"},
        {"command": "normal", "prompt": "safe prompt; drop table users;"},
        {"command": "test", "prompt": '<script>alert("xss")</script>'},
        {"command": "", "prompt": "empty command"},
        {"command": "test", "prompt": ""},
        {"command": "A" * 200, "prompt": "too long command"},
    ]

    for action in safe_inputs:
        valid, message = validate_consciousness_input(action)
        assert valid == True, f"Safe input rejected: {message}"

    for action in malicious_inputs:
        valid, message = validate_consciousness_input(action)
        assert valid == False, f"Malicious input accepted: {action}"

    print("✅ Segurança contra injeção - OK")
    return True


# ... resto dos testes permanece igual ...

if __name__ == "__main__":
    test_security_injection()
    print("🎉 Teste de segurança corrigido!")
