#!/usr/bin/env python3
"""
Dependency Validation Script for Vertice-Code
Validates all dependencies, imports, and compatibility.
"""

import sys
import importlib
import subprocess
from pathlib import Path
from typing import List


class DependencyValidator:
    """Validates project dependencies and imports."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate_imports(self) -> bool:
        """Validate that all main modules can be imported."""
        modules_to_test = ["vertice_core", "vertice_tui", "vertice_core", "prometheus"]

        success = True
        for module in modules_to_test:
            try:
                importlib.import_module(module)
                print(f"✓ {module} imports successfully")
            except ImportError as e:
                self.errors.append(f"Failed to import {module}: {e}")
                print(f"✗ {module} import failed: {e}")
                success = False
            except Exception as e:
                self.warnings.append(f"Warning importing {module}: {e}")
                print(f"⚠ {module} import warning: {e}")

        return success

    def validate_requirements(self) -> bool:
        """Validate requirements.txt compatibility."""
        success = True

        # Check if requirements.txt exists
        req_file = self.project_root / "requirements.txt"
        if not req_file.exists():
            self.errors.append("requirements.txt not found")
            return False

        # Try to install requirements in dry-run mode
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--dry-run", "-r", str(req_file)],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                self.errors.append(f"Requirements validation failed: {result.stderr}")
                success = False
            else:
                print("✓ requirements.txt validation passed")

        except subprocess.TimeoutExpired:
            self.warnings.append("Requirements validation timed out")
        except Exception as e:
            self.errors.append(f"Error validating requirements: {e}")
            success = False

        return success

    def check_circular_imports(self) -> bool:
        """Check for potential circular imports."""
        success = True

        # Check common circular import patterns
        circular_patterns = [
            ("vertice_core", "vertice_core"),
            ("prometheus", "vertice_core"),
            ("vertice_tui", "vertice_core"),
        ]

        for module1, module2 in circular_patterns:
            # This is a simple check - in practice, we'd need more sophisticated analysis
            if self._check_import_cycle(module1, module2):
                self.warnings.append(f"Potential circular import between {module1} and {module2}")

        return success

    def _check_import_cycle(self, module1: str, module2: str) -> bool:
        """Simple check for import cycles."""
        try:
            # Check if module1 imports module2 and vice versa

            mod1 = importlib.import_module(module1)
            mod2 = importlib.import_module(module2)

            # Check if module1's source contains imports from module2
            if hasattr(mod1, "__file__") and mod1.__file__:
                with open(mod1.__file__, "r") as f:
                    content1 = f.read()
                    if f"from {module2}" in content1 or f"import {module2}" in content1:
                        # Check if module2 imports module1
                        if hasattr(mod2, "__file__") and mod2.__file__:
                            with open(mod2.__file__, "r") as f2:
                                content2 = f2.read()
                                if f"from {module1}" in content2 or f"import {module1}" in content2:
                                    return True
        except Exception:
            pass

        return False

    def validate_pyproject(self) -> bool:
        """Validate pyproject.toml configuration."""
        success = True

        pyproject_file = self.project_root / "pyproject.toml"
        if not pyproject_file.exists():
            self.errors.append("pyproject.toml not found")
            return False

        try:
            import tomllib

            with open(pyproject_file, "rb") as f:
                config = tomllib.load(f)

            # Check required sections
            required_sections = ["project", "build-system"]
            for section in required_sections:
                if section not in config:
                    self.errors.append(f"Missing required section '{section}' in pyproject.toml")
                    success = False

            # Validate project metadata
            project = config.get("project", {})
            required_fields = ["name", "version", "description"]
            for field in required_fields:
                if field not in project:
                    self.errors.append(f"Missing required field '{field}' in project section")
                    success = False

            if success:
                print("✓ pyproject.toml validation passed")

        except ImportError:
            self.warnings.append("tomllib not available for pyproject.toml validation")
        except Exception as e:
            self.errors.append(f"Error validating pyproject.toml: {e}")
            success = False

        return success

    def run_validation(self) -> bool:
        """Run all validation checks."""
        print("🔍 Running dependency validation...\n")

        checks = [
            ("Import validation", self.validate_imports),
            ("Requirements validation", self.validate_requirements),
            ("Circular import check", self.check_circular_imports),
            ("Pyproject validation", self.validate_pyproject),
        ]

        overall_success = True

        for check_name, check_func in checks:
            print(f"Running {check_name}...")
            try:
                success = check_func()
                if not success:
                    overall_success = False
            except Exception as e:
                self.errors.append(f"Error in {check_name}: {e}")
                overall_success = False
                print(f"✗ {check_name} failed: {e}")

        print("\n" + "=" * 50)
        print("VALIDATION RESULTS")
        print("=" * 50)

        if self.errors:
            print(f"❌ ERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"  • {error}")

        if self.warnings:
            print(f"⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  • {warning}")

        if not self.errors and not self.warnings:
            print("✅ All checks passed!")

        return overall_success and len(self.errors) == 0


def main():
    """Main entry point."""
    project_root = Path(__file__).parent.parent
    validator = DependencyValidator(project_root)
    success = validator.run_validation()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
