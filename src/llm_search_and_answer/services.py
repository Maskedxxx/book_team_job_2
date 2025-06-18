# src/llm_search_and_answer/services.py

import re
import httpx
import json
import os

from openai import OpenAI
from pydantic import BaseModel
import instructor
from langsmith.wrappers import wrap_openai
from langsmith import traceable, Client

from src.llm_search_and_answer.models import LLMEvaluation
from src.llm_search_and_answer.prompts import SYSTEM_PROMPT_MENTOR_ASSESSMENT
from src.gigachat_init.config import settings
from src.config import settings as port_settings # Общие настройки (для портов из других сервисов)
from src.llm_search_and_answer.models import (
    BookPartReasoning,
    ChapterReasoning,
    SubchapterReasoning
)
from src.utils.logger import get_logger

logger = get_logger("llm_service")

def get_access_token() -> str:
    """
    Делает запрос к локальному эндпоинту, чтобы получить access_token.
    Возвращает строку access_token.
    """
    try:
        url = f"http://127.0.0.1:{port_settings.gigachat_init_port}/token/token"
        response = httpx.get(url, verify=False)
        response.raise_for_status()
        data = response.json()
        logger.debug("Токен получен успешно")
        return data["access_token"]
    except Exception as e:
        logger.error(f"Ошибка при получении access_token: {e}")
        raise
    
def create_llm_client_openai() -> OpenAI:
    """
    Создаёт клиента OpenAI с отключенной проверкой SSL,
    подставляет base_url из settings и токен, полученный от локального эндпоинта.
    """
    token = get_access_token()
    http_client = httpx.Client(verify=False)

    client = OpenAI(
        api_key=token,
        base_url=settings.gigachat_base_url,
        http_client=http_client
    )
    return client

def create_llm_client():
    """
    Создаёт клиента OpenAI с отключенной проверкой SSL и LangSmith трейсингом.
    Подставляет base_url из settings и токен, полученный от локального эндпоинта.
    
    Returns:
        instructor клиент, обёрнутый для трейсинга
    """
    # Получаем токен как обычно
    token = get_access_token()
    
    # Создаём HTTP клиент без проверки SSL
    http_client = httpx.Client(verify=False)
    
    # Создаём базовый OpenAI клиент
    base_openai_client = OpenAI(
        api_key=token, 
        base_url=settings.gigachat_base_url,
        http_client=http_client
    )
    
    # Оборачиваем клиент для LangSmith трейсинга
    wrapped_client = wrap_openai(base_openai_client)
    
    # Создаём instructor клиент из обёрнутого
    client = instructor.from_openai(wrapped_client, mode=instructor.Mode.JSON_SCHEMA)
    
    return client

def create_langsmith_client():
    """
    Создаёт клиента LangSmith для трейсинга.
    
    Returns:
        Client: LangSmith клиент
    """
    return Client(api_key=os.getenv("LANGCHAIN_API_KEY"))

# Создаём глобальный клиент для трейсинга (можно использовать в декораторах)
ls_client = create_langsmith_client()


# --------------------------------------------------------------------
# 3. Запросы к сервису parser (чтение частей, глав, подглав, контента)
# --------------------------------------------------------------------
def fetch_content_parts() -> str:
    """
    Запрашивает у сервиса /parser/parts список всех частей книги.
    Возвращает строку (или JSON-строку), которую потом передадим в LLM.
    """
    try:
        url = f"http://127.0.0.1:{port_settings.book_parser_port}/parser/parts"
        r = httpx.get(url, verify=False)
        r.raise_for_status()
        logger.debug("Получены части книги")
        return r.text  # или json.dumps(r.json())
    except Exception as e:
        logger.error(f"fetch_content_parts: {e}")
        raise

def fetch_chapters_content(part_number: int) -> str:
    """
    Запрашивает у сервиса /parser/parts/{part_number}/chapters
    список глав для указанной части.
    Возвращаем как строку или JSON.
    """
    try:
        url = f"http://127.0.0.1:{port_settings.book_parser_port}/parser/parts/{part_number}/chapters"
        r = httpx.get(url, verify=False)
        r.raise_for_status()
        logger.debug(f"Получены главы для части {part_number}")
        return r.text
    except Exception as e:
        logger.error(f"fetch_chapters_content: {e}")
        raise

