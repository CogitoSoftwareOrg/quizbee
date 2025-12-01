import asyncio
import fitz  # PyMuPDF
from io import BytesIO
from typing import Any
import logging
import re

from ....domain.out import DocumentParser
from ....domain.models import ParsedDocument, DocumentImage


class FitzPDFParser(DocumentParser):
    def __init__(
        self,
        max_text_length_for_images: int = 150,
    ):
        self.max_text_length_for_images = max_text_length_for_images

    async def parse(
        self, file_bytes: bytes, file_name: str
    ) -> ParsedDocument:
        result = await asyncio.to_thread(
            self._parse, file_bytes, file_name
        )

        return result

    def _parse(
        self, file_bytes: bytes, file_name: str
    ) -> ParsedDocument:
        """
        Извлекает текст и изображения из PDF-файла, фильтруя слишком маленькие изображения.

        Использует PyMuPDF для извлечения текста и изображений.

        Args:
            file_bytes: Байты PDF файла
            file_name: Имя файла (для логирования)

        Returns:
            ParsedDocument с извлечённым текстом и списком отфильтрованных изображений

        Raises:
            Exception: Если не удается обработать PDF файл
        """
        try:
            logging.info(f"📄 Парсинг PDF: {file_name}")
            pdf_stream = BytesIO(file_bytes)
            doc = fitz.open(stream=pdf_stream, filetype="pdf")
            page_count = len(doc)
            logging.info(f"PDF открыт. Количество страниц: {page_count}")

            images: list[DocumentImage] = []
            image_positions = {}
            is_book_doc = self.is_book(doc)
            toc_items = []  # Инициализируем пустым списком

            stats = {
                "total": 0,
                "filtered_size": 0,
                "filtered_dimensions": 0,
                "filtered_duplicates": 0,
                "filtered_background": 0,
                "accepted": 0,
                "full_page_screenshots": 0,
            }

            is_presentation = self.is_presentation(doc)

            if is_book_doc:
                logging.info(f"This is a book.")
                toc_items = self.extract_table_of_contents(doc)

                if not toc_items:
                    logging.warning(
                        "Оглавление (Table of Contents) не найдено в документе."
                    )
                else:
                    logging.info(f"Найдено оглавление из {len(toc_items)} элементов:")
                    for item in toc_items:
                        level = item["level"]
                        title = item["title"]
                        page_num = item["page"]

                        indent = "  " * (level - 1)
                        logging.info(f"{indent}- {title} (стр. {page_num})")

            # TEXT EXTRACTION
            md_text_parts = []

            for page_num in range(page_count):
                page = doc.load_page(page_num)
                page_text: str = page.get_text()  # type: ignore

                # Добавляем маркер номера страницы в начало 
                page_marker = f"{{quizbee_page_number_{page_num + 1}}}\n\n"

                page_text = page_marker + page_text

                md_text_parts.append(page_text)

            md_text = "\n\n".join(md_text_parts)

            doc.close()

            logging.info(f"Текст извлечен с маркерами, длина: {len(md_text)} символов")
            logging.info(
                f"Статистика изображений: всего={stats['total']}, "
                f"принято={stats['accepted']}, "
                f"отфильтровано_по_размеру={stats['filtered_size']}, "
                f"отфильтровано_по_измерениям={stats['filtered_dimensions']}, "
                f"отфильтровано_фон={stats['filtered_background']}, "
                f"дубликатов={stats['filtered_duplicates']}, "
                f"скриншотов_страниц={stats['full_page_screenshots']}"
            )

            logging.info(
                f"📄 PDF извлечение завершено: {len(md_text)} символов, {len(images)} изображений для обработки"
            )

            return ParsedDocument(
                text=md_text,
                images=images,
                contents=toc_items,
                is_book=is_book_doc,
            )

        except Exception as e:
            logging.error(f"❌ Ошибка при парсинге PDF файла {file_name}: {str(e)}")
            raise Exception(f"Ошибка при парсинге PDF файла: {str(e)}")



    def extract_table_of_contents(self, doc: fitz.Document) -> list[dict[str, Any]]:
        """
        Извлекает оглавление (Table of Contents) из PDF документа.

        Использует три метода в порядке приоритета:
        1. Встроенный get_toc()
        2. Анализ структуры документа через блоки текста (ищет крупные заголовки)
        3. Эвристический поиск страницы оглавления

        Args:
            doc: Открытый PDF документ

        Returns:
            Список элементов оглавления, каждый содержит:
            {
                "level": int,      # Уровень вложенности (1, 2, 3...)
                "title": str,      # Название главы/раздела
                "page": int        # Номер страницы
            }
        """
        toc_items = []

        # Метод 1: Пытаемся использовать встроенный get_toc()
        try:
            toc = doc.get_toc()  # type: ignore
            if toc:
                logging.info(
                    f"✓ Оглавление извлечено через get_toc(): {len(toc)} элементов"
                )
                for item in toc:
                    toc_items.append(
                        {"level": item[0], "title": item[1], "page": item[2]}
                    )
                return toc_items
        except Exception as e:
            logging.warning(f"get_toc() не сработал: {e}")

        # Метод 2: Анализ структуры документа через текстовые блоки
        # Применяется только для документов меньше 200 страниц
        if len(doc) < 150:
            logging.info(
                "Попытка извлечь оглавление через анализ структуры документа..."
            )
            toc_items = self.extract_toc_from_structure(doc)
            if toc_items:
                logging.info(
                    f"✓ Оглавление извлечено через анализ структуры: {len(toc_items)} элементов"
                )
                return toc_items
        else:
            logging.info(
                f"Документ содержит {len(doc)} страниц (>= 200), пропускаем анализ структуры"
            )

        return toc_items



    def is_book(self, doc: fitz.Document) -> bool:
        """
        Определяет, является ли PDF-документ книгой на основе нескольких эвристик.

        Критерии определения книги:
        1. Высокая плотность текста (много текста на страницу)
        2. Низкое соотношение изображений к тексту
        3. Формат страницы (книжная ориентация, стандартные размеры)
        4. Наличие структурных элементов книги (оглавление, главы)

        Args:
            doc: Открытый PDF документ

        Returns:
            True если документ является книгой, False в противном случае
        """
        page_count = len(doc)

        # Анализируем первые N страниц для определения характеристик
        sample_size = min(10, page_count)
        sample_pages = [
            0,
            page_count // 4,
            page_count // 2,
            3 * page_count // 4,
            page_count - 1,
        ]
        sample_pages = [p for p in sample_pages if p < page_count][:sample_size]

        total_text_length = 0
        total_images = 0
        portrait_pages = 0

        for page_num in sample_pages:
            page = doc.load_page(page_num)

            # 1. Подсчет текста
            text: str = page.get_text()  # type: ignore
            text_length = len(text.strip())
            total_text_length += text_length

            # 3. Проверка ориентации (книги обычно в портретной ориентации)
            rect = page.rect  # type: ignore
            if rect.height > rect.width:
                portrait_pages += 1

        # Средняя длина текста на страницу
        avg_text_length = total_text_length / len(sample_pages) if sample_pages else 0

        # Процент страниц в портретной ориентации
        portrait_ratio = portrait_pages / len(sample_pages) if sample_pages else 0

        logging.info(
            f"Анализ документа: страниц={page_count}, "
            f"средняя_длина_текста={avg_text_length:.0f}, "
            f"портретных_страниц={portrait_ratio:.1%}"
        )

        # Эвристики для определения книги:
        # - Много текста на странице (>1500 символов в среднем)
        # - Мало изображений (<2 на страницу)
        # - Преимущественно портретная ориентация (>80%)
        # - Много страниц (>50)

        is_book_candidate = (
            avg_text_length > 1000  # Высокая плотность текста
            and portrait_ratio > 0.8  # Портретная ориентация
            and page_count > 100  # Достаточно страниц
        )

        if is_book_candidate:
            logging.info(
                "📚 Документ определен как КНИГА - изображения извлекаться не будут"
            )
        else:
            logging.info(
                "📄 Документ определен как НЕ КНИГА - изображения будут извлечены"
            )

        return is_book_candidate

    def is_presentation(self, doc: fitz.Document) -> bool:
        """
        Определяет, является ли PDF-документ презентацией.

        Критерии:
        1. Меньше 600 страниц
        2. Преимущественно горизонтальная (ландшафтная) ориентация страниц

        Args:
            doc: Открытый PDF документ

        Returns:
            True если документ является презентацией, False в противном случае
        """
        page_count = len(doc)

        if page_count >= 600:
            logging.info(f"📄 Документ содержит {page_count} страниц (>= 600) - не презентация")
            return False

        sample_size = min(10, page_count)
        sample_pages = [
            0,
            page_count // 4,
            page_count // 2,
            3 * page_count // 4,
            page_count - 1,
        ]
        sample_pages = list(set(p for p in sample_pages if p < page_count))[:sample_size]

        landscape_pages = 0

        for page_num in sample_pages:
            page = doc.load_page(page_num)
            rect = page.rect
            if rect.width > rect.height:
                landscape_pages += 1

        landscape_ratio = landscape_pages / len(sample_pages) if sample_pages else 0

        is_presentation = landscape_ratio > 0.7

        if is_presentation:
            logging.info(
                f"🎯 Документ определен как ПРЕЗЕНТАЦИЯ - "
                f"{page_count} страниц, {landscape_ratio:.0%} горизонтальных"
            )
        else:
            logging.info(
                f"📄 Документ НЕ презентация - "
                f"{page_count} страниц, {landscape_ratio:.0%} горизонтальных"
            )

        return is_presentation

    def extract_toc_from_structure(self, doc: fitz.Document) -> list[dict[str, Any]]:
        """
        Извлекает оглавление, анализируя структуру текста в документе.

        Ищет заголовки по характеристикам:
        - Крупный размер шрифта (больше среднего)
        - Жирный шрифт
        - Короткий текст (обычно заголовки не длинные)
        - Позиция в начале страницы или отдельная строка

        Args:
            doc: Открытый PDF документ

        Returns:
            Список элементов оглавления
        """
        toc_items = []

        # Собираем статистику по размерам шрифтов для определения "крупного" текста
        font_sizes = []
        sample_size = min(10, len(doc))

        for page_num in range(0, len(doc), max(1, len(doc) // sample_size)):
            page = doc.load_page(page_num)
            blocks = page.get_text("dict")["blocks"]  # type: ignore

            for block in blocks:
                if block.get("type") == 0:  # текстовый блок  # type: ignore
                    for line in block.get("lines", []):  # type: ignore
                        for span in line.get("spans", []):  # type: ignore
                            font_sizes.append(span.get("size", 0))  # type: ignore

        if not font_sizes:
            return []

        # Вычисляем средний размер шрифта и порог для заголовков
        avg_font_size = sum(font_sizes) / len(font_sizes)
        heading_threshold = avg_font_size * 1.2  # заголовки обычно на 20%+ крупнее

        logging.info(
            f"Средний размер шрифта: {avg_font_size:.1f}, порог заголовков: {heading_threshold:.1f}"
        )

        # Проходим по всем страницам и ищем потенциальные заголовки
        seen_titles = set()  # для избежания дубликатов

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            blocks = page.get_text("dict")["blocks"]  # type: ignore

            for block in blocks:
                if (
                    block.get("type") != 0  # type: ignore
                ):  # пропускаем не-текстовые блоки
                    continue

                for line in block.get("lines", []):  # type: ignore
                    # Анализируем каждую строку
                    line_text = ""
                    max_font_size = 0
                    is_bold = False

                    for span in line.get("spans", []):  # type: ignore
                        line_text += span.get("text", "")  # type: ignore
                        font_size = span.get("size", 0)  # type: ignore
                        max_font_size = max(max_font_size, font_size)

                        # Проверяем, жирный ли шрифт
                        font_flags = span.get("flags", 0)
                        if font_flags & 2**4:  # бит 4 = bold
                            is_bold = True

                    line_text = line_text.strip()

                    # Критерии для заголовка:
                    # 1. Размер шрифта больше порога
                    # 2. Текст не слишком длинный (< 150 символов)
                    # 3. Текст не слишком короткий (> 3 символа)
                    # 4. Не является просто числом или символами
                    if (
                        max_font_size >= heading_threshold
                        and 3 < len(line_text) < 150
                        and line_text not in seen_titles
                        and not line_text.replace(".", "").replace(" ", "").isdigit()
                    ):

                        # Определяем уровень по размеру шрифта
                        if max_font_size >= heading_threshold * 1.3:
                            level = 1
                        elif max_font_size >= heading_threshold * 1.15:
                            level = 2
                        else:
                            level = 3

                        # Также можем использовать номер главы для определения уровня
                        # Например: "1. Глава" - уровень 1, "1.1 Раздел" - уровень 2
                        chapter_match = re.match(r"^(\d+(?:\.\d+)*)\s+", line_text)
                        if chapter_match:
                            number = chapter_match.group(1)
                            level = number.count(".") + 1

                        toc_items.append(
                            {"level": level, "title": line_text, "page": page_num + 1}
                        )
                        seen_titles.add(line_text)

        # Фильтруем слишком частые заголовки (вероятно, это не заголовки)
        if toc_items:
            # Удаляем элементы, которые встречаются слишком часто на соседних страницах
            filtered_items = []
            for i, item in enumerate(toc_items):
                # Проверяем, не повторяется ли похожий заголовок слишком близко
                is_duplicate = False
                for j in range(max(0, i - 3), i):
                    if (
                        abs(toc_items[j]["page"] - item["page"]) <= 2
                        and toc_items[j]["title"][:20] == item["title"][:20]
                    ):
                        is_duplicate = True
                        break

                if not is_duplicate:
                    filtered_items.append(item)

            toc_items = filtered_items

        return toc_items
