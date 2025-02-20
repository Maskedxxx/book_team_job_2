# src/llm_search_and_answer/services.py

import re
import httpx

from openai import OpenAI
from pydantic import BaseModel
import instructor

from src.llm_search_and_answer.prompts import SYSTEM_PROMPT_PART, SYSTEM_PROMPT_CHAPTER, SYSTEM_PROMPT_SUBCHAPTER, SYSTEM_PROMPT_FINAL
from src.gigachat_init.config import settings
from src.llm_search_and_answer.models import (
    BookPartReasoning,
    ChapterReasoning,
    SubchapterReasoning
)
from src.llm_search_and_answer.logger import get_logger

logger = get_logger(__name__)

def get_access_token() -> str:
    """
    Делает запрос к локальному эндпоинту, чтобы получить access_token.
    Возвращает строку access_token.
    """
    try:
        response = httpx.get("http://127.0.0.1:8000/token/token", verify=False)
        response.raise_for_status()
        data = response.json()
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
    Создаёт клиента OpenAI с отключенной проверкой SSL,
    подставляет base_url из settings и токен, полученный от локального эндпоинта.
    """
    token = get_access_token()
    http_client = httpx.Client(verify=False)

    client = instructor.from_openai(OpenAI(api_key=token, base_url=settings.gigachat_base_url,http_client=http_client), 
                                    mode=instructor.Mode.JSON_SCHEMA)
    return client


# --------------------------------------------------------------------
# 3. Запросы к сервису parser (чтение частей, глав, подглав, контента)
# --------------------------------------------------------------------
def fetch_content_parts() -> str:
    """
    Запрашивает у сервиса /parser/parts список всех частей книги.
    Возвращает строку (или JSON-строку), которую потом передадим в LLM.
    """
    try:
        url = "http://127.0.0.1:8001/parser/parts"
        r = httpx.get(url, verify=False)
        r.raise_for_status()
        # Допустим, parser возвращает JSON со списком частей,
        # мы можем либо вернуть r.text, либо сериализовать в строку нужного формата
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
        url = f"http://127.0.0.1:8001/parser/parts/{part_number}/chapters"
        r = httpx.get(url, verify=False)
        r.raise_for_status()
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
        url = f"http://127.0.0.1:8001/parser/parts/{part_number}/chapters/{chapter_number}/subchapters"
        r = httpx.get(url, verify=False)
        r.raise_for_status()
        return r.text
    except Exception as e:
        logger.error(f"fetch_subchapters_content: {e}")
        raise

def fetch_subchapter_text(subchapter_number: str) -> str:
    """
    Запрашивает у сервиса /parser/subchapters/{subchapter_number}/content
    текстовое содержимое указанной подглавы.
    """
    try:
        url = f"http://127.0.0.1:8001/parser/subchapters/{subchapter_number}/content"
        r = httpx.get(url, verify=False)
        r.raise_for_status()
        return r.text
    except Exception as e:
        logger.error(f"fetch_subchapter_text: {e}")
        raise

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
        print(f"Первичный парсинг не удался: {e}")
        print(f"Исходный текст: {text}")

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
            print(f"Попытка исправления не удалась: {e2}")
            print(f"Исправленный текст: {text}")
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
        logger.warning(f"Ошибка при выполнении запроса: {e}")
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

def get_final_answer(
    client: OpenAI,
    system_prompt: str,
    final_content: str,
    question_user: str
) -> str:
    """
    Шаг 4: Формируем итоговый ответ на вопрос, используя финальный контент (извлечённый текст).
    """
    response = client.chat.completions.create(
        model="GigaChat-Max",
        temperature=0.2,
        messages=[
            {"role": "system", "content": f"ИНСТРУКЦИИ: {system_prompt}"},
            {"role": "user", "content": (
                f"Финальный контент (извлечённый из страниц): <content_book>{final_content}</content_book>\n"
                f"Вопрос пользователя: {question_user}\n"
                "Ответь согласно ИНСТРУКЦИИ:"
            )}
        ],
    )
    return response.choices[0].message.content

# --------------------------------------------------------------------
# 6. Пример комплексной функции (все 4 шага) — опционально
# --------------------------------------------------------------------
def run_full_reasoning_pipeline(user_question: str) -> dict:
    """
    Примерная функция, которая последовательно выполняет все 4 шага:
    1) получает список частей -> get_book_part_reasoning
    2) получает главы выбранной части -> get_chapter_reasoning
    3) получает подглавы выбранной главы -> get_subchapter_reasoning
    4) извлекает текст подглавы -> get_final_answer

    Возвращает итоговый словарь с данными рассуждения и финальным ответом.
    Это просто демонстрация; на практике вы можете сделать несколько эндпоинтов.
    """

    logger.info("Запуск полного пайплайна LLM-рассуждения...")

    # 0) Создаём LLM-клиент
    client_openai = create_llm_client_openai()
    client = create_llm_client()

    # ---------------------------------------
    # ШАГ 1: Получаем все части из parser
    # ---------------------------------------
    content_parts = fetch_content_parts()
    # (SYSTEM_PROMPT_PART — ваш системный промпт для шага 1)
    SYSTEM_PROMPT_PART_1 = SYSTEM_PROMPT_PART
    part_reasoning = get_book_part_reasoning(
        client,
        SYSTEM_PROMPT_PART_1,
        content_parts,
        user_question
    )
    selected_part = part_reasoning.selected_part
    logger.info(f"Шаг 1 завершён. Выбранная часть книги: {selected_part}")

    # ---------------------------------------
    # ШАГ 2: Получаем главы для выбранной части
    # ---------------------------------------
    chapters_content = fetch_chapters_content(selected_part)
    SYSTEM_PROMPT_CHAPTER_1 = SYSTEM_PROMPT_CHAPTER
    chapter_reasoning = get_chapter_reasoning(
        client,
        SYSTEM_PROMPT_CHAPTER_1,
        chapters_content,
        user_question
    )
    selected_chapter = chapter_reasoning.selected_chapter
    logger.info(f"Шаг 2 завершён. Выбранная глава: {selected_chapter}")

    # ---------------------------------------
    # ШАГ 3: Получаем подглавы для выбранной главы
    # ---------------------------------------
    subchapters_content = fetch_subchapters_content(selected_part, selected_chapter)
    SYSTEM_PROMPT_SUBCHAPTER_1 = SYSTEM_PROMPT_SUBCHAPTER
    subchapter_reasoning = get_subchapter_reasoning(
        client,
        SYSTEM_PROMPT_SUBCHAPTER_1,
        subchapters_content,
        user_question
    )
    selected_subchapter = subchapter_reasoning.selected_subchapter
    logger.info(f"Шаг 3 завершён. Выбранная подглава: {selected_subchapter}")

    # ---------------------------------------
    # ШАГ 4: Получаем содержимое подглавы и формируем финальный ответ
    # ---------------------------------------
    final_content = fetch_subchapter_text(selected_subchapter)
    SYSTEM_PROMPT_FINAL_1 = SYSTEM_PROMPT_FINAL
    final_answer_text = get_final_answer(
        client_openai,
        SYSTEM_PROMPT_FINAL_1,
        final_content,
        user_question
    )
    logger.info(f"Шаг 4 завершён. Итоговый ответ:\n{final_answer_text}")

    # Собираем всё в структуру для возврата
    return {
        "part_reasoning": part_reasoning,
        "chapter_reasoning": chapter_reasoning,
        "subchapter_reasoning": subchapter_reasoning,
        "final_answer": final_answer_text
    }
