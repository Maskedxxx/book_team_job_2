# tests/google_sheets/test_services.py

import unittest
from datetime import datetime
from src.google_sheets.services import process_form_data
from src.google_sheets.models import QAPair, FormSubmission

class TestGoogleSheetsServices(unittest.TestCase):
    def test_process_form_data(self):
        # Тестовые данные
        test_data = {
            "row_id": "123",
            "Отметка времени": 1711108901,
            "Введите свои инициалы и должность (ФИО)": "Иванов И.И.",
            "Какая привычка по статистике Клуба Руководителей самая вредная?": "Ответ 1",
            "Какие признаки указывают на то, что человек перешел грань?": "Ответ 2",
            "Отправка ответов": "отправлено"
        }
        
        # Вызываем тестируемую функцию
        result = process_form_data(test_data)
        
        # Проверки
        self.assertIsInstance(result, FormSubmission)
        self.assertEqual(result.row_id, "123")
        self.assertFalse(result.processed)
        
        # Проверяем количество пар вопрос-ответ (должно быть 3 - без row_id, Отметка времени и Отпрарвка ответов)
        self.assertEqual(len(result.qa_pairs), 3)
        
        # Проверяем содержимое первой пары
        first_pair = result.qa_pairs[0]
        self.assertIsInstance(first_pair, QAPair)
        self.assertEqual(first_pair.question, "Введите свои инициалы и должность (ФИО)")
        self.assertEqual(first_pair.user_answer, "Иванов И.И.")
        self.assertEqual(first_pair.llm_response, "")  # Значение по умолчанию

if __name__ == "__main__":
    unittest.main()