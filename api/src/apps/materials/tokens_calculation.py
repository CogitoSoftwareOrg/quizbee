import tiktoken
from io import BytesIO
from typing import Optional, Dict, Any
from lib.clients.tiktoken import ENCODERS
from lib.config import LLMS
from .pdf_parser import parse_pdf


def count_image_tokens(width: int, height: int) -> int:
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
