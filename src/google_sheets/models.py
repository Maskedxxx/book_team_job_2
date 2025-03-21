# src/google_sheets/models.py

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class QAPair(BaseModel):
    """Модель для пары вопрос-ответ."""
    question: str = ""
    user_answer: str = ""
    llm_response: str = ""

class FormSubmission(BaseModel):
    """Модель для отправки данных формы в Google Sheets."""
    received_at: datetime = None
    processed: bool = False
    qa_pairs: List[QAPair] = []
    updated_at: Optional[datetime] = None
    row_id: str = ""

class SheetDataRequest(BaseModel):
    """Модель для запроса записи данных в Google Sheets."""
    form_submission: FormSubmission
    spreadsheet_id: Optional[str] = None
    sheet_name: Optional[str] = None