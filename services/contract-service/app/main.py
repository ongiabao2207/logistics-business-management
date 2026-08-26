from fastapi import FastAPI

from app.routers.contract_router import router as contract_router


app = FastAPI(title="Contract Service")
app.include_router(contract_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
