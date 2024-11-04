import json

from fastapi import APIRouter, Depends, UploadFile, HTTPException, status, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.models import models
from src.services.analysis_service import predict_disease, get_analysis_by_id
from src.utils.analysis_utils import get_authenticated_user

router_analysis = APIRouter(prefix="/analysis", tags=["Analysis management"])


@router_analysis.post("/predict")
async def predict_diseases(image: UploadFile, db: Session = Depends(get_db), user=Depends(get_authenticated_user)):
    try:
        result = await predict_disease(user.id, image, db)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router_analysis.get("/history")
async def get_analysis_history(request: Request, db: Session = Depends(get_db)):
    user = await get_authenticated_user(request, db)

    analyses = db.query(models.Analysis).filter(models.Analysis.user_id == user.id).all()

    analysis_history = []
    for analysis in analyses:
        analysis_data = {
            "id": analysis.id,
            "result": json.loads(analysis.result),
            "created_at": analysis.created_at.isoformat(),
            "image_url": f'static/uploads/{analysis.image_url}'
        }
        analysis_history.append(analysis_data)

    return JSONResponse(content=analysis_history)


@router_analysis.get("/{analysis_id}")
async def analysis_detail(analysis_id: int, db: Session = Depends(get_db), user=Depends(get_authenticated_user)):
    result = await get_analysis_by_id(analysis_id, user.id, db)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")
    return result
