import re
import unicodedata

CONDITION_SYNONYMS = {
    'NM': {'NM', 'NEAR MINT', 'MINT', 'N/M'},
    'SP': {'SP', 'SLIGHTLY PLAYED'},
    'LP': {'LP', 'LIGHT PLAYED'},
    'MP': {'MP', 'MODERATELY PLAYED'},
    'HP': {'HP', 'HEAVILY PLAYED'},
    'DMG': {'DMG', 'DAMAGED'},
}


def strip_accents(text: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')


def normalize_text(text: str) -> str:
    text = strip_accents(text or '').upper().strip()
    text = re.sub(r'\s+', ' ', text)
    return text


def normalize_condition(condition: str) -> str:
    base = normalize_text(condition)
    for normalized, aliases in CONDITION_SYNONYMS.items():
        if base in aliases:
            return normalized
    return base


def extract_card_number(text: str) -> str | None:
    match = re.search(r'(\d{1,3}\s*/\s*\d{1,3}|#\d{1,3})', normalize_text(text))
    return match.group(1).replace(' ', '') if match else None


def parse_price_brl(text: str) -> float | None:
    if not text:
        return None
    cleaned = re.sub(r'[^\d,\.]', '', text)
    if ',' in cleaned and '.' in cleaned:
        cleaned = cleaned.replace('.', '').replace(',', '.')
    elif ',' in cleaned:
        cleaned = cleaned.replace(',', '.')
    try:
        return float(cleaned)
    except ValueError:
        return None
