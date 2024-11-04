from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def root():
    return {
        "message": "Welcome to the Disease Classification API!",
        "endpoints": {
            "register": {"path": "/auth/register", "method": "POST"},
            "login": {"path": "/auth/login", "method": "POST"},
            "predict": {"path": "/analysis/predict", "method": "POST", "form-data": "image"},
            "history": {"path": "/analysis/history", "method": "GET"},
            "analysis_detail": {"path": "/analysis/{analysis_id}", "method": "GET"},
            "profile": {"path": "/profile", "method": "GET"},
            "change_password": {"path": "/profile", "method": "POST"}
        },
        "description": "Use this API to classify diseases from X-ray images and manage analysis history."
    }
