"""Application configuration management using Pydantic Settings and python-dotenv."""

from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

# Determine project backend root for env loading
BACKEND_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BACKEND_DIR / ".env"


class Settings(BaseSettings):
    """Runtime configuration validated from environment variables."""

    # LLM Settings (OpenAI-compatible)
    llm_api_key: str = Field(default="", alias="LLM_API_KEY")
    llm_base_url: str = Field(default="https://api.openai.com/v1", alias="LLM_BASE_URL")
    llm_model: str = Field(default="gpt-4o", alias="LLM_MODEL")

    # Server Settings
    backend_port: int = Field(default=8001, alias="BACKEND_PORT")
    backend_host: str = Field(default="127.0.0.1", alias="BACKEND_HOST")
    cors_origins: str = Field(
        default="http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173,http://127.0.0.1:5174",
        alias="CORS_ORIGINS",
    )

    # Operational & Token Safeguards
    max_upload_size_mb: int = Field(default=20, alias="MAX_UPLOAD_SIZE_MB")
    max_tool_iterations: int = Field(default=3, alias="MAX_TOOL_ITERATIONS")  # Reduced to 3 to strictly minimize token calls
    max_output_tokens: int = Field(default=350, alias="MAX_OUTPUT_TOKENS")    # Hard cap on LLM response length
    max_history_turns: int = Field(default=3, alias="MAX_HISTORY_TURNS")      # Keep only recent relevant context
    default_sample_rows: int = Field(default=5, alias="DEFAULT_SAMPLE_ROWS")

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.exists() else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> List[str]:
        """Parsed list of allowed CORS origins."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    def is_llm_configured(self) -> bool:
        """Check if an actual LLM key has been provided."""
        placeholder_indicators = {
            "",
            "your_api_key_here",
            "your_key_here",
            "your-api-key",
            "replace_me",
        }
        return bool(self.llm_api_key and self.llm_api_key.strip() not in placeholder_indicators)


# Singleton settings instance
settings = Settings()
