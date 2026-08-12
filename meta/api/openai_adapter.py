from .base_adapter import OpenAICompatibleAdapter


class OpenAIAdapter(OpenAICompatibleAdapter):
    provider = "openai"
    env_key = "OPENAI_API_KEY"
    endpoint = "https://api.openai.com/v1/chat/completions"

    def __init__(self, model: str = "gpt-5-mini", timeout: int = 120) -> None:
        super().__init__(model, timeout)
