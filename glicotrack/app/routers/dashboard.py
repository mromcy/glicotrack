from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from app.dependencies import get_current_user
from app.services.supabase_client import get_supabase_with_token
from datetime import datetime, timezone, timedelta

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).parent.parent / "templates")

TIPOS_MEDICAO = {
    "jejum": "Jejum",
    "pre_refeicao": "Pré-refeição",
    "pos_refeicao": "Pós-refeição",
    "outro": "Outro",
}


def classificar_glicemia(value: float, measurement_type: str) -> str:
    """Retorna 'normal', 'atencao' ou 'alerta' baseado no valor e momento."""
    if value < 70:
        return "alerta"
    if measurement_type == "jejum":
        if value < 100:
            return "normal"
        if value < 126:
            return "atencao"
        return "alerta"
    if measurement_type in ("pos_refeicao",):
        if value < 140:
            return "normal"
        if value < 180:
            return "atencao"
        return "alerta"
    # Para pre_refeicao e outro, usa faixa do jejum como referência
    if value < 100:
        return "normal"
    if value < 126:
        return "atencao"
    return "alerta"


PERIODOS = {
    "dia":    {"dias": 0,   "label": "Hoje",        "fmt_hora": True},
    "3dias":  {"dias": 3,   "label": "Últimos 3 dias", "fmt_hora": False},
    "semana": {"dias": 7,   "label": "Última semana",  "fmt_hora": False},
    "mes":    {"dias": 30,  "label": "Último mês",     "fmt_hora": False},
    "ano":    {"dias": 365, "label": "Último ano",     "fmt_hora": False},
}


def _fmt_label(measured_at: str, fmt_hora: bool) -> str:
    """Formata o label do eixo X do gráfico conforme o período."""
    if fmt_hora:
        return measured_at[11:16]          # HH:MM
    return measured_at[5:10].replace("-", "/")  # MM/DD


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    periodo: str = Query(default="dia"),
    session: dict = Depends(get_current_user),
):
    user = session["user"]
    token = session["access_token"]
    supabase = get_supabase_with_token(token)

    if periodo not in PERIODOS:
        periodo = "dia"
    cfg = PERIODOS[periodo]

    profile = supabase.table("profiles").select("*").eq("id", user.id).single().execute()
    profile_data = profile.data or {}
    family_group_id = profile_data.get("family_group_id")

    leituras = []
    ultima_leitura = None
    media_periodo = None
    dados_grafico = []

    if family_group_id:
        agora_utc = datetime.now(timezone.utc)
        if cfg["dias"] == 0:
            inicio = agora_utc.date().isoformat()
            inicio_ts = f"{inicio}T00:00:00Z"
        else:
            inicio_ts = (agora_utc - timedelta(days=cfg["dias"])).strftime("%Y-%m-%dT%H:%M:%SZ")

        resultado = (
            supabase.table("glucose_readings")
            .select("*")
            .eq("family_group_id", family_group_id)
            .gte("measured_at", inicio_ts)
            .order("measured_at", desc=True)
            .execute()
        )
        leituras = resultado.data or []

        for leitura in leituras:
            leitura["classificacao"] = classificar_glicemia(
                leitura["value"], leitura["measurement_type"]
            )
            leitura["tipo_label"] = TIPOS_MEDICAO.get(leitura["measurement_type"], "Outro")

        if leituras:
            ultima_leitura = leituras[0]
            media_periodo = round(sum(l["value"] for l in leituras) / len(leituras), 1)

        dados_grafico = [
            {
                "hora": _fmt_label(l["measured_at"], cfg["fmt_hora"]),
                "valor": l["value"],
                "classificacao": l["classificacao"],
            }
            for l in reversed(leituras)
        ]

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "perfil": profile_data,
            "ultima_leitura": ultima_leitura,
            "media_dia": media_periodo,
            "total_dia": len(leituras),
            "dados_grafico": dados_grafico,
            "periodo": periodo,
            "periodo_label": cfg["label"],
        },
    )
