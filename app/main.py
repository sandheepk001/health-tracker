from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.database import engine, Base
import os

app = FastAPI(title="Health Tracker")

from app.models import user, stats, food, food_log, body_measurement, workout, meal_template

Base.metadata.create_all(bind=engine)

from app.routers import auth, users, stats as stats_router, foods, food_log as food_log_router
from app.routers import summary, password_reset, measurements, workouts, templates, analysis, reports

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(stats_router.router)
app.include_router(foods.router)
app.include_router(food_log_router.router)
app.include_router(summary.router)
app.include_router(password_reset.router)
app.include_router(measurements.router)
app.include_router(workouts.router)
app.include_router(templates.router)
app.include_router(analysis.router)
app.include_router(reports.router)
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