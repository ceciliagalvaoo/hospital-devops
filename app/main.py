from fastapi import FastAPI

from app.routes import health

app = FastAPI(title="Hospital Management")
app.include_router(health.router)
