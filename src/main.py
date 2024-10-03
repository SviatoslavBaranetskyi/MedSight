import json
import base64
from fastapi import FastAPI, Form, UploadFile, File
from fastapi.responses import HTMLResponse
from starlette.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

import models, auth, ml_model
from utils import *
from database import engine
from auth import create_access_token
from schemas import UserResponse
from router import router_auth

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


def b64encode_image(image_data):
    return base64.b64encode(image_data).decode('utf-8')


# Filter registration
templates.env.filters['b64encode'] = b64encode_image


@router_auth.get("/register/", response_class=HTMLResponse)
def get_register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router_auth.post("/register/")
def register(username: str = Form(...), email: str = Form(...), password: str = Form(...),
             db: Session = Depends(get_db)):
    db_user = auth.get_user(db, username=username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = auth.get_password_hash(password)
    new_user = models.User(username=username, email=email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return RedirectResponse(url="/login/", status_code=status.HTTP_303_SEE_OTHER)


@router_auth.get("/login/", response_class=HTMLResponse)
def get_login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router_auth.post("/login/")
def login_for_access_token(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = auth.authenticate_user(db, username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True, secure=True)
    return response


@app.get("/")
async def read_root(request: Request, db: Session = Depends(get_db)):
    user = await get_authenticated_user(request, db)
    if isinstance(user, RedirectResponse):
        return user
    return templates.TemplateResponse("index.html", {"request": request, "user": user})


@router_auth.get("/logout/")
def logout():
    response = RedirectResponse(url="/login/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token")
    return response


@app.get("/analyze/", response_class=HTMLResponse)
async def get_current_analysis(request: Request, db: Session = Depends(get_db)):
    user = await get_authenticated_user(request, db)
    if isinstance(user, RedirectResponse):
        return user

    current_analysis = db.query(models.Analysis).filter(models.Analysis.user_id == user.id).order_by(
        models.Analysis.created_at.desc()).first()

    if not current_analysis:
        return templates.TemplateResponse("no_analysis.html", {"request": request})

    return templates.TemplateResponse("current_analysis.html", {"request": request, "analysis": current_analysis})


@app.post("/predict/")
async def predict_diseases(request: Request, image: UploadFile = File(...), db: Session = Depends(get_db)):
    user = await get_authenticated_user(request, db)
    if isinstance(user, RedirectResponse):
        return user

    image_data = await image.read()
    predicted_labels = ml_model.predict_image(image_data, ml_model.model, ml_model.transform, ml_model.class_map)

    result_as_string = json.dumps(predicted_labels)
    analysis = models.Analysis(user_id=user.id, image_data=image_data, result=result_as_string)
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/users/me", response_model=UserResponse)
async def current_user(request: Request, db: Session = Depends(get_db)):
    user = await check_auth(request, db)
    return user


app.include_router(router_auth)
