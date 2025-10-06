import spacy
import spacy.matcher
from collections import Counter
import fitz  # PyMuPDF
from pathlib import Path
import time
from typing import Union


try:
    nlp = spacy.load("en_core_web_sm", exclude=["parser"])
    if 'sentencizer' not in nlp.pipe_names:
        nlp.add_pipe('sentencizer', first=True)
    
    definition_pattern = [{"OP": "?"}, {"LEMMA": "be"}, {"POS": "DET"}]
    matcher = spacy.matcher.Matcher(nlp.vocab)
    matcher.add("DEFINITION", [definition_pattern])
    print("Модель spaCy успешно загружена.")
except IOError:
    print("Ошибка: Модель 'en_core_web_sm' не найдена.")
    print("Пожалуйста, установите её, выполнив команду: python -m spacy download en_core_web_sm")
    nlp = None # Устанавливаем в None, чтобы избежать ошибок при импорте
    matcher = None

# --- ФУНКЦИЯ КОНСПЕКТИРОВАНИЯ ---
def summarize_to_fixed_tokens(
    text: str,
    target_token_count: int = 50000,
    context_window: int = 2
) -> str:
    """
    Создает конспект, объем которого приближен к заданному количеству токенов,
    итеративно добавляя самые важные предложения и их контекст.
    """
    if not nlp:
        raise RuntimeError("Модель spaCy не была загружена. Невозможно продолжить.")
        
    if not text.strip():
        return ""

    text_chunks = [p.strip() for p in text.split('\n\n') if p.strip()]
    if not text_chunks:
        return ""

    all_sents_spans = []
    all_scored_sents = []
    
    # Шаг 1: Обработка текста и скоринг всех предложений
    print("Шаг 1: Анализ и оценка предложений...")
    for doc in nlp.pipe(text_chunks, n_process=-1, batch_size=100):
        sents_in_doc = list(doc.sents)
        all_sents_spans.extend(sents_in_doc)
        
        matches = matcher(doc)
        definition_sent_starts = {doc[match[1]].sent.start for match in matches}
        nouns = [
            token.lemma_.lower() for token in doc 
            if token.pos_ in {'NOUN', 'PROPN'} and not token.is_stop and len(token.text) > 3
        ]
        local_keywords_set = {word for word, freq in Counter(nouns).most_common(5)}
        
        for sent in sents_in_doc:
            score = 0
            sent_lemmas = {token.lemma_.lower() for token in sent if not token.is_punct}
            score += len(sent_lemmas.intersection(local_keywords_set)) * 5
            if sent.start in definition_sent_starts:
                score += 3
            score += len(sent.ents)
            all_scored_sents.append((score, len(all_sents_spans) - 1))

    total_sents_in_doc = len(all_sents_spans)
    if total_sents_in_doc == 0:
        return ""

    total_tokens_in_doc = sum(len(s) for s in all_sents_spans)
    if total_tokens_in_doc < target_token_count:
        print(f"Предупреждение: Весь документ ({total_tokens_in_doc} токенов) меньше целевого размера ({target_token_count} токенов). Возвращается полный текст.")
        return " ".join([s.text for s in all_sents_spans])

    # Шаг 2: Сортировка всех предложений по убыванию балла
    all_scored_sents.sort(key=lambda x: x[0], reverse=True)

    print("Шаг 2: Сборка конспекта до целевого объема...")
    final_indices = set()
    current_token_count = 0
    sentence_lengths = [len(s) for s in all_sents_spans]

    for score, pos in all_scored_sents:
        if current_token_count >= target_token_count:
            break

        if pos in final_indices:
            continue

        start_index = max(0, pos - context_window)
        end_index = min(total_sents_in_doc, pos + context_window + 1)
        
        for i in range(start_index, end_index):
            if i not in final_indices:
                final_indices.add(i)
                current_token_count += sentence_lengths[i]

    # Шаг 4: Сортировка и сборка финального текста
    sorted_indices = sorted(list(final_indices))
    summary_text = " ".join([all_sents_spans[i].text.strip() for i in sorted_indices])
    
    # Отчет о фактическом размере
    final_token_count = len(nlp(summary_text, disable=["parser", "tagger", "ner", "lemmatizer", "attribute_ruler"]))
    print(f"Фактический размер конспекта: ~{final_token_count} токенов.")

    return summary_text

