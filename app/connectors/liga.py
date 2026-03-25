from app.connectors.base import BaseConnector
from app.models.schemas import Listing


class LigaPokemonConnector(BaseConnector):
    source_name = 'liga'

    def build_params(self, query: str) -> dict:
        return {'search': query}

    def parse_search_results(self, html: str) -> list[Listing]:
        soup = self._soup(html)
        cards = soup.select('.product-item, .card-item, .item-card, .list-item')
        listings = [self._listing_from_node(node, 'liga', 'https://www.ligapokemon.com.br') for node in cards]
        return [listing for listing in listings if listing and listing.price is not None]
