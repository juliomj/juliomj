import pytest

from app.core.settings import Settings
from app.models.schemas import CardQuery, Listing, StatusCode
from app.services.comparator import ComparisonService


@pytest.mark.asyncio
async def test_compare_happy_path_with_myp_cheaper(monkeypatch):
    settings = Settings()
    service = ComparisonService(settings)

    async def fake_search_liga(_query):
        return [Listing(source='liga', name='Charizard 4/102', edition='Base Set', condition='NM', price=500.0, url='liga-url')]

    async def fake_search_myp(_query):
        return [Listing(source='myp', name='Charizard 4/102', edition='Base Set', condition='NM', price=450.0, url='myp-url')]

    monkeypatch.setattr(service.liga, 'search', fake_search_liga)
    monkeypatch.setattr(service.myp, 'search', fake_search_myp)

    result = await service.compare(CardQuery(nome='Charizard 4/102', condicao='NM', edicao='Base Set'))
    assert result.preco_liga == 500.0
    assert result.preco_myp == 450.0
    assert result.melhor_opcao == 'MYP'
    assert result.vale_a_pena_comprar_no_myp == 'SIM'


@pytest.mark.asyncio
async def test_compare_condition_not_found(monkeypatch):
    settings = Settings()
    service = ComparisonService(settings)

    async def fake_search(_query):
        return [Listing(source='liga', name='Mewtwo', edition='Base Set', condition='LP', price=30.0)]

    monkeypatch.setattr(service.liga, 'search', fake_search)
    monkeypatch.setattr(service.myp, 'search', fake_search)

    result = await service.compare(CardQuery(nome='Mewtwo', condicao='NM', edicao='Base Set'))
    assert 'CONDIÇÃO NÃO ENCONTRADA' in result.status_log
    assert result.vale_a_pena_comprar_no_myp == 'DADOS INSUFICIENTES'


@pytest.mark.asyncio
async def test_compare_edition_not_found(monkeypatch):
    settings = Settings()
    service = ComparisonService(settings)

    async def fake_search(_query):
        return [Listing(source='myp', name='Blastoise', edition='Jungle', condition='NM', price=100.0)]

    monkeypatch.setattr(service.liga, 'search', fake_search)
    monkeypatch.setattr(service.myp, 'search', fake_search)

    result = await service.compare(CardQuery(nome='Blastoise', condicao='NM', edicao='Base Set'))
    assert StatusCode.EDICAO_NAO_ENCONTRADA in result.status_log
