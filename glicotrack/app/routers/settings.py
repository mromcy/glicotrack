from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from app.dependencies import get_current_user
from app.services.supabase_client import get_supabase_with_token
import uuid

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).parent.parent / "templates")


@router.get("/configuracoes", response_class=HTMLResponse)
async def settings_page(request: Request, session: dict = Depends(get_current_user)):
    user = session["user"]
    supabase = get_supabase_with_token(session["access_token"])

    profile = supabase.table("profiles").select("*, family_groups(*)").eq("id", user.id).single().execute()
    profile_data = profile.data or {}

    family_members = []
    family_group_id = profile_data.get("family_group_id")
    if family_group_id:
        members = supabase.table("profiles").select("id, full_name, role").eq("family_group_id", family_group_id).execute()
        family_members = members.data or []

    return templates.TemplateResponse(
        "settings.html",
        {
            "request": request,
            "perfil": profile_data,
            "membros": family_members,
            "sucesso": request.query_params.get("sucesso"),
            "erro": request.query_params.get("erro"),
        },
    )


@router.post("/configuracoes/perfil")
async def update_profile(
    request: Request,
    session: dict = Depends(get_current_user),
    full_name: str = Form(...),
    medication_type: str = Form(...),
):
    user = session["user"]
    supabase = get_supabase_with_token(session["access_token"])
    supabase.table("profiles").update({
        "full_name": full_name,
        "medication_type": medication_type,
    }).eq("id", user.id).execute()
    return RedirectResponse(url="/configuracoes?sucesso=perfil", status_code=303)


@router.post("/configuracoes/criar-grupo")
async def create_family_group(
    request: Request,
    session: dict = Depends(get_current_user),
    group_name: str = Form(...),
):
    user = session["user"]
    supabase = get_supabase_with_token(session["access_token"])

    group = supabase.table("family_groups").insert({"name": group_name}).execute()
    group_id = group.data[0]["id"]

    supabase.table("profiles").update({"family_group_id": group_id}).eq("id", user.id).execute()
    return RedirectResponse(url="/configuracoes?sucesso=grupo", status_code=303)
