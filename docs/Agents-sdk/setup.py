"""
Setup script for Vertice MCP Python SDK

Generated with ❤️ by Vertex AI Codey
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="vertice-mcp",
    version="1.0.0",
    author="Vertice AI Collective",
    author_email="collective@vertice.ai",
    description="Python SDK for Vertice Model Context Protocol - Collective AI Ecosystem",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/vertice-ai/mcp-python",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=[
        "aiohttp>=3.8.0",
        "pydantic>=2.0.0",
        "dataclasses-json>=0.5.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "mypy>=1.0.0",
            "sphinx>=5.0.0",
        ],
        "docs": [
            "sphinx>=5.0.0",
            "sphinx-rtd-theme>=1.2.0",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/vertice-ai/mcp-python/issues",
        "Source": "https://github.com/vertice-ai/mcp-python",
        "Documentation": "https://docs.vertice.ai/mcp-python/",
        "Collective": "https://vertice.ai/collective",
    },
)
