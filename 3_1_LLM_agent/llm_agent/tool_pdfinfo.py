# llm_agent/tool_pdfinfo.py
import os
import tempfile
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import requests
from pypdf import PdfReader
import pdfplumber


class PDFInfoTool:
    """Инструмент для извлечения информации из PDF-файлов (метаданные, количество страниц, текст)."""

    name = "pdf_info"
    description = (
        "Извлекает метаданные, количество страниц и текст из PDF-файла. "
        "Принимает локальный путь к файлу или URL."
    )

    def use(self, source: str, max_pages: Optional[int] = None, max_chars: int = 15000) -> str:
        """
        Извлекает информацию из PDF.

        Args:
            source: путь к локальному PDF-файлу или URL
            max_pages: ограничение количества страниц для извлечения текста (None = все)
            max_chars: максимальная длина возвращаемого текста (по умолчанию 15000 символов)

        Returns:
            Строка с метаданными, количеством страниц и текстом.
        """
        try:
            print(f"> Обрабатываю PDF: '{source}'")

            # Определяем, это URL или локальный путь
            is_url = urlparse(source).scheme in ("http", "https")
            temp_file = None

            if is_url:
                print(f"> Скачиваю PDF по URL...")
                response = requests.get(source, timeout=30, stream=True)
                response.raise_for_status()

                # Проверяем Content-Type
                content_type = response.headers.get("Content-Type", "")
                if "pdf" not in content_type.lower() and not source.lower().endswith(".pdf"):
                    return f"Ошибка: по URL '{source}' не найден PDF (Content-Type: {content_type})"

                # Сохраняем во временный файл
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
                for chunk in response.iter_content(chunk_size=8192):
                    temp_file.write(chunk)
                temp_file.close()
                pdf_path = temp_file.name
                print(f"> PDF сохранён во временный файл: {pdf_path}")
            else:
                pdf_path = source
                if not os.path.isfile(pdf_path):
                    return f"Ошибка: файл '{pdf_path}' не найден."

            # --- Метаданные и количество страниц через pypdf ---
            reader = PdfReader(pdf_path)
            num_pages = len(reader.pages)

            meta = reader.metadata or {}
            metadata_lines = []
            for key in ("/Title", "/Author", "/Subject", "/Creator", "/Producer", "/CreationDate", "/ModDate"):
                value = meta.get(key)
                if value:
                    # Убираем ведущий слэш в названии ключа для читаемости
                    clean_key = key.lstrip("/")
                    metadata_lines.append(f"  {clean_key}: {value}")

            if not metadata_lines:
                metadata_str = "  (метаданные отсутствуют)"
            else:
                metadata_str = "\n".join(metadata_lines)

            # --- Текст через pdfplumber (лучше извлекает текст) ---
            text_parts = []
            pages_to_process = range(num_pages)
            if max_pages is not None:
                pages_to_process = range(min(max_pages, num_pages))

            with pdfplumber.open(pdf_path) as pdf:
                for i in pages_to_process:
                    page = pdf.pages[i]
                    page_text = page.extract_text() or ""
                    if page_text.strip():
                        text_parts.append(f"--- Страница {i + 1} ---\n{page_text}")

            full_text = "\n\n".join(text_parts).strip()

            if not full_text:
                full_text = "(текст не извлечён — возможно, PDF состоит из сканированных изображений)"

            # Обрезаем слишком длинный текст
            if len(full_text) > max_chars:
                full_text = full_text[:max_chars] + f"\n\n... [текст обрезан, всего ~{len(full_text)} символов]"

            # --- Формируем итоговый отчёт ---
            result = (
                f"PDF Info для: {source}\n"
                f"{'=' * 50}\n"
                f"Количество страниц: {num_pages}\n\n"
                f"Метаданные:\n{metadata_str}\n\n"
                f"Текст ({len(text_parts)} стр. из {num_pages}):\n"
                f"{'-' * 40}\n"
                f"{full_text}"
            )

            print(f"> Успешно обработано: {num_pages} страниц")
            return result

        except Exception as e:
            print(f"> Ошибка при обработке PDF: {e}")
            return f"Произошла ошибка при извлечении информации из PDF '{source}': {e}"

        finally:
            # Удаляем временный файл, если он был создан
            if temp_file is not None:
                try:
                    os.unlink(temp_file.name)
                except OSError:
                    pass


# Пример использования:
# tool = PDFInfoTool()
# print(tool.use("https://example.com/sample.pdf"))
# print(tool.use("/path/to/local.pdf", max_pages=3))