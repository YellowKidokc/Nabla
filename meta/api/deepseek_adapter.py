from .base_adapter import OpenAICompatibleAdapter


class DeepSeekAdapter(OpenAICompatibleAdapter):
    provider = "deepseek"
    env_key = "DEEPSEEK_API_KEY"
    endpoint = "https://api.deepseek.com/chat/completions"

    def __init__(self, model: str = "deepseek-chat", timeout: int = 120) -> None:
        super().__init__(model, timeout)
