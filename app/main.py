from fastapi import FastAPI
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.limiter import limiter

from app.routers import check, report

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="Scam URL/UPI Reputation Checker")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(check.router)
app.include_router(report.router)

@app.get("/health")
def health_check():
    return {"status": "ok"}

