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
from src.utils.logger import get_logger, get_pipeline_logger

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

async def check_services_availability(pipeline_logger) -> bool:
    """
    ЭТАП 1: Проверяет доступность всех необходимых сервисов.
    
    Args:
        pipeline_logger: Экземпляр PipelineLogger для логирования
        
    Returns:
        bool: True если все сервисы доступны, False иначе
    """
    pipeline_logger.stage_start("Проверка доступности сервисов", 1)
    
    services_status = {}
    
    # Список сервисов для проверки
    services_to_check = [
        ("gigachat_init", port_settings.gigachat_init_port, "/token/"),
        ("book_parser", port_settings.book_parser_port, "/parser/parts"),
        ("llm_service", port_settings.llm_service_port, "/docs")
    ]
    
    async with httpx.AsyncClient() as client:
        for service_name, port, endpoint in services_to_check:
            try:
                url = f"http://127.0.0.1:{port}{endpoint}"
                response = await client.get(url, timeout=10.0)
                
                if response.status_code < 500:
                    services_status[service_name] = True
                    pipeline_logger.service_check(service_name, port, True, f"код {response.status_code}")
                else:
                    services_status[service_name] = False
                    pipeline_logger.service_check(service_name, port, False, f"ошибка {response.status_code}")
                    
            except Exception as e:
                services_status[service_name] = False
                pipeline_logger.service_check(service_name, port, False, f"недоступен: {str(e)[:30]}...")
    
    # Проверяем, все ли сервисы доступны
    all_available = all(services_status.values())
    
    if all_available:
        pipeline_logger.stage_finish(1, "Все сервисы доступны")
    else:
        failed_services = [name for name, status in services_status.items() if not status]
        pipeline_logger.stage_finish(1, f"Недоступны: {', '.join(failed_services)}")
    
    return all_available

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
    # Создаем pipeline logger
    pipeline_logger = get_pipeline_logger("google_sheets")
    
    # Запускаем пайплайн в контексте
    with pipeline_logger.pipeline_context(row_id):
        
        # ЭТАП 1: Проверка доступности сервисов
        services_available = await check_services_availability(pipeline_logger)
        if not services_available:
            raise Exception("Не все сервисы доступны для обработки")
        
        # ЭТАП 2: Получение и валидация данных формы
        pipeline_logger.stage_start("Получение данных из Google Sheets", 2)
        
        # Путь к файлу данных
        json_file = Path(settings.data_dir) / settings.form_data_filename
        
        # Проверяем и загружаем данные
        if not json_file.exists():
            raise FileNotFoundError(f"Файл данных не найден: {json_file}")
        
        pipeline_logger.step("Загрузка JSON файла", f"файл: {json_file.name}")
        
        with open(json_file, "r", encoding="utf-8") as f:
            all_data = json.load(f)
        
        # Проверяем наличие нужной записи
        if "data" not in all_data or row_id not in all_data["data"]:
            raise ValueError(f"Форма с ID {row_id} не найдена")
        
        form_obj = all_data["data"][row_id]
        pipeline_logger.step("Валидация данных формы", f"email: {form_obj.get('user_email', 'не указан')}")
        
        # Пропускаем уже обработанные формы
        if form_obj.get("processed", False):
            pipeline_logger.step("Проверка статуса", "форма уже обработана")
            pipeline_logger.stage_finish(2, "Форма уже обработана")
            return form_obj
        
        # Проверяем наличие пар вопрос-ответ
        if not form_obj.get("qa_pairs"):
            pipeline_logger.step("Проверка Q&A пар", "пары отсутствуют")
            pipeline_logger.stage_finish(2, "Нет Q&A пар для обработки")
            return form_obj
        
        total_pairs = len(form_obj["qa_pairs"])
        expected_pairs = max(0, total_pairs - 1)  # Исключаем первую пару
        pipeline_logger.step("Подготовка к обработке", f"будет обработано {expected_pairs} пар из {total_pairs}")
        
        pipeline_logger.stage_finish(2, f"{total_pairs} Q&A пар загружено")
        
        # ЭТАП 3: LLM анализ (получение контекста)
        pipeline_logger.stage_start("LLM анализ", 3)
        
        # Здесь мы пропускаем детальное логирование LLM, так как это делается в llm_service
        pipeline_logger.step("Подготовка контекста", "сбор данных из подглав")
        pipeline_logger.stage_finish(3, "Контекст подготовлен")
        
        # ЭТАП 4: Обработка Q&A пар
        pipeline_logger.stage_start("Обработка Q&A пар", 4)
        
        processed_count = 0
        # Обрабатываем каждую пару вопрос-ответ
        async with httpx.AsyncClient() as client:
            for i, qa_pair in enumerate(form_obj["qa_pairs"]):
                # Пропускаем первую пару вопрос-ответ
                if i == 0:
                    pipeline_logger.step("Пропуск первой пары", "служебная информация")
                    continue
                    
                # Пропускаем пары, уже имеющие ответ LLM
                if qa_pair.get("llm_response"):
                    processed_count += 1
                    pipeline_logger.step(f"Пара {i+1} уже обработана", "пропуск")
                    continue
                
                # Формируем запрос для LLM
                question_preview = qa_pair.get('question', '')[:50]
                pipeline_logger.qa_pair_processed(i+1, total_pairs, question_preview)
                
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
                    
                    pipeline_logger.step(f"LLM ответ получен", f"пара {i+1}/{total_pairs}")
                    
                except Exception as e:
                    pipeline_logger.step(f"Ошибка обработки пары {i+1}", str(e), "error")
        
        pipeline_logger.stage_finish(4, f"Обработано {processed_count}/{expected_pairs} пар")
        
        # ЭТАП 5: Финализация
        pipeline_logger.stage_start("Сохранение результатов", 5)
        
        # Проверяем завершенность обработки (все кроме первой пары должны быть обработаны)
        if processed_count >= expected_pairs and expected_pairs > 0:
            form_obj["processed"] = True
            form_obj["updated_at"] = datetime.now().isoformat()
            pipeline_logger.step("Обновление статуса", "processed = True")
        else:
            pipeline_logger.step("Частичная обработка", f"{processed_count}/{expected_pairs} обработано", "warning")
        
        # Сохраняем результаты
        all_data["data"][row_id] = form_obj
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)
        
        pipeline_logger.step("Запись в файл", f"результаты сохранены в {json_file.name}")
        pipeline_logger.stage_finish(5, f"Форма {row_id} обработана")
        
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