# src/google_sheets/config.py

from src.config import BaseAppSettings
from pydantic import ConfigDict

class GoogleSheetsSettings(BaseAppSettings):
    """
    Настройки для сервиса Google Sheets.
    """
    data_dir: str
    form_data_filename: str

    model_config = ConfigDict(
        env_file='.env',
        env_prefix='GOOGLE_SHEETS_'
    )

settings = GoogleSheetsSettings()