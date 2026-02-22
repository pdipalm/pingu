from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.results import router as results_router
from app.api.routes.target_results import router as target_results_router
from app.api.routes.targets import router as targets_router

app = FastAPI(title="Pingu", version="0.1.0")
app.include_router(health_router)
app.include_router(targets_router)
app.include_router(results_router)
app.include_router(target_results_router)
