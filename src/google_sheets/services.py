# src/google_sheets/services.py

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
import httpx
from src.google_sheets.models import QAPair, FormSubmission
from src.google_sheets.config import settings
from src.config import settings as port_settings
from src.utils.logger import get_logger

logger = get_logger("google_sheets")

def process_form_data(form_data: Dict[str, Any]) -> FormSubmission:
    """
    Обрабатывает данные формы и создает объект FormSubmission.
    
    Преобразует сырые данные из Google Sheets в структурированный объект
    FormSubmission, выделяя вопросы и ответы пользователя.
    
    Args:
        form_data: Словарь с данными формы из Google Sheets
        
    Returns:
        FormSubmission: Структурированный объект с данными формы
    """
    # Получаем row_id и фильтруем служебные поля
    row_id = form_data.get('row_id')
    
    # Список служебных полей, которые нужно исключить
    service_fields = [
        "row_id", 
        "Отправка ответов", 
        "Отметка времени",
        "Рабочая почта для получения результатов"  # ← ДОБАВЛЕНО
    ]
    
    # Добавить извлечение email из данных формы
    user_email = form_data.get('Рабочая почта для получения результатов', '')
    
    # Создаем список пар вопрос-ответ
    qa_pairs = [
        QAPair(question=question, user_answer=answer)
        for question, answer in form_data.items()
        if question not in service_fields
    ]
    
    # Создаем объект FormSubmission
    submission = FormSubmission(
        received_at=datetime.now(),
        processed=False,
        qa_pairs=qa_pairs,
        row_id=row_id,
        user_email=user_email
    )
    
    logger.debug(f"Обработана форма {row_id}: {len(qa_pairs)} пар Q&A, email: {user_email}")
    return submission


def save_form_submission(submission: FormSubmission) -> str:
    """
    Сохраняет объект FormSubmission в JSON-файл.
    
    Загружает существующие данные, добавляет новую запись и сохраняет обратно в файл.
    Обеспечивает сохранение структуры данных с ключом "data" и корректное
    преобразование объектов datetime.
    
    Args:
        submission: Объект FormSubmission для сохранения
        
    Returns:
        str: ID сохраненной записи
    """
    # Настройка путей
    data_dir = Path(settings.data_dir)
    json_file = data_dir / settings.form_data_filename
        
    # Загружаем существующие данные или создаем новую структуру
    json_data = {"data": {}}
    
    if json_file.exists() and json_file.stat().st_size > 0:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
                # Создаем ключ data, если он отсутствует
                json_data.setdefault("data", {})
        except json.JSONDecodeError:
            logger.error(f"Невозможно прочитать JSON из {json_file}. Создаем новую структуру.")
    
    # Определяем ID записи (используем row_id или генерируем новый)
    entry_id = submission.row_id or str(len(json_data["data"]) + 1)
    
    # Преобразуем Pydantic-модель в словарь
    submission_dict = submission.model_dump()
    
    # Преобразуем datetime в строки
    for field in ['received_at', 'updated_at']:
        if submission_dict.get(field):
            submission_dict[field] = submission_dict[field].isoformat()
    
    # Сохраняем запись
    json_data["data"][entry_id] = submission_dict
    
    # Записываем в файл
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Форма {entry_id} сохранена")
    return entry_id

