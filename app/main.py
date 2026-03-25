from fastapi import Depends, FastAPI, HTTPException

from app.core.logging import configure_logging
from app.core.rate_limit import SlidingWindowRateLimiter
from app.core.settings import Settings, get_settings
from app.models.schemas import BatchRequest, BatchResponse, CardQuery, CompareResult
from app.services.comparator import ComparisonService

app = FastAPI(title='Pokemon Price Comparator', version='1.0.0')


@app.on_event('startup')
async def startup() -> None:
    settings = get_settings()
    configure_logging(settings)
    app.state.service = ComparisonService(settings)
    app.state.limiter = SlidingWindowRateLimiter(settings.rate_limit_per_minute)


def get_service() -> ComparisonService:
    return app.state.service


def rate_limiter() -> SlidingWindowRateLimiter:
    return app.state.limiter


@app.get('/health')
async def health(settings: Settings = Depends(get_settings)):
    return {'status': 'ok', 'app': settings.app_name, 'env': settings.env}


@app.post('/compare', response_model=CompareResult)
async def compare_card(
    payload: CardQuery,
    service: ComparisonService = Depends(get_service),
    limiter: SlidingWindowRateLimiter = Depends(rate_limiter),
):
    if not limiter.allow():
        raise HTTPException(status_code=429, detail='Rate limit exceeded')
    return await service.compare(payload)


@app.post('/compare/batch', response_model=BatchResponse)
async def compare_batch(
    payload: BatchRequest,
    service: ComparisonService = Depends(get_service),
    limiter: SlidingWindowRateLimiter = Depends(rate_limiter),
):
    if not limiter.allow():
        raise HTTPException(status_code=429, detail='Rate limit exceeded')

    results = []
    for item in payload.items:
        results.append(await service.compare(item))
    return BatchResponse(results=results)
