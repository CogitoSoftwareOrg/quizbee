import tiktoken
import PyPDF2
from io import BytesIO
from typing import Optional


def count_pdf_tokens(pdf_bytes: bytes, encoding_name: str = "cl100k_base") -> int:
    """
    Подсчитывает количество токенов в PDF файле.
    
    Args:
        pdf_bytes: Байты PDF файла
        encoding_name: Название кодировки для tiktoken (по умолчанию cl100k_base для GPT-4)
    
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
        encoding = tiktoken.get_encoding(encoding_name)
        
        # Подсчитываем токены
        tokens = encoding.encode(text)
        
        return len(tokens)
        
    except Exception as e:
        raise Exception(f"Ошибка при обработке PDF файла: {str(e)}")


def count_text_tokens(text: str, encoding_name: str = "cl100k_base") -> int:
    """
    Подсчитывает количество токенов в тексте.
    
    Args:
        text: Текст для подсчета токенов
        encoding_name: Название кодировки для tiktoken
    
    Returns:
        Количество токенов в тексте
    """
    try:
        encoding = tiktoken.get_encoding(encoding_name)
        tokens = encoding.encode(text)
        return len(tokens)
    except Exception as e:
        raise Exception(f"Ошибка при подсчете токенов: {str(e)}")