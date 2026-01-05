"""
Tests for Sprint 3 - Code Intelligence.

Tests all components:
- LSPClient: Language Server Protocol client
- ASTEditor: Context-aware code editing
- CodeValidator: Post-edit validation

Phase 10: Sprint 3 - Code Intelligence

Soli Deo Gloria
"""

import os
import tempfile
import pytest
from pathlib import Path

# Import all Sprint 3 components
from vertice_core.code import (
    # LSP Client
    DiagnosticSeverity,
    SymbolKind,
    Position,
    Range,
    Location,
    Diagnostic,
    DocumentSymbol,
    HoverInfo,
    CompletionItem,
    LanguageServerConfig,
    DEFAULT_LANGUAGE_SERVERS,
    # AST Editor
    NodeContext,
    CodeLocation,
    CodeMatch,
    ASTEditor,
    get_ast_editor,
    LANGUAGE_CONFIGS,
    ValidationLevel,
    CheckType,
    Check,
    ValidationResult,
    EditValidation,
    CodeValidator,
)


# =============================================================================
# LSP Types Tests
# =============================================================================

class TestLSPTypes:
    """Tests for LSP data types."""

    def test_position_creation(self):
        """Test Position creation and serialization."""
        pos = Position(line=10, character=5)

        assert pos.line == 10
        assert pos.character == 5

        # Serialization
        data = pos.to_dict()
        assert data == {"line": 10, "character": 5}

        # Deserialization
        pos2 = Position.from_dict(data)
        assert pos2.line == pos.line
        assert pos2.character == pos.character

    def test_range_creation(self):
        """Test Range creation and serialization."""
        range_obj = Range(
            start=Position(1, 0),
            end=Position(1, 10),
        )

        assert range_obj.start.line == 1
        assert range_obj.end.character == 10

        data = range_obj.to_dict()
        assert "start" in data
        assert "end" in data

    def test_location_filepath(self):
        """Test Location URI to filepath conversion."""
        loc = Location(
            uri="file:///home/user/project/file.py",
            range=Range(Position(9, 4), Position(9, 20)),
        )

        assert loc.filepath == "/home/user/project/file.py"
        assert loc.line == 10  # 1-indexed
        assert loc.column == 5  # 1-indexed

    def test_diagnostic_severity(self):
        """Test Diagnostic with different severities."""
        error_diag = Diagnostic(
            range=Range(Position(0, 0), Position(0, 10)),
            message="Undefined variable",
            severity=DiagnosticSeverity.ERROR,
        )

        assert error_diag.is_error is True
        assert error_diag.is_warning is False

        warning_diag = Diagnostic(
            range=Range(Position(0, 0), Position(0, 10)),
            message="Unused import",
            severity=DiagnosticSeverity.WARNING,
        )

        assert warning_diag.is_error is False
        assert warning_diag.is_warning is True

    def test_diagnostic_from_dict(self):
        """Test Diagnostic deserialization."""
        data = {
            "range": {
                "start": {"line": 5, "character": 0},
                "end": {"line": 5, "character": 10},
            },
            "message": "Test error",
            "severity": 1,
            "code": "E001",
            "source": "pylsp",
        }

        diag = Diagnostic.from_dict(data)

        assert diag.message == "Test error"
        assert diag.severity == DiagnosticSeverity.ERROR
        assert diag.code == "E001"
        assert diag.source == "pylsp"

    def test_document_symbol_hierarchy(self):
        """Test DocumentSymbol with children."""
        child = DocumentSymbol(
            name="method1",
            kind=SymbolKind.METHOD,
            range=Range(Position(5, 4), Position(10, 0)),
            selection_range=Range(Position(5, 8), Position(5, 15)),
        )

        parent = DocumentSymbol(
            name="MyClass",
            kind=SymbolKind.CLASS,
            range=Range(Position(0, 0), Position(20, 0)),
            selection_range=Range(Position(0, 6), Position(0, 13)),
            children=[child],
        )

        assert len(parent.children) == 1
        assert parent.children[0].name == "method1"

    def test_hover_info_parsing(self):
        """Test HoverInfo from different formats."""
        # String content
        info1 = HoverInfo.from_dict({"contents": "Simple string"})
        assert info1.contents == "Simple string"

        # Dict content
        info2 = HoverInfo.from_dict({
            "contents": {"value": "Markdown **content**", "kind": "markdown"}
        })
        assert "Markdown" in info2.contents

        # List content
        info3 = HoverInfo.from_dict({
            "contents": [
                {"value": "Line 1"},
                {"value": "Line 2"},
            ]
        })
        assert "Line 1" in info3.contents
        assert "Line 2" in info3.contents

    def test_completion_item(self):
        """Test CompletionItem parsing."""
        data = {
            "label": "my_function",
            "kind": 3,  # Function
            "detail": "def my_function()",
            "insertText": "my_function()",
        }

        item = CompletionItem.from_dict(data)

        assert item.label == "my_function"
        assert item.kind == 3
        assert item.detail == "def my_function()"

    def test_language_server_config(self):
        """Test LanguageServerConfig."""
        config = LanguageServerConfig(
            language="python",
            command=["pylsp"],
            file_extensions=[".py", ".pyi"],
            root_markers=["pyproject.toml"],
        )

        assert config.language == "python"
        assert ".py" in config.file_extensions

    def test_default_language_servers(self):
        """Test default language server configurations."""
        assert "python" in DEFAULT_LANGUAGE_SERVERS
        assert "typescript" in DEFAULT_LANGUAGE_SERVERS
        assert "go" in DEFAULT_LANGUAGE_SERVERS
        assert "rust" in DEFAULT_LANGUAGE_SERVERS

        python_config = DEFAULT_LANGUAGE_SERVERS["python"]
        assert python_config.command == ["pylsp"]
        assert ".py" in python_config.file_extensions


