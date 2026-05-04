from fastapi import APIRouter, Request, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from app.services.supabase_client import get_supabase

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).parent.parent / "templates")


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("auth/login.html", {"request": request})


@router.post("/login")
async def login(
    request: Request,
    response: Response,
    email: str = Form(...),
    password: str = Form(...),
):
    try:
        supabase = get_supabase()
        result = supabase.auth.sign_in_with_password({"email": email, "password": password})
        print(f"LOGIN OK: user={result.user.email}, token={result.session.access_token[:20]}...")
        redirect = RedirectResponse(url="/dashboard", status_code=303)
        redirect.set_cookie(
            key="access_token",
            value=result.session.access_token,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=60 * 60 * 24 * 7,
        )
        return redirect
    except Exception as e:
        print(f"ERRO LOGIN: {type(e).__name__}: {e}")
        return templates.TemplateResponse(
            "auth/login.html",
            {"request": request, "erro": f"Erro ao entrar: {str(e)}"},
            status_code=400,
        )


@router.get("/logout")
async def logout():
    redirect = RedirectResponse(url="/login", status_code=303)
    redirect.delete_cookie("access_token")
    return redirect


@router.get("/cadastro", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("auth/register.html", {"request": request})


@router.post("/cadastro")
async def register(
    request: Request,
    nome: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
):
    try:
        supabase = get_supabase()
        supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {"data": {"full_name": nome, "role": role}},
        })
        return templates.TemplateResponse(
            "auth/login.html",
            {"request": request, "sucesso": "Conta criada! Verifique seu e-mail e faça login."},
        )
    except Exception as e:
        print(f"ERRO CADASTRO: {type(e).__name__}: {e}")
        return templates.TemplateResponse(
            "auth/register.html",
            {"request": request, "erro": f"Erro ao criar conta: {str(e)}"},
            status_code=400,
        )
