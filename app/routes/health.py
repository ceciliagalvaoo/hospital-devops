from fastapi import APIRouter, Depends, Response, status

from app.db import database_is_available

router = APIRouter()


@router.get("/health")
def health(
    response: Response,
    database_available: bool = Depends(database_is_available),
) -> dict[str, str]:
    if not database_available:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "error", "database": "unavailable"}
    return {"status": "ok", "database": "ok"}