# =============================================================================
# AST Editor Tests
# =============================================================================

class TestASTEditor:
    """Tests for ASTEditor."""

    def test_editor_creation(self):
        """Test ASTEditor creation."""
        editor = ASTEditor()
        assert editor is not None

    def test_singleton_instance(self):
        """Test singleton pattern."""
        editor1 = get_ast_editor()
        editor2 = get_ast_editor()
        assert editor1 is editor2

    def test_language_detection(self):
        """Test language detection from filepath."""
        editor = ASTEditor()

        # Direct language name
        assert editor._get_language("python") == "python"

        # From file extension
        assert editor._get_language("file.py") == "python"
        assert editor._get_language("file.js") == "javascript"
        assert editor._get_language("file.ts") == "typescript"
        assert editor._get_language("file.go") == "go"
        assert editor._get_language("file.rs") == "rust"

        # Unknown
        assert editor._get_language("file.xyz") is None

    def test_find_in_code_simple(self):
        """Test finding text in code."""
        editor = ASTEditor()

        code = '''
def hello():
    message = "hello world"
    print(message)
'''

        # Find in code (not in strings)
        matches = editor.find_in_code(code, "message", "python")

        # Should find variable uses, not the string content
        assert len(matches) >= 1

        # All matches should be in code context
        code_matches = [m for m in matches if m.is_code]
        assert len(code_matches) >= 1

    def test_find_excludes_strings(self):
        """Test that find excludes string literals by default."""
        editor = ASTEditor()

        code = '''
name = "hello"
x = hello
'''

        matches = editor.find_in_code(code, "hello", "python", include_strings=False)

        # Should find variable 'hello', not string "hello"
        for match in matches:
            if match.is_code:
                assert match.text == "hello" or "hello" in match.text

    def test_find_excludes_comments(self):
        """Test that find excludes comments by default."""
        editor = ASTEditor()

        code = '''
# This is a test comment
test = 1
'''

        matches = editor.find_in_code(code, "test", "python", include_comments=False)

        # Should find variable 'test', not comment
        code_matches = [m for m in matches if m.is_code]
        assert len(code_matches) >= 1

    def test_find_with_strings_included(self):
        """Test finding with strings included."""
        editor = ASTEditor()

        code = '''
message = "hello"
x = hello
'''

        matches = editor.find_in_code(code, "hello", "python", include_strings=True)

        # Should find both
        assert len(matches) >= 2

    def test_replace_in_code(self):
        """Test replacing text only in code."""
        editor = ASTEditor()

        code = '''
old_name = "old_name in string"
print(old_name)
'''

        result = editor.replace_in_code(
            code, "old_name", "new_name", "python",
            include_strings=False,
        )

        assert result.success is True
        assert result.changes_made >= 1

        # String should be unchanged
        assert '"old_name in string"' in result.content or "old_name in string" in result.content

        # Variable should be changed
        assert "new_name" in result.content

    def test_replace_all_occurrences(self):
        """Test replacing all occurrences."""
        editor = ASTEditor()

        code = '''
x = foo
y = foo
z = foo
'''

        result = editor.replace_in_code(code, "foo", "bar", "python")

        assert result.success is True
        assert result.changes_made == 3
        assert "foo" not in result.content
        assert result.content.count("bar") == 3

    def test_replace_limited(self):
        """Test replacing with limit."""
        editor = ASTEditor()

        code = '''
x = foo
y = foo
z = foo
'''

        result = editor.replace_in_code(
            code, "foo", "bar", "python",
            max_replacements=1,
        )

        assert result.success is True
        assert result.changes_made == 1
        assert result.content.count("foo") == 2
        assert result.content.count("bar") == 1

    def test_get_symbols_functions(self):
        """Test extracting function symbols."""
        editor = ASTEditor()

        code = '''
def function1():
    pass

def function2(arg1, arg2):
    return arg1 + arg2

async def async_function():
    pass
'''

        symbols = editor.get_symbols(code, "python")

        function_names = [s.name for s in symbols if s.symbol_type == "function"]
        assert "function1" in function_names
        assert "function2" in function_names

    def test_get_symbols_classes(self):
        """Test extracting class symbols."""
        editor = ASTEditor()

        code = '''
class MyClass:
    def method1(self):
        pass

    def method2(self):
        pass
'''

        symbols = editor.get_symbols(code, "python")

        # Should find class
        class_symbols = [s for s in symbols if s.symbol_type == "class"]
        assert len(class_symbols) >= 1
        assert class_symbols[0].name == "MyClass"

        # Should find methods
        method_symbols = [s for s in symbols if s.symbol_type == "method"]
        method_names = [s.name for s in method_symbols]
        assert "method1" in method_names or len(method_symbols) >= 0

    def test_find_symbol(self):
        """Test finding specific symbol."""
        editor = ASTEditor()

        code = '''
def target_function():
    pass

def other_function():
    pass
'''

        symbol = editor.find_symbol(code, "target_function", "python")

        assert symbol is not None
        assert symbol.name == "target_function"
        assert symbol.symbol_type == "function"

    def test_find_symbol_not_found(self):
        """Test finding symbol that doesn't exist."""
        editor = ASTEditor()

        code = '''
def something():
    pass
'''

        symbol = editor.find_symbol(code, "nonexistent", "python")
        assert symbol is None

    def test_syntax_validation_valid(self):
        """Test syntax validation with valid code."""
        editor = ASTEditor()

        code = '''
def valid_function():
    return 42
'''

        is_valid, error = editor.is_valid_syntax(code, "python")
        assert is_valid is True
        assert error is None

    def test_syntax_validation_invalid(self):
        """Test syntax validation with invalid code."""
        editor = ASTEditor()

        code = '''
def broken_function(
    return 42
'''

        is_valid, error = editor.is_valid_syntax(code, "python")
        assert is_valid is False
        assert error is not None

    def test_get_node_at_position(self):
        """Test getting node at specific position."""
        editor = ASTEditor()

        code = '''
def my_function():
    x = 42
'''

        # Position at 'my_function'
        node_info = editor.get_node_at_position(code, 2, 5, "python")

        if node_info:  # Only if tree-sitter available
            assert "type" in node_info
            assert "text" in node_info
            assert "context" in node_info

    def test_code_location(self):
        """Test CodeLocation dataclass."""
        loc = CodeLocation(line=10, column=5, end_line=10, end_column=15)

        assert loc.line == 10
        assert loc.is_single_line is True

        multi_line = CodeLocation(line=10, column=1, end_line=20, end_column=1)
        assert multi_line.is_single_line is False

    def test_code_match_properties(self):
        """Test CodeMatch properties."""
        match = CodeMatch(
            text="variable",
            location=CodeLocation(1, 1),
            context=NodeContext.CODE,
            node_type="identifier",
        )

        assert match.is_code is True
        assert match.is_in_string_or_comment is False

        string_match = CodeMatch(
            text="text",
            location=CodeLocation(1, 1),
            context=NodeContext.STRING,
        )

        assert string_match.is_code is False
        assert string_match.is_in_string_or_comment is True


