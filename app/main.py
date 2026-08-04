from fastapi import FastAPI
from app.core.config import PROJECT_NAME
from app.routers.health import router as health_router
# main file 
app = FastAPI(title=PROJECT_NAME)

app.include_router(health_router, prefix="/api")