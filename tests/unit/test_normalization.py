from app.parsers.normalization import normalize_condition, normalize_text, parse_price_brl


def test_normalize_text_removes_accent_and_upcases():
    assert normalize_text('Pokémon Éxample') == 'POKEMON EXAMPLE'


def test_normalize_condition_synonyms():
    assert normalize_condition('Near Mint') == 'NM'
    assert normalize_condition('dmg') == 'DMG'


def test_parse_price_brl():
    assert parse_price_brl('R$ 1.234,56') == 1234.56
    assert parse_price_brl('12,90') == 12.9
