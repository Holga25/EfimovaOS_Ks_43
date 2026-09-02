import unittest
from unittest.mock import patch, Mock
import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from llm_agent.tools.wikipedia_tool import WikipediaTool

class TestWikipediaTool(unittest.TestCase):
    """Тесты для класса WikipediaTool"""
    
    def setUp(self):
        """Настройка перед каждым тестом"""
        self.tool_ru = WikipediaTool("ru")
        self.tool_en = WikipediaTool("en")
    
    # Тесты инициализации
    def test_init_russian_language(self):
        """Тест: Инициализация с русским языком"""
        tool = WikipediaTool("ru")
        self.assertEqual(tool.lang, "ru")
        self.assertEqual(tool.base_url, "https://ru.wikipedia.org/w/api.php")
        self.assertIn("User-Agent", tool.headers)
    
    def test_init_english_language(self):
        """Тест: Инициализация с английским языком"""
        tool = WikipediaTool("en")
        self.assertEqual(tool.lang, "en")
        self.assertEqual(tool.base_url, "https://en.wikipedia.org/w/api.php")
        self.assertIn("User-Agent", tool.headers)
    
    def test_init_invalid_language(self):
        """Тест: Инициализация с недопустимым языком"""
        with self.assertRaises(ValueError):
            WikipediaTool("fr")
        with self.assertRaises(ValueError):
            WikipediaTool("de")
        with self.assertRaises(ValueError):
            WikipediaTool("")
    
    # Тесты поиска
    @patch('llm_agent.tools.wikipedia_tool.requests.get')
    def test_search_russian(self, mock_get):
        """Тест: Поиск на русском языке"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "query": {
                "search": [
                    {"title": "Python", "snippet": "Язык программирования", "pageid": 1},
                    {"title": "История языка Python", "snippet": "История создания", "pageid": 2}
                ]
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        results = self.tool_ru.search("Python", limit=2)
        
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["title"], "Python")
        self.assertEqual(results[1]["title"], "История языка Python")
        self.assertIn("pageid", results[0])
        
        # Проверяем, что запрос был к русской Wikipedia
        args, kwargs = mock_get.call_args
        self.assertIn("https://ru.wikipedia.org", args[0])
    
    @patch('llm_agent.tools.wikipedia_tool.requests.get')
    def test_search_english(self, mock_get):
        """Тест: Поиск на английском языке"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "query": {
                "search": [
                    {"title": "Python (programming language)", "snippet": "Programming language", "pageid": 1}
                ]
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        results = self.tool_en.search("Python programming", limit=1)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Python (programming language)")
        
        # Проверяем, что запрос был к английской Wikipedia
        args, kwargs = mock_get.call_args
        self.assertIn("https://en.wikipedia.org", args[0])
    
    # Тесты получения выдержки
    @patch('llm_agent.tools.wikipedia_tool.requests.get')
    def test_get_summary_russian(self, mock_get):
        """Тест: Получение выдержки на русском"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "query": {
                "pages": {
                    "1": {
                        "extract": "Python — высокоуровневый язык программирования."
                    }
                }
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        summary = self.tool_ru.get_summary("Python")
        
        self.assertEqual(summary, "Python — высокоуровневый язык программирования.")
        self.assertIsInstance(summary, str)
    
    @patch('llm_agent.tools.wikipedia_tool.requests.get')
    def test_get_summary_english(self, mock_get):
        """Тест: Получение выдержки на английском"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "query": {
                "pages": {
                    "1": {
                        "extract": "Python is a high-level programming language."
                    }
                }
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        summary = self.tool_en.get_summary("Python (programming language)")
        
        self.assertEqual(summary, "Python is a high-level programming language.")
        self.assertIsInstance(summary, str)
    
    @patch('llm_agent.tools.wikipedia_tool.requests.get')
    def test_get_summary_not_found(self, mock_get):
        """Тест: Статья не найдена"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "query": {
                "pages": {
                    "-1": {
                        "missing": ""
                    }
                }
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        summary = self.tool_en.get_summary("NonexistentArticle123456")
        
        self.assertEqual(summary, "Статья не найдена")
    
    # Тесты комплексного поиска
    @patch('llm_agent.tools.wikipedia_tool.requests.get')
    def test_search_and_summarize_russian(self, mock_get):
        """Тест: Комплексный поиск на русском"""
        # Первый вызов - поиск
        mock_search_response = Mock()
        mock_search_response.json.return_value = {
            "query": {
                "search": [
                    {"title": "Машинное обучение", "snippet": "...", "pageid": 1}
                ]
            }
        }
        mock_search_response.raise_for_status.return_value = None
        
        # Второй вызов - получение выдержки
        mock_summary_response = Mock()
        mock_summary_response.json.return_value = {
            "query": {
                "pages": {
                    "1": {
                        "extract": "Машинное обучение — класс методов искусственного интеллекта."
                    }
                }
            }
        }
        mock_summary_response.raise_for_status.return_value = None
        
        mock_get.side_effect = [mock_search_response, mock_summary_response]
        
        result = self.tool_ru.search_and_summarize("машинное обучение")
        
        self.assertEqual(result["title"], "Машинное обучение")
        self.assertEqual(result["summary"], "Машинное обучение — класс методов искусственного интеллекта.")
        self.assertIn("url", result)
        self.assertIn("ru.wikipedia.org", result["url"])
    
    @patch('llm_agent.tools.wikipedia_tool.requests.get')
    def test_search_and_summarize_english(self, mock_get):
        """Тест: Комплексный поиск на английском"""
        # Первый вызов - поиск
        mock_search_response = Mock()
        mock_search_response.json.return_value = {
            "query": {
                "search": [
                    {"title": "Machine learning", "snippet": "...", "pageid": 1}
                ]
            }
        }
        mock_search_response.raise_for_status.return_value = None
        
        # Второй вызов - получение выдержки
        mock_summary_response = Mock()
        mock_summary_response.json.return_value = {
            "query": {
                "pages": {
                    "1": {
                        "extract": "Machine learning is a subset of artificial intelligence."
                    }
                }
            }
        }
        mock_summary_response.raise_for_status.return_value = None
        
        mock_get.side_effect = [mock_search_response, mock_summary_response]
        
        result = self.tool_en.search_and_summarize("machine learning")
        
        self.assertEqual(result["title"], "Machine learning")
        self.assertEqual(result["summary"], "Machine learning is a subset of artificial intelligence.")
        self.assertIn("url", result)
        self.assertIn("en.wikipedia.org", result["url"])
    
    # Тесты execute
    @patch('llm_agent.tools.wikipedia_tool.requests.get')
    def test_execute_search(self, mock_get):
        """Тест: Execute с действием search"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "query": {
                "search": [
                    {"title": "Python", "snippet": "...", "pageid": 1}
                ]
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.tool_en.execute("Python", "search")
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["data"][0]["title"], "Python")
    
    @patch('llm_agent.tools.wikipedia_tool.requests.get')
    def test_execute_summary(self, mock_get):
        """Тест: Execute с действием summary"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "query": {
                "pages": {
                    "1": {
                        "extract": "Python is a language."
                    }
                }
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.tool_en.execute("Python", "summary")
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["data"], "Python is a language.")
    
    def test_execute_invalid_action(self):
        """Тест: Execute с неверным действием"""
        result = self.tool_ru.execute("Python", "invalid")
        
        self.assertEqual(result["status"], "error")
        self.assertIn("Неизвестное действие", result["message"])
    
    # Тесты очистки текста
    def test_clean_text(self):
        """Тест: Очистка текста от лишних пробелов"""
        dirty = "  Это   текст   с   лишними   пробелами.  "
        clean = self.tool_ru._clean_text(dirty)
        self.assertEqual(clean, "Это текст с лишними пробелами.")
    
    def test_clean_html(self):
        """Тест: Очистка HTML-тегов"""
        dirty = "<b>Жирный</b> текст &amp; символы"
        clean = self.tool_ru._clean_html(dirty)
        self.assertEqual(clean, "Жирный текст символы")
    
    # Тест схемы инструмента
    def test_get_tool_schema(self):
        """Тест: Получение схемы инструмента"""
        schema = self.tool_ru.get_tool_schema()
        
        self.assertEqual(schema["name"], "wikipedia")
        self.assertIn("description", schema)
        self.assertIn("parameters", schema)
        
        # Проверяем параметры
        properties = schema["parameters"]["properties"]
        self.assertIn("query", properties)
        self.assertIn("action", properties)
        
        # Проверяем допустимые действия
        actions = properties["action"]["enum"]
        self.assertIn("search", actions)
        self.assertIn("summary", actions)
        self.assertIn("search_and_summarize", actions)

if __name__ == '__main__':
    unittest.main()