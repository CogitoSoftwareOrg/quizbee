import fitz  # PyMuPDF
from typing import Dict, List, Any
import logging
from io import BytesIO

# Настройка логирования для отладки
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def parse_pdf(
    pdf_bytes: bytes, 
    min_width: int = 90, 
    min_height: int = 90
) -> Dict[str, Any]:
    """
    Извлекает текст и изображения из PDF-файла, фильтруя слишком маленькие изображения.
    
    Args:
        pdf_bytes: Байты PDF файла.
        min_width: Минимальная ширина изображения для извлечения.
        min_height: Минимальная высота изображения для извлечения.

    Returns:
        Словарь с извлеченным текстом и списком отфильтрованных изображений.
    """
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        page_count = len(doc)
        logging.info(f"PDF открыт. Количество страниц: {page_count}")

        full_text = "\n\n".join(page.get_text("text", sort=True) for page in doc)
        logging.info(f"Текст извлечен, длина: {len(full_text)} символов")

        images = []
        
        # Если 100+ страниц - это книга, не извлекаем изображения
        if page_count >= 100:
            logging.info(f"Документ содержит {page_count} страниц (книга) - изображения не извлекаются")
        else:
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                image_list = page.get_images(full=True)

                if image_list:
                    logging.info(f"Найдено {len(image_list)} исходных изображений на странице {page_num + 1}")
                    for image_index, img in enumerate(image_list):
                        xref = img[0]
                        base_image = doc.extract_image(xref)
                        
                        width = base_image.get("width", 0)
                        height = base_image.get("height", 0)

                        # *** ГЛАВНОЕ ИЗМЕНЕНИЕ: УСЛОВИЕ ФИЛЬТРАЦИИ ***
                        # Пропускаем изображения, если они слишком маленькие
                        if width < min_width or height < min_height:
                            logging.debug(f"Пропущено маленькое изображение на стр. {page_num + 1} (размер: {width}x{height})")
                            continue

                        image_bytes = base_image["image"]
                        image_ext = base_image["ext"]
                        
                        images.append({
                            "bytes": image_bytes,
                            "ext": image_ext,
                            "width": width,
                            "height": height,
                            "page": page_num + 1,
                            "index": image_index + 1,
                        })

        doc.close()
        
        logging.info(f"Извлечено {len(images)} изображений после фильтрации")

        return {
            "text": full_text,
            "images": images,
        }

    except Exception as e:
        raise Exception(f"Ошибка при парсинге PDF из байтов: {str(e)}")