def fetch_subchapters_content(part_number: int, chapter_number: int) -> str:
    """
    Запрашивает у сервиса /parser/parts/{part_number}/chapters/{chapter_number}/subchapters
    список подглав.
    """
    try:
        url = f"http://127.0.0.1:{port_settings.book_parser_port}/parser/parts/{part_number}/chapters/{chapter_number}/subchapters"
        r = httpx.get(url, verify=False)
        r.raise_for_status()
        logger.debug(f"Получены подглавы для части {part_number}, главы {chapter_number}")
        return r.text
    except Exception as e:
        logger.error(f"fetch_subchapters_content: {e}")
        raise

# ==========================================
# TODO: ТРЕБУЕТСЯ РЕАЛИЗАЦИЯ SUMMARY СТРАНИЦ
# ==========================================
"""
TODO: Для полной работы системы необходимо реализовать:

1. ГЕНЕРАЦИЯ SUMMARY ДЛЯ КАЖДОЙ СТРАНИЦЫ:
   - Обработать все страницы в kniga_full_content.json
   - Создать summary для каждой страницы используя LLM
   - Добавить поле "summary" в каждый объект страницы
   
2. СТРУКТУРА СТРАНИЦЫ ДОЛЖНА БЫТЬ:
   {
     "pageNumber": 47,
     "content": "полный текст страницы...",
     "summary": "краткое описание содержимого страницы...",  # <- ДОБАВИТЬ
     "metadata": {...}
   }

3. ПОСЛЕ РЕАЛИЗАЦИИ:
   - Метод fetch_subchapter_text() будет корректно работать с summary страниц
   - Контекст для LLM станет более детализированным
   - Возможна гибкая настройка уровня детализации (summary подглавы VS summary страниц)

4. АЛЬТЕРНАТИВЫ РЕАЛИЗАЦИИ:
   - Использовать GigaChat для автоматической генерации summary
   - Создать отдельный скрипт для обработки всех страниц
   - Реализовать ленивую генерацию summary при первом обращении
"""

# ==========================================
# ВРЕМЕННОЕ РЕШЕНИЕ: SUMMARY ПОДГЛАВ
# ==========================================

def fetch_subchapter_text_original(subchapter_number: str) -> str:
    """
    ОРИГИНАЛЬНЫЙ МЕТОД - правильно спроектирован для работы с summary страниц.
    
    НЕ ИСПОЛЬЗУЕТСЯ пока не будут реализованы summary для каждой страницы.
    Оставлен как эталон правильной архитектуры.
    
    Ожидает что в kniga_full_content.json у каждой страницы есть поле "summary".
    """
    try:
        url = f"http://127.0.0.1:{port_settings.book_parser_port}/parser/subchapters/{subchapter_number}/content"
        r = httpx.get(url, verify=False)
        r.raise_for_status()
        raw_text = r.text

        data = json.loads(raw_text)
        if "content" in data and isinstance(data["content"], dict):
            data = data["content"]

        subchapter_title = data.get("subchapter_title", "Неизвестный заголовок")
        pages = data.get("pages", [])

        # Извлекаем номера страниц
        page_numbers = [str(page.get("page_number", "")) for page in pages if page.get("page_number") is not None]
        
        # ЗДЕСЬ БУДЕТ РАБОТАТЬ КОГДА ДОБАВЯТСЯ SUMMARY СТРАНИЦ
        page_summaries = [
            f"{page.get('page_number')}: {page.get('summary', '').strip()}" 
            for page in pages if page.get("page_number") is not None
        ]

        joined_summaries = ',\n '.join(page_summaries)

        formatted_text = (
            f"Контекст: вот имя подглавы <title>{subchapter_title}</title>,\n\n"
            f"Вот номера страницы этой подглавы <number_pages>{', '.join(page_numbers)}</number_pages>,\n\n"
            f"Вот выжимка текста каждой страницы: \n<summary>{joined_summaries}</summary>"
        )

        logger.debug(f"Получен контент подглавы {subchapter_number}: {len(pages)} страниц")
        return formatted_text
    except Exception as e:
        logger.error(f"fetch_subchapter_text_original: {e}")
        raise


