from fastapi import APIRouter, Request, Form, Depends, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from datetime import datetime, timezone, timedelta
from app.dependencies import get_current_user
from app.services.supabase_client import get_supabase_with_token

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).parent.parent / "templates")

TIPOS_REFEICAO = {
    "cafe_da_manha": "Café da manhã",
    "almoco": "Almoço",
    "jantar": "Jantar",
    "lanche": "Lanche",
}

SINTOMAS_LABELS = {
    "tontura": "Tontura",
    "fraqueza": "Fraqueza",
    "suor_frio": "Suor frio",
    "visao_turva": "Visão turva",
    "dor_de_cabeca": "Dor de cabeça",
    "nausea": "Náusea",
}

PERIODOS_HIST = {
    "hoje": 0,
    "3dias": 3,
    "semana": 7,
    "mes": 30,
    "ano": 365,
}


def _get_family_group(supabase, user_id: str) -> str | None:
    result = supabase.table("profiles").select("family_group_id").eq("id", user_id).single().execute()
    return result.data.get("family_group_id") if result.data else None


def _hora_br(ts: str) -> str:
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        dt_local = dt - timedelta(hours=3)
        return dt_local.strftime("%d/%m %H:%M")
    except Exception:
        return ts[:16] if ts else ""


@router.get("/registros/historico", response_class=HTMLResponse)
async def history_page(
    request: Request,
    periodo: str = Query(default="semana"),
    session: dict = Depends(get_current_user),
):
    user = session["user"]
    supabase = get_supabase_with_token(session["access_token"])
    family_group_id = _get_family_group(supabase, user.id)

    if periodo not in PERIODOS_HIST:
        periodo = "semana"
    dias = PERIODOS_HIST[periodo]
    agora_utc = datetime.now(timezone.utc)
    if dias == 0:
        inicio_ts = f"{agora_utc.date().isoformat()}T00:00:00Z"
    else:
        inicio_ts = (agora_utc - timedelta(days=dias)).strftime("%Y-%m-%dT%H:%M:%SZ")

    refeicoes = atividades = medicamentos = sintomas = sinais_vitais = []

    if family_group_id:
        refeicoes = (
            supabase.table("meals").select("*")
            .eq("family_group_id", family_group_id)
            .gte("recorded_at", inicio_ts)
            .order("recorded_at", desc=True).execute()
        ).data or []
        for r in refeicoes:
            r["_dt"] = _hora_br(r.get("recorded_at", ""))
            r["_tipo_label"] = TIPOS_REFEICAO.get(r.get("meal_type", ""), r.get("meal_type", ""))

        atividades = (
            supabase.table("activities").select("*")
            .eq("family_group_id", family_group_id)
            .gte("recorded_at", inicio_ts)
            .order("recorded_at", desc=True).execute()
        ).data or []
        for a in atividades:
            a["_dt"] = _hora_br(a.get("recorded_at", ""))

        medicamentos = (
            supabase.table("medication_logs").select("*")
            .eq("family_group_id", family_group_id)
            .gte("taken_at", inicio_ts)
            .order("taken_at", desc=True).execute()
        ).data or []
        for m in medicamentos:
            m["_dt"] = _hora_br(m.get("taken_at", ""))

        sintomas = (
            supabase.table("symptoms").select("*")
            .eq("family_group_id", family_group_id)
            .gte("recorded_at", inicio_ts)
            .order("recorded_at", desc=True).execute()
        ).data or []
        for s in sintomas:
            s["_dt"] = _hora_br(s.get("recorded_at", ""))
            s["_labels"] = [SINTOMAS_LABELS.get(x, x) for x in (s.get("symptom_list") or [])]

        sinais_vitais = (
            supabase.table("vital_signs").select("*")
            .eq("family_group_id", family_group_id)
            .gte("recorded_at", inicio_ts)
            .order("recorded_at", desc=True).execute()
        ).data or []
        for sv in sinais_vitais:
            sv["_dt"] = _hora_br(sv.get("recorded_at", ""))

    return templates.TemplateResponse(
        "records/history.html",
        {
            "request": request,
            "periodo": periodo,
            "refeicoes": refeicoes,
            "atividades": atividades,
            "medicamentos": medicamentos,
            "sintomas": sintomas,
            "sinais_vitais": sinais_vitais,
        },
    )


