import fitz  # PyMuPDF
import re
import math
import time
from typing import Union

# -----------------------------------------------------------------------------
# БЛОК КОДА ДЛЯ СУММАРИЗАЦИИ
# -----------------------------------------------------------------------------

STOP_WORDS = {'the', 'a', 'an', 'in', 'on', 'is', 'are', 'was', 'were', 'it', 'he', 'she', 'they', 
              'this', 'that', 'these', 'those', 'and', 'or', 'but', 'with', 'at', 'from', 'by', 
              'for', 'of', 'to', 'as', 'into', 'through', 'during', 'before', 'after', 'above',
              'below', 'between', 'under', 'over', 'again', 'further', 'then', 'once'}

def score_paragraph(paragraph: str) -> float:
    """
    Оценивает абзац/предложение на основе множественных эвристик.
    """
    score = 0.0
    para_lower = paragraph.lower()
    words = paragraph.split()
    
    if not words:
        return 0
    
    word_count = len(words)
    
    # 1. ЧИСЛА И СТАТИСТИКА - очень важно для научных текстов
    numbers = re.findall(r'\b\d+(?:\.\d+)?%?\b', paragraph)
    if numbers:
        score += 2.0 + len(numbers) * 0.5  # Бонус за каждое число
    
    # 2. ОПРЕДЕЛЕНИЯ И КЛЮЧЕВЫЕ ФРАЗЫ
    definition_patterns = [
        'is defined as', 'refers to', 'consists of', 'is a type of', 'means that',
        'can be described as', 'is called', 'known as', 'is termed', 'is considered',
        'we define', 'definition', 'denotes', 'signifies', 'represents'
    ]
    if any(pattern in para_lower for pattern in definition_patterns):
        score += 4.0
    
    # 3. ВАЖНЫЕ КЛЮЧЕВЫЕ СЛОВА (академические маркеры)
    important_keywords = [
        'important', 'significant', 'crucial', 'essential', 'critical', 'key',
        'fundamental', 'primary', 'main', 'major', 'principal', 'vital',
        'notable', 'remarkable', 'substantial', 'considerable'
    ]
    keyword_count = sum(1 for kw in important_keywords if kw in para_lower)
    score += keyword_count * 2.0
    
    # 4. ПРИЧИННО-СЛЕДСТВЕННЫЕ СВЯЗИ
    causal_markers = [
        'because', 'therefore', 'thus', 'hence', 'consequently', 'as a result',
        'leads to', 'causes', 'results in', 'due to', 'since', 'so that',
        'in order to', 'for this reason', 'this is why'
    ]
    if any(marker in para_lower for marker in causal_markers):
        score += 3.0
    
    # 5. КОНТРАСТНЫЕ И СРАВНИТЕЛЬНЫЕ КОНСТРУКЦИИ
    contrast_markers = [
        'however', 'but', 'although', 'whereas', 'while', 'on the other hand',
        'in contrast', 'conversely', 'nevertheless', 'nonetheless', 'unlike',
        'compared to', 'in comparison', 'similarly', 'likewise'
    ]
    if any(marker in para_lower for marker in contrast_markers):
        score += 2.5
    
    # 6. ВЫВОДЫ И ЗАКЛЮЧЕНИЯ
    conclusion_markers = [
        'in conclusion', 'to summarize', 'in summary', 'overall', 'finally',
        'in short', 'to sum up', 'ultimately', 'in essence', 'basically'
    ]
    if any(marker in para_lower for marker in conclusion_markers):
        score += 3.5
    
    # 7. ВВОДНЫЕ ФРАЗЫ ДЛЯ НОВЫХ КОНЦЕПЦИЙ
    introduction_markers = [
        'first', 'second', 'third', 'initially', 'to begin with', 'firstly',
        'secondly', 'next', 'furthermore', 'moreover', 'additionally', 'also'
    ]
    if any(marker in para_lower for marker in introduction_markers):
        score += 1.5
    
    # 8. НАУЧНЫЕ И ТЕХНИЧЕСКИЕ ТЕРМИНЫ (заглавные буквы в середине текста)
    capitalized_words = 0
    acronyms = 0
    for i, word in enumerate(words):
        clean_word = re.sub(r'[^\w]', '', word)
        if i > 0 and clean_word.istitle() and clean_word.lower() not in STOP_WORDS:
            capitalized_words += 1
        # Акронимы (все заглавные буквы, длина 2-6)
        if clean_word.isupper() and 2 <= len(clean_word) <= 6:
            acronyms += 1
    
    score += capitalized_words * 0.6
    score += acronyms * 1.5
    
    # 9. МАТЕМАТИЧЕСКИЕ И НАУЧНЫЕ СИМВОЛЫ
    math_symbols = ['=', '≈', '≠', '±', '×', '÷', '∑', '∫', '∆', '∇', '∞']
    if any(symbol in paragraph for symbol in math_symbols):
        score += 2.5
    
    # 10. ЦИТАТЫ И ССЫЛКИ
    if re.search(r'\[\d+\]|\(\d{4}\)|et al\.', paragraph):
        score += 2.0
    
    # 11. ФОРМУЛЫ И УРАВНЕНИЯ (скобки, специальные символы)
    if re.search(r'\(.*[a-z].*=.*\)|[a-zA-Z]\s*=\s*[a-zA-Z0-9]', paragraph):
        score += 3.0
    
    # 12. СПИСКИ И ПЕРЕЧИСЛЕНИЯ
    if re.search(r'^\s*[\-\*\•]|^\s*\d+[\.\)]', paragraph):
        score += 1.0
    
    # 13. ВОПРОСИТЕЛЬНЫЕ ПРЕДЛОЖЕНИЯ (могут вводить важные темы)
    if '?' in paragraph:
        score += 1.5
    
    # 14. ОПТИМАЛЬНАЯ ДЛИНА ПРЕДЛОЖЕНИЯ
    # Слишком короткие или слишком длинные предложения менее информативны
    if 10 <= word_count <= 30:
        score += 2.0
    elif 30 < word_count <= 50:
        score += 1.0
    elif word_count < 5:
        score -= 2.0  # Штраф за очень короткие предложения
    
    # 15. КАВЫЧКИ (цитаты, определения)
    if '"' in paragraph or '"' in paragraph or '"' in paragraph or "'" in paragraph:
        score += 1.5
    
    # 16. ДВОЕТОЧИЕ (часто вводит важную информацию или списки)
    if ':' in paragraph:
        score += 1.0
    
    # 17. МЕТОДОЛОГИЯ И ПРОЦЕССЫ
    method_markers = [
        'method', 'approach', 'technique', 'procedure', 'process', 'algorithm',
        'framework', 'model', 'system', 'mechanism', 'strategy'
    ]
    if any(marker in para_lower for marker in method_markers):
        score += 2.0
    
    # 18. РЕЗУЛЬТАТЫ И НАХОДКИ
    result_markers = [
        'results show', 'found that', 'discovered', 'observed', 'demonstrated',
        'proved', 'indicated', 'revealed', 'showed that', 'evidence suggests'
    ]
    if any(marker in para_lower for marker in result_markers):
        score += 3.0
    
    # 19. ПРОБЛЕМЫ И ВЫЗОВЫ
    problem_markers = [
        'problem', 'challenge', 'issue', 'difficulty', 'limitation', 'constraint',
        'obstacle', 'barrier', 'drawback', 'weakness'
    ]
    if any(marker in para_lower for marker in problem_markers):
        score += 2.0
    
    # 20. ЛОГАРИФМИЧЕСКИЙ БОНУС ЗА ДЛИНУ (чтобы не было доминирования)
    score += math.log(word_count + 1) * 0.15
    
    # 21. ПОЗИЦИОННЫЙ БОНУС (первое предложение часто важное)
    # Это можно будет использовать позже, если передавать позицию
    
    # 22. РАЗНООБРАЗИЕ СЛОВАРЯ (уникальные слова)
    unique_words = len(set(word.lower() for word in words))
    lexical_diversity = unique_words / word_count if word_count > 0 else 0
    score += lexical_diversity * 2.0
    
    return score

