from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.database import engine, Base
import os

app = FastAPI(title="Health Tracker")

from app.models import user, stats, food, food_log
Base.metadata.create_all(bind=engine)

from app.routers import auth, users, stats, foods, food_log, summary
from app.routers import auth, users, stats, foods, food_log, summary, password_reset

app.include_router(password_reset.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(stats.router)
app.include_router(foods.router)
app.include_router(food_log.router)
app.include_router(summary.router)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/")
def root():
    return FileResponse("app/static/index.html")

@app.get("/{page}", include_in_schema=False)
def serve_page(page: str):
    path = f"app/static/pages/{page}.html"
    if os.path.exists(path):
        return FileResponse(path)
    return FileResponse("app/static/index.html")