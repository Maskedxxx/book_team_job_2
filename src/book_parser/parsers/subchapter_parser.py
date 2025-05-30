from typing import List, Dict, Any
from src.book_parser.models import SubchapterOutput
from src.utils.logger import get_logger

class SubchapterParser:
    """
    Парсинг подглав для выбранной главы в know_map_full.json.

    Ожидаемый формат:
    {
        "content": {
            "parts": [
                {
                    "part_number": <number>,
                    "chapters": [
                        {
                            "chapter_number": <number>,
                            "subchapters": [
                                {
                                    "title": "...",
                                    "summary": "...",
                                    "key_points": [...],
                                    "subchapter_number": ...
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
    """
    def __init__(self, data: Dict[str, Any]) -> None:
        self.data = data
        self.logger = get_logger(__name__)

    def to_model(self, subchapter: Dict[str, Any]) -> SubchapterOutput:
        """
        Преобразует словарь с данными подглавы в модель SubchapterOutput.
        Логгирует имя заголовка (title) распарсенной подглавы.
        """
        key_points = subchapter.get("key_points", [])
        key_points_str = ", ".join(str(point) for point in key_points) if isinstance(key_points, list) else str(key_points)
        model = SubchapterOutput(
            subchapter_number=str(subchapter.get("subchapter_number", "Не указан номер")),
            title=subchapter.get("title", "Нет заголовка"),
            summary=subchapter.get("summary", "Нет описания"),
            key_points=key_points_str
        )
        self.logger.debug(f"Распарсена подглава: {model.title}")
        return model

    def parse_subchapters_by_chapter(self, selected_part: int, selected_chapter: int) -> List[SubchapterOutput]:
        """
        Находит часть с заданным part_number, затем главу с заданным chapter_number и парсит её подглавы.
        Логгирует список заголовков всех распарсенных подглав.
        """
        parts = self.data.get("content", {}).get("parts", [])
        for part in parts:
            if part.get("part_number") == selected_part:
                chapters = part.get("chapters", [])
                for chapter in chapters:
                    if chapter.get("chapter_number") == selected_chapter:
                        subchapters = chapter.get("subchapters", [])
                        models = [self.to_model(sub) for sub in subchapters]
                        subchapter_titles = [model.title for model in models]
                        self.logger.debug(f"Успешно распарсены подглавы: {subchapter_titles}")
                        return models
        self.logger.debug(f"Для части {selected_part} и главы {selected_chapter} подглавы не найдены")
        return []
