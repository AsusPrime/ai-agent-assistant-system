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
    LLM_BASE_URL: str = "http://localhost:11434/v1"

    DATA_DIR: str = "~/.my_data"
    MEMORY_TURNS: int = 8

    DEBUG: bool = False

    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000
    API_AUTO_APPROVE: bool = False

    WEB_TIMEOUT: float = 10.0
    HTTP_TIMEOUT: float = 15.0
    WEB_MAX_RESULTS: int = 5
    WEB_MAX_TEXT_LEN: int = 8000
    HTTP_MAX_BODY_LEN: int = 8000

    MCP_CONFIG_PATH: str = "~/.akashi/mcp_servers.json"
    MCP_CALL_TIMEOUT: float = 30.0
    MCP_DESC_MAX_LEN: int = 500
    MCP_ERROR_BODY_MAX: int = 800

    PLANNER_MAX_RETRIES: int = 3

    KB_MAX_FILE_BYTES: int = 512 * 1024
    KB_CHUNK_SIZE: int = 500
    KB_CHUNK_OVERLAP: int = 50


settings = Settings()
