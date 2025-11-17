"""Configuration management for qwen-dev-cli."""

import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class Config:
    """Application configuration."""
    
    # HuggingFace Inference API
    hf_token: Optional[str] = None
    hf_model: str = "Qwen/Qwen2.5-Coder-7B-Instruct"
    
    # Ollama (optional local mode)
    ollama_enabled: bool = False
    ollama_model: str = "qwen2.5-coder:7b"
    ollama_base_url: str = "http://localhost:11434"
    
    # Generation settings
    max_tokens: int = 2048
    temperature: float = 0.7
    stream: bool = True
    
    # Context settings
    max_context_files: int = 5
    max_file_size_kb: int = 100
    
    # Gradio UI
    gradio_port: int = 7860
    gradio_share: bool = False
    
    def __post_init__(self):
        """Load environment variables."""
        if self.hf_token is None:
            self.hf_token = os.getenv("HF_TOKEN")
        
        if os.getenv("OLLAMA_ENABLED"):
            self.ollama_enabled = os.getenv("OLLAMA_ENABLED").lower() == "true"
        
        if os.getenv("GRADIO_PORT"):
            self.gradio_port = int(os.getenv("GRADIO_PORT"))
        
        if os.getenv("HF_MODEL"):
            self.hf_model = os.getenv("HF_MODEL")
    
    def validate(self) -> tuple[bool, str]:
        """Validate configuration.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.hf_token and not self.ollama_enabled:
            return False, "HF_TOKEN not set and Ollama not enabled"
        
        return True, ""


# Global config instance
config = Config()
