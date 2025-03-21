# src/google_sheets/services.py

import json
import os
from datetime import datetime
from typing import Dict, Any, List
from src.google_sheets.models import QAPair, FormSubmission
from src.google_sheets.logger import get_logger

logger = get_logger(__name__)

def process_form_data(form_data: Dict[str, Any]) -> FormSubmission:
    """
    Обрабатывает данные формы и создает объект FormSubmission.
    
    Args:
        form_data: Словарь с данными формы из Google Sheets
        
    Returns:
        FormSubmission: Структурированный объект с данными формы
    """
    # Получаем row_id 
    row_id = form_data.get('row_id')
    
    # Создаем список пар вопрос-ответ
    qa_pairs = []
    for question, answer in form_data.items():
        # Пропускаем служебные поля
        if question not in ["row_id", "Отправка ответов", "Отметка времени"]:
            qa_pairs.append(QAPair(
                question=question,
                user_answer=answer
            ))
    
    # Создаем и возвращаем объект FormSubmission
    submission = FormSubmission(
        received_at=datetime.now(),
        processed=False,
        qa_pairs=qa_pairs,
        row_id=row_id
    )
    
    logger.info(f"Создан объект FormSubmission с {len(qa_pairs)} парами вопрос-ответ")
    return submission


def save_form_submission(submission: FormSubmission, filename: str = 'form_data.json') -> str:
    """
    Сохраняет объект FormSubmission в JSON-файл с вложенной структурой data.
    
    Args:
        submission: Объект FormSubmission для сохранения
        filename: Имя файла для сохранения (по умолчанию 'form_data.json')
        
    Returns:
        str: ID сохраненной записи
    """
    # Загружаем существующие данные или создаем новую коллекцию
    json_data = {"data": {}}
    if os.path.exists(filename) and os.path.getsize(filename) > 0:
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
                # Если структура не содержит ключ data, создаем его
                if "data" not in json_data:
                    json_data["data"] = {}
        except json.JSONDecodeError:
            logger.error(f"Ошибка при чтении файла {filename}. Создаем новую коллекцию.")
            json_data = {"data": {}}
    
    # Определяем ID для записи
    entry_id = submission.row_id or str(len(json_data["data"]) + 1)
    
    # Преобразуем объект Pydantic в словарь, который можно сериализовать в JSON
    submission_dict = submission.model_dump()
    # Преобразуем datetime в строку ISO формата
    if submission_dict.get('received_at'):
        submission_dict['received_at'] = submission_dict['received_at'].isoformat()
    if submission_dict.get('updated_at'):
        submission_dict['updated_at'] = submission_dict['updated_at'].isoformat()
    
    # Сохраняем в коллекцию под ключом "data"
    json_data["data"][entry_id] = submission_dict
    
    # Записываем обратно в файл
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Данные сохранены в файл {filename} с ID: {entry_id}")
    return entry_id