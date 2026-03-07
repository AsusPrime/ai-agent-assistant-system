from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import find_dotenv


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=find_dotenv(filename=".env", usecwd=True),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    LLM_PROVIDER: str = "gemini"
    API_KEY: str = ""
    MODEL_NAME: str = "gemini-2.0-flash"


settings = Settings()
