from fastapi import FastAPI, Depends, Form, Request, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

import models, auth
from utils import *
from database import engine
from auth import create_access_token

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/register/", response_class=HTMLResponse)
def get_register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@app.post("/register/")
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
    # Редирект на страницу логина после успешной регистрации
    return RedirectResponse(url="/login/", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/login/", response_class=HTMLResponse)
def get_login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login/")
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
    # Устанавливаем JWT-токен в cookie
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    return response


@app.get("/", response_class=HTMLResponse)
def read_root(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")

    if not token:
        return RedirectResponse(url="/login/", status_code=status.HTTP_303_SEE_OTHER)

    token = token.split(" ")[1] if " " in token else token
    try:
        current_user = auth.get_current_user(db=db, token=token)
    except HTTPException:
        return RedirectResponse(url="/login/", status_code=status.HTTP_303_SEE_OTHER)

    return templates.TemplateResponse("index.html", {"request": request, "user": current_user})


@app.get("/logout/")
def logout():
    response = RedirectResponse(url="/login/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token")
    return response