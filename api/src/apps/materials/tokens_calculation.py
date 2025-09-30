import tiktoken
import PyPDF2
from io import BytesIO
from typing import Optional
from lib.clients.tiktoken import ENCODERS
from lib.config import LLMS


def count_pdf_tokens(pdf_bytes: bytes) -> int:
    """
    Подсчитывает количество токенов в PDF файле.

    Args:
        pdf_bytes: Байты PDF файла

    Returns:
        Количество токенов в тексте PDF

    Raises:
        Exception: Если не удается обработать PDF файл
    """
    try:
        # Создаем BytesIO объект из байтов
        pdf_stream = BytesIO(pdf_bytes)

        # Извлекаем текст из PDF
        pdf_reader = PyPDF2.PdfReader(pdf_stream)
        text = ""

        for page in pdf_reader.pages:
            text += page.extract_text()

        # Получаем энкодер для подсчета токенов
        encoding = ENCODERS[LLMS.GPT_5_MINI]

        # Подсчитываем токены
        tokens = encoding.encode(text)

        return len(tokens)

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
