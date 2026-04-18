import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "HR Recruitment Agent Pipeline"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./hr_pipeline.db") # Fallback to sqlite for ease of local testing
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.mock.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "mock_key_for_now")
    
    # Google API Config
    GOOGLE_CREDENTIALS_FILE: str = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
