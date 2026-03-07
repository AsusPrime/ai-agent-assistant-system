from pydantic_ai.models import Model

from config import settings


def get_model() -> Model:
    if settings.LLM_PROVIDER == "gemini":
        if not settings.API_KEY or not settings.API_KEY.strip():
            raise ValueError(
                "Gemini provider requires an API key. Set GOOGLE_API_KEY in your .env file (in the project root)."
            )
        from pydantic_ai.models.google import GoogleModel
        from pydantic_ai.providers.google import GoogleProvider

        return GoogleModel(
            settings.MODEL_NAME, provider=GoogleProvider(api_key=settings.API_KEY)
        )
    elif settings.LLM_PROVIDER == "ollama":
        from pydantic_ai.models.openai import OpenAIChatModel

        return OpenAIChatModel(
            settings.MODEL_NAME,
            base_url="http://localhost:11434/v1",
            api_key="ollama",
        )
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {settings.LLM_PROVIDER}")
