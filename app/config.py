from starlette.config import Config

config = Config(".env")

SECRET_KEY: str = config("SECRET_KEY", cast=str)
