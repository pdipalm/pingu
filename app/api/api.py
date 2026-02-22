from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.targets import router as targets_router

app = FastAPI(title="Pingu", version="0.1.0")
app.include_router(health_router)
app.include_router(targets_router)
