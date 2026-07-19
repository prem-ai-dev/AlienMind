from pydantic_settings import BaseSettings, SettingsConfigDict

class EnvData(BaseSettings):
    mongodb_username:str
    mongodb_password:str
    mongodb_clustername:str
    your_secret_code:str
    algorithm:str
    auto_expire_token_in_minutes:int

    model_config=SettingsConfigDict(env_file=".env")

access=EnvData()