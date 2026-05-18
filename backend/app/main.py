from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from .api import router
import os

app = FastAPI(title="Clinic Analytics")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(router)

@app.get("/", response_class=HTMLResponse)
def root():
    """Отдаем главную страницу"""
    html_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()