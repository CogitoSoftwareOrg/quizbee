import pymupdf4llm
import fitz  # PyMuPDF для извлечения изображений
from io import BytesIO
from typing import Dict, List, Any
import logging


def parse_pdf(pdf_bytes: bytes) -> Dict[str, Any]:
    """
    Извлекает текст и изображения из PDF-файла.
    
    Использует PyMuPDF4LLM для извлечения текста в формате Markdown,
    что обеспечивает лучшее качество извлечения, поддержку таблиц,
    многоколоночных страниц и правильную последовательность чтения.

    Args:
        pdf_bytes: Байты PDF файла

    Returns:
        Словарь с извлеченным текстом и списком изображений:
        {
            "text": str,  # Текст в формате Markdown
            "images": List[Dict[str, any]]  # каждое изображение содержит bytes, ext, width, height
        }

    Raises:
        Exception: Если не удается обработать PDF файл
    """
    try:
        # Открываем PDF из байтов для PyMuPDF4LLM
        pdf_stream = BytesIO(pdf_bytes)
        doc = fitz.open(stream=pdf_stream, filetype="pdf")
        
        logging.info(f"PDF открыт. Количество страниц: {len(doc)}")

        # Извлечение текста с помощью PyMuPDF4LLM
        # PyMuPDF4LLM возвращает текст в формате Markdown с поддержкой таблиц,
        # заголовков, списков, жирного/курсивного текста и т.д.
        md_text = pymupdf4llm.to_markdown(doc)
        
        logging.info(f"Текст извлечен в формате Markdown, длина: {len(md_text)} символов")

        # Извлечение изображений (используем стандартный PyMuPDF)
        images = []
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            image_list = page.get_images(full=True)

            if image_list:
                logging.info(f"Найдено {len(image_list)} изображений на странице {page_num + 1}")
                for image_index, img in enumerate(image_list):
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    
                    # Получаем размеры изображения
                    width = base_image.get("width", 0)
                    height = base_image.get("height", 0)
                    
                    images.append({
                        "bytes": image_bytes,
                        "ext": image_ext,
                        "width": width,
                        "height": height,
                        "page": page_num + 1,
                        "index": image_index + 1,
                    })

        doc.close()
        
        logging.info(f"Извлечено {len(images)} изображений из PDF")

        return {
            "text": md_text,
            "images": images,
        }

    except Exception as e:
        raise Exception(f"Ошибка при парсинге PDF файла: {str(e)}")


def calculate_image_tokens(width: int, height: int) -> int:
    """
    Рассчитывает количество токенов для изображения на основе его размеров.
    
    Эвристика основана на подходе OpenAI для vision моделей:
    - Изображения разбиваются на тайлы 512x512
    - Каждый тайл ~85 токенов
    - Плюс базовые 85 токенов за низкое разрешение
    
    Args:
        width: Ширина изображения в пикселях
        height: Высота изображения в пикселях
        
    Returns:
        Примерное количество токенов
    """
    if width == 0 or height == 0:
        return 85  # Минимальная стоимость
    
    # Масштабируем изображение, чтобы самая короткая сторона была 768px
    scale = 768 / min(width, height)
    scaled_width = int(width * scale)
    scaled_height = int(height * scale)
    
    # Количество тайлов 512x512
    tiles_width = (scaled_width + 511) // 512
    tiles_height = (scaled_height + 511) // 512
    total_tiles = tiles_width * tiles_height
    
    # 85 токенов за тайл + 85 базовых
    return (total_tiles * 85) + 85
