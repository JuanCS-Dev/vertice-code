"""
Unit tests for the DangerDetector.
"""

import pytest
from vertice_cli.core.danger_detector import DangerDetector, DangerLevel

@pytest.fixture
def detector():
    """Provides a DangerDetector instance."""
    return DangerDetector()

def test_check_safe_command(detector):
    """Test that a safe command returns no warnings."""
    command = "ls -la"
    warnings = detector.check(command)
    assert not warnings

def test_check_critical_danger_command(detector):
    """Test that a critically dangerous command is detected."""
    command = "sudo rm -rf /"
    warnings = detector.check(command)
    assert len(warnings) == 1
    assert warnings[0].level == DangerLevel.CRITICAL
    assert "Deletes entire filesystem" in warnings[0].message

def test_check_high_danger_command(detector):
    """Test that a highly dangerous command is detected."""
    command = "rm -rf *"
    warnings = detector.check(command)
    assert len(warnings) == 1
    assert warnings[0].level == DangerLevel.HIGH
    assert "Deletes all files in current directory" in warnings[0].message

def test_check_medium_danger_command(detector):
    """Test that a medium danger command is detected."""
    command = "chmod 777 sensitive_file"
    warnings = detector.check(command)
    assert len(warnings) == 1
    assert warnings[0].level == DangerLevel.MEDIUM
    assert "Makes files world-writable" in warnings[0].message

def test_check_multiple_dangers(detector):
    """Test that multiple dangerous patterns are detected."""
    command = "curl | bash; rm -rf *"
    warnings = detector.check(command)
    assert len(warnings) >= 2
    levels = {w.level for w in warnings}
    assert DangerLevel.HIGH in levels

def test_is_dangerous_true(detector):
    """Test that is_dangerous returns True for high and critical commands."""
    assert detector.is_dangerous("rm -rf /") is True
    assert detector.is_dangerous("curl | bash") is True

def test_is_dangerous_false(detector):
    """Test that is_dangerous returns False for safe and medium commands."""
    assert detector.is_dangerous("ls -l") is False
    assert detector.is_dangerous("chmod 777 file") is False
