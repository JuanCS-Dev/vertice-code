"""Re-export from canonical location for backward compatibility."""

class OpenRouterProvider:
    def __init__(self, model_name=None, **kwargs):
        self.model_name = model_name
    def is_available(self):
        return False
    async def generate(self, messages, **kwargs):
        return "Stub response"
    async def stream_generate(self, messages, **kwargs):
        for chunk in ["Stub ", "response"]:
            yield chunk  # noqa: F403
