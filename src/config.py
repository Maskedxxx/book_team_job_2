from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class BaseAppSettings(BaseSettings):
    """
    Базовый класс настроек с общими параметрами для всех сервисов.
    """
    env_name: str = 'local'  
    debug: bool = True 

    model_config = ConfigDict(
        env_file='.env',
        extra='ignore'
    )