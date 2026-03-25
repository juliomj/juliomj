from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = Field(default='pokemon-price-compare', alias='APP_NAME')
    env: str = Field(default='dev', alias='ENV')
    log_level: str = Field(default='INFO', alias='LOG_LEVEL')
    request_timeout_seconds: int = Field(default=12, alias='REQUEST_TIMEOUT_SECONDS')
    retry_attempts: int = Field(default=3, alias='RETRY_ATTEMPTS')
    cache_ttl_seconds: int = Field(default=300, alias='CACHE_TTL_SECONDS')
    match_min_score: int = Field(default=75, alias='MATCH_MIN_SCORE')
    rate_limit_per_minute: int = Field(default=120, alias='RATE_LIMIT_PER_MINUTE')
    myp_search_url: str = Field(default='https://www.mypcards.com.br/busca', alias='MYP_SEARCH_URL')
    liga_search_url: str = Field(default='https://www.ligapokemon.com.br/?view=cards/search', alias='LIGA_SEARCH_URL')
    enable_playwright_fallback: bool = Field(default=False, alias='ENABLE_PLAYWRIGHT_FALLBACK')
    myp_headers_user_agent: str = Field(default='Mozilla/5.0 (compatible; PokemonPriceBot/1.0)', alias='MYP_HEADERS_USER_AGENT')
    liga_headers_user_agent: str = Field(default='Mozilla/5.0 (compatible; PokemonPriceBot/1.0)', alias='LIGA_HEADERS_USER_AGENT')
    decision_min_savings_percent: float = Field(default=0, alias='DECISION_MIN_SAVINGS_PERCENT')


@lru_cache
def get_settings() -> Settings:
    return Settings()
