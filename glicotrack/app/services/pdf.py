from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, HRFlowable
from reportlab.lib.enums import TA_CENTER

TIPOS_MEDICAO = {
    "jejum": "Jejum",
    "pre_refeicao": "Pré-refeição",
    "pos_refeicao": "Pós-refeição",
    "outro": "Outro",
}

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

COR_NORMAL = colors.HexColor("#16a34a")
COR_ATENCAO = colors.HexColor("#ca8a04")
COR_ALERTA = colors.HexColor("#dc2626")
COR_FUNDO_HEADER = colors.HexColor("#1e40af")


def _classificar(value: float, measurement_type: str) -> tuple[str, colors.Color]:
    if value < 70:
        return "Alerta", COR_ALERTA
    if measurement_type == "jejum":
        if value < 100:
            return "Normal", COR_NORMAL
        if value < 126:
            return "Atenção", COR_ATENCAO
        return "Alerta", COR_ALERTA
    if measurement_type == "pos_refeicao":
        if value < 140:
            return "Normal", COR_NORMAL
        if value < 180:
            return "Atenção", COR_ATENCAO
        return "Alerta", COR_ALERTA
    if value < 100:
        return "Normal", COR_NORMAL
    if value < 126:
        return "Atenção", COR_ATENCAO
    return "Alerta", COR_ALERTA


