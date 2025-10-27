import tiktoken

from src.lib.config import LLMS


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
        return 85

    scale = 768 / min(width, height)
    scaled_width = int(width * scale)
    scaled_height = int(height * scale)

    tiles_width = (scaled_width + 511) // 512
    tiles_height = (scaled_height + 511) // 512
    total_tiles = tiles_width * tiles_height

    return (total_tiles * 85) + 85


def count_text_tokens(concatenated_texts: str) -> int:
    """
    Подсчитывает количество токенов в тексте.

    Args:
        concatenated_texts: Объединенный текст для подсчета токенов

    Returns:
        Количество токенов в тексте
    """
    try:
        encoder = tiktoken.encoding_for_model(
            LLMS.GPT_5_MINI
        )  # pyright: ignore[reportUndefinedVariable]
        tokens = encoder.encode(concatenated_texts)
        return len(tokens)
    except Exception as e:
        raise Exception(f"Ошибка при подсчете токенов: {str(e)}")
