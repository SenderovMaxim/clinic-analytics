from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .api import router

app = FastAPI(title="Clinic Doctor Analytics")
app.include_router(router)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def index():
    from fastapi.responses import FileResponse
    return FileResponse("static/index.html")