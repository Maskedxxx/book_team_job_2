from typing import List, Dict, Any
from src.book_parser.models import ChapterOutput
from src.utils.logger import get_logger


class ChapterParser:
    """
    Класс для парсинга глав из файла know_map_full.json.

    Ожидаемый формат:
    {
        "content": {
            "parts": [
                {
                    "part_number": <number>,
                    "chapters": [
                        {
                            "title": "...",
                            "summary": "...",
                            "key_points": [...],
                            "chapter_number": ...
                        },
                        ...
                    ]
                },
                ...
            ]
        }
    }
    """
    def __init__(self, data: Dict[str, Any]) -> None:
        self.data = data
        self.logger = get_logger(__name__)

    def to_model(self, chapter: Dict[str, Any]) -> ChapterOutput:
        """
        Преобразует словарь с данными главы в модель ChapterOutput.
        Логгирует имя заголовка (title) распарсенной главы.
        """
        key_points = chapter.get("key_points", [])
        key_points_str = ", ".join(str(point) for point in key_points) if isinstance(key_points, list) else str(key_points)
        model = ChapterOutput(
            chapter_number=str(chapter.get("chapter_number", "Не указан номер")),
            title=chapter.get("title", "Нет заголовка"),
            summary=chapter.get("summary", "Нет описания"),
            key_points=key_points_str
        )
        self.logger.debug(f"Распарсена глава: {model.title}")
        return model

    def parse_chapters_by_part(self, selected_part: int) -> List[ChapterOutput]:
        """
        Находит часть с заданным part_number и парсит все её главы.
        Логгирует список заголовков всех распарсенных глав.
        """
        parts = self.data.get("content", {}).get("parts", [])
        for part in parts:
            if part.get("part_number") == selected_part:
                chapters = part.get("chapters", [])
                models = [self.to_model(chapter) for chapter in chapters]
                chapter_titles = [model.title for model in models]
                self.logger.debug(f"Успешно распарсены главы: {chapter_titles}")
                return models
        self.logger.warning(f"Для части {selected_part} главы не найдены")
        return []
