"""
Sync API - Public Synchronous Wrappers for Documentation Agent.

Provides synchronous API for documentation generation, useful for:
- Testing
- Direct usage without async context
- Integration with sync codebases

Note: These wrap async LLM calls with asyncio.run_until_complete().
"""

import asyncio
from typing import Any, Dict


class DocumentationSyncAPI:
    """Synchronous API wrapper for documentation generation."""

    def __init__(self, llm_client: Any):
        """Initialize sync API with LLM client.

        Args:
            llm_client: LLM provider client (must support .generate())
        """
        self.llm_client = llm_client

    def generate_documentation(
        self,
        code: str,
        doc_type: str = "function",
        style: str = "google"
    ) -> Dict[str, Any]:
        """Generate documentation for code snippet (SYNC wrapper).

        Args:
            code: Source code to document
            doc_type: Type of documentation ("function", "class", "module", "dockerfile")
            style: Docstring style ("google", "numpy", "sphinx")

        Returns:
            Dict with keys:
                - success: bool
                - documentation: str (generated docs)
                - error: Optional[str]
        """
        if not code or not code.strip():
            return {
                "success": False,
                "error": "Empty code provided",
                "documentation": ""
            }

        try:
            prompt = f"""Generate {style}-style documentation for this {doc_type}:

```python
{code}
```

Return ONLY the documentation text, no explanations."""

            response = self._run_async(
                self.llm_client.generate(
                    prompt=prompt,
                    max_tokens=2000,
                    temperature=0.3
                )
            )

            return {
                "success": True,
                "documentation": response.strip()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "documentation": ""
            }

    def generate_api_docs(
        self,
        code: str,
        api_type: str = "rest"
    ) -> Dict[str, Any]:
        """Generate API documentation (SYNC wrapper).

        Args:
            code: API route code
            api_type: Type of API ("rest", "graphql", "grpc")

        Returns:
            Dict with success, documentation, error
        """
        try:
            prompt = f"""Generate {api_type.upper()} API documentation for:

```python
{code}
```

Include: endpoints, methods, parameters, responses, examples."""

            response = self._run_async(
                self.llm_client.generate(
                    prompt=prompt,
                    max_tokens=3000,
                    temperature=0.2
                )
            )

            return {
                "success": True,
                "documentation": response.strip()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "documentation": ""
            }

    def generate_readme(
        self,
        project_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate README for project (SYNC wrapper).

        Args:
            project_info: Dict with keys:
                - name: str
                - description: str
                - tech_stack: List[str]
                - features: List[str]

        Returns:
            Dict with success, documentation, error
        """
        try:
            name = project_info.get("name", "Project")
            desc = project_info.get("description", "")
            tech = ", ".join(project_info.get("tech_stack", []))
            features = "\n".join(f"- {f}" for f in project_info.get("features", []))

            prompt = f"""Generate a professional README.md for:

**Project:** {name}
**Description:** {desc}
**Tech Stack:** {tech}
**Features:**
{features}

Include: Installation, Usage, Contributing, License sections."""

            response = self._run_async(
                self.llm_client.generate(
                    prompt=prompt,
                    max_tokens=4000,
                    temperature=0.4
                )
            )

            return {
                "success": True,
                "documentation": response.strip()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "documentation": ""
            }

    def _run_async(self, coro):
        """Run async coroutine synchronously.

        Args:
            coro: Coroutine to run

        Returns:
            Coroutine result
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(coro)


__all__ = ["DocumentationSyncAPI"]
