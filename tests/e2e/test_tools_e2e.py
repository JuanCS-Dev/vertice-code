"""
E2E Tests - Tools Infrastructure.

Tests REAL tool imports and structure.
NO MOCKS - tests actual tool classes.
"""



# =============================================================================
# TOOL IMPORTS - FILE OPS
# =============================================================================


class TestFileOperationToolImports:
    """Test file operation tool imports."""

    def test_read_file_tool(self):
        """Can import ReadFileTool."""
        from vertice_cli.tools.file_ops import ReadFileTool
        tool = ReadFileTool()
        assert tool.name == "read_file"

    def test_write_file_tool(self):
        """Can import WriteFileTool."""
        from vertice_cli.tools.file_ops import WriteFileTool
        tool = WriteFileTool()
        assert tool.name == "write_file"

    def test_edit_file_tool(self):
        """Can import EditFileTool."""
        from vertice_cli.tools.file_ops import EditFileTool
        tool = EditFileTool()
        assert tool.name == "edit_file"

    def test_list_dir_tool(self):
        """Can import ListDirectoryTool."""
        from vertice_cli.tools.file_ops import ListDirectoryTool
        tool = ListDirectoryTool()
        assert tool.name == "list_directory"

    def test_delete_file_tool(self):
        """Can import DeleteFileTool."""
        from vertice_cli.tools.file_ops import DeleteFileTool
        tool = DeleteFileTool()
        assert tool.name == "delete_file"


# =============================================================================
# TOOL IMPORTS - TERMINAL
# =============================================================================


class TestTerminalToolImports:
    """Test terminal tool imports."""

    def test_ls_tool(self):
        """Can import LsTool."""
        from vertice_cli.tools.terminal import LsTool
        tool = LsTool()
        assert tool.name == "ls"

    def test_cd_tool(self):
        """Can import CdTool."""
        from vertice_cli.tools.terminal import CdTool
        tool = CdTool()
        assert tool.name == "cd"

    def test_mkdir_tool(self):
        """Can import MkdirTool."""
        from vertice_cli.tools.terminal import MkdirTool
        tool = MkdirTool()
        assert tool.name == "mkdir"

    def test_cat_tool(self):
        """Can import CatTool."""
        from vertice_cli.tools.terminal import CatTool
        tool = CatTool()
        assert tool.name == "cat"


# =============================================================================
# TOOL IMPORTS - GIT
# =============================================================================


class TestGitToolImports:
    """Test git tool imports."""

    def test_git_status_tool(self):
        """Can import GitStatusEnhancedTool."""
        from vertice_cli.tools.git import GitStatusEnhancedTool
        tool = GitStatusEnhancedTool()
        assert "status" in tool.name

    def test_git_diff_tool(self):
        """Can import GitDiffEnhancedTool."""
        from vertice_cli.tools.git import GitDiffEnhancedTool
        tool = GitDiffEnhancedTool()
        assert "diff" in tool.name

    def test_git_commit_tool(self):
        """Can import GitCommitTool."""
        from vertice_cli.tools.git import GitCommitTool
        tool = GitCommitTool()
        assert "commit" in tool.name

    def test_git_log_tool(self):
        """Can import GitLogTool."""
        from vertice_cli.tools.git import GitLogTool
        tool = GitLogTool()
        assert "log" in tool.name


# =============================================================================
# TOOL IMPORTS - CONTEXT
# =============================================================================


class TestContextToolImports:
    """Test context tool imports."""

    def test_get_context_tool(self):
        """Can import GetContextTool."""
        from vertice_cli.tools.context import GetContextTool
        tool = GetContextTool()
        assert "context" in tool.name

    def test_save_session_tool(self):
        """Can import SaveSessionTool."""
        from vertice_cli.tools.context import SaveSessionTool
        tool = SaveSessionTool()
        assert "session" in tool.name or "save" in tool.name


