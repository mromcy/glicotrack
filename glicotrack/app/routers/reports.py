from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from datetime import datetime, timezone, timedelta
from app.dependencies import get_current_user
from app.services.supabase_client import get_supabase_with_token
from app.services.pdf import gerar_relatorio_pdf

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).parent.parent / "templates")


@router.get("/relatorio", response_class=HTMLResponse)
async def report_page(request: Request, session: dict = Depends(get_current_user)):
    hoje = datetime.now(timezone.utc).date()
    data_fim = hoje.isoformat()
    data_inicio = (hoje - timedelta(days=30)).isoformat()
    return templates.TemplateResponse(
        "reports/index.html",
        {"request": request, "data_inicio": data_inicio, "data_fim": data_fim},
    )


@router.get("/relatorio/pdf")
async def download_pdf(
    request: Request,
    session: dict = Depends(get_current_user),
    data_inicio: str = "",
    data_fim: str = "",
):
    user = session["user"]
    supabase = get_supabase_with_token(session["access_token"])

    profile = supabase.table("profiles").select("*").eq("id", user.id).single().execute()
    profile_data = profile.data or {}
    family_group_id = profile_data.get("family_group_id")

    if not family_group_id:
        return HTMLResponse("Nenhum grupo familiar configurado.", status_code=400)

    if not data_inicio:
        data_inicio = (datetime.now(timezone.utc).date() - timedelta(days=30)).isoformat()
    if not data_fim:
        data_fim = datetime.now(timezone.utc).date().isoformat()

    leituras = (
        supabase.table("glucose_readings")
        .select("*")
        .eq("family_group_id", family_group_id)
        .gte("measured_at", f"{data_inicio}T00:00:00Z")
        .lte("measured_at", f"{data_fim}T23:59:59Z")
        .order("measured_at")
        .execute()
    ).data or []

    medicamentos = (
        supabase.table("medication_logs")
        .select("*")
        .eq("family_group_id", family_group_id)
        .gte("taken_at", f"{data_inicio}T00:00:00Z")
        .lte("taken_at", f"{data_fim}T23:59:59Z")
        .order("taken_at")
        .execute()
    ).data or []

    sintomas = (
        supabase.table("symptoms")
        .select("*")
        .eq("family_group_id", family_group_id)
        .gte("recorded_at", f"{data_inicio}T00:00:00Z")
        .lte("recorded_at", f"{data_fim}T23:59:59Z")
        .order("recorded_at")
        .execute()
    ).data or []

    refeicoes = (
        supabase.table("meals")
        .select("*")
        .eq("family_group_id", family_group_id)
        .gte("recorded_at", f"{data_inicio}T00:00:00Z")
        .lte("recorded_at", f"{data_fim}T23:59:59Z")
        .order("recorded_at")
        .execute()
    ).data or []

    atividades = (
        supabase.table("activities")
        .select("*")
        .eq("family_group_id", family_group_id)
        .gte("recorded_at", f"{data_inicio}T00:00:00Z")
        .lte("recorded_at", f"{data_fim}T23:59:59Z")
        .order("recorded_at")
        .execute()
    ).data or []

    sinais_vitais = (
        supabase.table("vital_signs")
        .select("*")
        .eq("family_group_id", family_group_id)
        .gte("recorded_at", f"{data_inicio}T00:00:00Z")
        .lte("recorded_at", f"{data_fim}T23:59:59Z")
        .order("recorded_at")
        .execute()
    ).data or []

    pdf_bytes = gerar_relatorio_pdf(
        perfil=profile_data,
        leituras=leituras,
        medicamentos=medicamentos,
        sintomas=sintomas,
        refeicoes=refeicoes,
        atividades=atividades,
        sinais_vitais=sinais_vitais,
        data_inicio=data_inicio,
        data_fim=data_fim,
    )

    nome_arquivo = f"glicotrack_{data_inicio}_{data_fim}.pdf"
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={nome_arquivo}"},
    )
