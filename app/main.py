from fastapi import FastAPI
from app.routers import check

app = FastAPI(title="Scam URL/UPI Reputation Checker")

app.include_router(check.router)

@app.get("/health")
def health_check():
    return {"status": "ok"}