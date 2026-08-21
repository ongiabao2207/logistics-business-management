from fastapi import FastAPI

from app.db.base import Base
from app.db.session import engine
from app.models import contract_model
from app.routers.contract_router import router as contract_router


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Contract Service")
app.include_router(contract_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
