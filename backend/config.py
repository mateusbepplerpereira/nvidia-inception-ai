from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # OpenAI Configuration
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    openai_temperature: float = 0.3
    openai_max_tokens: int = 1500

    # Database Configuration
    database_url: str
    db_host: str = "postgres"
    db_port: int = 5432
    db_user: str = "nvidia_user"
    db_pass: str = "nvidia_pass"
    db_name: str = "nvidia_inception_db"

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True

    # Agent Configuration
    agent_timeout: int = 60
    agent_max_tokens: int = 3000

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra environment variables

settings = Settings()