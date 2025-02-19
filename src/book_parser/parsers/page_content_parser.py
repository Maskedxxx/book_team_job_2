from typing import List, Dict, Any
from src.book_parser.models import PageContentOutput
from src.book_parser.logger import get_logger

class PageContentParser:
    """
    Парсинг страниц по выбранной подглаве.

    Сначала ищем в know_map_full.json подглаву с нужным subchapter_number,
    затем извлекаем список номеров страниц (поле pages) и по ним ищем
    содержимое в файле kniga.json.

    Ожидаемый формат know_map_full.json для подглав:
    {
        "content": {
            "parts": [
                {
                    "part_number": ...,
                    "chapters": [
                        {
                            "chapter_number": ...,
                            "subchapters": [
                                {
                                    "subchapter_number": "<значение>",
                                    "pages": [номер_страницы, ...],
                                    ... 
                                },
                                ...
                            ]
                        },
                        ...
                    ]
                },
                ...
            ]
        }
    }

    Ожидаемый формат kniga_full_content.json:
    {
        "book": {
            "pages": [
                {
                    "pageNumber": <номер_страницы>,
                    "content": "Содержимое страницы"
                },
                ...
            ]
        }
    }
    """
    def __init__(self, know_map_data: Dict[str, Any], kniga_data: Dict[str, Any]) -> None:
        self.know_map_data = know_map_data
        self.kniga_data = kniga_data
        self.logger = get_logger(__name__)

    def get_pages_for_subchapter(self, selected_subchapter: str) -> List[int]:
        """
        Ищет в know_map_data подглаву с заданным subchapter_number и возвращает список номеров страниц.
        Логгирует найденные номера страниц.
        """
        parts = self.know_map_data.get("content", {}).get("parts", [])
        for part in parts:
            chapters = part.get("chapters", [])
            for chapter in chapters:
                subchapters = chapter.get("subchapters", [])
                for sub in subchapters:
                    if str(sub.get("subchapter_number")) == str(selected_subchapter):
                        pages = sub.get("pages", [])
                        self.logger.info(f"Найдено страницы для подглавы {selected_subchapter}: {pages}")
                        return pages
        self.logger.info(f"Страницы для подглавы {selected_subchapter} не найдены")
        return []

    def get_page_content(self, page_numbers: List[int]) -> str:
        """
        Ищет содержимое страниц в kniga_full_content по заданным номерам страниц.
        Логгирует номера страниц, для которых получено содержимое.
        """
        pages = self.kniga_data.get("book", {}).get("pages", [])
        contents: List[str] = []
        for page in pages:
            if page.get("pageNumber") in page_numbers:
                contents.append(str(page.get("content", "")))
        self.logger.info(f"Получено содержимое для страниц: {page_numbers}")
        return "\n\n".join(contents)

    def parse_final_content(self, selected_subchapter: str) -> PageContentOutput:
        """
        Собирает финальное содержимое для подглавы:
        1. Получает номера страниц.
        2. Извлекает и объединяет содержимое этих страниц.
        Логгирует успешное получение финального контента.
        """
        page_numbers = self.get_pages_for_subchapter(selected_subchapter)
        content = self.get_page_content(page_numbers)
        self.logger.info(f"Финальное содержимое успешно распарсено для подглавы {selected_subchapter}")
        return PageContentOutput(content=content)
