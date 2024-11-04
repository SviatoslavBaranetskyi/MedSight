import json
import os
import uuid

from fastapi import Depends, HTTPException, status, UploadFile, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.utils.auth_utils import get_current_user

UPLOAD_FOLDER = "static/uploads/"
XRAY_INFO_FILE = "src/xray_info.json"


def load_disease_info():
    with open(XRAY_INFO_FILE, 'r') as file:
        return json.load(file)


DISEASE_INFO = load_disease_info()


async def get_authenticated_user(request: Request, db: Session = Depends(get_db)):
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    token = auth_header.split(" ")[1] if " " in auth_header else auth_header

    try:
        user = get_current_user(token=token, db=db)
    except HTTPException:
        return RedirectResponse(url="/auth/login/", status_code=status.HTTP_303_SEE_OTHER)

    return user


async def save_user_image(user_id: int, file: UploadFile):
    user_dir = os.path.join(UPLOAD_FOLDER, f'user_{user_id}')
    os.makedirs(user_dir, exist_ok=True)

    file_extension = file.filename.split('.')[-1]
    file_name = f"{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join(user_dir, file_name)

    with open(file_path, 'wb') as f:
        f.write(await file.read())

    return os.path.join(f'user_{user_id}', file_name).replace("\\", "/")


def get_disease_description(predicted_labels):
    return {disease: DISEASE_INFO.get(disease, "Description not available") for disease in predicted_labels}