async def process_form_submission_with_llm(row_id: str) -> Dict[str, Any]:
    """
    Обрабатывает форму с помощью LLM сервиса и сохраняет ответы.
    
    Args:
        row_id (str): Идентификатор строки из Google Sheets
        
    Returns:
        Dict[str, Any]: Обновленный объект с ответами LLM
        
    Raises:
        FileNotFoundError: Если файл с данными не найден
        ValueError: Если данные для указанного row_id не найдены
    """
    logger.info(f"Начинаем LLM обработку формы {row_id}")
    
    # Путь к файлу данных
    json_file = Path(settings.data_dir) / settings.form_data_filename
    
    # Проверяем и загружаем данные
    if not json_file.exists():
        raise FileNotFoundError(f"Файл данных не найден: {json_file}")
    
    with open(json_file, "r", encoding="utf-8") as f:
        all_data = json.load(f)
    
    # Проверяем наличие нужной записи
    if "data" not in all_data or row_id not in all_data["data"]:
        raise ValueError(f"Форма с ID {row_id} не найдена")
    
    form_obj = all_data["data"][row_id]
    
    # Пропускаем уже обработанные формы
    if form_obj.get("processed", False):
        logger.info(f"Форма {row_id} уже обработана")
        return form_obj
    
    # Проверяем наличие пар вопрос-ответ
    if not form_obj.get("qa_pairs"):
        logger.warning(f"Форма {row_id} не содержит пар вопрос-ответ")
        return form_obj
    
    processed_count = 0
    # Обрабатываем каждую пару вопрос-ответ
    async with httpx.AsyncClient() as client:
        for i, qa_pair in enumerate(form_obj["qa_pairs"]):
            # Пропускаем первую пару вопрос-ответ
            if i == 0:
                logger.debug(f"Форма {row_id}: первая пара пропущена")
                continue
                
            # Пропускаем пары, уже имеющие ответ LLM
            if qa_pair.get("llm_response"):
                processed_count += 1
                continue
            
            # Формируем запрос для LLM
            prompt = f"Вот вопрос пользователя: {qa_pair.get('question', '')}\nВот как ответил пользователь: {qa_pair.get('user_answer', '')}"
            
            try:
                # Отправляем запрос к LLM сервису
                response = await client.post(
                    f"http://127.0.0.1:{port_settings.llm_service_port}/llm/full-reasoning",
                    json={"question": prompt},
                    timeout=60.0
                )
                response.raise_for_status()
                
                # Сохраняем ответ модели
                form_obj["qa_pairs"][i]["llm_response"] = response.json().get("answer", "")
                processed_count += 1
                logger.debug(f"Форма {row_id}: обработана пара {i+1}")
                
            except Exception as e:
                logger.error(f"Ошибка при обработке пары {i+1} для формы {row_id}: {str(e)}")
    
    # Проверяем завершенность обработки (все кроме первой пары должны быть обработаны)
    total_pairs = len(form_obj["qa_pairs"])
    expected_processed = max(0, total_pairs - 1)  # Исключаем первую пару
    
    if processed_count >= expected_processed and expected_processed > 0:
        form_obj["processed"] = True
        form_obj["updated_at"] = datetime.now().isoformat()
        logger.info(f"Форма {row_id} полностью обработана ({processed_count}/{expected_processed})")
    else:
        logger.warning(f"Форма {row_id} обработана частично ({processed_count}/{expected_processed})")
    
    # Сохраняем результаты
    all_data["data"][row_id] = form_obj
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    
    return form_obj

def get_form_submission_by_row_id(row_id: str) -> Optional[Dict[str, Any]]:
    """
    Находит форму в JSON-данных по ID строки из Google Sheets.
    
    Args:
        row_id (str): Идентификатор строки из Google Sheets
        
    Returns:
        Optional[Dict[str, Any]]: Найденная форма или None, если не найдена
    """
    # Путь к файлу с данными
    json_file = Path(settings.data_dir) / settings.form_data_filename
    
    # Проверяем существование файла
    if not json_file.exists():
        logger.warning(f"Файл данных не существует: {json_file}")
        return None
    
    try:
        # Читаем данные из файла
        with open(json_file, "r", encoding="utf-8") as f:
            all_data = json.load(f)
        
        # Ищем запись по row_id
        result = all_data.get("data", {}).get(row_id)
        if result:
            logger.debug(f"Найдены данные для формы {row_id}")
        else:
            logger.debug(f"Данные для формы {row_id} не найдены")
        return result
    
    except json.JSONDecodeError:
        logger.error(f"Ошибка формата JSON в файле {json_file}")
        return None
    except Exception as e:
        logger.error(f"Ошибка при чтении данных для строки {row_id}: {str(e)}")
        return None