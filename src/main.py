from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.db.database import engine, Base
from src.routers import user_routers, analysis_routers, health

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(user_routers.router)
app.include_router(analysis_routers.router_analysis)
app.include_router(health.router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