def gerar_relatorio_pdf(
    perfil: dict,
    leituras: list,
    medicamentos: list,
    sintomas: list,
    refeicoes: list,
    atividades: list,
    sinais_vitais: list,
    data_inicio: str,
    data_fim: str,
) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    titulo_style = ParagraphStyle("titulo", parent=styles["Title"], textColor=COR_FUNDO_HEADER, fontSize=20)
    subtitulo_style = ParagraphStyle("subtitulo", parent=styles["Heading2"], textColor=COR_FUNDO_HEADER)
    normal = styles["Normal"]
    center = ParagraphStyle("center", parent=normal, alignment=TA_CENTER)

    story = []

    # Cabeçalho
    story.append(Paragraph("GlicoTrack", titulo_style))
    story.append(Paragraph("Relatório de Acompanhamento de Glicemia", subtitulo_style))
    story.append(Spacer(1, 0.3 * cm))

    nome = perfil.get("full_name", "Paciente")
    story.append(Paragraph(f"<b>Paciente:</b> {nome}", normal))
    story.append(Paragraph(f"<b>Período:</b> {data_inicio} a {data_fim}", normal))
    story.append(Spacer(1, 0.5 * cm))
    story.append(HRFlowable(width="100%", color=COR_FUNDO_HEADER))
    story.append(Spacer(1, 0.5 * cm))

    # Resumo estatístico
    if leituras:
        valores = [l["value"] for l in leituras]
        media = round(sum(valores) / len(valores), 1)
        minimo = min(valores)
        maximo = max(valores)
        alertas = sum(1 for l in leituras if _classificar(l["value"], l["measurement_type"])[0] == "Alerta")

        story.append(Paragraph("Resumo do Período", subtitulo_style))
        resumo_data = [
            ["Total de medições", "Média", "Mínimo", "Máximo", "Alertas"],
            [str(len(leituras)), f"{media} mg/dL", f"{minimo} mg/dL", f"{maximo} mg/dL", str(alertas)],
        ]
        resumo_table = Table(resumo_data, colWidths=[3.2 * cm] * 5)
        resumo_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COR_FUNDO_HEADER),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4ff")]),
        ]))
        story.append(resumo_table)
        story.append(Spacer(1, 0.8 * cm))

    # Tabela de leituras
    story.append(Paragraph("Leituras de Glicemia", subtitulo_style))

    if leituras:
        header = ["Data/Hora", "Valor", "Momento", "Classificação", "Método"]
        rows = [header]
        row_colors = [None]

        for l in leituras:
            classificacao, cor = _classificar(l["value"], l["measurement_type"])
            data_hora = l["measured_at"][:16].replace("T", " ")
            rows.append([
                data_hora,
                f"{l['value']} mg/dL",
                TIPOS_MEDICAO.get(l["measurement_type"], "Outro"),
                classificacao,
                "Glicosímetro" if l["measurement_method"] == "glicosimetro" else "Sensor Contínuo",
            ])
            row_colors.append(cor)

        table = Table(rows, colWidths=[3.8 * cm, 2.5 * cm, 3 * cm, 2.8 * cm, 4 * cm])
        style_cmds = [
            ("BACKGROUND", (0, 0), (-1, 0), COR_FUNDO_HEADER),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
        ]
        for i, cor in enumerate(row_colors[1:], start=1):
            style_cmds.append(("TEXTCOLOR", (3, i), (3, i), cor))
            style_cmds.append(("FONTNAME", (3, i), (3, i), "Helvetica-Bold"))
            if i % 2 == 0:
                style_cmds.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#f8fafc")))

        table.setStyle(TableStyle(style_cmds))
        story.append(table)
    else:
        story.append(Paragraph("Nenhuma leitura no período.", normal))

    story.append(Spacer(1, 0.8 * cm))

    # Medicamentos
    if medicamentos:
        story.append(Paragraph("Medicamentos Registrados", subtitulo_style))
        med_data = [["Data/Hora", "Medicamento", "Dose"]]
        for m in medicamentos:
            med_data.append([
                m["taken_at"][:16].replace("T", " "),
                m["medication_name"],
                m.get("dose") or "—",
            ])
        med_table = Table(med_data, colWidths=[4 * cm, 8 * cm, 4 * cm])
        med_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COR_FUNDO_HEADER),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ]))
        story.append(med_table)
        story.append(Spacer(1, 0.5 * cm))

    # Refeições
    if refeicoes:
        story.append(Paragraph("Refeições", subtitulo_style))
        ref_data = [["Data/Hora", "Tipo", "Descrição"]]
        for r in refeicoes:
            ref_data.append([
                r["recorded_at"][:16].replace("T", " "),
                TIPOS_REFEICAO.get(r.get("meal_type", ""), r.get("meal_type", "")),
                r.get("description", ""),
            ])
        ref_table = Table(ref_data, colWidths=[3.5 * cm, 3.5 * cm, 9 * cm])
        ref_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COR_FUNDO_HEADER),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ]))
        story.append(ref_table)
        story.append(Spacer(1, 0.5 * cm))

    # Atividades físicas
    if atividades:
        story.append(Paragraph("Atividades Físicas", subtitulo_style))
        atv_data = [["Data/Hora", "Atividade", "Duração"]]
        for a in atividades:
            duracao = f"{a['duration_minutes']} min" if a.get("duration_minutes") else "—"
            atv_data.append([
                a["recorded_at"][:16].replace("T", " "),
                a.get("type", ""),
                duracao,
            ])
        atv_table = Table(atv_data, colWidths=[3.5 * cm, 10 * cm, 2.5 * cm])
        atv_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COR_FUNDO_HEADER),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ]))
        story.append(atv_table)
        story.append(Spacer(1, 0.5 * cm))

    # Sintomas
    if sintomas:
        story.append(Paragraph("Sintomas Registrados", subtitulo_style))
        sin_data = [["Data/Hora", "Sintomas", "Observações"]]
        for s in sintomas:
            lista = s.get("symptom_list") or []
            labels = ", ".join(SINTOMAS_LABELS.get(x, x) for x in lista)
            sin_data.append([
                s["recorded_at"][:16].replace("T", " "),
                labels or "—",
                s.get("notes") or "—",
            ])
        sin_table = Table(sin_data, colWidths=[3.5 * cm, 6 * cm, 6.5 * cm])
        sin_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COR_FUNDO_HEADER),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ]))
        story.append(sin_table)
        story.append(Spacer(1, 0.5 * cm))

    # Sinais vitais
    if sinais_vitais:
        story.append(Paragraph("Sinais Vitais", subtitulo_style))
        sv_data = [["Data/Hora", "Peso (kg)", "Pressão sistólica", "Pressão diastólica"]]
        for sv in sinais_vitais:
            sv_data.append([
                sv["recorded_at"][:16].replace("T", " "),
                str(sv.get("weight_kg") or "—"),
                str(sv.get("systolic_bp") or "—"),
                str(sv.get("diastolic_bp") or "—"),
            ])
        sv_table = Table(sv_data, colWidths=[4 * cm, 3 * cm, 4 * cm, 4 * cm])
        sv_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COR_FUNDO_HEADER),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ]))
        story.append(sv_table)
        story.append(Spacer(1, 0.5 * cm))

    # Rodapé informativo
    story.append(HRFlowable(width="100%", color=colors.grey))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(
        "Este relatório foi gerado automaticamente pelo GlicoTrack. "
        "As faixas de referência seguem as diretrizes para Diabetes Tipo 2. "
        "Sempre consulte seu médico para orientação clínica.",
        ParagraphStyle("rodape", parent=normal, fontSize=7, textColor=colors.grey),
    ))

    doc.build(story)
    return buffer.getvalue()