def fetch_subchapter_text(subchapter_number: str) -> str:
    """
    ВРЕМЕННАЯ РЕАЛИЗАЦИЯ: использует summary подглавы вместо summary страниц.
    
    Эта функция будет заменена на fetch_subchapter_text_original() 
    после реализации summary для каждой страницы.
    """
    try:
        # 1. Получаем данные о страницах от API
        url = f"http://127.0.0.1:{port_settings.book_parser_port}/parser/subchapters/{subchapter_number}/content"
        r = httpx.get(url, verify=False)
        r.raise_for_status()
        raw_text = r.text

        data = json.loads(raw_text)
        if "content" in data and isinstance(data["content"], dict):
            data = data["content"]

        subchapter_title = data.get("subchapter_title", "Неизвестный заголовок")
        pages = data.get("pages", [])

        # 2. Извлекаем номера страниц
        page_numbers = [str(page.get("page_number", "")) for page in pages if page.get("page_number") is not None]

        # 3. ВРЕМЕННОЕ РЕШЕНИЕ: используем summary подглавы
        subchapter_summary = get_subchapter_summary_from_knowmap(subchapter_number)

        # 4. Формируем текст в том же формате что ожидает LLM
        formatted_text = (
            f"Контекст: вот имя подглавы <title>{subchapter_title}</title>,\n\n"
            f"Вот номера страницы этой подглавы <number_pages>{', '.join(page_numbers)}</number_pages>,\n\n"
            f"Вот выжимка текста каждой страницы: \n<summary>{subchapter_summary}</summary>"
        )

        logger.debug(f"Получен контент подглавы {subchapter_number}: {len(pages)} страниц, используется summary подглавы")
        return formatted_text
        
    except Exception as e:
        logger.error(f"fetch_subchapter_text: {e}")
        raise


def get_subchapter_summary_from_knowmap(subchapter_number: str) -> str:
    """
    ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ: получает summary подглавы из know_map_data.
    
    Будет удалена после реализации summary для страниц.
    """
    try:
        from src.book_parser.services import load_json
        from src.book_parser.config import settings as book_settings
        from pathlib import Path
        
        know_map_path = Path(book_settings.know_map_path)
        know_map_data = load_json(know_map_path)
        
        def find_subchapter_summary(obj):
            """Рекурсивно ищет подглаву по номеру и возвращает её summary."""
            if isinstance(obj, dict):
                if str(obj.get("subchapter_number")) == str(subchapter_number):
                    summary = obj.get("summary", "")
                    return summary
                
                for value in obj.values():
                    result = find_subchapter_summary(value)
                    if result:
                        return result
                        
            elif isinstance(obj, list):
                for item in obj:
                    result = find_subchapter_summary(item)
                    if result:
                        return result
            
            return None
        
        summary = find_subchapter_summary(know_map_data)
        if summary:
            return summary
        else:
            logger.warning(f"Summary для подглавы {subchapter_number} не найден")
            return f"Краткое описание для подглавы {subchapter_number} недоступно"
            
    except Exception as e:
        logger.error(f"Ошибка получения summary для подглавы {subchapter_number}: {e}")
        return f"Ошибка получения краткого описания: {str(e)}"


# ==========================================
# ПЛАН МИГРАЦИИ
# ==========================================
"""
ПЛАН ПЕРЕХОДА НА ПОЛНУЮ РЕАЛИЗАЦИЮ:

1. ТЕКУЩЕЕ СОСТОЯНИЕ:
   ✅ fetch_subchapter_text() - работает с summary подглав
   ✅ LLM получает контекст с заполненными summary
   ✅ Пайплайн функционирует корректно

2. СЛЕДУЮЩИЕ ШАГИ:
   🔲 Создать скрипт генерации summary для всех страниц
   🔲 Обновить kniga_full_content.json с новыми summary
   🔲 Переключить fetch_subchapter_text() на оригинальную логику
   🔲 Удалить временные функции
   🔲 Протестировать работу с summary страниц

3. ПРЕИМУЩЕСТВА ПОСЛЕ МИГРАЦИИ:
   - Более детализированный контекст для LLM
   - Возможность работы на уровне отдельных страниц
   - Лучшая точность ответов для специфических вопросов
"""

