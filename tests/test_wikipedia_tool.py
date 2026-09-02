import unittest
from unittest.mock import patch, Mock
import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from llm_agent.tools.wikipedia_tool import WikipediaTool

class TestWikipediaTool(unittest.TestCase):
    
    def setUp(self):
        """Настройка перед каждым тестом"""
        self.tool_ru = WikipediaTool("ru")
        self.tool_en = WikipediaTool("en")
    
    def test_init_valid_languages(self):
        """Тест 1: Инициализация с допустимыми языками"""
        self.assertEqual(self.tool_ru.lang, "ru")
        self.assertEqual(self.tool_en.lang, "en")
        self.assertEqual(self.tool_ru.base_url, "https://ru.wikipedia.org/w/api.php")
        self.assertIn("User-Agent", self.tool_ru.headers)
    
    def test_init_invalid_language(self):
        """Тест 2: Инициализация с недопустимым языком"""
        with self.assertRaises(ValueError):
            WikipediaTool("fr")
    
    def test_get_tool_schema(self):
        """Тест 3: Получение схемы инструмента"""
        schema = self.tool_ru.get_tool_schema()
        
        self.assertEqual(schema["name"], "wikipedia")
        self.assertIn("description", schema)
        self.assertIn("parameters", schema)
        self.assertIn("query", schema["parameters"]["properties"])
        self.assertIn("action", schema["parameters"]["properties"])
    
    @patch('llm_agent.tools.wikipedia_tool.requests.get')
    def test_search_success(self, mock_get):
        """Тест 4: Успешный поиск статей"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "query": {
                "search": [
                    {"title": "Python", "snippet": "Python is a <b>programming</b> language", "pageid": 123},
                    {"title": "Python (programming language)", "snippet": "High-level language", "pageid": 124}
                ]
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        results = self.tool_en.search("Python")
        
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["title"], "Python")
        self.assertIn("pageid", results[0])
        # Проверяем, что requests.get вызван с headers
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertIn("headers", kwargs)
    
    @patch('llm_agent.tools.wikipedia_tool.requests.get')
    def test_get_summary_success(self, mock_get):
        """Тест 5: Получение выдержки из статьи"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "query": {
                "pages": {
                    "123": {
                        "extract": "Python is a high-level programming language."
                    }
                }
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        summary = self.tool_en.get_summary("Python")
        
        self.assertIsInstance(summary, str)
        self.assertGreater(len(summary), 0)
        self.assertEqual(summary, "Python is a high-level programming language.")
        # Проверяем headers
        args, kwargs = mock_get.call_args
        self.assertIn("headers", kwargs)
    
    @patch('llm_agent.tools.wikipedia_tool.requests.get')
    def test_execute_search_action(self, mock_get):
        """Тест 6: Выполнение поиска через execute"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "query": {
                "search": [
                    {"title": "Python", "snippet": "Python is...", "pageid": 123}
                ]
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.tool_en.execute("Python", "search")
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(len(result["data"]), 1)
        self.assertEqual(result["data"][0]["title"], "Python")
    
    def test_execute_invalid_action(self):
        """Тест 7: Неверное действие"""
        result = self.tool_ru.execute("Python", "invalid_action")
        
        self.assertEqual(result["status"], "error")
        self.assertIn("Неизвестное действие", result["message"])
    
    @patch('llm_agent.tools.wikipedia_tool.requests.get')
    def test_search_and_summarize(self, mock_get):
        """Тест 8: Комплексный поиск и получение выдержки"""
        # Первый вызов - поиск
        mock_search_response = Mock()
        mock_search_response.json.return_value = {
            "query": {
                "search": [
                    {"title": "Python (programming language)", "snippet": "...", "pageid": 123}
                ]
            }
        }
        mock_search_response.raise_for_status.return_value = None
        
        # Второй вызов - получение выдержки
        mock_summary_response = Mock()
        mock_summary_response.json.return_value = {
            "query": {
                "pages": {
                    "123": {
                        "extract": "Python is a programming language."
                    }
                }
            }
        }
        mock_summary_response.raise_for_status.return_value = None
        
        mock_get.side_effect = [mock_search_response, mock_summary_response]
        
        result = self.tool_en.search_and_summarize("Python programming")
        
        self.assertIsInstance(result, dict)
        self.assertIn("title", result)
        self.assertIn("summary", result)
        self.assertEqual(result["title"], "Python (programming language)")
        self.assertEqual(result["summary"], "Python is a programming language.")
        
        # Проверяем, что requests.get вызван дважды с headers
        self.assertEqual(mock_get.call_count, 2)
        for call in mock_get.call_args_list:
            args, kwargs = call
            self.assertIn("headers", kwargs)

if __name__ == '__main__':
    unittest.main()