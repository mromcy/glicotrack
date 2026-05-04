from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

from app.routers import auth, dashboard, glucose, records, reports, settings

app = FastAPI(title="GlicoTrack")

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(glucose.router)
app.include_router(records.router)
app.include_router(reports.router)
app.include_router(settings.router)


@app.get("/")
async def root():
    return RedirectResponse(url="/dashboard")


@app.exception_handler(303)
async def redirect_handler(request: Request, exc):
    return RedirectResponse(url=exc.headers["Location"])
