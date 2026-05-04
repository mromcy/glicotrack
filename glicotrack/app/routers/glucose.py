from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from datetime import datetime, timezone
from app.dependencies import get_current_user
from app.services.supabase_client import get_supabase_with_token
from app.routers.dashboard import classificar_glicemia, TIPOS_MEDICAO

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).parent.parent / "templates")

METODOS = {"glicosimetro": "Glicosímetro", "sensor_continuo": "Sensor Contínuo (CGM)"}


@router.get("/glicemia/registrar", response_class=HTMLResponse)
async def add_glucose_page(request: Request, session: dict = Depends(get_current_user)):
    return templates.TemplateResponse("glucose/add.html", {"request": request})


@router.post("/glicemia/registrar")
async def add_glucose(
    request: Request,
    session: dict = Depends(get_current_user),
    value: float = Form(...),
    measurement_type: str = Form(...),
    measurement_method: str = Form(...),
    notes: str = Form(""),
    measured_at: str = Form(""),
):
    user = session["user"]
    token = session["access_token"]
    supabase = get_supabase_with_token(token)

    profile = supabase.table("profiles").select("family_group_id").eq("id", user.id).single().execute()
    family_group_id = profile.data.get("family_group_id") if profile.data else None

    if not family_group_id:
        return templates.TemplateResponse(
            "glucose/add.html",
            {"request": request, "erro": "Você precisa estar vinculado a um grupo familiar. Configure em Configurações."},
            status_code=400,
        )

    dt = datetime.now(timezone.utc).isoformat() if not measured_at else measured_at

    supabase.table("glucose_readings").insert({
        "family_group_id": family_group_id,
        "user_id": user.id,
        "value": value,
        "measurement_type": measurement_type,
        "measurement_method": measurement_method,
        "notes": notes or None,
        "measured_at": dt,
    }).execute()

    return RedirectResponse(url="/glicemia/historico?sucesso=1", status_code=303)


@router.get("/glicemia/historico", response_class=HTMLResponse)
async def glucose_history(
    request: Request,
    session: dict = Depends(get_current_user),
    pagina: int = 1,
    data_inicio: str = "",
    data_fim: str = "",
):
    user = session["user"]
    token = session["access_token"]
    supabase = get_supabase_with_token(token)

    profile = supabase.table("profiles").select("family_group_id").eq("id", user.id).single().execute()
    family_group_id = profile.data.get("family_group_id") if profile.data else None

    leituras = []
    total = 0

    if family_group_id:
        por_pagina = 20
        inicio = (pagina - 1) * por_pagina

        query = (
            supabase.table("glucose_readings")
            .select("*", count="exact")
            .eq("family_group_id", family_group_id)
            .order("measured_at", desc=True)
            .range(inicio, inicio + por_pagina - 1)
        )

        if data_inicio:
            query = query.gte("measured_at", f"{data_inicio}T00:00:00Z")
        if data_fim:
            query = query.lte("measured_at", f"{data_fim}T23:59:59Z")

        resultado = query.execute()
        leituras = resultado.data or []
        total = resultado.count or 0

        for leitura in leituras:
            leitura["classificacao"] = classificar_glicemia(leitura["value"], leitura["measurement_type"])
            leitura["tipo_label"] = TIPOS_MEDICAO.get(leitura["measurement_type"], "Outro")
            leitura["metodo_label"] = METODOS.get(leitura["measurement_method"], leitura["measurement_method"])

    total_paginas = (total + 19) // 20

    return templates.TemplateResponse(
        "glucose/list.html",
        {
            "request": request,
            "leituras": leituras,
            "pagina": pagina,
            "total_paginas": total_paginas,
            "total": total,
            "data_inicio": data_inicio,
            "data_fim": data_fim,
            "sucesso": request.query_params.get("sucesso"),
        },
    )
