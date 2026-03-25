from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class StatusCode(str, Enum):
    OK = 'OK'
    AMBIGUO = 'AMBÍGUO'
    EDICAO_NAO_ENCONTRADA = 'EDIÇÃO NÃO ENCONTRADA'
    CONDICAO_NAO_ENCONTRADA = 'CONDIÇÃO NÃO ENCONTRADA'
    ERRO_TEMPORARIO = 'ERRO TEMPORÁRIO'
    CARTA_NAO_ENCONTRADA = 'CARTA NÃO ENCONTRADA'
    DADOS_INSUFICIENTES = 'DADOS INSUFICIENTES'


class CardQuery(BaseModel):
    nome: str = Field(min_length=1)
    condicao: str = Field(min_length=1)
    edicao: str = Field(min_length=1)
    threshold_percent: float | None = Field(default=None, ge=0)


class Listing(BaseModel):
    source: Literal['liga', 'myp']
    name: str
    edition: str | None = None
    condition: str | None = None
    price: float | None = None
    url: str | None = None
    card_number: str | None = None
    confidence: float = 0.0


class SourceResult(BaseModel):
    source: Literal['liga', 'myp']
    status: StatusCode
    listings: list[Listing] = Field(default_factory=list)
    selected: Listing | None = None
    message: str = ''


class CompareResult(BaseModel):
    preco_liga: float | None
    preco_myp: float | None
    diferenca_reais: float | None
    diferenca_percentual: float | None
    melhor_opcao: Literal['MYP', 'LIGA', 'EMPATE', 'INDEFINIDO']
    vale_a_pena_comprar_no_myp: Literal['SIM', 'NÃO', 'DADOS INSUFICIENTES']
    status_log: str
    url_liga: str | None
    url_myp: str | None
    detalhes: dict


class BatchRequest(BaseModel):
    items: list[CardQuery]


class BatchResponse(BaseModel):
    results: list[CompareResult]
