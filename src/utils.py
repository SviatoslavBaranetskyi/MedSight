import database
from sqlalchemy.orm import Session
from fastapi import Request, Depends, HTTPException, status
from fastapi.responses import RedirectResponse


def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_authenticated_user(request: Request, db: Session = Depends(get_db)):
    from auth import get_current_user
    token = request.cookies.get("access_token")

    if not token:
        return RedirectResponse(url="/login/", status_code=status.HTTP_303_SEE_OTHER)

    token = token.split(" ")[1] if " " in token else token
    try:
        user = get_current_user(token=token, db=db)
    except HTTPException:
        return RedirectResponse(url="/login/", status_code=status.HTTP_303_SEE_OTHER)

    return user