@router.get("/registros/novo", response_class=HTMLResponse)
async def add_record_page(request: Request, session: dict = Depends(get_current_user)):
    return templates.TemplateResponse("records/add.html", {"request": request})


@router.post("/registros/refeicao")
async def add_meal(
    request: Request,
    session: dict = Depends(get_current_user),
    description: str = Form(...),
    meal_type: str = Form(...),
):
    user = session["user"]
    supabase = get_supabase_with_token(session["access_token"])
    family_group_id = _get_family_group(supabase, user.id)

    if not family_group_id:
        return RedirectResponse(url="/configuracoes?erro=grupo", status_code=303)

    supabase.table("meals").insert({
        "family_group_id": family_group_id,
        "user_id": user.id,
        "description": description,
        "meal_type": meal_type,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }).execute()
    return RedirectResponse(url="/registros/novo?sucesso=refeicao", status_code=303)


@router.post("/registros/atividade")
async def add_activity(
    request: Request,
    session: dict = Depends(get_current_user),
    type: str = Form(...),
    duration_minutes: str = Form(""),
):
    user = session["user"]
    supabase = get_supabase_with_token(session["access_token"])
    family_group_id = _get_family_group(supabase, user.id)

    if not family_group_id:
        return RedirectResponse(url="/configuracoes?erro=grupo", status_code=303)

    supabase.table("activities").insert({
        "family_group_id": family_group_id,
        "user_id": user.id,
        "type": type,
        "duration_minutes": int(duration_minutes) if duration_minutes else None,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }).execute()
    return RedirectResponse(url="/registros/novo?sucesso=atividade", status_code=303)


@router.post("/registros/medicamento")
async def add_medication(
    request: Request,
    session: dict = Depends(get_current_user),
    medication_name: str = Form(...),
    dose: str = Form(""),
):
    user = session["user"]
    supabase = get_supabase_with_token(session["access_token"])
    family_group_id = _get_family_group(supabase, user.id)

    if not family_group_id:
        return RedirectResponse(url="/configuracoes?erro=grupo", status_code=303)

    supabase.table("medication_logs").insert({
        "family_group_id": family_group_id,
        "user_id": user.id,
        "medication_name": medication_name,
        "dose": dose or None,
        "taken_at": datetime.now(timezone.utc).isoformat(),
    }).execute()
    return RedirectResponse(url="/registros/novo?sucesso=medicamento", status_code=303)


@router.post("/registros/sintomas")
async def add_symptoms(
    request: Request,
    session: dict = Depends(get_current_user),
    symptom_list: list[str] = Form([]),
    notes: str = Form(""),
):
    user = session["user"]
    supabase = get_supabase_with_token(session["access_token"])
    family_group_id = _get_family_group(supabase, user.id)

    if not family_group_id:
        return RedirectResponse(url="/configuracoes?erro=grupo", status_code=303)

    supabase.table("symptoms").insert({
        "family_group_id": family_group_id,
        "user_id": user.id,
        "symptom_list": symptom_list,
        "notes": notes or None,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }).execute()
    return RedirectResponse(url="/registros/novo?sucesso=sintomas", status_code=303)


@router.post("/registros/sinais-vitais")
async def add_vital_signs(
    request: Request,
    session: dict = Depends(get_current_user),
    weight_kg: str = Form(""),
    systolic_bp: str = Form(""),
    diastolic_bp: str = Form(""),
):
    user = session["user"]
    supabase = get_supabase_with_token(session["access_token"])
    family_group_id = _get_family_group(supabase, user.id)

    if not family_group_id:
        return RedirectResponse(url="/configuracoes?erro=grupo", status_code=303)

    if bool(systolic_bp) != bool(diastolic_bp):
        return templates.TemplateResponse(
            "records/add.html",
            {"request": request, "erro_sinais": "Preencha as duas pressões (sistólica e diastólica) ou deixe ambas em branco."},
            status_code=422,
        )

    supabase.table("vital_signs").insert({
        "family_group_id": family_group_id,
        "user_id": user.id,
        "weight_kg": float(weight_kg) if weight_kg else None,
        "systolic_bp": int(systolic_bp) if systolic_bp else None,
        "diastolic_bp": int(diastolic_bp) if diastolic_bp else None,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }).execute()
    return RedirectResponse(url="/registros/novo?sucesso=sinais", status_code=303)
