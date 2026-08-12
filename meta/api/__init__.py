"""Independent external model adapters."""

from .claude_adapter import ClaudeAdapter
from .deepseek_adapter import DeepSeekAdapter
from .openai_adapter import OpenAIAdapter

__all__ = ["ClaudeAdapter", "DeepSeekAdapter", "OpenAIAdapter"]
