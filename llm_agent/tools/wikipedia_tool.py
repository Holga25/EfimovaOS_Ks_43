import requests
import re
from typing import Dict, Any, List

class WikipediaTool:
    """Инструмент для поиска и извлечения информации из Wikipedia"""
    
    def __init__(self, lang: str = "ru"):
        """
        Инициализация инструмента Wikipedia
        
        Args:
            lang: Язык Wikipedia ('ru' или 'en')
        """
        if lang not in ["ru", "en"]:
            raise ValueError("Язык должен быть 'ru' или 'en'")
        
        self.lang = lang
        self.base_url = f"https://{lang}.wikipedia.org/w/api.php"
        self.name = "wikipedia"
        self.description = "Поиск и извлечение информации из Wikipedia"
    
    def get_tool_schema(self) -> Dict[str, Any]:
        """Возвращает схему инструмента для LLM"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Поисковый запрос"
                    },
                    "action": {
                        "type": "string",
                        "enum": ["search", "summary", "search_and_summarize"],
                        "description": "Действие: search - поиск статей, summary - получение выдержки, search_and_summarize - поиск и выдержка"
                    }
                },
                "required": ["query", "action"]
            }
        }
    
    def execute(self, query: str, action: str = "search_and_summarize", **kwargs) -> Dict[str, Any]:
        """
        Выполнение действия инструмента
        
        Args:
            query: Поисковый запрос
            action: Тип действия
            
        Returns:
            Результат выполнения
        """
        if action == "search":
            return {"status": "success", "data": self.search(query)}
        elif action == "summary":
            return {"status": "success", "data": self.get_summary(query)}
        elif action == "search_and_summarize":
            return {"status": "success", "data": self.search_and_summarize(query)}
        else:
            return {"status": "error", "message": f"Неизвестное действие: {action}"}
    
    def search(self, query: str, limit: int = 5) -> List[Dict[str, str]]:
        """Поиск статей в Wikipedia"""
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json",
            "srlimit": limit
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data.get("query", {}).get("search", []):
                results.append({
                    "title": item["title"],
                    "snippet": self._clean_html(item.get("snippet", "")),
                    "pageid": item.get("pageid")
                })
            
            return results
        except requests.RequestException as e:
            raise ConnectionError(f"Ошибка при запросе к Wikipedia: {e}")
    
    def get_summary(self, title: str, sentences: int = 3) -> str:
        """Получение краткой выдержки из статьи"""
        params = {
            "action": "query",
            "prop": "extracts",
            "exintro": True,
            "explaintext": True,
            "titles": title,
            "format": "json",
            "exsentences": sentences
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            pages = data.get("query", {}).get("pages", {})
            for page_id, page_data in pages.items():
                if "extract" in page_data:
                    return self._clean_text(page_data["extract"])
                else:
                    return "Статья не найдена"
            
            return "Статья не найдена"
        except requests.RequestException as e:
            raise ConnectionError(f"Ошибка при запросе к Wikipedia: {e}")
    
    def search_and_summarize(self, query: str) -> Dict[str, Any]:
        """Поиск статьи и получение её краткого содержания"""
        results = self.search(query, limit=1)
        
        if not results:
            return {"title": None, "summary": "Ничего не найдено"}
        
        title = results[0]["title"]
        summary = self.get_summary(title)
        
        return {
            "title": title,
            "summary": summary,
            "url": f"https://{self.lang}.wikipedia.org/wiki/{title.replace(' ', '_')}"
        }
    
    def _clean_text(self, text: str) -> str:
        """Очистка текста от лишних символов"""
        cleaned = re.sub(r'\s+', ' ', text)
        cleaned = cleaned.strip()
        return cleaned
    
    def _clean_html(self, text: str) -> str:
        """Очистка текста от HTML-тегов"""
        cleaned = re.sub(r'<[^>]+>', '', text)
        cleaned = re.sub(r'&[a-zA-Z]+;', ' ', cleaned)
        return self._clean_text(cleaned)