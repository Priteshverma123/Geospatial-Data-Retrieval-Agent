import os

from dotenv import load_dotenv


class Config:
    DEBUG = False
    TESTING = False
    FILE_TYPE = os.getenv("FILE_TYPE", "pdf,image")  # pdf,image,docx



class DevelopmentConfig(Config):
    DEBUG = True
    ENV = "development"
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    TEMPERATURE=os.getenv("TEMPERATURE")
    LLM_PROVIDER=os.getenv("LLM_PROVIDER")
    LLM_MODEL_NAME=os.getenv("LLM_MODEL_NAME")
    EMBEDDING_PROVIDER=os.getenv("EMBEDDING_PROVIDER")
    EMBEDDING_MODEL_NAME=os.getenv("EMBEDDING_MODEL_NAME")
    NEWS_API_KEY=os.getenv("NEWS_API_KEY")
    NEWS_API_URL=os.getenv("NEWS_API_URL")
    CLIENT_ID=os.getenv("CLIENT_ID")
    CLIENT_SECRET=os.getenv("CLIENT_SECRET")
    
class ProductionConfig(Config):
    ENV = "production"


class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    ENV = "testing"


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}


def load_env_variables():
    """Load environment variables from .env file."""

    load_dotenv(dotenv_path="mage_retrieval\.env")
    env_name = os.getenv("FLASK_ENV", "development")
    return env_name


env_name = load_env_variables()
