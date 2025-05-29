# src/llm_search_and_answer/services.py

import re
import httpx
import json

from openai import OpenAI
from pydantic import BaseModel
import instructor

from src.llm_search_and_answer.models import LLMEvaluation
from src.llm_search_and_answer.prompts import SYSTEM_PROMPT_MENTOR_ASSESSMENT
from src.gigachat_init.config import settings
from src.config import settings as port_settings # Общие настройки (для портов из других сервисов)
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
        url = f"http://127.0.0.1:{port_settings.gigachat_init_port}/token/token"
        response = httpx.get(url, verify=False)
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
        url = f"http://127.0.0.1:{port_settings.book_parser_port}/parser/parts"
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
        url = f"http://127.0.0.1:{port_settings.book_parser_port}/parser/parts/{part_number}/chapters"
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
        url = f"http://127.0.0.1:{port_settings.book_parser_port}/parser/parts/{part_number}/chapters/{chapter_number}/subchapters"
        r = httpx.get(url, verify=False)
        r.raise_for_status()
        return r.text
    except Exception as e:
        logger.error(f"fetch_subchapters_content: {e}")
        raise

def fetch_subchapter_text(subchapter_number: str) -> str:
    """
    Запрашивает у сервиса /parser/subchapters/{subchapter_number}/content
    текстовое содержимое указанной подглавы, выполняет предобработку и возвращает
    структурированный текст с префиксами и постфиксами, удобными для понимания LLM.
    
    Из полученного объекта:
      - Извлекается subchapter_title,
      - Из списка pages берутся номера страниц и summary каждой страницы.
      
    Формат итогового текста:
      Контекст: вот имя главы <subchapter_title>, вот номера страницы этой главы <номера через запятую>, 
      вот выжимка текста каждой страницы: <Номер страницы: summary, Номер страницы: summary, ...>.
      
      Содержимое content (полный текст страницы) остаётся без изменений.
    """
    try:
        url = f"http://127.0.0.1:{port_settings.book_parser_port}/parser/subchapters/{subchapter_number}/content"
        r = httpx.get(url, verify=False)
        r.raise_for_status()
        raw_text = r.text

        # Пробуем распарсить полученный текст как JSON
        data = json.loads(raw_text)
        # Если API оборачивает результат в ключ "content", берем данные из него
        if "content" in data and isinstance(data["content"], dict):
            data = data["content"]

        subchapter_title = data.get("subchapter_title", "Неизвестный заголовок")
        pages = data.get("pages", [])

        # Извлекаем номера страниц (просто цифры)
        page_numbers = [str(page.get("page_number", "")) for page in pages if page.get("page_number") is not None]
        # Формируем выжимку текста для каждой страницы в виде "Номер страницы: summary"
        page_summaries = [
            f"{page.get('page_number')}: {page.get('summary', '').strip()}" 
            for page in pages if page.get("page_number") is not None
        ]

        # Выносим операцию join в отдельную переменную
        joined_summaries = ',\n '.join(page_summaries)

        formatted_text = (
            f"Контекст: вот имя подглавы <title>{subchapter_title}</title>,\n\n"
            f"Вот номера страницы этой подглавы <number_pages>{', '.join(page_numbers)}</number_pages>,\n\n"
            f"Вот выжимка текста каждой страницы: \n<summary>{joined_summaries}</summary>"
        )

        return formatted_text
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
            model="GigaChat-Max",
            response_model=LLMEvaluation,  # ← Используем новую модель
            temperature=0.2,
            messages=[
                {"role": "system", "content": f"ИНСТРУКЦИИ: {system_prompt}"},
                {"role": "user", "content": (
                    f"Финальный контент (извлечённый из страниц): <content_book>{final_content}</content_book>\n"
                    f"Вопрос пользователя: {question_user}\n"
                    "Ответь согласно ИНСТРУКЦИИ в формате JSON:"
                )}
            ],
        )
        
        # Форматируем ответ: оценка в начале, потом обоснование
        formatted_response = f"ИТОГОВАЯ ОЦЕНКА: {response.evaluation}\n\n{response.analysis_text}"
        return formatted_response
        
    except Exception as e:
        logger.error(f"Ошибка при получении финального ответа: {e}")
        # Возвращаем базовый ответ в случае ошибки
        return f"ИТОГОВАЯ ОЦЕНКА: НЕВЕРНО\n\nПроизошла ошибка при анализе ответа. Обратитесь к куратору."

# --------------------------------------------------------------------
# 6. Пример комплексной функции (все 4 шага) — опционально
# --------------------------------------------------------------------
def run_full_reasoning_pipeline(user_question: str) -> dict:
    logger.info("Запуск нового пайплайна LLM-рассуждения для всех подглав...")

    # Фиксированный список номеров подглав для финального ответа
    available_subchapters = ['3.11.1', '3.11.2', '3.11.3', '3.12.1', '3.12.2']

    # Создаем LLM-клиент для финального ответа
    client_openai = create_llm_client()

    # Получаем тексты для всех подглав и объединяем их
    final_contents = []
    for subchapter in available_subchapters:
        try:
            content = fetch_subchapter_text(subchapter)
            # Обрамляем текст подглавы идентификатором для удобства в финальном контенте
            final_contents.append(f"<content_subchapter id='{subchapter}'>\n{content}\n</content_subchapter>")
            logger.info(f"Получен текст подглавы {subchapter}")
        except Exception as e:
            logger.error(f"Ошибка получения текста для подглавы {subchapter}: {e}")

    # Объединяем все тексты в один итоговый контент
    combined_final_content = "\n".join(final_contents)
    logger.info(f"финальный контент: {combined_final_content[:150]}...")
    # Формируем финальный ответ, используя объединенный контент и вопрос пользователя
    final_answer_text = get_final_answer(
        client_openai,
        SYSTEM_PROMPT_MENTOR_ASSESSMENT,
        combined_final_content,
        user_question
    )
    logger.info(f"Финальный ответ:\n{final_answer_text}")

    return {
        "selected_subchapters": available_subchapters,
        "combined_final_content": combined_final_content,
        "final_answer": final_answer_text
    }
    
if __name__ == "__main__":
    run_full_reasoning_pipeline("вопрос: Почему отслеживание работает - назовите 4 урока о которых говорит автор. Ответ: Урок первый : не каждый реагирует на процесс обучения или не так как хотелось бы организации. Урок 2; между пониманием и действием дистанция огромного размера. Урок 3: люди не становятся лучше без отслеживания")
