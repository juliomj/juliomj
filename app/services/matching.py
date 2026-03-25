from rapidfuzz import fuzz

from app.models.schemas import CardQuery, Listing
from app.parsers.normalization import extract_card_number, normalize_condition, normalize_text


def score_listing(query: CardQuery, listing: Listing) -> float:
    name_score = fuzz.token_set_ratio(normalize_text(query.nome), normalize_text(listing.name))
    edition_score = fuzz.partial_ratio(normalize_text(query.edicao), normalize_text(listing.edition or ''))

    query_number = extract_card_number(query.nome)
    listing_number = extract_card_number(' '.join([listing.name, listing.edition or '', listing.card_number or '']))
    number_bonus = 10 if query_number and listing_number and query_number == listing_number else 0

    condition_match = normalize_condition(query.condicao) == normalize_condition(listing.condition or '')
    condition_bonus = 15 if condition_match else -20

    score = 0.5 * name_score + 0.35 * edition_score + number_bonus + condition_bonus
    return max(0, min(100, score))


def select_best_listing(query: CardQuery, listings: list[Listing], min_score: int) -> tuple[Listing | None, bool]:
    if not listings:
        return None, False

    scored = []
    for listing in listings:
        listing.confidence = score_listing(query, listing)
        scored.append(listing)

    scored.sort(key=lambda x: (x.confidence, -(x.price or float('inf'))), reverse=True)
    top = scored[0]
    if top.confidence < min_score:
        return None, False

    if len(scored) > 1 and abs(scored[0].confidence - scored[1].confidence) < 2:
        return None, True
    return top, False
