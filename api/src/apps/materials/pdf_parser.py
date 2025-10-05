import fitz  # PyMuPDF
from typing import Dict, List, Any
import logging
from io import BytesIO

# pymupdf4llm больше не используется для извлечения текста, 
# но может быть полезен для других целей. Оставим импорт закомментированным.
# import pymupdf4llm 

def parse_pdf(pdf_bytes: bytes) -> Dict[str, Any]:
    """
    Извлекает текст и изображения из PDF-файла, переданного в виде байтов.
    
    Использует стандартный метод get_text() из PyMuPDF для извлечения текста.

    Args:
        pdf_bytes: Байты PDF файла

    Returns:
        Словарь с извлеченным текстом и списком изображений:
        {
            "text": str,  # Извлеченный текст
            "images": List[Dict[str, any]]  # Каждое изображение содержит bytes, ext, width, height
        }

    Raises:
        Exception: Если не удается обработать PDF файл
    """
    try:
        # Открываем PDF из байтов
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        logging.info(f"PDF из байтов открыт. Количество страниц: {len(doc)}")

        # Извлечение текста с помощью стандартного метода PyMuPDF
        # Соединяем текст со всех страниц, разделяя двойным переносом строки
        full_text = "\n\n".join(page.get_text("text", sort=True) for page in doc)
        
        logging.info(f"Текст извлечен, длина: {len(full_text)} символов")

        # Извлечение изображений (логика осталась без изменений)
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
            "text": full_text,
            "images": images,
        }

    except Exception as e:
        raise Exception(f"Ошибка при парсинге PDF из байтов: {str(e)}")