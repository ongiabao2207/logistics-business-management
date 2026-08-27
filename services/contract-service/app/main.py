from fastapi import FastAPI

from app.routers.contract_router import router as contract_router


app = FastAPI(title="Contract Service")
app.include_router(contract_router, prefix="/api/v1")


@app.get("/api/v1/health")
def health_check():
    return {"status": "ok"}
