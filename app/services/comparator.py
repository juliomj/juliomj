from app.connectors.liga import LigaPokemonConnector
from app.connectors.myp import MypCardsConnector
from app.core.cache import QueryCache
from app.core.logging import get_logger
from app.core.settings import Settings
from app.models.schemas import CardQuery, CompareResult, SourceResult, StatusCode
from app.parsers.normalization import normalize_condition, normalize_text
from app.services.matching import select_best_listing

logger = get_logger(__name__)


class ComparisonService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.cache = QueryCache(ttl_seconds=settings.cache_ttl_seconds)
        self.liga = LigaPokemonConnector(
            search_url=settings.liga_search_url,
            user_agent=settings.liga_headers_user_agent,
            timeout=settings.request_timeout_seconds,
            retry_attempts=settings.retry_attempts,
        )
        self.myp = MypCardsConnector(
            search_url=settings.myp_search_url,
            user_agent=settings.myp_headers_user_agent,
            timeout=settings.request_timeout_seconds,
            retry_attempts=settings.retry_attempts,
        )

    async def compare(self, query: CardQuery) -> CompareResult:
        cache_key = f"{normalize_text(query.nome)}|{normalize_condition(query.condicao)}|{normalize_text(query.edicao)}|{query.threshold_percent}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        liga_result = await self._search_source(query, source='liga')
        myp_result = await self._search_source(query, source='myp')

        result = self._build_response(query, liga_result, myp_result)
        self.cache.set(cache_key, result)
        return result

    async def _search_source(self, query: CardQuery, source: str) -> SourceResult:
        connector = self.liga if source == 'liga' else self.myp
        try:
            listings = await connector.search(query)
        except Exception as exc:  # noqa: BLE001
            logger.warning('search_error', source=source, error=str(exc))
            return SourceResult(source=source, status=StatusCode.ERRO_TEMPORARIO, message='Falha ao consultar origem.')

        if not listings:
            return SourceResult(source=source, status=StatusCode.CARTA_NAO_ENCONTRADA, message='Sem listagens.')

        by_edition = [l for l in listings if normalize_text(query.edicao) in normalize_text(l.edition or l.name)]
        if not by_edition:
            return SourceResult(source=source, status=StatusCode.EDICAO_NAO_ENCONTRADA, listings=listings)

        condition = normalize_condition(query.condicao)
        by_condition = [l for l in by_edition if normalize_condition(l.condition or '') == condition]
        if not by_condition:
            return SourceResult(source=source, status=StatusCode.CONDICAO_NAO_ENCONTRADA, listings=by_edition)

        selected, ambiguous = select_best_listing(query, by_condition, self.settings.match_min_score)
        if ambiguous:
            return SourceResult(source=source, status=StatusCode.AMBIGUO, listings=by_condition)
        if not selected:
            return SourceResult(source=source, status=StatusCode.CARTA_NAO_ENCONTRADA, listings=by_condition)

        selected_same_card = [
            item for item in by_condition if normalize_text(item.name) == normalize_text(selected.name) and item.price is not None
        ]
        if selected_same_card:
            selected = min(selected_same_card, key=lambda x: x.price)

        return SourceResult(source=source, status=StatusCode.OK, listings=by_condition, selected=selected)

    def _build_response(self, query: CardQuery, liga: SourceResult, myp: SourceResult) -> CompareResult:
        preco_liga = liga.selected.price if liga.selected else None
        preco_myp = myp.selected.price if myp.selected else None

        diferenca_reais = round(preco_liga - preco_myp, 2) if preco_liga is not None and preco_myp is not None else None
        diferenca_percentual = (
            round(((preco_liga - preco_myp) / preco_liga) * 100, 2)
            if preco_liga not in (None, 0) and preco_myp is not None
            else None
        )

        if preco_liga is None or preco_myp is None:
            melhor_opcao = 'INDEFINIDO'
            vale = 'DADOS INSUFICIENTES'
        elif preco_myp < preco_liga:
            melhor_opcao = 'MYP'
            threshold = query.threshold_percent if query.threshold_percent is not None else self.settings.decision_min_savings_percent
            vale = 'SIM' if diferenca_percentual is not None and diferenca_percentual >= threshold else 'NÃO'
        elif preco_myp > preco_liga:
            melhor_opcao = 'LIGA'
            vale = 'NÃO'
        else:
            melhor_opcao = 'EMPATE'
            vale = 'NÃO'

        status_parts = [f"liga={liga.status}", f"myp={myp.status}"]
        return CompareResult(
            preco_liga=preco_liga,
            preco_myp=preco_myp,
            diferenca_reais=diferenca_reais,
            diferenca_percentual=diferenca_percentual,
            melhor_opcao=melhor_opcao,
            vale_a_pena_comprar_no_myp=vale,
            status_log='; '.join(status_parts),
            url_liga=liga.selected.url if liga.selected else None,
            url_myp=myp.selected.url if myp.selected else None,
            detalhes={
                'entrada': query.model_dump(),
                'liga_status': liga.status,
                'myp_status': myp.status,
                'liga_listings': [x.model_dump() for x in liga.listings],
                'myp_listings': [x.model_dump() for x in myp.listings],
            },
        )
