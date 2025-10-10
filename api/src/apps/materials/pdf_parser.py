
import fitz  # PyMuPDF для извлечения изображений
from io import BytesIO
from typing import Dict, List, Any
import logging
import re

# Настройка логирования для отладки
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def is_book(doc: fitz.Document) -> bool:
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
    
    # Слишком короткие документы не книги (< 30 страниц)
    if page_count < 100:
        return False
    
    # Анализируем первые N страниц для определения характеристик
    sample_size = min(10, page_count)
    sample_pages = [0, page_count // 4, page_count // 2, 3 * page_count // 4, page_count - 1]
    sample_pages = [p for p in sample_pages if p < page_count][:sample_size]
    
    total_text_length = 0
    total_images = 0
    portrait_pages = 0
    
    for page_num in sample_pages:
        page = doc.load_page(page_num)
        
        # 1. Подсчет текста
        text = page.get_text()  # type: ignore
        text_length = len(text.strip())
        total_text_length += text_length
        
        # 2. Подсчет изображений
        images = page.get_images(full=True)  # type: ignore
        total_images += len(images)
        
        # 3. Проверка ориентации (книги обычно в портретной ориентации)
        rect = page.rect  # type: ignore
        if rect.height > rect.width:
            portrait_pages += 1
    
    # Средняя длина текста на страницу
    avg_text_length = total_text_length / len(sample_pages) if sample_pages else 0
    
    # Среднее количество изображений на страницу
    avg_images = total_images / len(sample_pages) if sample_pages else 0
    
    # Процент страниц в портретной ориентации
    portrait_ratio = portrait_pages / len(sample_pages) if sample_pages else 0
    
    logging.info(
        f"Анализ документа: страниц={page_count}, "
        f"средняя_длина_текста={avg_text_length:.0f}, "
        f"среднее_изображений={avg_images:.1f}, "
        f"портретных_страниц={portrait_ratio:.1%}"
    )
    
    # Эвристики для определения книги:
    # - Много текста на странице (>1500 символов в среднем)
    # - Мало изображений (<2 на страницу)
    # - Преимущественно портретная ориентация (>80%)
    # - Много страниц (>50)
    
    is_book_candidate = (
        avg_text_length > 1000 and  # Высокая плотность текста
        avg_images < 2 and  # Мало изображений
        portrait_ratio > 0.8 and  # Портретная ориентация
        page_count > 50  # Достаточно страниц
    )
    
    if is_book_candidate:
        logging.info("📚 Документ определен как КНИГА - изображения извлекаться не будут")
    else:
        logging.info("📄 Документ определен как НЕ КНИГА - изображения будут извлечены")
    
    return is_book_candidate


def parse_pdf(
    pdf_bytes: bytes, 
    min_width: int = 50, 
    min_height: int = 50,
    min_file_size: int = 3 * 1024  # 10 KB по умолчанию
) -> Dict[str, Any]:
    """
    Извлекает текст и изображения из PDF-файла, фильтруя слишком маленькие изображения.

    Использует PyMuPDF4LLM для извлечения текста в формате Markdown,
    что обеспечивает лучшее качество извлечения, поддержку таблиц,
    многоколоночных страниц и правильную последовательность чтения.
    
    В текст вставляются маркеры вида {image_1}, {image_2} и т.д. на места,
    где находятся изображения, для последующего восстановления их позиций.
    
    Фильтрация изображений по нескольким критериям:
    - Размер (ширина/высота) - отсеивает слишком маленькие
    - Размер файла - отсеивает черные экраны и другой "мусор" с низкой энтропией

    Args:
        pdf_bytes: Байты PDF файла
        min_width: Минимальная ширина изображения для извлечения (пиксели)
        min_height: Минимальная высота изображения для извлечения (пиксели)
        min_file_size: Минимальный размер файла изображения в байтах (по умолчанию 10 KB)

    Returns:
        Словарь с извлеченным текстом и списком отфильтрованных изображений:
        {
            "text": str,  # Текст в формате Markdown с маркерами {image_N}
            "images": List[Dict[str, any]]  # каждое изображение содержит bytes, ext, width, height, marker, size
        }

    Raises:
        Exception: Если не удается обработать PDF файл
    """
    try:
        
      
        pdf_stream = BytesIO(pdf_bytes)
        doc = fitz.open(stream=pdf_stream, filetype="pdf")
        page_count = len(doc)
        logging.info(f"PDF открыт. Количество страниц: {page_count}")

    
        images = []
        image_positions = {}  
        is_book_doc = is_book(doc)
        
        # Статистика фильтрации
        stats = {
            "total": 0,
            "filtered_size": 0,
            "filtered_dimensions": 0,
            "filtered_duplicates": 0,
            "accepted": 0,
            "full_page_screenshots": 0
        }
        
        # Для отслеживания уже обработанных изображений (дедупликация)
        seen_xrefs = set()  
        
        # Порог минимального количества текста на странице (в символах), чтобы решать, делать ли скриншот всей страницы
        MIN_TEXT_LENGTH = 100

        # Если документ определен как книга - не извлекаем изображения
        if is_book_doc:
            logging.info(
                f"Документ является книгой - изображения не извлекаются"
            )
        else:
            global_image_counter = 1
            
            for page_num in range(page_count):
                page = doc.load_page(page_num)
                
                
                page_text = page.get_text()  # type: ignore
                text_length = len(page_text.strip())
                
                # Если текста очень мало, создаём полноразмерный скриншот страницы
                if text_length < MIN_TEXT_LENGTH:
                    
                   
                    pix = page.get_pixmap()  # type: ignore 
                    img_bytes = pix.tobytes("png")  # type: ignore
                    
                    marker = f"{{quizbee_unique_image_{global_image_counter}}}"
                    
                    images.append({
                        "bytes": img_bytes,
                        "ext": "png",
                        "width": pix.width,  # type: ignore
                        "height": pix.height,  # type: ignore
                        "page": page_num + 1,
                        "index": 0,  
                        "marker": marker,
                        "size": len(img_bytes),
                        "is_full_page": True
                    })
                    
                    image_positions[page_num] = [(0, marker)]
                    global_image_counter += 1
                    stats["full_page_screenshots"] += 1
                    
                    continue  
                
                image_list = page.get_images(full=True)  # type: ignore

                if not image_list:
                    continue
                    
                logging.info(
                    f"Найдено {len(image_list)} исходных изображений на странице {page_num + 1}"
                )
                
                # Получаем bbox для всех изображений на странице
                image_rects = []
                for image_index, img in enumerate(image_list):
                    xref = img[0]
                    stats["total"] += 1
                    
                    # Проверяем дубликаты
                    if xref in seen_xrefs:
                        stats["filtered_duplicates"] += 1
                        continue
                    
                    # Получаем все вхождения изображения на странице
                    img_instances = page.get_image_rects(xref)  # type: ignore
                    if img_instances:
                        # Берем первое вхождение (обычно изображение встречается один раз)
                        rect = img_instances[0]
                        
                        base_image = doc.extract_image(xref)
                        width = base_image.get("width", 0)
                        height = base_image.get("height", 0)
                        file_size = len(base_image["image"])
                        
                        # Фильтрация
                        if width < min_width or height < min_height:
                            stats["filtered_dimensions"] += 1
                            continue
                        
                        if file_size < min_file_size:
                            stats["filtered_size"] += 1
                            continue
                        
                        seen_xrefs.add(xref)
                        stats["accepted"] += 1
                        
                        image_rects.append({
                            "xref": xref,
                            "rect": rect,
                            "image_data": base_image,
                            "width": width,
                            "height": height,
                            "file_size": file_size
                        })
                
                if not image_rects:
                    continue
                
                # Группируем близкие изображения
                # Порог близости в пунктах (points) - если изображения ближе, объединяем
                PROXIMITY_THRESHOLD = 50  # пикселей
                
                def group_nearby_images(img_rects):
                    """Группирует изображения, которые находятся близко друг к другу"""
                    if not img_rects:
                        return []
                    
                    # Сортируем по Y-координате (сверху вниз)
                    sorted_imgs = sorted(img_rects, key=lambda x: x["rect"].y0)
                    
                    groups = []
                    current_group = [sorted_imgs[0]]
                    
                    for img in sorted_imgs[1:]:
                        # Проверяем расстояние до последнего изображения в текущей группе
                        last_img = current_group[-1]
                        
                        # Расстояние по вертикали
                        vertical_dist = img["rect"].y0 - last_img["rect"].y1
                        
                        # Проверяем пересечение по горизонтали
                        horizontal_overlap = not (
                            img["rect"].x1 < last_img["rect"].x0 or 
                            img["rect"].x0 > last_img["rect"].x1
                        )
                        
                        # Если изображения близко или есть горизонтальное пересечение
                        if vertical_dist < PROXIMITY_THRESHOLD or horizontal_overlap:
                            current_group.append(img)
                        else:
                            groups.append(current_group)
                            current_group = [img]
                    
                    groups.append(current_group)
                    return groups
                
                image_groups = group_nearby_images(image_rects)
                page_img_positions = []
                
                for group in image_groups:
                    if len(group) == 1:
                        # Одиночное изображение - делаем скриншот области с отступами
                        # чтобы захватить весь контекст (подписи, текст и т.д.)
                        rect = group[0]["rect"]
                        
                        # Добавляем отступы со всех сторон
                        padding_left = 30
                        padding_right = 30
                        padding_top = 30
                        padding_bottom = 30
                        
                        # Получаем размеры страницы для ограничения области
                        page_rect = page.rect  # type: ignore
                        
                        clip_rect = fitz.Rect(  # type: ignore
                            max(0, rect.x0 - padding_left),
                            max(0, rect.y0 - padding_top),
                            min(page_rect.width, rect.x1 + padding_right),
                            min(page_rect.height, rect.y1 + padding_bottom)
                        )
                        
                        # Создаём скриншот области
                        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), clip=clip_rect)  # type: ignore
                        img_bytes = pix.tobytes("png")  # type: ignore
                        
                        marker = f"{{quizbee_unique_image_{global_image_counter}}}"
                        
                        images.append({
                            "bytes": img_bytes,
                            "ext": "png",
                            "width": pix.width,  # type: ignore
                            "height": pix.height,  # type: ignore
                            "page": page_num + 1,
                            "index": len(images) + 1,
                            "marker": marker,
                            "size": len(img_bytes),
                        })
                        
                        page_img_positions.append((rect.y0, marker))
                        global_image_counter += 1
                        
                    else:
                        # Группа изображений - делаем скриншот области
                        logging.info(
                            f"Найдена группа из {len(group)} близких изображений на стр. {page_num + 1}, "
                            f"создаём объединённый скриншот"
                        )
                        
                        # Находим общий bbox для всех изображений в группе
                        min_x = min(img["rect"].x0 for img in group)
                        min_y = min(img["rect"].y0 for img in group)
                        max_x = max(img["rect"].x1 for img in group)
                        max_y = max(img["rect"].y1 for img in group)
                        
                        # Добавляем отступы со всех сторон для захвата контекста
      
                        padding_left = 30
                        padding_right = 30
                        padding_top = 30
                        padding_bottom = 30
                        
                        # Получаем размеры страницы для ограничения области
                        page_rect = page.rect  # type: ignore
                        
                        clip_rect = fitz.Rect(  # type: ignore
                            max(0, min_x - padding_left),
                            max(0, min_y - padding_top),
                            min(page_rect.width, max_x + padding_right),
                            min(page_rect.height, max_y + padding_bottom)
                        )
                        
                        # Создаём скриншот этой области
                        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), clip=clip_rect)  # type: ignore
                        img_bytes = pix.tobytes("png")  # type: ignore
                        
                        marker = f"{{quizbee_unique_image_{global_image_counter}}}"
                        
                        images.append({
                            "bytes": img_bytes,
                            "ext": "png",
                            "width": pix.width,  # type: ignore
                            "height": pix.height,  # type: ignore
                            "page": page_num + 1,
                            "index": len(images) + 1,
                            "marker": marker,
                            "size": len(img_bytes),
                            "is_grouped": True,
                            "group_size": len(group)
                        })
                        
                        page_img_positions.append((min_y, marker))
                        global_image_counter += 1
                        stats["full_page_screenshots"] += 1
                
                if page_img_positions:
                    # Сортируем по Y-позиции (сверху вниз)
                    page_img_positions.sort(key=lambda x: x[0])
                    image_positions[page_num] = page_img_positions

        # Извлечение текста постранично с встраиванием маркеров
        md_text_parts = []
        
        for page_num in range(page_count):
            
            
            page = doc.load_page(page_num)
            page_text = page.get_text()  # type: ignore
        
            # Если на странице есть изображения, вставляем маркеры
            if page_num in image_positions:
                # Разбиваем текст на параграфы/блоки
                paragraphs = re.split(r'\n\n+', page_text)
                
                # Определяем количество параграфов и изображений
                num_paragraphs = len(paragraphs)
                num_images = len(image_positions[page_num])
                
                # Вставляем маркеры изображений между параграфами
                # Распределяем их равномерно
                result_parts = []
                images_inserted = 0
                
                for i, para in enumerate(paragraphs):
                    result_parts.append(para)
                    
                    # Вставляем изображение после каждого N-го параграфа
                    if images_inserted < num_images and num_paragraphs > 0:
                        # Простая эвристика: вставляем изображения пропорционально
                        insert_threshold = (i + 1) / num_paragraphs
                        image_threshold = (images_inserted + 1) / num_images
                        
                        if insert_threshold >= image_threshold:
                            _, marker = image_positions[page_num][images_inserted]
                            result_parts.append(f"\n{marker}\n")
                            images_inserted += 1
                
                # Вставляем оставшиеся изображения в конец
                while images_inserted < num_images:
                    _, marker = image_positions[page_num][images_inserted]
                    result_parts.append(f"\n{marker}\n")
                    images_inserted += 1
                
                page_text = "\n\n".join(result_parts)
            
            md_text_parts.append(page_text)
        
        md_text = "\n\n-----\n\n".join(md_text_parts)
        
        doc.close()

        
        logging.info(
            f"Текст извлечен в формате Markdown с маркерами, длина: {len(md_text)} символов"
        )

        return {
            "text": md_text,
            "images": images,
        }

    except Exception as e:
        raise Exception(f"Ошибка при парсинге PDF файла: {str(e)}")

