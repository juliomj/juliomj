from app.models.schemas import CardQuery, Listing
from app.services.matching import select_best_listing


def test_select_best_listing_returns_best_confidence():
    query = CardQuery(nome='Pikachu 001/025', condicao='NM', edicao='Celebrations')
    listings = [
        Listing(source='liga', name='Pikachu 001/025', edition='Celebrations', condition='NM', price=20.0),
        Listing(source='liga', name='Pikachu V', edition='Vivid Voltage', condition='NM', price=10.0),
    ]
    selected, ambiguous = select_best_listing(query, listings, min_score=70)
    assert ambiguous is False
    assert selected is not None
    assert selected.name == 'Pikachu 001/025'
