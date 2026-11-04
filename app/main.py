from fastapi import FastAPI

from app.routes import auth, health

app = FastAPI(title="Hospital Management")
app.include_router(health.router)
app.include_router(auth.router)
