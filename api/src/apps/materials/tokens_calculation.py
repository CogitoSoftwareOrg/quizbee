import tiktoken
from io import BytesIO
from typing import Optional, Dict, Any
from lib.clients.tiktoken import ENCODERS
from lib.config import LLMS
from .pdf_parser import parse_pdf


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


def count_pdf_tokens(pdf_bytes: bytes) -> Dict[str, Any]:
    """
    Подсчитывает количество токенов в PDF файле (текст и изображения).

    Args:
        pdf_bytes: Байты PDF файла

    Returns:
        Словарь с данными:
        {
            "text": str,  # Извлеченный текст
            "text_tokens": int,  # Количество токенов в тексте
            "images": List[Dict],  # Список изображений с их данными
            "image_tokens": int,  # Общее количество токенов для всех изображений
            "total_tokens": int,  # text_tokens + image_tokens
        }

    Raises:
        Exception: Если не удается обработать PDF файл
    """
    try:
        # Парсим PDF
        parsed_data = parse_pdf(pdf_bytes)
        text = parsed_data["text"]
        images = parsed_data["images"]

        # Получаем энкодер для подсчета токенов
        encoding = ENCODERS[LLMS.GPT_5_MINI]

        # Подсчитываем токены текста
        text_tokens_list = encoding.encode(text)
        text_tokens = len(text_tokens_list)

        # Подсчитываем токены изображений
        image_tokens = 0
        images_with_tokens = []

        for img in images:
            img_tokens = calculate_image_tokens(img["width"], img["height"])
            image_tokens += img_tokens

            images_with_tokens.append(
                {
                    "bytes": img["bytes"],
                    "ext": img["ext"],
                    "width": img["width"],
                    "height": img["height"],
                    "page": img["page"],
                    "index": img["index"],
                    "tokens": img_tokens,
                }
            )

        total_tokens = text_tokens + image_tokens

        return {
            "text": text,
            "text_tokens": text_tokens,
            "images": images_with_tokens,
            "image_tokens": image_tokens,
            "total_tokens": total_tokens,
        }

    except Exception as e:
        raise Exception(f"Ошибка при обработке PDF файла: {str(e)}")


def count_text_tokens(text: str) -> int:
    """
    Подсчитывает количество токенов в тексте.

    Args:
        text: Текст для подсчета токенов

    Returns:
        Количество токенов в тексте
    """
    try:
        encoding = ENCODERS[LLMS.GPT_5_MINI]
        tokens = encoding.encode(text)
        return len(tokens)
    except Exception as e:
        raise Exception(f"Ошибка при подсчете токенов: {str(e)}")
