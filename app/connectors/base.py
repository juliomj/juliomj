from abc import ABC, abstractmethod

import httpx
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

from app.models.schemas import CardQuery, Listing
from app.parsers.normalization import normalize_condition, parse_price_brl


class BaseConnector(ABC):
    source_name: str

    def __init__(self, search_url: str, user_agent: str, timeout: int, retry_attempts: int) -> None:
        self.search_url = search_url
        self.headers = {'User-Agent': user_agent}
        self.timeout = timeout
        self.retry_attempts = retry_attempts

    @retry(wait=wait_exponential(multiplier=1, min=1, max=8), stop=stop_after_attempt(3), reraise=True)
    async def _fetch(self, client: httpx.AsyncClient, query: str) -> str:
        response = await client.get(self.search_url, params=self.build_params(query), headers=self.headers)
        response.raise_for_status()
        return response.text

    async def search(self, query: CardQuery) -> list[Listing]:
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            html = await self._fetch(client, query.nome)
        return self.parse_search_results(html)

    @abstractmethod
    def build_params(self, query: str) -> dict:
        raise NotImplementedError

    @abstractmethod
    def parse_search_results(self, html: str) -> list[Listing]:
        raise NotImplementedError

    def _extract_condition(self, text: str) -> str | None:
        for token in ['NM', 'MINT', 'NEAR MINT', 'SP', 'LP', 'MP', 'HP', 'DMG']:
            if token in (text or '').upper():
                return normalize_condition(token)
        return None

    def _listing_from_node(self, node, source: str, base_url: str = '') -> Listing | None:
        name = node.select_one('.product-name, .item-name, h2, h3, a')
        if not name:
            return None

        price_node = node.select_one('.price, .product-price, .valor, [data-price]')
        edition_node = node.select_one('.edition, .set-name, .product-edition, .expansion')
        condition_node = node.select_one('.condition, .estado, .product-condition')
        url_node = node.select_one('a[href]')

        url = None
        if url_node and url_node.get('href'):
            href = url_node['href']
            url = href if href.startswith('http') else f"{base_url.rstrip('/')}/{href.lstrip('/')}"

        price = parse_price_brl(price_node.get_text(' ', strip=True) if price_node else '')
        name_text = name.get_text(' ', strip=True)
        raw_condition = condition_node.get_text(' ', strip=True) if condition_node else name_text

        return Listing(
            source=source,
            name=name_text,
            edition=edition_node.get_text(' ', strip=True) if edition_node else None,
            condition=self._extract_condition(raw_condition),
            price=price,
            url=url,
        )

    def _soup(self, html: str) -> BeautifulSoup:
        return BeautifulSoup(html, 'lxml')