# =============================================================================
# TOOL STRUCTURE TESTS
# =============================================================================


class TestToolBaseInterface:
    """Test tool base interface."""

    def test_tool_has_name(self):
        """Tools have name attribute."""
        from vertice_cli.tools.file_ops import ReadFileTool
        tool = ReadFileTool()
        assert hasattr(tool, 'name')
        assert isinstance(tool.name, str)

    def test_tool_has_description(self):
        """Tools have description."""
        from vertice_cli.tools.file_ops import ReadFileTool
        tool = ReadFileTool()
        assert hasattr(tool, 'description')
        assert len(tool.description) > 0


# =============================================================================
# TOOL BRIDGE TESTS
# =============================================================================


class TestToolBridge:
    """Test TUI ToolBridge."""

    def test_bridge_initialization(self):
        """ToolBridge initializes."""
        from vertice_tui.core.tools_bridge import ToolBridge
        bridge = ToolBridge()
        assert bridge is not None

    def test_bridge_list_tools(self):
        """ToolBridge can list tools."""
        from vertice_tui.core.tools_bridge import ToolBridge
        bridge = ToolBridge()
        tools = bridge.list_tools()
        assert len(tools) > 0

    def test_bridge_get_tool(self):
        """Can get tool from bridge."""
        from vertice_tui.core.tools_bridge import ToolBridge
        bridge = ToolBridge()
        tool = bridge.get_tool("read_file")
        assert tool is not None

    def test_bridge_get_tool_count(self):
        """Bridge reports tool count."""
        from vertice_tui.core.tools_bridge import ToolBridge
        bridge = ToolBridge()
        count = bridge.get_tool_count()
        assert count > 0


# =============================================================================
# TOOL CATEGORIES
# =============================================================================


class TestToolCategories:
    """Test tool categorization."""

    def test_file_ops_tools_exist(self):
        """File operation tools exist."""
        from vertice_cli.tools import file_ops
        assert hasattr(file_ops, 'ReadFileTool')
        assert hasattr(file_ops, 'WriteFileTool')
        assert hasattr(file_ops, 'EditFileTool')
        assert hasattr(file_ops, 'ListDirectoryTool')

    def test_git_tools_exist(self):
        """Git tools exist."""
        from vertice_cli.tools import git
        assert hasattr(git, 'GitStatusEnhancedTool')
        assert hasattr(git, 'GitDiffEnhancedTool')
        assert hasattr(git, 'GitCommitTool')
        assert hasattr(git, 'GitLogTool')

    def test_terminal_tools_exist(self):
        """Terminal tools exist."""
        from vertice_cli.tools import terminal
        assert hasattr(terminal, 'LsTool')
        assert hasattr(terminal, 'CdTool')
        assert hasattr(terminal, 'MkdirTool')
        assert hasattr(terminal, 'CatTool')

    def test_context_tools_exist(self):
        """Context tools exist."""
        from vertice_cli.tools import context
        assert hasattr(context, 'GetContextTool')
        assert hasattr(context, 'SaveSessionTool')


# =============================================================================
# GIT SAFETY TESTS
# =============================================================================


class TestGitSafety:
    """Test git safety features."""

    def test_safety_config_exists(self):
        """Git safety config exists."""
        from vertice_cli.tools.git import get_safety_config
        config = get_safety_config()
        assert config is not None

    def test_validate_git_command_exists(self):
        """Git command validation exists."""
        from vertice_cli.tools.git import validate_git_command
        assert callable(validate_git_command)

    def test_git_inspect_tools(self):
        """Git inspect tools function exists."""
        from vertice_cli.tools.git import get_git_inspect_tools
        tools = get_git_inspect_tools()
        assert len(tools) > 0

    def test_git_mutate_tools(self):
        """Git mutate tools function exists."""
        from vertice_cli.tools.git import get_git_mutate_tools
        tools = get_git_mutate_tools()
        assert len(tools) > 0
