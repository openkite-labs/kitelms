from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application settings
    APP_NAME: str = "kiteLMS"
    APP_VERSION: str = "0.0.1"
    APP_DESCRIPTION: str = "kiteLMS is a learning management system"
    APP_OPENAPI_URL: str = "/openapi.json"
    APP_SCALAR_URL: str = "/scalar"
    APP_DOCS_URL: None | str = None
    APP_REDOC_URL: None | str = None
    APP_DEBUG: bool = False

    # Database settings
    DB_NAME: str = "postgres"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432

    @property
    def DB_URI(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # JWT settings
    JWT_SECRET_KEY: str = "not-very-safe-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS settings
    CORS_ORIGINS: list = ["*"]
    CORS_ALLOW_METHODS: list = ["*"]
    CORS_ALLOW_HEADERS: list = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True

    # Email settings
    EMAIL_HOST: str = "smtp.gmail.com"
    EMAIL_PORT: int = 587
    EMAIL_USER: str = "kite.lms@gmail.com"
    EMAIL_PASSWORD: str = "kite.lms.123"
    EMAIL_FROM: str = "kite.lms@gmail.com"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
