from fastapi import FastAPI

from app.db.base import Base
from app.db.session import engine
from app.routers.production_router import router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Production Service", version="1.0.0")
app.include_router(router)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
