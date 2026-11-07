from fastapi import Depends, FastAPI

from app.csrf import csrf_protect
from app.routes import auth, health

# CSRF protection applies to every route; safe methods pass through unchecked.
app = FastAPI(title="Hospital Management", dependencies=[Depends(csrf_protect)])
app.include_router(health.router)
app.include_router(auth.router)