# --------------------------------------------------------------------
# 4. Утилита для "робастного" парсинга JSON
# --------------------------------------------------------------------
def robust_json_parse(model: BaseModel, text: str) -> BaseModel:
    """
    Пытается распарсить JSON, исправляя распространенные ошибки GigaChat.
    Возвращает объект model (pydantic-модель).
    """
    try:
        return model.model_validate_json(text)
    except Exception as e:
        logger.debug(f"Первичный парсинг не удался: {e}")

        # Попытка 1: Добавить закрывающую фигурную скобку, если её нет
        if not text.strip().endswith("}"):
            text += "}"

        # Попытка 2: Удаляем "мусор" после последней запятой или }
        text = re.sub(r"[,}]\s*[^{}\[\],]*$", "}", text)

        # Попытка 3. Убрать всё после последнего }
        index = text.rfind("}")
        if index > 0:
            text = text[:index+1]

        # Попытка 4: Убираем незаконченные строки, etc.
        lines = text.split('\n')
        filtered_lines = []
        for line in lines:
            if ':' in line:
                filtered_lines.append(line)
        text = '\n'.join(filtered_lines)
        index = text.rfind("}")
        if index > 0:
            text = text[:index+1]

        try:
            return model.model_validate_json(text)
        except Exception as e2:
            logger.error(f"Попытка исправления JSON не удалась: {e2}")
            logger.debug(f"Исправленный текст: {text}")
            raise

# --------------------------------------------------------------------
# 5. Функции для взаимодействия с LLM на каждом шаге
# --------------------------------------------------------------------
def get_book_part_reasoning(
    client,
    system_prompt: str,
    content_parts: str,
    question_user: str,
) -> BookPartReasoning:
    """
    Шаг 1: Выбор части книги.
    Парсим ответ в формате BookPartReasoning (pydantic).
    """
    try:
        response = client.chat.completions.create(
            model="GigaChat-Max",
            response_model=BookPartReasoning,
            temperature=0,
            messages=[
                {"role": "system", "content": f"ИНСТРУКЦИИ: {system_prompt}"},
                {"role": "user", "content": (
                    f"Описания частей книги: {content_parts}\n"
                    f"Вопрос пользователя: {question_user}"
                    """
                    \nНАПОМИНАЮ pydantic СХЕМУ ОТВЕТА:
                    {
                        "initial_analysis": "...",
                        "chapter_comparison": "...",
                        "final_answer": "...",
                        "selected_part": 2
                    }
                    """
                )}
            ],
        )
        return response
    except Exception as e:
        logger.error(f"Ошибка при выполнении запроса: {e}")
        raise

def get_chapter_reasoning(
    client,
    system_prompt: str,
    chapters_content: str,
    question_user: str
) -> ChapterReasoning:
    """
    Шаг 2: Выбор конкретной главы.
    """
    response = client.chat.completions.create(
        model="GigaChat-Max",
        response_model=ChapterReasoning,
        temperature=0,
        messages=[
            {"role": "system", "content": f"ИНСТРУКЦИИ: {system_prompt}"},
            {"role": "user", "content": (
                f"Описания глав (part): {chapters_content}\n"
                f"Вопрос пользователя: {question_user}"
                """\nНАПОМИНАЮ pydantic СХЕМУ ОТВЕТА:
                {
                    "preliminary_analysis": "...",
                    "chapter_analysis": "...",
                    "final_reasoning": "...",
                    "selected_chapter": 4
                }"""
            )}
        ],
    )
    return response

