from ...app.contracts import ImageTokenizer


class OpenAIImageTokenizer(ImageTokenizer):
    def count_image(self, width: int, height: int) -> int:
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