def summarize_to_fixed_tokens(
    text: str, 
    target_token_count: int, 
    num_chunks: int = 10
) -> str:
    """
    Создает быструю экстрактивную саммаризацию на уровне абзацев.
    """
    print("Шаг 1: Разделение текста на абзацы...")
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    if not paragraphs:
        return ""

    total_paragraphs = len(paragraphs)
    print(f"Найдено {total_paragraphs} абзацев.")

    para_lengths = [len(p.split()) for p in paragraphs]
    total_tokens_in_doc = sum(para_lengths)

    if total_tokens_in_doc < target_token_count:
        print("Предупреждение: Весь документ меньше целевого размера. Возвращается полный текст.")
        return text

    print("Шаг 2: Разделение на чанки и оценка абзацев...")
    chunk_size = math.ceil(total_paragraphs / num_chunks)
    selected_paragraphs_indices = set()
    
    target_tokens_per_chunk = target_token_count / num_chunks
    
    for i in range(num_chunks):
        start_idx = i * chunk_size
        end_idx = min(start_idx + chunk_size, total_paragraphs)
        
        chunk_paragraphs = []
        for j in range(start_idx, end_idx):
            score = score_paragraph(paragraphs[j])
            chunk_paragraphs.append((score, j, para_lengths[j]))
        
        chunk_paragraphs.sort(key=lambda x: x[0], reverse=True)
        
        current_chunk_tokens = 0
        for score, original_idx, length in chunk_paragraphs:
            if current_chunk_tokens + length <= target_tokens_per_chunk:
                selected_paragraphs_indices.add(original_idx)
                current_chunk_tokens += length
            elif current_chunk_tokens == 0:
                 selected_paragraphs_indices.add(original_idx)
                 break

    print(f"Шаг 3: Сборка итогового конспекта... Выбрано {len(selected_paragraphs_indices)} абзацев.")
    sorted_indices = sorted(list(selected_paragraphs_indices))
    
    summary = "\n\n".join([paragraphs[i] for i in sorted_indices])
    
    final_token_count = len(summary.split())
    print(f"Финальный размер конспекта: примерно {final_token_count} токенов.")
    
    return summary