def get_subchapter_reasoning(
    client,
    system_prompt: str,
    subchapters_content: str,
    question_user: str
) -> SubchapterReasoning:
    """
    Шаг 3: Выбор подглавы.
    """
    response = client.chat.completions.create(
        model="GigaChat-Max",
        response_model=SubchapterReasoning,
        temperature=0,
        messages=[
            {"role": "system", "content": f"ИНСТРУКЦИИ: {system_prompt}"},
            {"role": "user", "content": (
                f"Описания подглав (chapter): {subchapters_content}\n"
                f"Вопрос пользователя: {question_user}"
                """\nНАПОМИНАЮ pydantic СХЕМУ ОТВЕТА:
                {
                    "preliminary_analysis": "...",
                    "subchapter_analysis": "...",
                    "final_reasoning": "...",
                    "selected_subchapter": "3.2"
                }"""
            )}
        ],
    )
    return response

@traceable(client=ls_client, project_name="llamaindex_test", run_type = "retriever")
def get_final_answer(
    client,
    system_prompt: str,
    final_content: str,
    question_user: str
) -> str:
    """
    Шаг 4: Формируем итоговый ответ на вопрос, используя финальный контент (извлечённый текст).
    """
    try:
        response = client.chat.completions.create(
            model="GigaChat-2-Max",
            response_model=LLMEvaluation,  # ← Используем новую модель
            temperature=0.2,
            messages=[
                {"role": "system", "content": f"ИНСТРУКЦИИ: {system_prompt}"},
                {"role": "user", "content": (
                    f"Финальный контент (извлечённый из страниц): <content_book>{final_content}</content_book>\n"
                    f"Вопрос к пользователю: {question_user}\n"
                    "Ответь согласно ИНСТРУКЦИИ в формате JSON:"
                )}
            ],
        )
        
        # Форматируем ответ: оценка в начале, потом обоснование
        formatted_response = f"ИТОГОВАЯ ОЦЕНКА: {response.evaluation}\n\n{response.analysis_text}"
        logger.info(f"Получен финальный ответ: {response.evaluation}")
        return formatted_response
        
    except Exception as e:
        logger.error(f"Ошибка при получении финального ответа: {e}")
        # Возвращаем базовый ответ в случае ошибки
        return f"ИТОГОВАЯ ОЦЕНКА: НЕВЕРНО\n\nПроизошла ошибка при анализе ответа. Обратитесь к куратору."

# --------------------------------------------------------------------
# 6. Пример комплексной функции (все 4 шага) — опционально
# --------------------------------------------------------------------
def run_full_reasoning_pipeline(user_question: str) -> dict:
    logger.info("Запуск LLM пайплайна")

    # Получаем список подглав из конфигурации
    available_subchapters = port_settings.available_subchapters
    logger.info(f"Используем подглавы из конфига: {available_subchapters}")

    # Создаем LLM-клиент для финального ответа
    client_openai = create_llm_client()

    # Получаем тексты для всех подглав и объединяем их
    final_contents = []
    for subchapter in available_subchapters:
        try:
            content = fetch_subchapter_text(subchapter)
            # Обрамляем текст подглавы идентификатором для удобства в финальном контенте
            final_contents.append(f"<content_subchapter id='{subchapter}'>\n{content}\n</content_subchapter>")
            logger.debug(f"Обработана подглава {subchapter}")
        except Exception as e:
            logger.error(f"Ошибка получения текста для подглавы {subchapter}: {e}")

    # Объединяем все тексты в один итоговый контент
    combined_final_content = "\n".join(final_contents)
    logger.debug(f"Собран контент из {len(final_contents)} подглав")
    
    # Формируем финальный ответ, используя объединенный контент и вопрос пользователя
    final_answer_text = get_final_answer(
        client_openai,
        SYSTEM_PROMPT_MENTOR_ASSESSMENT,
        combined_final_content,
        user_question
    )

    logger.info("LLM пайплайн завершен")
    return {
        "selected_subchapters": available_subchapters,
        "combined_final_content": combined_final_content,
        "final_answer": final_answer_text
    }
    
if __name__ == "__main__":
    run_full_reasoning_pipeline("вопрос: Почему отслеживание работает - назовите 4 урока о которых говорит автор. Ответ: Урок первый : не каждый реагирует на процесс обучения или не так как хотелось бы организации. Урок 2; между пониманием и действием дистанция огромного размера. Урок 3: люди не становятся лучше без отслеживания")