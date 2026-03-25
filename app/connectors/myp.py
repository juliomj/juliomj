from app.connectors.base import BaseConnector
from app.models.schemas import Listing


class MypCardsConnector(BaseConnector):
    source_name = 'myp'

    def build_params(self, query: str) -> dict:
        return {'q': query}

    def parse_search_results(self, html: str) -> list[Listing]:
        soup = self._soup(html)
        cards = soup.select('.product-item, .search-result-item, .item, .vitrine-item')
        listings = [self._listing_from_node(node, 'myp', 'https://www.mypcards.com.br') for node in cards]
        return [listing for listing in listings if listing and listing.price is not None]
