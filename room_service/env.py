from pydantic import SecretStr
from pydantic_settings import BaseSettings

class Environment(BaseSettings):
  OPENAI_API_KEY: SecretStr

  class Config:
    env_file = ".env"

ENV = Environment()
