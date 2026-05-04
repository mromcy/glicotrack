import os
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

from app.routers import auth, dashboard, glucose, records, reports, settings

app = FastAPI(title="GlicoTrack")

# diagnóstico temporário
_url = os.environ.get("SUPABASE_URL", "")
_key = os.environ.get("SUPABASE_ANON_KEY", "")
print(f"[D1]{_url[:30]!r}")
print(f"[D2]{_key[:20]!r}")
try:
    from app.config import get_settings
    _s = get_settings()
    print(f"[D3]{_s.supabase_url[:30]!r}")
    print(f"[D4]{_s.supabase_anon_key[:20]!r}")
except Exception as _e:
    print(f"[D5]settings_error={_e}")

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(glucose.router)
app.include_router(records.router)
app.include_router(reports.router)
app.include_router(settings.router)


@app.get("/debug-env")
async def debug_env():
    from app.config import get_settings
    from app.services.supabase_client import get_supabase
    import traceback
    try:
        s = get_settings()
        sb = get_supabase()
        sb.auth.sign_in_with_password({"email": "debug@test.com", "password": "wrongpass123"})
        return {"status": "unexpected_success"}
    except Exception as e:
        return {
            "exception_type": type(e).__name__,
            "exception_module": type(e).__module__,
            "message": str(e)[:200],
            "traceback": traceback.format_exc()[-500:],
        }


@app.get("/")
async def root():
    return RedirectResponse(url="/dashboard")


@app.exception_handler(303)
async def redirect_handler(request: Request, exc):
    return RedirectResponse(url=exc.headers["Location"])
