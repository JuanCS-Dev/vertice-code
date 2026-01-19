class BaseTool:
    pass


class ToolResult:
    def __init__(self, success=True, message="", data=None, metadata=None, error=None):
        self.success = success
        self.message = message
        self.data = data
        self.metadata = metadata
        self.error = error


class CleanToolRegistry:
    def __init__(self):
        self.tools = {}

    def register(self, tool):
        name = getattr(tool, "name", tool.__class__.__name__)
        self.tools[name] = tool

    def get(self, name):
        return self.tools.get(name)

    def get_tool(self, name):
        return self.tools.get(name)