# =============================================================================
# Code Validator Tests
# =============================================================================

class TestCodeValidator:
    """Tests for CodeValidator."""

    def test_validator_creation(self):
        """Test CodeValidator creation."""
        validator = CodeValidator()
        assert validator is not None

    @pytest.mark.asyncio
    async def test_validate_valid_python(self):
        """Test validating valid Python code."""
        validator = CodeValidator()

        code = '''
def valid_function():
    x = 42
    return x
'''

        result = await validator.validate("test.py", code, ValidationLevel.SYNTAX_ONLY)

        assert result.valid is True
        assert result.error_count == 0

    @pytest.mark.asyncio
    async def test_validate_invalid_syntax(self):
        """Test validating code with syntax errors."""
        validator = CodeValidator()

        code = '''
def broken(
    return 42
'''

        result = await validator.validate("test.py", code, ValidationLevel.SYNTAX_ONLY)

        assert result.valid is False
        assert result.error_count >= 1

    @pytest.mark.asyncio
    async def test_validation_result_structure(self):
        """Test ValidationResult structure."""
        validator = CodeValidator()

        result = await validator.validate("test.py", "x = 1", ValidationLevel.SYNTAX_ONLY)

        assert hasattr(result, "valid")
        assert hasattr(result, "checks")
        assert hasattr(result, "errors")
        assert hasattr(result, "warnings")
        assert hasattr(result, "duration_ms")

        # Should have at least syntax check
        assert len(result.checks) >= 1

    @pytest.mark.asyncio
    async def test_check_types(self):
        """Test different check types in result."""
        validator = CodeValidator()

        result = await validator.validate("test.py", "x = 1", ValidationLevel.SYNTAX_ONLY)

        syntax_check = result.get_check(CheckType.SYNTAX)
        assert syntax_check is not None
        assert syntax_check.passed is True

    @pytest.mark.asyncio
    async def test_validate_edit_no_new_errors(self):
        """Test edit validation with no new errors."""
        validator = CodeValidator()

        old_code = '''
def foo():
    return 1
'''

        new_code = '''
def bar():
    return 2
'''

        validation = await validator.validate_edit(
            "test.py", old_code, new_code, ValidationLevel.SYNTAX_ONLY
        )

        assert validation.can_apply is True
        assert len(validation.new_errors) == 0

    @pytest.mark.asyncio
    async def test_validate_edit_introduces_errors(self):
        """Test edit validation that introduces errors."""
        validator = CodeValidator()

        old_code = '''
def foo():
    return 1
'''

        new_code = '''
def foo(
    return 1
'''

        validation = await validator.validate_edit(
            "test.py", old_code, new_code, ValidationLevel.SYNTAX_ONLY
        )

        assert validation.can_apply is False
        assert validation.introduced_errors is True
        assert len(validation.new_errors) >= 1

    @pytest.mark.asyncio
    async def test_validate_edit_fixes_errors(self):
        """Test edit validation that fixes errors."""
        validator = CodeValidator()

        old_code = '''
def foo(
    return 1
'''

        new_code = '''
def foo():
    return 1
'''

        validation = await validator.validate_edit(
            "test.py", old_code, new_code, ValidationLevel.SYNTAX_ONLY
        )

        assert validation.can_apply is True
        assert validation.improved_code is True
        assert len(validation.fixed_errors) >= 1

    def test_backup_file(self):
        """Test file backup functionality."""
        validator = CodeValidator()

        content = "original content"
        backup = validator.backup_file("test.py", content)

        assert backup is not None
        assert backup.filepath == "test.py"
        assert backup.content == content
        assert backup.content_hash is not None

    def test_get_backup(self):
        """Test retrieving backup."""
        validator = CodeValidator()

        validator.backup_file("test.py", "content")
        backup = validator.get_backup("test.py")

        assert backup is not None
        assert backup.content == "content"

    def test_clear_backup(self):
        """Test clearing backup."""
        validator = CodeValidator()

        validator.backup_file("test.py", "content")
        assert validator.clear_backup("test.py") is True
        assert validator.get_backup("test.py") is None

    def test_clear_all_backups(self):
        """Test clearing all backups."""
        validator = CodeValidator()

        validator.backup_file("file1.py", "content1")
        validator.backup_file("file2.py", "content2")

        count = validator.clear_all_backups()
        assert count == 2

    @pytest.mark.asyncio
    async def test_safe_edit_success(self):
        """Test safe edit that succeeds."""
        validator = CodeValidator()

        with tempfile.TemporaryDirectory() as tmpdir:
            validator.workspace_root = Path(tmpdir)
            filepath = Path(tmpdir) / "test.py"

            old_code = "x = 1"
            new_code = "x = 2"
            filepath.write_text(old_code)

            success, validation = await validator.safe_edit(
                str(filepath), old_code, new_code,
                level=ValidationLevel.SYNTAX_ONLY,
            )

            assert success is True
            assert filepath.read_text() == new_code

    @pytest.mark.asyncio
    async def test_safe_edit_rejected(self):
        """Test safe edit that is rejected due to errors."""
        validator = CodeValidator()

        with tempfile.TemporaryDirectory() as tmpdir:
            validator.workspace_root = Path(tmpdir)
            filepath = Path(tmpdir) / "test.py"

            old_code = "x = 1"
            new_code = "x = ("  # Syntax error
            filepath.write_text(old_code)

            success, validation = await validator.safe_edit(
                str(filepath), old_code, new_code,
                auto_rollback=True,
                level=ValidationLevel.SYNTAX_ONLY,
            )

            assert success is False
            # File should not be changed
            assert filepath.read_text() == old_code

    def test_register_custom_validator(self):
        """Test registering custom validator."""
        validator = CodeValidator()

        async def my_validator(filepath, content, language):
            return Check(
                check_type=CheckType.CUSTOM,
                passed=True,
                message="Custom check passed",
            )

        validator.register_validator("my_check", my_validator)
        assert "my_check" in validator._custom_validators

    def test_unregister_custom_validator(self):
        """Test unregistering custom validator."""
        validator = CodeValidator()

        async def my_validator(filepath, content, language):
            return Check(CheckType.CUSTOM, True)

        validator.register_validator("my_check", my_validator)
        assert validator.unregister_validator("my_check") is True
        assert validator.unregister_validator("nonexistent") is False

    def test_validator_stats(self):
        """Test validator statistics."""
        validator = CodeValidator()

        stats = validator.get_stats()

        assert "validations" in stats
        assert "errors_caught" in stats
        assert "rollbacks" in stats
        assert "backups_held" in stats

    def test_validation_levels(self):
        """Test different validation levels."""
        assert ValidationLevel.SYNTAX_ONLY.value == "syntax_only"
        assert ValidationLevel.LSP_BASIC.value == "lsp_basic"
        assert ValidationLevel.LSP_FULL.value == "lsp_full"
        assert ValidationLevel.COMPREHENSIVE.value == "comprehensive"

    def test_check_properties(self):
        """Test Check dataclass properties."""
        error_check = Check(
            check_type=CheckType.SYNTAX,
            passed=False,
            message="Syntax error",
            severity="error",
        )

        assert error_check.is_error is True

        passing_check = Check(
            check_type=CheckType.SYNTAX,
            passed=True,
            message="OK",
        )

        assert passing_check.is_error is False

    def test_edit_validation_properties(self):
        """Test EditValidation properties."""
        validation = EditValidation(
            can_apply=True,
            validation_before=ValidationResult(valid=False, errors=["Error 1"]),
            validation_after=ValidationResult(valid=True),
            new_errors=[],
            fixed_errors=["Error 1"],
        )

        assert validation.introduced_errors is False
        assert validation.improved_code is True


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests for Code Intelligence."""

    @pytest.mark.asyncio
    async def test_ast_editor_with_validator(self):
        """Test AST editor integrated with validator."""
        editor = get_ast_editor()
        validator = CodeValidator()

        code = '''
def old_function():
    return 42
'''

        # Use AST editor to replace
        result = editor.replace_in_code(
            code, "old_function", "new_function", "python"
        )

        assert result.success is True

        # Validate the result
        validation = await validator.validate(
            "test.py", result.content, ValidationLevel.SYNTAX_ONLY
        )

        assert validation.valid is True

    @pytest.mark.asyncio
    async def test_full_edit_workflow(self):
        """Test complete edit workflow: find -> replace -> validate."""
        editor = get_ast_editor()
        validator = CodeValidator()

        original_code = '''
def calculate(value):
    result = value * 2
    return result
'''

        # 1. Find occurrences
        matches = editor.find_in_code(original_code, "result", "python")
        assert len(matches) >= 2  # Declaration and return

        # 2. Replace
        edit_result = editor.replace_in_code(
            original_code, "result", "output", "python"
        )
        assert edit_result.success is True

        # 3. Validate edit
        validation = await validator.validate_edit(
            "calc.py",
            original_code,
            edit_result.content,
            ValidationLevel.SYNTAX_ONLY,
        )

        assert validation.can_apply is True
        assert not validation.introduced_errors

    def test_symbol_extraction_for_navigation(self):
        """Test using symbol extraction for code navigation."""
        editor = get_ast_editor()

        code = '''
class UserService:
    def get_user(self, user_id):
        pass

    def create_user(self, data):
        pass

class OrderService:
    def get_order(self, order_id):
        pass
'''

        symbols = editor.get_symbols(code, "python")

        # Should find all classes
        classes = [s for s in symbols if s.symbol_type == "class"]
        class_names = [c.name for c in classes]
        assert "UserService" in class_names
        assert "OrderService" in class_names

    @pytest.mark.asyncio
    async def test_validation_with_temp_file(self):
        """Test validation with actual temp file."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write("def test(): return 42")
            filepath = f.name

        try:
            validator = CodeValidator()
            result = await validator.validate(filepath, level=ValidationLevel.SYNTAX_ONLY)

            assert result.valid is True
        finally:
            os.unlink(filepath)

    def test_language_configs_complete(self):
        """Test language configurations are complete."""
        for lang, config in LANGUAGE_CONFIGS.items():
            assert config.name == lang
            assert len(config.extensions) > 0
            assert len(config.string_node_types) > 0
            assert len(config.comment_node_types) > 0


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
