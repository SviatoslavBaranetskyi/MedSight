import json
import os

from fastapi import UploadFile
from sqlalchemy.orm import Session

from src import ml_model
from src.models.models import Analysis
from src.utils.analysis_utils import save_user_image, get_disease_description

UPLOAD_FOLDER = "static/uploads/"


async def predict_disease(user_id: int, image: UploadFile, db: Session):
    image_url = await save_user_image(user_id, image)
    full_image_path = os.path.join(UPLOAD_FOLDER, image_url)

    with open(full_image_path, 'rb') as image_file:
        image_data = image_file.read()

    predicted_labels = ml_model.predict_image(image_data, ml_model.model, ml_model.transform, ml_model.class_map)
    result_as_string = json.dumps(predicted_labels)

    analysis = Analysis(user_id=user_id, image_url=image_url, result=result_as_string)
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    return {
        "message": "Prediction completed successfully.",
        "predicted_labels": predicted_labels,
        "image_url": f"/static/uploads/{image_url}"
    }


async def get_analysis_history(user_id: int, db: Session):
    analyses = db.query(Analysis).filter(Analysis.user_id == user_id).all()
    return [{"id": analysis.id, "result": json.loads(analysis.result),
             "created_at": analysis.created_at.isoformat(),
             "image_url": f"/static/uploads/{analysis.image_url}"} for analysis in analyses]


async def get_analysis_by_id(analysis_id: int, user_id: int, db: Session):
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id, Analysis.user_id == user_id).first()
    if not analysis:
        return None
    predicted_labels = json.loads(analysis.result)
    description = get_disease_description(predicted_labels)
    return {
        "analysis_id": analysis.id,
        "user_id": analysis.user_id,
        "result": predicted_labels,
        "description": description,
        "image_url": f"/static/uploads/{analysis.image_url}",
        "created_at": analysis.created_at.isoformat()
    }
