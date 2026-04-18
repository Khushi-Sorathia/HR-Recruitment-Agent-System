from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "HR Recruitment Agent Pipeline"

    # Database
    DATABASE_URL: str = "sqlite:///./hr_pipeline.db"

    # LLM — Google Gemini (default for all agents)
    GOOGLE_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # OpenAI (optional fallback)
    OPENAI_API_KEY: str = ""

    # Google Workspace — Gmail OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_CREDENTIALS_FILE: str = "credentials.json"

    # SMTP Fallback (used when Gmail OAuth credentials are not available)
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = "ks.felizina@gmail.com"
    SMTP_PASSWORD: str = "uwkychtbffhbsgqr"
    HR_TEAM_EMAIL: str = "ks.felizina@gmail.com"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
