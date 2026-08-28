import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import altair as alt
import re
import unicodedata
import math
import textwrap
import calendar
import base64
import json
from io import BytesIO
from datetime import datetime, date, timedelta, timezone
from zoneinfo import ZoneInfo
from urllib.parse import quote
from urllib import request, parse
from io import BytesIO
import matplotlib.pyplot as plt
from matplotlib import font_manager
from supabase import create_client
from PIL import Image, ImageDraw, ImageFont


# =========================================================
# CONFIGURACIÓN GENERAL
# =========================================================

APP_NAME = "GEN Control"
APP_SUBTITLE = "Cobranzas Inmobiliarias"

META_GESTIONES = 2400
META_COMPROMISOS = 550
META_DIARIA_GESTIONES = 98
META_DIARIA_COMPROMISOS = 25
JORNADA_INICIO_HORA = 8
JORNADA_FIN_HORA = 17

# =========================================================
# REGLA DEFINITIVA DE RECUPERACIÓN
# NO MODIFICAR SIN AUTORIZACIÓN
# =========================================================

META_RECUPERACION = 170400
CANTIDAD_OPERADORES = 8


OPERADORES = {
    "avargas": {
        "nombre": "Aracely Peña Vargas",
        "nombre_mensaje": "Aracely",
        "correo": "apena@gestionia.bo",
    },
    "cvaca": {
        "nombre": "Carla Fernanda Vaca Cespedes",
        "nombre_mensaje": "Carla",
        "correo": "cvaca@gestionia.bo",
    },
    "jborja": {
        "nombre": "James Abel Borja Chirinos",
        "nombre_mensaje": "James",
        "correo": "jborja@gestionia.bo",
    },
    "arodriguez": {
        "nombre": "Leen Alisson Rodriguez Espinoza",
        "nombre_mensaje": "Leen",
        "correo": "lrodriguez@gestionia.bo",
    },
    "malvarez": {
        "nombre": "Mirla Anahir Alvarez",
        "nombre_mensaje": "Anahir",
        "correo": "malvarez@gestionia.bo",
    },
    "projas": {
        "nombre": "Percy Daniel Rojas Ortega",
        "nombre_mensaje": "Percy",
        "correo": "projas@gestionia.bo",
    },
    "yarinez": {
        "nombre": "Yanine Ariñez Rivero",
        "nombre_mensaje": "Yanine",
        "correo": "yarinez@gestionia.bo",
    },
    "yrivas": {
        "nombre": "Yessica Rivas Blanco",
        "nombre_mensaje": "Yessica",
        "correo": "yrivas@gestionia.bo",
    },
}


# =========================================================
# HORARIOS OPERATIVOS POR OPERADOR
# Basados en el rol compartido por coordinación.
# La meta diaria se distribuye SOLO sobre tiempo efectivo de trabajo.
# El break de 30 min congela el esperado.
# =========================================================

HORARIOS_OPERADORES = {
    "arodriguez": {
        0: {"entrada": "08:30", "break_inicio": "13:00", "break_fin": "13:30", "salida": "15:30", "jornada_horas": 7},
        1: {"entrada": "09:00", "break_inicio": "13:00", "break_fin": "13:30", "salida": "16:00", "jornada_horas": 7},
        2: {"entrada": "08:30", "break_inicio": "13:00", "break_fin": "13:30", "salida": "15:30", "jornada_horas": 7},
        3: {"entrada": "09:00", "break_inicio": "13:00", "break_fin": "13:30", "salida": "16:00", "jornada_horas": 7},
        4: {"entrada": "08:30", "break_inicio": "13:00", "break_fin": "13:30", "salida": "15:30", "jornada_horas": 7},
        5: {"entrada": "08:00", "break_inicio": None, "break_fin": None, "salida": "13:00", "jornada_horas": 5},
    },
    "malvarez": {
        0: {"entrada": "08:30", "break_inicio": "12:30", "break_fin": "13:00", "salida": "15:30", "jornada_horas": 7},
        1: {"entrada": "08:30", "break_inicio": "12:30", "break_fin": "13:00", "salida": "15:30", "jornada_horas": 7},
        2: {"entrada": "08:30", "break_inicio": "12:30", "break_fin": "13:00", "salida": "15:30", "jornada_horas": 7},
        3: {"entrada": "08:30", "break_inicio": "12:30", "break_fin": "13:00", "salida": "15:30", "jornada_horas": 7},
        4: {"entrada": "08:30", "break_inicio": "12:30", "break_fin": "13:00", "salida": "15:30", "jornada_horas": 7},
        5: {"entrada": "08:30", "break_inicio": None, "break_fin": None, "salida": "13:30", "jornada_horas": 5},
    },
    "avargas": {
        0: {"entrada": "12:30", "break_inicio": "15:30", "break_fin": "16:00", "salida": "19:30", "jornada_horas": 7},
        1: {"entrada": "12:30", "break_inicio": "15:30", "break_fin": "16:00", "salida": "19:30", "jornada_horas": 7},
        2: {"entrada": "12:30", "break_inicio": "15:30", "break_fin": "16:00", "salida": "19:30", "jornada_horas": 7},
        3: {"entrada": "12:30", "break_inicio": "15:30", "break_fin": "16:00", "salida": "19:30", "jornada_horas": 7},
        4: {"entrada": "12:30", "break_inicio": "15:30", "break_fin": "16:00", "salida": "19:30", "jornada_horas": 7},
        5: {"entrada": "14:00", "break_inicio": None, "break_fin": None, "salida": "19:00", "jornada_horas": 5},
    },
    "yarinez": {
        0: {"entrada": "08:00", "break_inicio": "12:00", "break_fin": "12:30", "salida": "15:00", "jornada_horas": 7},
        1: {"entrada": "08:00", "break_inicio": "12:00", "break_fin": "12:30", "salida": "15:00", "jornada_horas": 7},
        2: {"entrada": "08:00", "break_inicio": "12:00", "break_fin": "12:30", "salida": "15:00", "jornada_horas": 7},
        3: {"entrada": "08:00", "break_inicio": "12:00", "break_fin": "12:30", "salida": "15:00", "jornada_horas": 7},
        4: {"entrada": "08:00", "break_inicio": "12:00", "break_fin": "12:30", "salida": "15:00", "jornada_horas": 7},
        5: {"entrada": "09:00", "break_inicio": None, "break_fin": None, "salida": "14:00", "jornada_horas": 5},
    },
    "jborja": {
        0: {"entrada": "12:00", "break_inicio": "13:00", "break_fin": "13:30", "salida": "20:00", "jornada_horas": 8},
        1: {"entrada": "12:00", "break_inicio": "13:00", "break_fin": "13:30", "salida": "20:00", "jornada_horas": 8},
        2: {"entrada": "12:00", "break_inicio": "13:00", "break_fin": "13:30", "salida": "20:00", "jornada_horas": 8},
        3: {"entrada": "12:00", "break_inicio": "13:00", "break_fin": "13:30", "salida": "20:00", "jornada_horas": 8},
        4: {"entrada": "12:00", "break_inicio": "13:00", "break_fin": "13:30", "salida": "20:00", "jornada_horas": 8},
        5: {"entrada": "12:00", "break_inicio": "13:00", "break_fin": "13:30", "salida": "20:00", "jornada_horas": 8},
    },
    "cvaca": {
        0: {"entrada": "13:00", "break_inicio": "16:00", "break_fin": "16:30", "salida": "20:00", "jornada_horas": 7},
        1: {"entrada": "13:00", "break_inicio": "16:00", "break_fin": "16:30", "salida": "20:00", "jornada_horas": 7},
        2: {"entrada": "13:00", "break_inicio": "16:00", "break_fin": "16:30", "salida": "20:00", "jornada_horas": 7},
        3: {"entrada": "13:00", "break_inicio": "16:00", "break_fin": "16:30", "salida": "20:00", "jornada_horas": 7},
        4: {"entrada": "13:00", "break_inicio": "16:00", "break_fin": "16:30", "salida": "20:00", "jornada_horas": 7},
        5: {"entrada": "14:30", "break_inicio": None, "break_fin": None, "salida": "19:30", "jornada_horas": 5},
    },
    "projas": {
        0: {"entrada": "10:00", "break_inicio": "12:30", "break_fin": "13:00", "salida": "18:00", "jornada_horas": 8},
        1: {"entrada": "10:00", "break_inicio": "12:30", "break_fin": "13:00", "salida": "18:00", "jornada_horas": 8},
        2: {"entrada": "10:00", "break_inicio": "12:30", "break_fin": "13:00", "salida": "18:00", "jornada_horas": 8},
        3: {"entrada": "10:00", "break_inicio": "12:30", "break_fin": "13:00", "salida": "18:00", "jornada_horas": 8},
        4: {"entrada": "10:00", "break_inicio": "12:30", "break_fin": "13:00", "salida": "18:00", "jornada_horas": 8},
        5: {"entrada": "09:30", "break_inicio": "12:30", "break_fin": "13:00", "salida": "17:30", "jornada_horas": 8},
    },
    "yrivas": {
        0: {"entrada": "08:00", "break_inicio": "12:00", "break_fin": "12:30", "salida": "15:00", "jornada_horas": 7},
        1: {"entrada": "08:00", "break_inicio": "12:00", "break_fin": "12:30", "salida": "15:00", "jornada_horas": 7},
        2: {"entrada": "08:00", "break_inicio": "12:00", "break_fin": "12:30", "salida": "15:00", "jornada_horas": 7},
        3: {"entrada": "08:00", "break_inicio": "12:00", "break_fin": "12:30", "salida": "15:00", "jornada_horas": 7},
        4: {"entrada": "08:00", "break_inicio": "12:00", "break_fin": "12:30", "salida": "15:00", "jornada_horas": 7},
        5: {"entrada": "08:00", "break_inicio": None, "break_fin": None, "salida": "13:00", "jornada_horas": 5},
    },
}


def _hora_en_fecha(fecha_base, hhmm):
    hora, minuto = [
        int(x)
        for x in str(hhmm).split(":")
    ]

    return datetime(
        fecha_base.year,
        fecha_base.month,
        fecha_base.day,
        hora,
        minuto,
        tzinfo=ZoneInfo("America/La_Paz"),
    )


def obtener_horario_operador(usuario, fecha=None):
    """
    Devuelve el horario real según operador + día de la semana.
    Lunes=0 ... Sábado=5. Domingo no tiene jornada.
    """
    if fecha is None:
        fecha = fecha_local_actual()

    if hasattr(fecha, "date") and not hasattr(fecha, "weekday"):
        fecha = fecha.date()

    dia_semana = fecha.weekday()

    if dia_semana == 6:
        return None

    return HORARIOS_OPERADORES.get(
        usuario,
        {},
    ).get(
        dia_semana
    )


def calcular_progreso_jornada_operador(
    usuario,
    corte,
):
    """
    Calcula el porcentaje REAL de jornada efectiva transcurrida.

    Reglas:
    - antes de entrada: 0%;
    - durante break: esperado congelado;
    - después de salida: 100%;
    - break no cuenta como tiempo productivo;
    - mujeres: jornada nominal de 7 h;
    - hombres: jornada nominal de 8 h;
    - break: 30 min.
    """
    horario = obtener_horario_operador(
        usuario,
        corte.date(),
    )

    if not horario:
        return {
            "horario_configurado": False,
            "estado_jornada": "Horario pendiente",
            "proporcion": 0.0,
            "minutos_efectivos_transcurridos": 0,
            "minutos_efectivos_totales": 0,
            "entrada": None,
            "break_inicio": None,
            "break_fin": None,
            "salida": None,
        }

    entrada = _hora_en_fecha(
        corte,
        horario["entrada"],
    )
    tiene_break = bool(
        horario.get("break_inicio")
        and horario.get("break_fin")
    )

    break_inicio = (
        _hora_en_fecha(
            corte,
            horario["break_inicio"],
        )
        if tiene_break
        else None
    )
    break_fin = (
        _hora_en_fecha(
            corte,
            horario["break_fin"],
        )
        if tiene_break
        else None
    )
    salida = _hora_en_fecha(
        corte,
        horario["salida"],
    )

    # Si corte viene sin tzinfo (por pandas), asignar Bolivia.
    if corte.tzinfo is None:
        corte = corte.replace(
            tzinfo=ZoneInfo(
                "America/La_Paz"
            )
        )

    if tiene_break:
        tramo_1 = max(
            (break_inicio - entrada).total_seconds() / 60,
            0,
        )
        tramo_2 = max(
            (salida - break_fin).total_seconds() / 60,
            0,
        )
        minutos_totales = tramo_1 + tramo_2

        if corte < entrada:
            minutos_transcurridos = 0
            estado = "Jornada aún no iniciada"
        elif corte < break_inicio:
            minutos_transcurridos = min(
                (corte - entrada).total_seconds() / 60,
                tramo_1,
            )
            estado = "En jornada"
        elif corte < break_fin:
            minutos_transcurridos = tramo_1
            estado = "En break"
        elif corte < salida:
            minutos_transcurridos = tramo_1 + min(
                (corte - break_fin).total_seconds() / 60,
                tramo_2,
            )
            estado = "En jornada"
        else:
            minutos_transcurridos = minutos_totales
            estado = "Jornada finalizada"
    else:
        minutos_totales = max(
            (salida - entrada).total_seconds() / 60,
            0,
        )

        if corte < entrada:
            minutos_transcurridos = 0
            estado = "Jornada aún no iniciada"
        elif corte < salida:
            minutos_transcurridos = min(
                (corte - entrada).total_seconds() / 60,
                minutos_totales,
            )
            estado = "En jornada"
        else:
            minutos_transcurridos = minutos_totales
            estado = "Jornada finalizada"

    proporcion = (
        minutos_transcurridos
        / minutos_totales
        if minutos_totales
        else 0
    )

    return {
        "horario_configurado": True,
        "estado_jornada": estado,
        "proporcion": min(
            max(
                proporcion,
                0,
            ),
            1,
        ),
        "minutos_efectivos_transcurridos": int(
            round(
                minutos_transcurridos
            )
        ),
        "minutos_efectivos_totales": int(
            round(
                minutos_totales
            )
        ),
        "entrada": horario["entrada"],
        "break_inicio": horario["break_inicio"],
        "break_fin": horario["break_fin"],
        "salida": horario["salida"],
        "jornada_horas": horario[
            "jornada_horas"
        ],
    }


st.set_page_config(
    page_title=APP_NAME,
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# DISEÑO VISUAL EJECUTIVO — FINAL VISUAL
# =========================================================
st.markdown(
    """
    <style>
    :root{
        --gen-navy:#102A43;
        --gen-navy-2:#163A5F;
        --gen-blue:#2F80ED;
        --gen-cyan:#22B8CF;
        --gen-green:#12B76A;
        --gen-orange:#F79009;
        --gen-red:#F04438;
        --gen-purple:#7A5AF8;
        --gen-bg:#F4F7FB;
        --gen-card:#FFFFFF;
        --gen-border:#E6ECF3;
        --gen-text:#172B4D;
        --gen-muted:#6B7C93;
    }

    /* Fondo general */
    .stApp{
        background:
            radial-gradient(circle at 92% 4%, rgba(47,128,237,.07), transparent 24rem),
            radial-gradient(circle at 15% 92%, rgba(34,184,207,.05), transparent 28rem),
            var(--gen-bg);
    }

    .block-container{
        max-width: 1500px;
        padding-top: 1.35rem !important;
        padding-bottom: 3.5rem !important;
        padding-left: 2.25rem !important;
        padding-right: 2.25rem !important;
    }

    /* Tipografía y jerarquía */
    h1,h2,h3{
        letter-spacing:-.025em !important;
        color:var(--gen-text) !important;
    }
    h2{font-weight:800!important}
    h3{font-weight:780!important}

    /* Sidebar */
    [data-testid="stSidebar"]{
        background:
            linear-gradient(180deg,#0E2742 0%,#102A43 55%,#0B2037 100%) !important;
        border-right:1px solid rgba(255,255,255,.06)!important;
        box-shadow:16px 0 40px rgba(16,42,67,.08);
    }

    [data-testid="stSidebar"] div[role="radiogroup"] label{
        min-height:42px;
        border-radius:12px!important;
        margin:2px 3px!important;
        padding:9px 11px!important;
    }

    [data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked){
        background:
            linear-gradient(90deg,rgba(47,128,237,.30),rgba(34,184,207,.14))!important;
        border:1px solid rgba(112,189,255,.18)!important;
        box-shadow:
            inset 3px 0 0 #47D7D0,
            0 8px 18px rgba(0,0,0,.08)!important;
    }

    .sidebar-logo{
        background:linear-gradient(135deg,#2F80ED,#22B8CF)!important;
        box-shadow:0 10px 22px rgba(47,128,237,.24)!important;
    }

    .sidebar-status-card{
        background:
            linear-gradient(135deg,rgba(34,184,207,.18),rgba(47,128,237,.16))!important;
        border:1px solid rgba(106,203,213,.18)!important;
        box-shadow:0 12px 24px rgba(0,0,0,.08)!important;
    }

    /* Hero principal */
    .hero-card{
        position:relative;
        overflow:hidden;
        border:none!important;
        border-radius:20px!important;
        padding:24px 26px!important;
        margin-bottom:18px!important;
        background:
            linear-gradient(115deg,#102A43 0%,#163A5F 56%,#1D5D7C 100%)!important;
        box-shadow:0 18px 42px rgba(16,42,67,.16)!important;
    }

    .hero-card:after{
        content:"";
        position:absolute;
        width:220px;height:220px;
        right:-55px;top:-100px;
        border-radius:50%;
        background:rgba(71,215,208,.12);
        box-shadow:
            -115px 160px 0 15px rgba(47,128,237,.10);
        pointer-events:none;
    }

    .hero-title{
        position:relative;
        z-index:1;
        color:#fff!important;
        font-size:26px!important;
        font-weight:850!important;
        letter-spacing:-.035em;
    }

    .hero-subtitle{
        position:relative;
        z-index:1;
        color:#BCD0E5!important;
        font-size:12px!important;
        margin-top:5px!important;
    }

    /* Estado del equipo */
    .team-state-v79{
        border-radius:16px!important;
        padding:14px 18px!important;
        border:1px solid var(--gen-border)!important;
        box-shadow:0 8px 24px rgba(16,42,67,.05)!important;
        background:#fff!important;
        margin-bottom:14px!important;
    }

    .team-state-green-v79{
        border-left:5px solid var(--gen-green)!important;
        background:linear-gradient(90deg,#F0FDF6,#FFFFFF 34%)!important;
    }
    .team-state-orange-v79{
        border-left:5px solid var(--gen-orange)!important;
        background:linear-gradient(90deg,#FFF8EB,#FFFFFF 34%)!important;
    }
    .team-state-red-v79{
        border-left:5px solid var(--gen-red)!important;
        background:linear-gradient(90deg,#FFF3F2,#FFFFFF 34%)!important;
    }

    .team-state-title-v79{
        font-size:17px!important;
        font-weight:830!important;
        color:var(--gen-text)!important;
    }
    .team-state-sub-v79{
        font-size:10px!important;
        color:var(--gen-muted)!important;
        margin-top:2px!important;
    }
    .team-focus-v79{
        border-radius:999px!important;
        padding:7px 11px!important;
        background:#F2F6FA!important;
        color:#40566D!important;
        font-size:10px!important;
        font-weight:750!important;
    }

    /* KPIs */
    .kpi-card-v79{
        min-height:126px;
        border-radius:17px!important;
        padding:15px 17px!important;
        border:1px solid var(--gen-border)!important;
        background:#fff!important;
        box-shadow:0 10px 26px rgba(16,42,67,.055)!important;
        transition:transform .14s ease, box-shadow .14s ease;
    }
    .kpi-card-v79:hover{
        transform:translateY(-2px);
        box-shadow:0 16px 34px rgba(16,42,67,.09)!important;
    }
    .kpi-card-blue-v79{border-top:3px solid var(--gen-blue)!important}
    .kpi-card-orange-v79{border-top:3px solid var(--gen-orange)!important}
    .kpi-card-green-v79{border-top:3px solid var(--gen-green)!important}
    .kpi-card-purple-v79{border-top:3px solid var(--gen-purple)!important}

    .kpi-label-v79{
        font-size:10px!important;
        font-weight:800!important;
        color:#61758A!important;
        text-transform:uppercase;
        letter-spacing:.04em;
    }
    .kpi-value-v79{
        color:#102A43!important;
        font-size:27px!important;
        line-height:1.05!important;
        font-weight:860!important;
        margin:10px 0 7px!important;
        letter-spacing:-.04em;
    }
    .kpi-foot-v79{
        font-size:9px!important;
        color:#7A8DA1!important;
    }

    /* Avance vs esperado */
    .compare-card-v79{
        border-radius:16px!important;
        background:#fff!important;
        border:1px solid var(--gen-border)!important;
        padding:15px 16px!important;
        box-shadow:0 8px 22px rgba(16,42,67,.045)!important;
    }
    .compare-title-v79{
        font-size:10px!important;
        text-transform:uppercase;
        letter-spacing:.04em;
        color:#708399!important;
        font-weight:800!important;
    }
    .compare-value-v79{
        font-size:25px!important;
        color:#102A43!important;
        font-weight:850!important;
        margin:7px 0 5px!important;
    }

    /* Contenedores estándar */
    [data-testid="stVerticalBlockBorderWrapper"]{
        border:1px solid var(--gen-border)!important;
        border-radius:16px!important;
        background:#fff!important;
        box-shadow:0 7px 22px rgba(16,42,67,.035)!important;
    }

    /* Métricas Streamlit */
    [data-testid="stMetric"]{
        border:1px solid var(--gen-border)!important;
        background:#fff!important;
        border-radius:14px!important;
        padding:10px 12px!important;
        box-shadow:none!important;
    }
    [data-testid="stMetricValue"]{
        color:#102A43!important;
        font-weight:850!important;
        letter-spacing:-.035em!important;
    }
    [data-testid="stMetricLabel"] p{
        color:#71849A!important;
        font-weight:700!important;
    }

    /* Inputs */
    [data-baseweb="input"] > div,
    [data-baseweb="select"] > div,
    [data-testid="stTextArea"] textarea{
        border-radius:11px!important;
        border-color:#DDE6EF!important;
        background:#fff!important;
    }

    /* Tabs */
    button[data-baseweb="tab"]{
        border-radius:10px!important;
        padding:9px 14px!important;
        font-weight:750!important;
        color:#5C7085!important;
    }
    button[data-baseweb="tab"][aria-selected="true"]{
        color:#12395B!important;
        background:#EAF3FB!important;
    }

    /* Botones */
    [data-testid="stButton"] button{
        min-height:40px;
        border-radius:11px!important;
        font-weight:760!important;
        transition:transform .12s ease, box-shadow .12s ease!important;
    }
    [data-testid="stButton"] button:hover{
        transform:translateY(-1px);
        box-shadow:0 7px 16px rgba(16,42,67,.10)!important;
    }
    [data-testid="stButton"] button[kind="primary"]{
        background:linear-gradient(135deg,#2F80ED,#2570D7)!important;
        border:none!important;
        color:#fff!important;
    }

    /* Dataframes */
    [data-testid="stDataFrame"]{
        border:1px solid var(--gen-border)!important;
        border-radius:14px!important;
        overflow:hidden!important;
        box-shadow:0 8px 24px rgba(16,42,67,.04)!important;
        background:#fff!important;
    }

    /* Expanders */
    [data-testid="stExpander"]{
        border:1px solid var(--gen-border)!important;
        border-radius:13px!important;
        background:#fff!important;
        box-shadow:none!important;
    }

    /* Alertas */
    [data-testid="stAlert"]{
        border-radius:13px!important;
        border-width:1px!important;
    }

    /* Ranking / alertas */
    .leader-strip-v77{
        border-radius:13px!important;
        padding:11px 13px!important;
        box-shadow:none!important;
    }
    .alert-summary-v77{
        border-radius:16px!important;
        border:1px solid #F3D7D2!important;
        background:linear-gradient(90deg,#FFF7F5,#FFFFFF)!important;
        box-shadow:0 8px 20px rgba(240,68,56,.04)!important;
    }

    /* Mensajes diarios: tarjetas operadores */
    .op-head-v74{margin-bottom:9px!important}
    .op-name-v74{
        font-size:16px!important;
        color:#172B4D!important;
        font-weight:850!important;
        letter-spacing:-.02em;
    }
    .op-contact-v74{
        color:#7A8EA5!important;
        font-size:9px!important;
    }
    .schedule-v74{
        border-radius:8px!important;
        background:#F6F9FC!important;
        border:1px solid #E7EDF4!important;
        color:#60748A!important;
    }
    .action-v74{
        border-radius:9px!important;
        font-weight:760!important;
    }
    .monthly-v74{
        border-top:1px solid #EDF1F5!important;
    }

    /* Scrollbar sutil */
    ::-webkit-scrollbar{width:10px;height:10px}
    ::-webkit-scrollbar-track{background:transparent}
    ::-webkit-scrollbar-thumb{
        background:#C7D3DF;
        border-radius:999px;
        border:3px solid transparent;
        background-clip:padding-box;
    }

    /* Responsive */
    @media(max-width:1100px){
        .block-container{
            padding-left:1.35rem!important;
            padding-right:1.35rem!important;
        }
        .kpi-value-v79{font-size:23px!important}
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# VERSIÓN FINAL VISUAL · UI ejecutiva
# =========================================================

# =========================================================
# FUNCIONES AUXILIARES
# =========================================================

def quitar_acentos(texto):
    texto = str(texto)
    return "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )


def normalizar_texto(texto):
    texto = quitar_acentos(texto).lower().strip()
    texto = re.sub(r"\s+", " ", texto)
    return texto


def normalizar_columna(columna):
    texto = normalizar_texto(columna)
    texto = texto.replace("$", "")
    texto = texto.replace("bs.", "")
    texto = texto.replace("bs", "")
    texto = re.sub(r"[^a-z0-9 ]", "", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


def convertir_numero(valor):
    """
    Convierte valores como:
    99.892,47
    170400
    Bs 99.892,47
    $ 99,892.47
    """
    if pd.isna(valor):
        return 0.0

    if isinstance(valor, (int, float)):
        return float(valor)

    texto = str(valor).strip()

    if texto == "":
        return 0.0

    texto = texto.replace("Bs.", "")
    texto = texto.replace("Bs", "")
    texto = texto.replace("$", "")
    texto = texto.replace(" ", "")

    # Formato latino: 99.892,47
    if "," in texto:
        texto = texto.replace(".", "")
        texto = texto.replace(",", ".")
    else:
        # Si únicamente tiene puntos, determinar si es decimal
        partes = texto.split(".")
        if len(partes) > 2:
            texto = "".join(partes)
        elif len(partes) == 2 and len(partes[1]) == 3:
            texto = "".join(partes)

    texto = re.sub(r"[^0-9.\-]", "", texto)

    try:
        return float(texto)
    except Exception:
        return 0.0


def formato_entero(valor):
    try:
        return f"{int(round(valor)):,}".replace(",", ".")
    except Exception:
        return "0"


def formato_bs(valor):
    try:
        return (
            f"Bs {valor:,.2f}"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )
    except Exception:
        return "Bs 0,00"


def formato_usd(valor):
    try:
        return (
            f"USD {valor:,.2f}"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )
    except Exception:
        return "USD 0,00"


def formato_porcentaje(valor):
    try:
        return f"{valor:.2f}%".replace(".", ",")
    except Exception:
        return "0,00%"


def buscar_columna(df, palabras):
    """
    Busca una columna usando partes de su nombre.
    """
    columnas_norm = {
        col: normalizar_columna(col)
        for col in df.columns
    }

    for col_original, col_norm in columnas_norm.items():
        if all(palabra in col_norm for palabra in palabras):
            return col_original

    return None


# =========================================================
# CALENDARIO Y MENSAJES
# =========================================================

def fecha_local_actual():
    return datetime.now(ZoneInfo("America/La_Paz")).date()


def ahora_bolivia():
    """
    Hora Bolivia calculada desde UTC real.
    Evita depender de la zona horaria del servidor de Streamlit.
    """
    return datetime.now(
        timezone.utc
    ).astimezone(
        ZoneInfo("America/La_Paz")
    )


def datetime_bolivia(valor):
    """
    Convierte cualquier timestamp guardado a hora Bolivia.

    Regla V96:
    - si viene con zona/offset: se convierte a America/La_Paz;
    - si viene sin zona (registros antiguos): se interpreta como UTC,
      que es como Supabase/Postgres suele entregar timestamptz serializado.
    """
    if valor is None or valor == "":
        return None

    try:
        if isinstance(valor, datetime):
            dt = valor
        else:
            dt = pd.to_datetime(
                valor
            ).to_pydatetime()

        if dt.tzinfo is None:
            dt = dt.replace(
                tzinfo=timezone.utc
            )

        return dt.astimezone(
            ZoneInfo("America/La_Paz")
        )
    except Exception:
        return None

def es_jornada_laboral(fecha):
    # Regla actual: lunes a sábado. Domingo no cuenta.
    return fecha.weekday() != 6


def jornadas_mes(fecha_ref):
    primer_dia = fecha_ref.replace(day=1)
    if fecha_ref.month == 12:
        siguiente_mes = fecha_ref.replace(
            year=fecha_ref.year + 1,
            month=1,
            day=1,
        )
    else:
        siguiente_mes = fecha_ref.replace(
            month=fecha_ref.month + 1,
            day=1,
        )

    ultimo_dia = siguiente_mes - timedelta(days=1)

    dias = []
    actual = primer_dia

    while actual <= ultimo_dia:
        if es_jornada_laboral(actual):
            dias.append(actual)
        actual += timedelta(days=1)

    return dias


def calcular_jornadas(fecha_ref=None):
    fecha_ref = fecha_ref or fecha_local_actual()
    dias = jornadas_mes(fecha_ref)

    transcurridas = len(
        [d for d in dias if d <= fecha_ref]
    )

    disponibles = len(
        [d for d in dias if d >= fecha_ref]
    )

    return {
        "total": len(dias),
        "transcurridas": transcurridas,
        "disponibles": disponibles,
        "esperado_pct": (
            transcurridas / len(dias) * 100
            if dias
            else 0
        ),
    }


def inicializar_calendario_mes(fecha_ref):
    clave_mes = f"{fecha_ref.year:04d}-{fecha_ref.month:02d}"

    if clave_mes not in st.session_state.calendario_laboral:
        dias_mes = calendar.monthrange(
            fecha_ref.year,
            fecha_ref.month,
        )[1]

        st.session_state.calendario_laboral[clave_mes] = {
            dia: (
                date(
                    fecha_ref.year,
                    fecha_ref.month,
                    dia,
                ).weekday() != 6
            )
            for dia in range(1, dias_mes + 1)
        }

    return clave_mes


def jornadas_configuradas(fecha_ref=None):
    fecha_ref = fecha_ref or fecha_local_actual()
    clave_mes = inicializar_calendario_mes(fecha_ref)

    calendario_mes = st.session_state.calendario_laboral[
        clave_mes
    ]

    dias_laborales = [
        date(
            fecha_ref.year,
            fecha_ref.month,
            dia,
        )
        for dia, es_laboral in calendario_mes.items()
        if es_laboral
    ]

    transcurridas = len(
        [d for d in dias_laborales if d <= fecha_ref]
    )

    disponibles = len(
        [d for d in dias_laborales if d >= fecha_ref]
    )

    return {
        "total": len(dias_laborales),
        "transcurridas": transcurridas,
        "disponibles": disponibles,
        "esperado_pct": (
            transcurridas / len(dias_laborales) * 100
            if dias_laborales
            else 0
        ),
        "dias": dias_laborales,
        "clave_mes": clave_mes,
    }


def metas_actuales():
    return {
        "gestiones": st.session_state.meta_gestiones_cfg,
        "compromisos": st.session_state.meta_compromisos_cfg,
        "recuperacion": st.session_state.meta_recuperacion_cfg,
        "diaria_compromisos": st.session_state.meta_diaria_compromisos_cfg,
    }


def objetivo_hoy_gestiones(acumulado, jornadas_disponibles):
    meta = st.session_state.meta_gestiones_cfg
    faltante = max(meta - acumulado, 0)

    if faltante <= 0:
        return 0

    if jornadas_disponibles <= 0:
        return int(math.ceil(faltante))

    return int(
        math.ceil(faltante / jornadas_disponibles)
    )


def objetivo_hoy_compromisos(acumulado, jornadas_disponibles):
    meta = st.session_state.meta_compromisos_cfg
    minimo_diario = (
        st.session_state.meta_diaria_compromisos_cfg
    )

    faltante = max(meta - acumulado, 0)

    # Aunque la meta mensual ya esté cumplida,
    # se mantiene el mínimo diario definido.
    if faltante <= 0:
        return int(minimo_diario)

    if jornadas_disponibles <= 0:
        return max(
            int(math.ceil(faltante)),
            int(minimo_diario),
        )

    recuperacion_diaria = int(
        math.ceil(faltante / jornadas_disponibles)
    )

    return max(
        int(minimo_diario),
        recuperacion_diaria,
    )


def clasificar_avance(porcentaje, esperado):
    if porcentaje >= 100:
        return "Meta cumplida"
    if porcentaje >= esperado + 5:
        return "Excelente avance"
    if porcentaje >= esperado - 3:
        return "Buen avance"
    if porcentaje >= esperado - 10:
        return "En seguimiento"
    return "Reforzar"



def obtener_fila_operador_actual(usuario):
    """
    Devuelve SIEMPRE la fila más reciente del operador desde
    st.session_state.resultado_operadores.

    Así Ranking, tarjetas, vista previa y Telegram usan exactamente
    la misma fuente y no pueden enviar cifras de una versión anterior.
    """
    resultado_actual = st.session_state.get(
        "resultado_operadores"
    )

    if (
        resultado_actual is None
        or resultado_actual.empty
    ):
        return None

    coincidencia = resultado_actual[
        resultado_actual["Usuario"]
        .astype(str)
        == str(usuario)
    ]

    if coincidencia.empty:
        return None

    return coincidencia.iloc[0].copy()


def generar_mensaje_operador_actual(
    usuario,
    jornadas_info,
):
    fila_actual = obtener_fila_operador_actual(
        usuario
    )

    if fila_actual is None:
        return None

    # Enlace humano de contacto directo con coordinación.
    # Se agrega solo al seguimiento privado del operador.
    mensaje = (
        mensaje.rstrip()
        + "\n\n💬 ¿Necesitas comentarme algo? "
        + "[Escríbeme directamente](https://t.me/josecarlos_27)"
    )

    return generar_mensaje_diario(
        fila_actual,
        jornadas_info,
    )


def generar_mensaje_diario(fila, jornadas_info):
    usuario = fila["Usuario"]
    datos = OPERADORES.get(usuario, {})
    nombre = datos.get(
        "nombre_mensaje",
        fila["Operador"].split()[0],
    )

    gestiones = int(fila["Gestiones"])
    compromisos = int(fila["Compromisos"])
    recuperacion = float(fila["Recuperación acumulada"])

    meta_g = int(st.session_state.meta_gestiones_cfg)
    meta_c = int(st.session_state.meta_compromisos_cfg)
    meta_r = float(st.session_state.meta_recuperacion_cfg)

    pct_g = gestiones / meta_g * 100 if meta_g else 0
    pct_c = compromisos / meta_c * 100 if meta_c else 0
    pct_r = recuperacion / meta_r * 100 if meta_r else 0

    esperado = jornadas_info["esperado_pct"]

    minimo_g = int(
        st.session_state.get(
            "meta_diaria_gestiones_cfg",
            META_DIARIA_GESTIONES,
        )
    )
    minimo_c = int(st.session_state.meta_diaria_compromisos_cfg)

    faltante_r = max(meta_r - recuperacion, 0)

    check_g = " ✅" if gestiones >= meta_g else ""
    check_c = " ✅" if compromisos >= meta_c else ""
    check_r = " ✅" if recuperacion >= meta_r else ""

    linea_g = (
        f"🔹 Gestiones: {formato_entero(gestiones)} / "
        f"{formato_entero(meta_g)} — {formato_porcentaje(pct_g)}{check_g}"
    )
    linea_c = (
        f"🔹 Compromisos: {formato_entero(compromisos)} / "
        f"{formato_entero(meta_c)} — {formato_porcentaje(pct_c)}{check_c}"
    )
    linea_r = (
        f"🔹 Recuperación: {formato_usd(recuperacion)} / "
        f"{formato_usd(meta_r)} — {formato_porcentaje(pct_r)}{check_r}"
    )

    if gestiones >= meta_g and compromisos >= meta_c:
        cierre = (
            "Mantengamos los mínimos diarios y reforcemos la recuperación "
            "para sostener el resultado."
        )
    elif pct_r < esperado - 10:
        cierre = (
            "Mantengamos el ritmo y reforcemos la recuperación "
            "para acercarnos a la meta mensual."
        )
    else:
        cierre = (
            "Mantengamos el ritmo diario para seguir avanzando "
            "hacia las metas del mes."
        )

    saludo_individual, emoji_individual = saludo_segun_hora()

    avance_hora = calcular_avance_hora_operador(
        usuario,
        st.session_state.callcenter_df,
    )

    bloque_hoy = ""

    if avance_hora["disponible"]:
        horario_msg = avance_hora.get(
            "horario"
        ) or {}

        linea_horario_msg = ""

        if horario_msg.get(
            "horario_configurado"
        ):
            linea_horario_msg = (
                f"🕒 Jornada: "
                f"{horario_msg['entrada']}–{horario_msg['salida']} "
                f"· Break {horario_msg['break_inicio']}–{horario_msg['break_fin']}\n"
                f"📍 Estado: {avance_hora.get('estado_jornada', '')}\n"
            )

        bloque_hoy = (
            f"\n\n⏱️ Avance de hoy · corte {avance_hora['hora_corte']}\n"
            f"{linea_horario_msg}"
            f"📞 Gestiones: {formato_entero(avance_hora['gestiones_hoy'])} / "
            f"{formato_entero(minimo_g)}\n"
            f"{texto_estado_ritmo(avance_hora['delta_gestiones'], 'gestiones')}\n"
            f"🎯 Faltan {formato_entero(avance_hora['faltan_gestiones'])} "
            f"para el mínimo diario"
        )

        if avance_hora.get(
            "compromisos_disponibles"
        ):
            bloque_hoy += (
                f"\n\n🤝 Compromisos: "
                f"{formato_entero(avance_hora['compromisos_hoy'])} / "
                f"{formato_entero(minimo_c)}\n"
                f"{texto_estado_ritmo(avance_hora['delta_compromisos'], 'compromisos')}\n"
                f"🎯 Faltan "
                f"{formato_entero(avance_hora['faltan_compromisos'])} "
                f"para el mínimo diario"
            )

    # V87 · La recuperación no se repite en cada seguimiento.
    # Se muestra en el primer seguimiento individual del día y vuelve
    # a aparecer desde las 17:00 como referencia de cierre.
    ahora_mensaje_v87 = ahora_bolivia()
    ya_recibio_seguimiento_v87 = envio_ya_realizado_hoy(
        usuario,
        "seguimiento",
    )
    mostrar_recuperacion_v87 = (
        not ya_recibio_seguimiento_v87
        or ahora_mensaje_v87.hour >= 17
    )

    if mostrar_recuperacion_v87:
        bloque_mes_v87 = (
            f"📊 Acumulado del mes\n"
            f"{linea_g}\n"
            f"{linea_c}\n"
            f"{linea_r}"
        )
    else:
        bloque_mes_v87 = (
            f"📊 Acumulado del mes\n"
            f"{linea_g}\n"
            f"{linea_c}"
        )

    # En los seguimientos intermedios el cierre se enfoca en lo que el
    # operador puede corregir durante la jornada: gestiones y compromisos.
    if (
        ya_recibio_seguimiento_v87
        and ahora_mensaje_v87.hour < 17
    ):
        if avance_hora.get("disponible"):
            cierre_v87 = (
                "Sigamos enfocados en el avance de hoy y en recuperar "
                "cualquier brecha antes del siguiente corte."
            )
        else:
            cierre_v87 = (
                "Mantengamos el ritmo diario para continuar avanzando "
                "hacia las metas del mes."
            )
    elif ahora_mensaje_v87.hour >= 17:
        cierre_v87 = (
            "Aprovechemos las horas restantes para cerrar la jornada "
            "con el mejor cumplimiento posible."
        )
    else:
        cierre_v87 = cierre

    mensaje = (
        f"{saludo_individual}, {nombre}. {emoji_individual}\n\n"
        f"{bloque_mes_v87}"
        f"{bloque_hoy}\n\n"
        f"{cierre_v87} 💪"
    )

    return {
        "mensaje": mensaje,
        "objetivo_gestiones": minimo_g,
        "objetivo_compromisos": minimo_c,
        "faltante_recuperacion": faltante_r,
        "avance_hora": avance_hora,
        "estado_gestiones": clasificar_avance(pct_g, esperado),
        "estado_compromisos": clasificar_avance(pct_c, esperado),
        "estado_recuperacion": clasificar_avance(pct_r, esperado),
    }


# =========================================================
# ORDENAMIENTO DE TABLAS
# =========================================================

def controles_ordenamiento(
    df,
    columnas,
    key_prefix,
    columna_default=None,
    descendente_default=True,
    etiquetas=None,
):
    """
    Ordena la tabla ANTES de formatear los valores.
    etiquetas permite mostrar nombres más claros al usuario.
    """
    columnas_validas = [
        c for c in columnas
        if c in df.columns
    ]

    if not columnas_validas:
        return df

    if columna_default not in columnas_validas:
        columna_default = columnas_validas[0]

    etiquetas = etiquetas or {
        c: c for c in columnas_validas
    }

    inverso = {
        etiquetas.get(c, c): c
        for c in columnas_validas
    }

    opciones_visibles = [
        etiquetas.get(c, c)
        for c in columnas_validas
    ]

    default_visible = etiquetas.get(
        columna_default,
        columna_default,
    )

    c1, c2 = st.columns([2, 1])

    with c1:
        visible_sel = st.selectbox(
            "Ordenar resultados por",
            opciones_visibles,
            index=opciones_visibles.index(
                default_visible
            ),
            key=f"{key_prefix}_columna",
        )

    with c2:
        sentido = st.radio(
            "Sentido",
            ["Mayor → menor", "Menor → mayor"],
            index=0 if descendente_default else 1,
            horizontal=True,
            key=f"{key_prefix}_sentido",
        )

    columna_orden = inverso[visible_sel]

    ordenado = df.sort_values(
        by=columna_orden,
        ascending=(sentido == "Menor → mayor"),
        na_position="last",
        kind="stable",
    ).reset_index(drop=True)

    return ordenado


# =========================================================
# LECTOR FLEXIBLE DE ARCHIVOS
# =========================================================

def leer_archivo(archivo):
    nombre = archivo.name.lower()
    contenido = archivo.getvalue()

    # CSV
    if nombre.endswith(".csv"):
        for sep in [";", ",", "\t"]:
            try:
                df = pd.read_csv(
                    BytesIO(contenido),
                    sep=sep,
                    encoding="utf-8",
                )
                if len(df.columns) > 1:
                    return df
            except Exception:
                pass

        try:
            return pd.read_csv(
                BytesIO(contenido),
                sep=";",
                encoding="latin1",
            )
        except Exception as e:
            raise ValueError(f"No se pudo leer el CSV: {e}")

    # XLSX
    if nombre.endswith(".xlsx"):
        try:
            return pd.read_excel(
                BytesIO(contenido),
                engine="openpyxl",
            )
        except Exception as e:
            raise ValueError(f"No se pudo leer el XLSX: {e}")

    # XLS que realmente viene como tabla HTML
    if nombre.endswith(".xls"):
        try:
            tablas = pd.read_html(BytesIO(contenido))

            if not tablas:
                raise ValueError("No se encontraron tablas.")

            # Tomamos la tabla con mayor cantidad de registros
            df = max(tablas, key=lambda x: len(x))

            return df

        except Exception:
            # Intento alternativo por si fuera un XLS real
            try:
                return pd.read_excel(BytesIO(contenido))
            except Exception as e:
                raise ValueError(
                    "No se pudo interpretar el archivo .xls. "
                    f"Detalle: {e}"
                )

    raise ValueError("Formato de archivo no reconocido.")


# =========================================================
# DETECCIÓN DEL TIPO DE REPORTE
# =========================================================

def detectar_tipo_reporte(df):
    columnas = [
        normalizar_columna(c)
        for c in df.columns
    ]

    texto_columnas = " | ".join(columnas)

    criterios_promesas = [
        "nombre usuario",
        "total gestion",
        "total compromisos",
        "compromisos cumplidos",
    ]

    coincidencias = sum(
        criterio in texto_columnas
        for criterio in criterios_promesas
    )

    if coincidencias >= 3:
        return "PROMESAS"

    criterios_callcenter = [
        "contrato",
        "cliente",
        "usuario",
    ]

    coincidencias_call = sum(
        criterio in texto_columnas
        for criterio in criterios_callcenter
    )

    if coincidencias_call >= 2 and len(df) > 100:
        return "CALLCENTER"

    return "DESCONOCIDO"


# =========================================================
# PROCESAMIENTO DEFINITIVO DE PROMESAS / RECUPERACIÓN
# =========================================================

def procesar_promesas(df):
    """
    REGLA DEFINITIVA:

    1. Tomar Compromisos Cumplidos en $ del registro SIN USUARIO.
    2. Dividir ese monto entre 8 operadores.
    3. Sumar esa parte al monto individual de cada operador.
    4. Recuperación ajustada / Bs 170.400 * 100.
    5. Resultado principal = porcentaje.
    """

    df = df.copy()

    # Limpiar nombres de columnas multinivel si existieran
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [
            " ".join(
                str(x)
                for x in col
                if str(x) != "nan"
            ).strip()
            for col in df.columns
        ]

    col_usuario = buscar_columna(
        df,
        ["nombre", "usuario"],
    )

    col_gestiones = buscar_columna(
        df,
        ["total", "gestion"],
    )

    col_compromisos = buscar_columna(
        df,
        ["total", "compromisos"],
    )

    col_cumplidos = buscar_columna(
        df,
        ["compromisos", "cumplidos"],
    )

    # Buscar específicamente columna monetaria de cumplidos.
    columnas_cumplidos = []

    for col in df.columns:
        norm = normalizar_columna(col)

        if (
            "compromisos" in norm
            and "cumplidos" in norm
        ):
            columnas_cumplidos.append(col)

    col_cumplidos_monto = None

    # Normalmente la última columna coincidente es la monetaria.
    if columnas_cumplidos:
        col_cumplidos_monto = columnas_cumplidos[-1]

    if col_usuario is None:
        raise ValueError(
            "No se encontró la columna 'Nombre Usuario'."
        )

    if col_cumplidos_monto is None:
        raise ValueError(
            "No se encontró la columna de "
            "'Compromisos Cumplidos en $'."
        )

    # Normalizar usuario
    df["_usuario_norm"] = (
        df[col_usuario]
        .astype(str)
        .apply(normalizar_texto)
    )

    # -----------------------------------------------------
    # DETECTAR FILA SIN USUARIO
    # -----------------------------------------------------

    mascara_sin_usuario = df["_usuario_norm"].apply(
        lambda x:
        "sin usuario" in x
        or x in ["sinusuario", "sin user"]
    )

    filas_sin_usuario = df[mascara_sin_usuario]

    if filas_sin_usuario.empty:
        monto_sin_usuario = 0.0
    else:
        monto_sin_usuario = filas_sin_usuario[
            col_cumplidos_monto
        ].apply(convertir_numero).sum()

    # REGLA FIJA: DIVIDIR ENTRE 8
    distribucion_por_operador = (
        monto_sin_usuario / CANTIDAD_OPERADORES
    )

    resultados = []

    # -----------------------------------------------------
    # LOS 8 OPERADORES OFICIALES
    # -----------------------------------------------------

    for usuario, datos in OPERADORES.items():

        usuario_norm = normalizar_texto(usuario)

        mascara = df["_usuario_norm"] == usuario_norm

        fila_operador = df[mascara]

        if fila_operador.empty:

            gestiones = 0
            compromisos = 0
            cumplidos = 0
            monto_individual = 0.0

        else:

            fila = fila_operador.iloc[0]

            gestiones = (
                convertir_numero(fila[col_gestiones])
                if col_gestiones
                else 0
            )

            compromisos = (
                convertir_numero(fila[col_compromisos])
                if col_compromisos
                else 0
            )

            cumplidos = (
                convertir_numero(fila[col_cumplidos])
                if col_cumplidos
                else 0
            )

            monto_individual = convertir_numero(
                fila[col_cumplidos_monto]
            )

        # =================================================
        # CÁLCULO OFICIAL DE RECUPERACIÓN
        # =================================================

        recuperacion_ajustada = (
            monto_individual
            + distribucion_por_operador
        )

        porcentaje_recuperacion = (
            recuperacion_ajustada
            / st.session_state.meta_recuperacion_cfg
            * 100
        )

        porcentaje_gestiones = (
            gestiones
            / st.session_state.meta_gestiones_cfg
            * 100
            if st.session_state.meta_gestiones_cfg
            else 0
        )

        porcentaje_compromisos = (
            compromisos
            / st.session_state.meta_compromisos_cfg
            * 100
            if st.session_state.meta_compromisos_cfg
            else 0
        )

        resultados.append(
            {
                "Usuario": usuario,
                "Operador": datos["nombre"],
                "Correo": datos["correo"],

                "Gestiones": int(round(gestiones)),
                "% Gestiones": porcentaje_gestiones,

                "Compromisos": int(round(compromisos)),
                "% Compromisos": porcentaje_compromisos,

                "Compromisos cumplidos": int(
                    round(cumplidos)
                ),

                "Recuperación original": monto_individual,

                "Distribución sin usuario":
                    distribucion_por_operador,

                "Recuperación acumulada":
                    recuperacion_ajustada,

                "% Recuperación":
                    porcentaje_recuperacion,
            }
        )

    resultado_df = pd.DataFrame(resultados)

    return (
        resultado_df,
        monto_sin_usuario,
        distribucion_por_operador,
    )




def mostrar_boton_copiar_imagen(imagen_bytes):
    """
    Renderiza un botón que intenta copiar el PNG directamente
    al portapapeles del navegador para pegarlo con Ctrl+V.
    """
    if hasattr(imagen_bytes, "getvalue"):
        raw = imagen_bytes.getvalue()
    else:
        raw = imagen_bytes

    imagen_b64 = base64.b64encode(raw).decode("utf-8")

    html = f"""
    <div style="font-family:Arial,sans-serif;">
      <button
        id="copy-image-btn"
        style="
          width:100%;
          padding:0.62rem 1rem;
          border:1px solid #d0d5dd;
          border-radius:0.5rem;
          background:#ffffff;
          color:#101828;
          font-size:14px;
          font-weight:600;
          cursor:pointer;
        "
      >
        📋 Copiar imagen
      </button>

      <div
        id="copy-status"
        style="
          margin-top:6px;
          font-size:12px;
          min-height:18px;
          color:#475467;
        "
      ></div>
    </div>

    <script>
      const btn = document.getElementById("copy-image-btn");
      const status = document.getElementById("copy-status");

      btn.addEventListener("click", async () => {{
        try {{
          status.textContent = "Copiando imagen...";

          const response = await fetch(
            "data:image/png;base64,{imagen_b64}"
          );

          const blob = await response.blob();

          if (!navigator.clipboard || !window.ClipboardItem) {{
            throw new Error(
              "Tu navegador no permite copiar imágenes directamente."
            );
          }}

          await navigator.clipboard.write([
            new ClipboardItem({{
              "image/png": blob
            }})
          ]);

          status.textContent =
            "✅ Imagen copiada. Ya puedes pegarla con Ctrl + V.";
          status.style.color = "#067647";

        }} catch (error) {{
          console.error(error);
          status.textContent =
            "⚠️ El navegador bloqueó el portapapeles. Usa Descargar imagen como alternativa.";
          status.style.color = "#b54708";
        }}
      }});
    </script>
    """

    components.html(
        html,
        height=92,
        scrolling=False,
    )


# =========================================================
# IMAGEN EJECUTIVA DE AVANCE DE RECUPERACIÓN
# =========================================================

def generar_imagen_avance_recuperacion(
    tabla_general,
    fecha_reporte,
    meta_individual,
):
    """
    Genera una imagen PNG compacta y legible para pegar directamente
    en Outlook o WhatsApp.
    """
    tabla = tabla_general.copy()

    columnas_requeridas = [
        "Operador",
        "Recuperación acumulada",
        "% Recuperación",
    ]

    faltantes = [
        c for c in columnas_requeridas
        if c not in tabla.columns
    ]

    if faltantes:
        raise ValueError(
            "No se puede generar la imagen. Faltan columnas: "
            + ", ".join(faltantes)
        )

    tabla = tabla.sort_values(
        "% Recuperación",
        ascending=False,
        kind="stable",
    ).reset_index(drop=True)

    total_equipo = float(
        tabla["Recuperación acumulada"].sum()
    )

    meta_equipo = float(meta_individual) * len(tabla)

    pct_equipo = (
        total_equipo / meta_equipo * 100
        if meta_equipo
        else 0
    )

    falta_equipo = max(
        meta_equipo - total_equipo,
        0,
    )

    # Imagen pensada para correo: aprox. 820 px de ancho.
    fig, ax = plt.subplots(
        figsize=(7.4, 5.6),
        dpi=110,
    )
    ax.axis("off")

    titulo = (
        f"AVANCE DE RECUPERACIÓN · "
        f"{fecha_reporte.strftime('%d/%m/%Y')}"
    )

    fig.text(
        0.04,
        0.955,
        titulo,
        fontsize=15,
        fontweight="bold",
        ha="left",
        va="top",
    )

    fig.text(
        0.04,
        0.915,
        (
            f"Meta mensual por operador: "
            f"{formato_usd(meta_individual)}"
        ),
        fontsize=9.5,
        ha="left",
        va="top",
    )

    fig.text(
        0.04,
        0.875,
        (
            f"Equipo: {formato_usd(total_equipo)}   ·   "
            f"Cumplimiento: {formato_porcentaje(pct_equipo)}   ·   "
            f"Falta: {formato_usd(falta_equipo)}"
        ),
        fontsize=9.5,
        fontweight="bold",
        ha="left",
        va="top",
    )

    # Nombres más compactos para que nunca se corten.
    def nombre_corto(nombre):
        partes = str(nombre).split()

        if len(partes) <= 2:
            return str(nombre)

        # Nombre + último apellido.
        return f"{partes[0]} {partes[-1]}"

    filas = []

    for i, fila in tabla.iterrows():

        recuperacion = float(
            fila["Recuperación acumulada"]
        )

        porcentaje = float(
            fila["% Recuperación"]
        )

        falta = max(
            float(meta_individual) - recuperacion,
            0,
        )

        filas.append(
            [
                str(i + 1),
                nombre_corto(
                    fila["Operador"]
                ),
                formato_usd(
                    recuperacion
                ),
                formato_porcentaje(
                    porcentaje
                ),
                formato_usd(
                    falta
                ),
            ]
        )

    tabla_plot = ax.table(
        cellText=filas,
        colLabels=[
            "#",
            "Operador",
            "Recuperación",
            "Cumpl.",
            "Falta",
        ],
        cellLoc="left",
        colLoc="left",
        bbox=[
            0.035,
            0.08,
            0.93,
            0.70,
        ],
        colWidths=[
            0.055,
            0.24,
            0.245,
            0.16,
            0.245,
        ],
    )

    tabla_plot.auto_set_font_size(
        False
    )

    tabla_plot.set_fontsize(
        8.8
    )

    for (
        fila_idx,
        col_idx,
    ), celda in tabla_plot.get_celld().items():

        celda.set_linewidth(
            0.6
        )

        if fila_idx == 0:
            celda.get_text().set_fontweight(
                "bold"
            )

        if (
            fila_idx > 0
            and col_idx == 1
        ):
            celda.get_text().set_fontweight(
                "bold"
            )

    fig.text(
        0.04,
        0.025,
        (
            "GEN Control · Recuperación acumulada en USD · "
            "Distribución Sin usuario ÷ 8"
        ),
        fontsize=7.8,
        ha="left",
        va="bottom",
    )

    buffer = BytesIO()

    fig.savefig(
        buffer,
        format="png",
        dpi=110,
        bbox_inches="tight",
        pad_inches=0.12,
    )

    plt.close(
        fig
    )

    buffer.seek(
        0
    )

    return buffer




# =========================================================
# SUPABASE / PERSISTENCIA
# =========================================================

@st.cache_resource
def get_supabase():
    """
    Conexión robusta a Supabase.
    Acepta distintas formas de guardar los Secrets en Streamlit.
    """
    try:
        url = None
        key = None

        # Opción 1: claves en la raíz
        try:
            url = st.secrets.get("SUPABASE_URL")
            key = st.secrets.get("SUPABASE_KEY")
        except Exception:
            pass

        # Opción 2: sección [supabase]
        if not url or not key:
            try:
                supa = st.secrets.get("supabase", {})
                url = (
                    url
                    or supa.get("url")
                    or supa.get("SUPABASE_URL")
                )
                key = (
                    key
                    or supa.get("key")
                    or supa.get("SUPABASE_KEY")
                )
            except Exception:
                pass

        if not url:
            raise ValueError(
                "No se encontró SUPABASE_URL en Streamlit Secrets."
            )

        if not key:
            raise ValueError(
                "No se encontró SUPABASE_KEY en Streamlit Secrets."
            )

        cliente = create_client(
            str(url).strip(),
            str(key).strip(),
        )

        # Prueba real de conexión
        cliente.table("configuracion").select(
            "id"
        ).limit(1).execute()

        st.session_state["_supabase_error"] = ""
        return cliente

    except Exception as e:
        st.session_state["_supabase_error"] = str(e)
        return None


def supabase_disponible():
    return get_supabase() is not None


def diagnostico_supabase():
    """
    Devuelve un mensaje seguro; nunca muestra URL ni key.
    """
    if get_supabase() is not None:
        return True, "Supabase conectado correctamente."

    error = st.session_state.get(
        "_supabase_error",
        "No se pudo establecer conexión.",
    )

    return False, error


def cargar_configuracion_supabase():
    sb = get_supabase()

    if sb is None:
        return

    try:
        resp = (
            sb.table("configuracion")
            .select("*")
            .eq("id", 1)
            .execute()
        )

        if resp.data:
            fila = resp.data[0]

            st.session_state.meta_gestiones_cfg = int(
                fila.get(
                    "meta_gestiones",
                    st.session_state.meta_gestiones_cfg,
                )
            )

            st.session_state.meta_compromisos_cfg = int(
                fila.get(
                    "meta_compromisos",
                    st.session_state.meta_compromisos_cfg,
                )
            )

            st.session_state.meta_recuperacion_cfg = float(
                fila.get(
                    "meta_recuperacion",
                    st.session_state.meta_recuperacion_cfg,
                )
            )

            st.session_state.meta_diaria_compromisos_cfg = int(
                fila.get(
                    "meta_diaria_compromisos",
                    st.session_state.meta_diaria_compromisos_cfg,
                )
            )
    except Exception:
        pass


def guardar_configuracion_supabase():
    sb = get_supabase()

    if sb is None:
        return False, "Supabase no está conectado."

    payload = {
        "id": 1,
        "meta_gestiones": int(
            st.session_state.meta_gestiones_cfg
        ),
        "meta_compromisos": int(
            st.session_state.meta_compromisos_cfg
        ),
        "meta_recuperacion": float(
            st.session_state.meta_recuperacion_cfg
        ),
        "meta_diaria_compromisos": int(
            st.session_state.meta_diaria_compromisos_cfg
        ),
        "updated_at": ahora_bolivia().isoformat(),
    }

    try:
        (
            sb.table("configuracion")
            .upsert(payload)
            .execute()
        )
        return True, "Configuración guardada en Supabase."
    except Exception as e:
        return False, str(e)


def guardar_calendario_supabase(
    anio,
    mes,
    calendario_mes,
):
    sb = get_supabase()

    if sb is None:
        return False, "Supabase no está conectado."

    registros = []

    for dia, laboral in calendario_mes.items():
        fecha_dia = date(
            int(anio),
            int(mes),
            int(dia),
        )

        registros.append(
            {
                "fecha": fecha_dia.isoformat(),
                "es_laboral": bool(laboral),
            }
        )

    try:
        (
            sb.table("calendario_laboral")
            .upsert(
                registros,
                on_conflict="fecha",
            )
            .execute()
        )
        return True, "Calendario guardado."
    except Exception as e:
        return False, str(e)


def cargar_calendario_supabase(
    anio,
    mes,
):
    sb = get_supabase()

    if sb is None:
        return None

    inicio = date(
        int(anio),
        int(mes),
        1,
    )

    dias_mes = calendar.monthrange(
        int(anio),
        int(mes),
    )[1]

    fin = date(
        int(anio),
        int(mes),
        dias_mes,
    )

    try:
        resp = (
            sb.table("calendario_laboral")
            .select("fecha,es_laboral")
            .gte("fecha", inicio.isoformat())
            .lte("fecha", fin.isoformat())
            .execute()
        )

        if not resp.data:
            return None

        return {
            int(
                pd.to_datetime(
                    fila["fecha"]
                ).day
            ): bool(fila["es_laboral"])
            for fila in resp.data
        }
    except Exception:
        return None


def guardar_resultados_supabase(
    resultado_df,
    fecha_reporte,
    nombre_archivo,
):
    sb = get_supabase()

    if sb is None:
        return False, "Supabase no está conectado."

    registros = []

    for _, fila in resultado_df.iterrows():
        registros.append(
            {
                "fecha": fecha_reporte.isoformat(),
                "usuario": fila["Usuario"],
                "operador": fila["Operador"],
                "gestiones": int(
                    fila["Gestiones"]
                ),
                "compromisos": int(
                    fila["Compromisos"]
                ),
                "compromisos_cumplidos": int(
                    fila["Compromisos cumplidos"]
                ),
                "recuperacion_original": float(
                    fila["Recuperación original"]
                ),
                "distribucion_sin_usuario": float(
                    fila["Distribución sin usuario"]
                ),
                "recuperacion_acumulada": float(
                    fila["Recuperación acumulada"]
                ),
                "porcentaje_recuperacion": float(
                    fila["% Recuperación"]
                ),
                "archivo_origen": nombre_archivo,
            }
        )

    try:
        (
            sb.table("resultados_diarios")
            .upsert(
                registros,
                on_conflict="fecha,usuario",
            )
            .execute()
        )
        return True, "Resultados guardados en histórico."
    except Exception as e:
        return False, str(e)


def cargar_operadores_supabase():
    sb = get_supabase()

    if sb is None:
        return None

    try:
        resp = (
            sb.table("operadores")
            .select("*")
            .eq("activo", True)
            .order("nombre")
            .execute()
        )

        if not resp.data:
            return None

        return pd.DataFrame(resp.data)

    except Exception:
        return None


def guardar_operador_supabase(payload):
    sb = get_supabase()

    if sb is None:
        return False, "Supabase no está conectado."

    try:
        (
            sb.table("operadores")
            .upsert(
                payload,
                on_conflict="usuario",
            )
            .execute()
        )
        return True, "Operador guardado."
    except Exception as e:
        return False, str(e)


def sincronizar_operadores_base():
    """
    Carga inicial de los 8 operadores SIN sobrescribir datos ya guardados.
    Importante: no debe borrar teléfonos, correos editados ni nombres
    personalizados existentes en Supabase.
    """
    sb = get_supabase()

    if sb is None:
        return

    try:
        existentes_resp = (
            sb.table("operadores")
            .select("usuario")
            .execute()
        )

        usuarios_existentes = {
            str(fila["usuario"])
            for fila in (existentes_resp.data or [])
        }

        nuevos = []

        for usuario, datos in OPERADORES.items():
            if usuario in usuarios_existentes:
                continue

            nuevos.append(
                {
                    "usuario": usuario,
                    "nombre": datos["nombre"],
                    "nombre_mensaje": datos.get(
                        "nombre_mensaje",
                        datos["nombre"].split()[0],
                    ),
                    "correo": datos.get("correo", ""),
                    "telefono": datos.get("telefono", ""),
                    "telegram_chat_id": "",
                    "activo": True,
                }
            )

        if nuevos:
            (
                sb.table("operadores")
                .insert(nuevos)
                .execute()
            )

    except Exception:
        pass


def guardar_carga_supabase(
    nombre_archivo,
    tipo,
    registros,
):
    sb = get_supabase()

    if sb is None:
        return

    try:
        sb.table("cargas").insert(
            {
                "fecha_carga": datetime.now(
                    ZoneInfo("America/La_Paz")
                ).isoformat(),
                "nombre_archivo": nombre_archivo,
                "tipo_reporte": tipo,
                "registros": int(registros),
            }
        ).execute()
    except Exception:
        pass



# =========================================================
# PERSISTENCIA DEL ESTADO OPERATIVO — V93
# =========================================================

def guardar_estado_operativo_supabase(clave, nombre_archivo="", datos=None):
    sb = get_supabase()
    if sb is None:
        return False, "Supabase no está conectado."

    payload = {
        "clave": str(clave),
        "actualizado_en": ahora_bolivia().isoformat(),
        "nombre_archivo": str(nombre_archivo or ""),
        "datos": datos or {},
    }

    try:
        (
            sb.table("estado_operativo")
            .upsert(payload, on_conflict="clave")
            .execute()
        )
        return True, "Estado guardado."
    except Exception as e:
        return False, str(e)


def cargar_estado_operativo_supabase(clave):
    sb = get_supabase()
    if sb is None:
        return None

    try:
        resp = (
            sb.table("estado_operativo")
            .select("*")
            .eq("clave", str(clave))
            .limit(1)
            .execute()
        )
        if resp.data:
            return resp.data[0]
    except Exception:
        pass

    return None


def dataframe_a_json_v93(df):
    if df is None or df.empty:
        return []

    return json.loads(
        df.to_json(
            orient="records",
            date_format="iso",
            force_ascii=False,
        )
    )


def guardar_snapshot_promesas_v93(
    resultado_df,
    monto_sin_usuario,
    distribucion,
    nombre_archivo,
):
    return guardar_estado_operativo_supabase(
        "promesas_actual",
        nombre_archivo,
        {
            "resultado_operadores": dataframe_a_json_v93(
                resultado_df
            ),
            "monto_sin_usuario": float(
                monto_sin_usuario or 0.0
            ),
            "distribucion_sin_usuario": float(
                distribucion or 0.0
            ),
        },
    )


def guardar_snapshot_callcenter_v93(df, nombre_archivo):
    if df is None or df.empty:
        return False, "CallCenter vacío."

    # Solo se guardan columnas útiles para los cálculos de GEN Control.
    cols = []
    grupos = [
        ["fecha"],
        ["usuario"],
        ["compromiso"],
        ["tipo gestion", "tipo gestión"],
        ["contacto"],
        ["resultado"],
        ["monto($us)", "monto"],
    ]

    for candidatos in grupos:
        col = buscar_columna(df, candidatos)
        if col is not None and col not in cols:
            cols.append(col)

    compacto = df[cols].copy() if cols else df.copy()

    return guardar_estado_operativo_supabase(
        "callcenter_actual",
        nombre_archivo,
        {
            "filas": dataframe_a_json_v93(compacto),
            "registros": int(len(compacto)),
        },
    )


def restaurar_estado_operativo_v93():
    """
    Recupera automáticamente los últimos reportes procesados
    después de F5, cierre de pestaña, reinicio o nueva sesión.
    """
    if get_supabase() is None:
        return

    if st.session_state.get("resultado_operadores") is None:
        snap = cargar_estado_operativo_supabase(
            "promesas_actual"
        )
        if snap:
            datos = snap.get("datos") or {}
            filas = datos.get("resultado_operadores") or []

            if filas:
                st.session_state.resultado_operadores = pd.DataFrame(
                    filas
                )
                st.session_state.monto_sin_usuario = float(
                    datos.get("monto_sin_usuario", 0.0) or 0.0
                )
                st.session_state.distribucion_sin_usuario = float(
                    datos.get("distribucion_sin_usuario", 0.0) or 0.0
                )
                st.session_state.promesas_nombre_archivo = str(
                    snap.get("nombre_archivo") or ""
                )

                ts = snap.get("actualizado_en")
                if ts:
                    try:
                        st.session_state.promesas_cargado_en = (
                            datetime_bolivia(ts)
                        )
                    except Exception:
                        pass

    call = st.session_state.get("callcenter_df")
    if call is None or (
        hasattr(call, "empty") and call.empty
    ):
        snap = cargar_estado_operativo_supabase(
            "callcenter_actual"
        )
        if snap:
            datos = snap.get("datos") or {}
            filas = datos.get("filas") or []

            if filas:
                st.session_state.callcenter_df = pd.DataFrame(
                    filas
                )
                st.session_state.callcenter_nombre_archivo = str(
                    snap.get("nombre_archivo") or ""
                )

                ts = snap.get("actualizado_en")
                if ts:
                    try:
                        st.session_state.callcenter_cargado_en = (
                            datetime_bolivia(ts)
                        )
                    except Exception:
                        pass


# =========================================================
# SESSION STATE
# =========================================================

if "resultado_operadores" not in st.session_state:
    st.session_state.resultado_operadores = None

if "monto_sin_usuario" not in st.session_state:
    st.session_state.monto_sin_usuario = 0.0

if "distribucion_sin_usuario" not in st.session_state:
    st.session_state.distribucion_sin_usuario = 0.0

if "archivos_cargados" not in st.session_state:
    st.session_state.archivos_cargados = []

if "callcenter_df" not in st.session_state:
    st.session_state.callcenter_df = None

if "callcenter_cargado_en" not in st.session_state:
    st.session_state.callcenter_cargado_en = None

if "callcenter_nombre_archivo" not in st.session_state:
    st.session_state.callcenter_nombre_archivo = ""

if "promesas_cargado_en" not in st.session_state:
    st.session_state.promesas_cargado_en = None

if "promesas_nombre_archivo" not in st.session_state:
    st.session_state.promesas_nombre_archivo = ""

if "envios_diarios_cache" not in st.session_state:
    st.session_state.envios_diarios_cache = {}

if "permitir_envio_fuera_turno" not in st.session_state:
    st.session_state.permitir_envio_fuera_turno = False


if "config_desbloqueada" not in st.session_state:
    st.session_state.config_desbloqueada = False

if "meta_gestiones_cfg" not in st.session_state:
    st.session_state.meta_gestiones_cfg = META_GESTIONES

if "meta_compromisos_cfg" not in st.session_state:
    st.session_state.meta_compromisos_cfg = META_COMPROMISOS

if "meta_recuperacion_cfg" not in st.session_state:
    st.session_state.meta_recuperacion_cfg = META_RECUPERACION

if "meta_diaria_gestiones_cfg" not in st.session_state:
    st.session_state.meta_diaria_gestiones_cfg = META_DIARIA_GESTIONES

if "meta_diaria_compromisos_cfg" not in st.session_state:
    st.session_state.meta_diaria_compromisos_cfg = META_DIARIA_COMPROMISOS

if "calendario_laboral" not in st.session_state:
    st.session_state.calendario_laboral = {}

if "config_supabase_cargada" not in st.session_state:
    st.session_state.config_supabase_cargada = False

if "operadores_supabase_cargados" not in st.session_state:
    st.session_state.operadores_supabase_cargados = False

if "operador_guardado_ok" not in st.session_state:
    st.session_state.operador_guardado_ok = False

if not st.session_state.config_supabase_cargada:
    cargar_configuracion_supabase()
    st.session_state.config_supabase_cargada = True

if (
    supabase_disponible()
    and not st.session_state.operadores_supabase_cargados
):
    sincronizar_operadores_base()
    st.session_state.operadores_supabase_cargados = True

if "estado_operativo_restaurado_v93" not in st.session_state:
    st.session_state.estado_operativo_restaurado_v93 = False

if not st.session_state.estado_operativo_restaurado_v93:
    restaurar_estado_operativo_v93()
    st.session_state.estado_operativo_restaurado_v93 = True




# =========================================================
# TELEGRAM
# =========================================================

def obtener_telegram_group_chat_id():
    try:
        chat_id = st.secrets.get("TELEGRAM_GROUP_CHAT_ID")
        if chat_id:
            return str(chat_id).strip()

        telegram_cfg = st.secrets.get("telegram", {})
        chat_id = (
            telegram_cfg.get("group_chat_id")
            or telegram_cfg.get("TELEGRAM_GROUP_CHAT_ID")
        )
        return str(chat_id).strip() if chat_id else ""
    except Exception:
        return ""



def obtener_telegram_coordinador_chat_id():
    try:
        chat_id = st.secrets.get("TELEGRAM_COORDINADOR_CHAT_ID")
        if chat_id:
            return normalizar_telegram_chat_id(chat_id)

        telegram_cfg = st.secrets.get("telegram", {})
        chat_id = (
            telegram_cfg.get("coordinador_chat_id")
            or telegram_cfg.get("TELEGRAM_COORDINADOR_CHAT_ID")
        )
        return normalizar_telegram_chat_id(chat_id)
    except Exception:
        return ""


def obtener_telegram_bot_token():
    try:
        token = st.secrets.get("TELEGRAM_BOT_TOKEN")
        if token:
            return str(token).strip()

        telegram_cfg = st.secrets.get("telegram", {})
        token = (
            telegram_cfg.get("bot_token")
            or telegram_cfg.get("TELEGRAM_BOT_TOKEN")
        )
        return str(token).strip() if token else ""
    except Exception:
        return ""



def normalizar_telegram_chat_id(valor):
    """
    Devuelve un Chat ID válido o cadena vacía.

    Evita contar como configurados valores provenientes de Supabase
    como None, nan, null o cadenas vacías.
    Acepta IDs privados positivos y grupos negativos.
    """
    if valor is None:
        return ""

    try:
        if pd.isna(valor):
            return ""
    except Exception:
        pass

    texto = str(valor).strip()

    if texto.lower() in {
        "",
        "none",
        "nan",
        "null",
        "<na>",
    }:
        return ""

    # Telegram Chat ID debe ser numérico; grupos pueden llevar signo negativo.
    if not re.fullmatch(r"-?\d+", texto):
        return ""

    return texto


def enviar_mensaje_telegram(chat_id, texto):
    token = obtener_telegram_bot_token()

    if not token:
        return False, "Falta TELEGRAM_BOT_TOKEN en Streamlit Secrets."

    chat_id = str(chat_id or "").strip()

    if not chat_id:
        return False, "El operador no tiene Telegram Chat ID."

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    payload = parse.urlencode(
        {
            "chat_id": chat_id,
            "text": str(texto),
            "disable_web_page_preview": "true",
        }
    ).encode("utf-8")

    try:
        req = request.Request(
            url,
            data=payload,
            method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        with request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        if data.get("ok") is True:
            return True, "Mensaje enviado."

        return False, str(
            data.get("description", "Telegram rechazó el mensaje.")
        )
    except Exception as e:
        return False, str(e)



def _fuente_reporte(size, bold=False):
    """
    Fuente escalable REAL para las imágenes de Telegram.

    Usa matplotlib.font_manager para encontrar una fuente TrueType
    instalada en el entorno de Streamlit. Esto evita que PIL caiga en
    ImageFont.load_default(), que era la causa de que todo se viera
    diminuto aunque el código pidiera 40, 50 o 60 px.
    """
    try:
        propiedad = font_manager.FontProperties(
            family="DejaVu Sans",
            weight="bold" if bold else "normal",
        )

        ruta_fuente = font_manager.findfont(
            propiedad,
            fallback_to_default=True,
        )

        return ImageFont.truetype(
            ruta_fuente,
            size=int(size),
        )

    except Exception:
        # Segundo intento con la fuente incluida por matplotlib.
        try:
            ruta_fuente = font_manager.findfont(
                "DejaVu Sans",
                fallback_to_default=True,
            )
            return ImageFont.truetype(
                ruta_fuente,
                size=int(size),
            )
        except Exception:
            # Solo como último recurso.
            return ImageFont.load_default()


def generar_imagen_recuperacion_telegram(
    tabla_general,
    meta_individual,
):
    """
    UNA sola imagen vertical para Telegram,
    inspirada en la referencia aprobada:
    - nombres grandes;
    - porcentaje grande a la derecha;
    - monto debajo del nombre;
    - barra de avance visible;
    - 8 operadores en una sola imagen;
    - diseño limpio y proporcional para celular.
    """
    import io

    tabla = tabla_general.copy().sort_values(
        "% Recuperación",
        ascending=False,
        kind="stable",
    ).reset_index(drop=True)

    # Formato vertical similar a 1080 x 1536.
    W = 1080
    H = 1540
    margin = 22

    navy = (7, 29, 52)
    green = (67, 166, 68)
    green_dark = (30, 137, 46)
    white = (255, 255, 255)
    bg = (247, 249, 251)
    dark = (18, 29, 42)
    border = (218, 224, 230)
    bar_bg = (224, 229, 234)
    gold = (242, 182, 24)
    silver = (172, 181, 191)
    bronze = (195, 108, 48)

    img = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(img)

    # Tipografías grandes, como en la referencia.
    f_title = _fuente_reporte(62, True)
    f_date = _fuente_reporte(34, True)

    f_name = _fuente_reporte(58, True)
    f_name_long = _fuente_reporte(52, True)
    f_name_xlong = _fuente_reporte(46, True)

    f_amount = _fuente_reporte(36, True)
    f_pct = _fuente_reporte(52, True)
    f_pos = _fuente_reporte(40, True)
    f_footer = _fuente_reporte(28, True)

    # -----------------------------------------------------
    # HEADER
    # -----------------------------------------------------
    header_y1 = margin
    header_y2 = 155

    d.rounded_rectangle(
        (
            margin,
            header_y1,
            W - margin,
            header_y2,
        ),
        radius=28,
        fill=navy,
    )

    d.text(
        (
            margin + 34,
            header_y1 + 27,
        ),
        "RANKING DE RECUPERACIÓN",
        font=f_title,
        fill=white,
    )

    d.text(
        (
            margin + 34,
            header_y1 + 91,
        ),
        fecha_local_actual().strftime("%d/%m/%Y"),
        font=f_date,
        fill=green,
    )

    # -----------------------------------------------------
    # TARJETAS
    # -----------------------------------------------------
    cards_top = 177
    card_h = 153
    gap = 10

    for i, fila in tabla.iterrows():
        y1 = cards_top + i * (card_h + gap)
        y2 = y1 + card_h

        d.rounded_rectangle(
            (
                margin,
                y1,
                W - margin,
                y2,
            ),
            radius=24,
            fill=white,
            outline=border,
            width=2,
        )

        # Puesto
        pos_color = (
            gold if i == 0
            else silver if i == 1
            else bronze if i == 2
            else navy
        )

        badge_x1 = margin + 18
        badge_y1 = y1 + 28
        badge_x2 = badge_x1 + 78
        badge_y2 = badge_y1 + 78

        d.rounded_rectangle(
            (
                badge_x1,
                badge_y1,
                badge_x2,
                badge_y2,
            ),
            radius=16,
            fill=pos_color,
        )

        pos_txt = str(i + 1)
        pos_box = d.textbbox(
            (0, 0),
            pos_txt,
            font=f_pos,
        )

        d.text(
            (
                (badge_x1 + badge_x2) / 2
                - (pos_box[2] - pos_box[0]) / 2,
                badge_y1 + 18,
            ),
            pos_txt,
            font=f_pos,
            fill=white,
        )

        nombre = str(
            fila["Operador"]
        ).strip()

        recuperacion = float(
            fila["Recuperación acumulada"]
        )

        porcentaje = float(
            fila["% Recuperación"]
        )

        # El nombre es el elemento principal.
        name_x = badge_x2 + 34

        # Porcentaje grande a la derecha.
        pct_txt = formato_porcentaje(
            porcentaje
        )
        pct_box = d.textbbox(
            (0, 0),
            pct_txt,
            font=f_pct,
        )
        pct_w = pct_box[2] - pct_box[0]

        # Reservar espacio al porcentaje.
        available_name_w = (
            W
            - margin
            - 30
            - pct_w
            - name_x
        )

        fuente_nombre = f_name

        name_box = d.textbbox(
            (0, 0),
            nombre,
            font=fuente_nombre,
        )

        if (
            name_box[2] - name_box[0]
            > available_name_w
        ):
            fuente_nombre = f_name_long
            name_box = d.textbbox(
                (0, 0),
                nombre,
                font=fuente_nombre,
            )

        if (
            name_box[2] - name_box[0]
            > available_name_w
        ):
            fuente_nombre = f_name_xlong

        d.text(
            (
                name_x,
                y1 + 23,
            ),
            nombre,
            font=fuente_nombre,
            fill=dark,
        )

        # Monto debajo del nombre.
        d.text(
            (
                name_x,
                y1 + 87,
            ),
            formato_usd(
                recuperacion
            ),
            font=f_amount,
            fill=green_dark,
        )

        # % grande, alineado a la derecha.
        d.text(
            (
                W
                - margin
                - 28
                - pct_w,
                y1 + 45,
            ),
            pct_txt,
            font=f_pct,
            fill=dark,
        )

        # Barra de progreso, gruesa y limpia.
        bar_x1 = name_x
        bar_x2 = W - margin - 28
        bar_y = y2 - 23

        d.rounded_rectangle(
            (
                bar_x1,
                bar_y,
                bar_x2,
                bar_y + 14,
            ),
            radius=7,
            fill=bar_bg,
        )

        fill_x = bar_x1 + int(
            (
                bar_x2 - bar_x1
            )
            * min(
                max(
                    porcentaje / 100,
                    0,
                ),
                1,
            )
        )

        if fill_x > bar_x1:
            d.rounded_rectangle(
                (
                    bar_x1,
                    bar_y,
                    fill_x,
                    bar_y + 14,
                ),
                radius=7,
                fill=green,
            )

    # -----------------------------------------------------
    # FOOTER
    # -----------------------------------------------------
    footer_y1 = 1490
    footer_y2 = H - margin

    d.rounded_rectangle(
        (
            margin,
            footer_y1,
            W - margin,
            footer_y2,
        ),
        radius=22,
        fill=navy,
    )

    footer_txt = "🏆 Ranking actualizado de recuperación"

    footer_box = d.textbbox(
        (0, 0),
        footer_txt,
        font=f_footer,
    )

    d.text(
        (
            (W - (footer_box[2] - footer_box[0])) / 2,
            footer_y1 + 16,
        ),
        footer_txt,
        font=f_footer,
        fill=white,
    )

    buffer = io.BytesIO()

    img.save(
        buffer,
        format="PNG",
        optimize=True,
    )

    buffer.seek(0)

    return buffer


def enviar_foto_telegram(chat_id, imagen_bytes, caption=""):
    """
    Envía una imagen PNG directamente a Telegram mediante sendPhoto.
    """
    token = obtener_telegram_bot_token()
    chat_id = str(chat_id or "").strip()

    if not token:
        return False, "Falta TELEGRAM_BOT_TOKEN en Streamlit Secrets."
    if not chat_id:
        return False, "Falta el Chat ID de Telegram."

    import uuid

    boundary = "----GENControl" + uuid.uuid4().hex
    partes = []

    def campo(nombre, valor):
        partes.append(f"--{boundary}\r\n".encode())
        partes.append(
            f'Content-Disposition: form-data; name="{nombre}"\r\n\r\n'.encode()
        )
        partes.append(str(valor).encode("utf-8"))
        partes.append(b"\r\n")

    campo("chat_id", chat_id)
    if caption:
        campo("caption", caption)

    partes.append(f"--{boundary}\r\n".encode())
    partes.append(
        b'Content-Disposition: form-data; name="photo"; filename="avance_recuperacion.png"\r\n'
    )
    partes.append(b"Content-Type: image/png\r\n\r\n")
    partes.append(imagen_bytes.getvalue())
    partes.append(b"\r\n")
    partes.append(f"--{boundary}--\r\n".encode())

    body = b"".join(partes)
    url = f"https://api.telegram.org/bot{token}/sendPhoto"

    try:
        req = request.Request(
            url,
            data=body,
            method="POST",
            headers={
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "Content-Length": str(len(body)),
            },
        )
        with request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        if data.get("ok") is True:
            return True, "Imagen enviada."
        return False, str(data.get("description", "Telegram rechazó la imagen."))
    except Exception as e:
        return False, str(e)

def saludo_segun_hora():
    hora = ahora_bolivia().hour

    if 5 <= hora < 12:
        return "Buenos días", "☀️"
    elif 12 <= hora < 19:
        return "Buenas tardes", "🌤️"
    else:
        return "Buenas noches", "🌙"


def generar_mensaje_grupo_recuperacion(
    tabla_general,
    meta_individual,
):
    """
    Texto breve que acompaña la imagen del ranking en Telegram.
    El saludo cambia automáticamente según la hora de Bolivia.
    """
    tabla = tabla_general.copy()

    total_rec = float(
        tabla["Recuperación acumulada"].sum()
    )

    meta_equipo = (
        float(meta_individual)
        * len(tabla)
    )

    pct_equipo = (
        total_rec / meta_equipo * 100
        if meta_equipo
        else 0
    )

    falta_equipo = max(
        meta_equipo - total_rec,
        0,
    )

    saludo, emoji_saludo = saludo_segun_hora()

    return (
        f"{emoji_saludo} {saludo}, equipo. 💪\n\n"
        f"📊 AVANCE DE RECUPERACIÓN | "
        f"{fecha_local_actual().strftime('%d/%m/%Y')}\n\n"
        f"💰 Recuperado: {formato_usd(total_rec)}\n"
        f"🎯 Meta equipo: {formato_usd(meta_equipo)}\n"
        f"📈 Cumplimiento: {formato_porcentaje(pct_equipo)}\n"
        f"📉 Brecha pendiente: {formato_usd(falta_equipo)}\n\n"
        f"Adjunto el ranking actualizado de recuperación por operador.\n\n"
        f"Sigamos con enfoque y constancia para alcanzar la meta del mes. 🚀"
    )



def obtener_usuarios_telegram_bot():
    """
    Lee getUpdates del bot y devuelve los chats privados que le escribieron.
    No envía mensajes.
    """
    token = obtener_telegram_bot_token()

    if not token:
        return [], "Falta TELEGRAM_BOT_TOKEN en Secrets."

    try:
        url = f"https://api.telegram.org/bot{token}/getUpdates"

        with request.urlopen(url, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        if data.get("ok") is not True:
            return [], str(
                data.get(
                    "description",
                    "Telegram no devolvió los usuarios.",
                )
            )

        encontrados = {}

        for update in data.get("result", []):
            mensaje = (
                update.get("message")
                or update.get("edited_message")
                or update.get("channel_post")
                or {}
            )

            chat = mensaje.get("chat", {}) or {}
            remitente = mensaje.get("from", {}) or {}

            chat_id = chat.get("id")

            # Solo chats privados para operadores.
            if not chat_id or chat.get("type") != "private":
                continue

            nombre = " ".join(
                [
                    str(remitente.get("first_name") or "").strip(),
                    str(remitente.get("last_name") or "").strip(),
                ]
            ).strip()

            username = str(
                remitente.get("username") or ""
            ).strip()

            encontrados[str(chat_id)] = {
                "chat_id": str(chat_id),
                "nombre": nombre or "Sin nombre",
                "username": (
                    f"@{username}"
                    if username
                    else "Sin username"
                ),
            }

        usuarios = list(encontrados.values())

        usuarios.sort(
            key=lambda x: x["nombre"].lower()
        )

        if not usuarios:
            return [], (
                "Todavía no hay chats privados disponibles. "
                "Cada operador debe abrir el bot y enviar /start."
            )

        return usuarios, ""

    except Exception as e:
        return [], str(e)


def probar_conexion_telegram():
    token = obtener_telegram_bot_token()

    if not token:
        return False, "Falta TELEGRAM_BOT_TOKEN en Secrets."

    try:
        url = f"https://api.telegram.org/bot{token}/getMe"

        with request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        if data.get("ok") is True:
            username = data.get("result", {}).get("username", "bot")
            return True, f"Conectado con @{username}"

        return False, str(
            data.get("description", "No se pudo validar el bot.")
        )
    except Exception as e:
        return False, str(e)



# =========================================================
# HORA DE CORTE DEL ARCHIVO CALLCENTER
# =========================================================

def obtener_corte_callcenter(callcenter_df):
    """
    Hora de corte operativa del reporte.

    Prioridad:
    1) momento en que GEN CallCenter fue cargado a la app;
    2) última fecha/hora contenida en el archivo, como respaldo.

    Esto evita que el esperado siga avanzando después de cargar
    un archivo que ya quedó congelado.
    """
    cargado_en = st.session_state.get(
        "callcenter_cargado_en"
    )

    if cargado_en is not None:
        return (
            datetime_bolivia(cargado_en)
            or cargado_en
        )

    if callcenter_df is None or callcenter_df.empty:
        return None

    df = callcenter_df.copy()
    col_fecha = buscar_columna(df, ["fecha"])

    if col_fecha is None:
        return None

    serie = pd.to_datetime(
        df[col_fecha],
        dayfirst=True,
        errors="coerce",
    ).dropna()

    if serie.empty:
        return None

    return serie.max()


# =========================================================
# AVANCE DE HOY / A LA HORA
# =========================================================

def calcular_avance_hora_operador(
    usuario,
    callcenter_df=None,
    ahora=None,
):
    meta_g_dia = int(
        st.session_state.get(
            "meta_diaria_gestiones_cfg",
            META_DIARIA_GESTIONES,
        )
    )
    meta_c_dia = int(
        st.session_state.meta_diaria_compromisos_cfg
    )

    corte_operativo = obtener_corte_callcenter(
        callcenter_df
    )

    base = {
        "disponible": False,
        "gestiones_hoy": 0,
        "compromisos_hoy": None,
        "compromisos_disponibles": False,
        "esperado_gestiones": 0,
        "esperado_compromisos": 0,
        "delta_gestiones": 0,
        "delta_compromisos": None,
        "faltan_gestiones": meta_g_dia,
        "faltan_compromisos": None,
        "hora_corte": "--:--",
        "fecha_corte": None,
        "progreso_jornada_pct": 0.0,
        "estado_jornada": "Sin corte",
        "horario": None,
    }

    if (
        corte_operativo is None
        or callcenter_df is None
        or callcenter_df.empty
    ):
        return base

    if hasattr(
        corte_operativo,
        "to_pydatetime",
    ):
        corte_operativo = (
            corte_operativo.to_pydatetime()
        )

    # Asegurar tz Bolivia.
    if corte_operativo.tzinfo is None:
        corte_operativo = (
            corte_operativo.replace(
                tzinfo=ZoneInfo(
                    "America/La_Paz"
                )
            )
        )

    df = callcenter_df.copy()

    col_fecha = buscar_columna(
        df,
        ["fecha"],
    )
    col_usuario = buscar_columna(
        df,
        ["usuario"],
    )
    col_compromiso = buscar_columna(
        df,
        ["compromiso"],
    )

    if col_fecha is None or col_usuario is None:
        return base

    df["_fecha_hora"] = pd.to_datetime(
        df[col_fecha],
        dayfirst=True,
        errors="coerce",
    )

    df = df.dropna(
        subset=["_fecha_hora"]
    )

    fechas_validas = (
        df["_fecha_hora"]
        .dt.date
        .dropna()
    )

    if fechas_validas.empty:
        return base

    fecha_corte = max(
        fechas_validas
    )

    datos_op = OPERADORES.get(
        usuario,
        {},
    )

    aliases = {
        normalizar_texto(usuario),
        normalizar_texto(
            datos_op.get("nombre", "")
        ),
        normalizar_texto(
            datos_op.get(
                "nombre_mensaje",
                "",
            )
        ),
        normalizar_texto(
            datos_op.get("correo", "")
        ),
    }

    correo_op = str(
        datos_op.get("correo", "")
    ).strip()

    if "@" in correo_op:
        aliases.add(
            normalizar_texto(
                correo_op.split("@")[0]
            )
        )

    aliases = {
        x
        for x in aliases
        if x
    }

    df["_usuario_norm"] = (
        df[col_usuario]
        .astype(str)
        .apply(normalizar_texto)
    )

    mascara_usuario = (
        df["_usuario_norm"].isin(
            aliases
        )
    )

    if not mascara_usuario.any():
        aliases_largos = [
            x
            for x in aliases
            if len(x) >= 4
        ]

        mascara_usuario = (
            df["_usuario_norm"]
            .apply(
                lambda valor: any(
                    alias in valor
                    or valor in alias
                    for alias in aliases_largos
                )
            )
        )

    df_hoy = df[
        mascara_usuario
        & (
            df["_fecha_hora"].dt.date
            == fecha_corte
        )
    ].copy()

    gestiones_hoy = int(
        len(df_hoy)
    )

    compromisos_disponibles = (
        col_compromiso is not None
    )

    compromisos_hoy = None

    if compromisos_disponibles:
        compromiso_txt = (
            df_hoy[col_compromiso]
            .astype(str)
            .str.strip()
        )

        compromisos_hoy = int(
            (
                df_hoy[
                    col_compromiso
                ].notna()
                & (
                    compromiso_txt
                    != ""
                )
                & (
                    compromiso_txt
                    .str.lower()
                    != "nan"
                )
            ).sum()
        )

    # La fecha viene del archivo y la hora del momento de carga/corte.
    corte_para_ritmo = (
        corte_operativo.replace(
            year=fecha_corte.year,
            month=fecha_corte.month,
            day=fecha_corte.day,
        )
    )

    jornada = (
        calcular_progreso_jornada_operador(
            usuario,
            corte_para_ritmo,
        )
    )

    proporcion = float(
        jornada.get(
            "proporcion",
            0,
        )
    )

    esperado_g = int(
        math.ceil(
            meta_g_dia
            * proporcion
        )
    )

    esperado_c = int(
        math.ceil(
            meta_c_dia
            * proporcion
        )
    )

    delta_c = (
        compromisos_hoy
        - esperado_c
        if compromisos_disponibles
        else None
    )

    faltan_c = (
        max(
            meta_c_dia
            - compromisos_hoy,
            0,
        )
        if compromisos_disponibles
        else None
    )

    return {
        "disponible": True,
        "gestiones_hoy": gestiones_hoy,
        "compromisos_hoy": compromisos_hoy,
        "compromisos_disponibles": compromisos_disponibles,
        "esperado_gestiones": esperado_g,
        "esperado_compromisos": esperado_c,
        "delta_gestiones": (
            gestiones_hoy
            - esperado_g
        ),
        "delta_compromisos": delta_c,
        "faltan_gestiones": max(
            meta_g_dia
            - gestiones_hoy,
            0,
        ),
        "faltan_compromisos": faltan_c,
        "hora_corte": (
            corte_para_ritmo
            .strftime("%H:%M")
        ),
        "fecha_corte": fecha_corte,
        "progreso_jornada_pct": (
            proporcion * 100
        ),
        "estado_jornada": jornada.get(
            "estado_jornada",
            "",
        ),
        "horario": jornada,
    }


def texto_estado_ritmo(delta, indicador):
    if delta > 0:
        return (
            f"🟢 Vas {formato_entero(delta)} {indicador} "
            f"por encima del ritmo esperado"
        )
    if delta == 0:
        return "🟢 Vas exactamente en el ritmo esperado"
    return (
        f"🔴 Vas {formato_entero(abs(delta))} {indicador} "
        f"por debajo del ritmo esperado"
    )



# =========================================================
# CONTROL DE ENVÍOS DIARIOS
# =========================================================

def _clave_envio_local(usuario, fecha=None, tipo="seguimiento"):
    fecha = fecha or fecha_local_actual()
    return f"{fecha.isoformat()}|{usuario}|{tipo}"


def obtener_envio_diario(usuario, fecha=None, tipo="seguimiento"):
    """
    V96: Supabase es la fuente principal del último envío.
    Session State queda únicamente como respaldo si Supabase no responde.
    """
    fecha = fecha or fecha_local_actual()
    clave = _clave_envio_local(
        usuario,
        fecha,
        tipo,
    )

    sb = get_supabase()

    if sb is not None:
        try:
            resp = (
                sb.table("envios_mensajes")
                .select("*")
                .eq("fecha", fecha.isoformat())
                .eq("usuario", str(usuario))
                .eq("tipo", str(tipo))
                .eq("estado", "enviado")
                .order(
                    "fecha_hora",
                    desc=True,
                )
                .limit(1)
                .execute()
            )

            if resp.data:
                registro = resp.data[0]
                st.session_state.envios_diarios_cache[
                    clave
                ] = registro
                return registro
        except Exception:
            pass

    cache = st.session_state.get(
        "envios_diarios_cache",
        {},
    )
    return cache.get(clave)


def registrar_envio_diario(
    usuario,
    operador,
    canal="telegram",
    tipo="seguimiento",
    detalle="",
):
    """
    Registra un envío exitoso. El cambio de fecha reinicia
    automáticamente el control porque la clave incluye la fecha.
    """
    ahora_local = ahora_bolivia()
    ahora_utc = datetime.now(
        timezone.utc
    )

    registro = {
        "fecha": ahora_local.date().isoformat(),
        "fecha_hora": ahora_utc.isoformat(),
        "usuario": str(usuario),
        "operador": str(operador),
        "canal": str(canal),
        "tipo": str(tipo),
        "estado": "enviado",
        "detalle": str(detalle or ""),
    }

    clave = _clave_envio_local(
        usuario,
        ahora_local.date(),
        tipo,
    )

    st.session_state.envios_diarios_cache[
        clave
    ] = registro

    sb = get_supabase()

    if sb is not None:
        try:
            (
                sb.table("envios_mensajes")
                .insert(registro)
                .execute()
            )
        except Exception:
            # La app sigue funcionando con Session State.
            pass

    return registro


def envio_ya_realizado_hoy(
    usuario,
    tipo="seguimiento",
):
    return obtener_envio_diario(
        usuario,
        fecha_local_actual(),
        tipo,
    ) is not None


def hora_envio_hoy(
    usuario,
    tipo="seguimiento",
):
    registro = obtener_envio_diario(
        usuario,
        fecha_local_actual(),
        tipo,
    )

    if not registro:
        return ""

    fecha_hora = str(
        registro.get(
            "fecha_hora",
            "",
        )
    )

    try:
        dt = datetime_bolivia(
            fecha_hora
        )
        return (
            dt.strftime("%H:%M")
            if dt is not None
            else ""
        )
    except Exception:
        return ""




CORTES_SEGUIMIENTO = ["10:30", "13:30", "15:30", "17:30"]
MINUTOS_RECOMENDADOS_ENTRE_SEGUIMIENTOS = 60


def ultimo_envio_datetime(
    usuario,
    tipo="seguimiento",
):
    registro = obtener_envio_diario(
        usuario,
        fecha_local_actual(),
        tipo,
    )

    if not registro:
        return None

    valor = str(
        registro.get(
            "fecha_hora",
            "",
        )
    ).strip()

    if not valor:
        return None

    try:
        return datetime_bolivia(
            valor
        )
    except Exception:
        return None


def minutos_desde_ultimo_envio(
    usuario,
    momento=None,
    tipo="seguimiento",
):
    momento = momento or ahora_bolivia()

    ultimo = ultimo_envio_datetime(
        usuario,
        tipo,
    )

    if ultimo is None:
        return None

    minutos = int(
        (momento - ultimo).total_seconds()
        // 60
    )

    return max(
        minutos,
        0,
    )


def seguimiento_muy_reciente(
    usuario,
    momento=None,
    minimo_minutos=MINUTOS_RECOMENDADOS_ENTRE_SEGUIMIENTOS,
):
    minutos = minutos_desde_ultimo_envio(
        usuario,
        momento,
    )

    return (
        minutos is not None
        and minutos < minimo_minutos
    )


def informacion_corte_recomendado(
    momento=None,
):
    """
    Devuelve el corte recomendado más útil para la hora actual.
    Los cortes son orientativos; nunca bloquean un envío manual.
    """
    momento = momento or ahora_bolivia()

    cortes_dt = []

    for hora_txt in CORTES_SEGUIMIENTO:
        cortes_dt.append(
            (
                hora_txt,
                _hora_en_fecha(
                    momento,
                    hora_txt,
                ),
            )
        )

    for hora_txt, corte_dt in cortes_dt:
        if momento <= corte_dt:
            minutos = int(
                (corte_dt - momento).total_seconds()
                // 60
            )
            return {
                "hora": hora_txt,
                "estado": "proximo",
                "minutos": max(minutos, 0),
                "texto": (
                    f"Próximo corte recomendado: {hora_txt}"
                    if minutos > 0
                    else f"Corte recomendado ahora: {hora_txt}"
                ),
            }

    return {
        "hora": CORTES_SEGUIMIENTO[-1],
        "estado": "finalizado",
        "minutos": None,
        "texto": "Los cortes recomendados del día ya finalizaron.",
    }


def resumen_frecuencia_seguimiento(
    usuarios,
    momento=None,
):
    momento = momento or ahora_bolivia()

    recientes = []
    disponibles = []

    for usuario in usuarios:
        minutos = minutos_desde_ultimo_envio(
            usuario,
            momento,
        )

        if minutos is None:
            disponibles.append(
                usuario
            )
        elif minutos < MINUTOS_RECOMENDADOS_ENTRE_SEGUIMIENTOS:
            recientes.append(
                (
                    usuario,
                    minutos,
                )
            )
        else:
            disponibles.append(
                usuario
            )

    return recientes, disponibles


def puede_enviar_seguimiento(usuario, momento=None):
    """
    Permite envío normal dentro de turno.
    Si coordinación activa el modo excepcional, también permite
    enviar fuera de turno.
    """
    return (
        operador_en_turno(
            usuario,
            momento,
        )
        or bool(
            st.session_state.get(
                "permitir_envio_fuera_turno",
                False,
            )
        )
    )


def operador_en_turno(
    usuario,
    momento=None,
):
    """
    True únicamente si el operador está dentro de su jornada actual:
    entrada <= hora actual < salida.

    El break sigue siendo parte del turno, aunque el cálculo productivo
    permanezca congelado durante esos 30 minutos.
    """
    momento = momento or ahora_bolivia()

    horario = obtener_horario_operador(
        usuario,
        momento.date(),
    )

    if not horario:
        return False

    entrada = _hora_en_fecha(
        momento,
        horario["entrada"],
    )
    salida = _hora_en_fecha(
        momento,
        horario["salida"],
    )

    return entrada <= momento < salida


def texto_estado_turno(
    usuario,
    momento=None,
):
    momento = momento or ahora_bolivia()

    horario = obtener_horario_operador(
        usuario,
        momento.date(),
    )

    if not horario:
        return "Horario no configurado"

    entrada = _hora_en_fecha(
        momento,
        horario["entrada"],
    )
    salida = _hora_en_fecha(
        momento,
        horario["salida"],
    )

    if momento < entrada:
        return f"Inicia a las {horario['entrada']}"

    if momento >= salida:
        return f"Fuera de turno · salió {horario['salida']}"

    return f"En turno · hasta {horario['salida']}"


def operador_fuera_de_horario(
    usuario,
    momento=None,
):
    """
    Devuelve True si el momento actual ya es posterior
    a la hora de salida configurada del operador.
    """
    momento = momento or ahora_bolivia()

    horario = obtener_horario_operador(
        usuario,
        momento.date(),
    )

    if not horario:
        return False

    salida = _hora_en_fecha(
        momento,
        horario["salida"],
    )

    return momento >= salida



def _clave_aviso_grupal(fecha=None):
    fecha = fecha or fecha_local_actual()
    return f"aviso_grupal_seguimiento|{fecha.isoformat()}"


def contar_avisos_grupales_hoy():
    """
    Cuenta cuántos avisos grupales de seguimiento se enviaron hoy.
    Usa Supabase si está disponible y Session State como respaldo.
    """
    fecha = fecha_local_actual()
    clave = _clave_aviso_grupal(fecha)

    cache = st.session_state.setdefault(
        "avisos_grupales_cache",
        {},
    )

    # Supabase es la fuente preferida porque conserva el conteo
    # aunque Streamlit reinicie la sesión.
    sb = get_supabase()
    if sb is not None:
        try:
            resp = (
                sb.table("envios_mensajes")
                .select("fecha_hora")
                .eq("fecha", fecha.isoformat())
                .eq("tipo", "aviso_grupal_seguimiento")
                .eq("estado", "enviado")
                .execute()
            )
            if resp.data is not None:
                total = len(resp.data)
                cache[clave] = total
                return total
        except Exception:
            pass

    return int(cache.get(clave, 0) or 0)


def registrar_aviso_grupal_enviado(detalle=""):
    ahora_local = ahora_bolivia()
    ahora_utc = datetime.now(
        timezone.utc
    )
    clave = _clave_aviso_grupal(
        ahora_local.date()
    )

    cache = st.session_state.setdefault(
        "avisos_grupales_cache",
        {},
    )
    cache[clave] = int(
        cache.get(clave, 0) or 0
    ) + 1

    registro = {
        "fecha": ahora_local.date().isoformat(),
        "fecha_hora": ahora_utc.isoformat(),
        "usuario": "grupo",
        "operador": "Grupo Inmobiliaria",
        "canal": "telegram",
        "tipo": "aviso_grupal_seguimiento",
        "estado": "enviado",
        "detalle": str(detalle or ""),
    }

    sb = get_supabase()
    if sb is not None:
        try:
            (
                sb.table("envios_mensajes")
                .insert(registro)
                .execute()
            )
        except Exception:
            pass

    return registro


def generar_aviso_grupo_envios(
    operadores_enviados,
    operadores_fuera_turno=None,
    numero_seguimiento=None,
):
    """
    Genera un aviso grupal distinto según el momento de la jornada y
    la cantidad de seguimientos grupales realizados hoy.

    No expone nombres ni resultados individuales.
    """
    operadores_enviados = list(
        operadores_enviados or []
    )

    if not operadores_enviados:
        return ""

    ahora = ahora_bolivia()

    if numero_seguimiento is None:
        numero_seguimiento = (
            contar_avisos_grupales_hoy()
            + 1
        )

    hora = ahora.strftime("%H:%M")

    # V89 · El texto no depende de decir "primer/segundo seguimiento".
    # Así sigue siendo correcto aunque Streamlit reinicie la sesión o el
    # historial anterior no se encuentre en Supabase.
    if ahora.hour < 12:
        cuerpo = (
            "Se realizó un seguimiento individual de avance a los operadores "
            "que se encuentran actualmente de turno.\n\n"
            "Mantengamos el ritmo para continuar avanzando con las metas del día. 💪"
        )

    elif ahora.hour < 17:
        cuerpo = (
            "Se realizó una nueva actualización y seguimiento individual "
            "de los avances a los operadores que se encuentran de turno.\n\n"
            "Continuemos enfocados en las metas del día y en recuperar "
            "cualquier brecha pendiente. 💪"
        )

    else:
        cuerpo = (
            "Se realizó un nuevo corte y seguimiento individual a los operadores "
            "que continúan de turno.\n\n"
            "Aprovechemos las horas restantes para cerrar la jornada "
            "con el mejor cumplimiento posible. 💪"
        )

    return (
        f"📊 Seguimiento de avance · {hora}\n\n"
        + cuerpo
    )


def enviar_aviso_grupo_post_envio(
    operadores_enviados,
    operadores_fuera_turno=None,
):
    chat_grupo = obtener_telegram_group_chat_id()

    if not chat_grupo:
        return False, "No está configurado TELEGRAM_GROUP_CHAT_ID."

    numero_seguimiento = (
        contar_avisos_grupales_hoy()
        + 1
    )

    mensaje = generar_aviso_grupo_envios(
        operadores_enviados,
        operadores_fuera_turno,
        numero_seguimiento=numero_seguimiento,
    )

    if not mensaje:
        return False, "No hubo envíos individuales para informar."

    ok, detalle = enviar_mensaje_telegram(
        chat_grupo,
        mensaje,
    )

    if ok:
        registrar_aviso_grupal_enviado(
            detalle=(
                f"Seguimiento grupal #{numero_seguimiento}. "
                f"Operadores con envío individual: "
                f"{len(list(operadores_enviados or []))}."
            )
        )

    return ok, detalle

def enviar_copia_coordinador(operador, mensaje_original, detalle_envio):
    chat_coord = obtener_telegram_coordinador_chat_id()

    if not chat_coord:
        return False, "Falta TELEGRAM_COORDINADOR_CHAT_ID."

    copia = (
        f"✅ MENSAJE ENVIADO\n\n"
        f"👤 Operador: {operador}\n"
        f"📬 Estado: {detalle_envio}\n\n"
        f"--- Copia del mensaje ---\n"
        f"{mensaje_original}"
    )

    return enviar_mensaje_telegram(chat_coord, copia)


# =========================================================
# TELÉFONOS
# =========================================================

def normalizar_telefono_whatsapp(valor):
    numero = re.sub(
        r"\D",
        "",
        str(valor or ""),
    )

    if not numero:
        return ""

    # Bolivia: si se ingresan 8 dígitos, agregar automáticamente 591.
    if len(numero) == 8:
        numero = "591" + numero

    return numero


# =========================================================
# ESTILO
# =========================================================

st.markdown(
    """
    <style>

        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 3rem;
        }

        [data-testid="stSidebar"] {
            background:
                linear-gradient(180deg, #10233f 0%, #0d1d35 100%);
            border-right: 1px solid rgba(255,255,255,.06);
        }

        [data-testid="stSidebar"] > div:first-child {
            padding-top: 1rem;
        }

        [data-testid="stSidebar"] * {
            color: white;
        }

        /* Marca / encabezado */
        .sidebar-brand {
            display:flex;
            align-items:center;
            gap:12px;
            padding:10px 8px 16px 8px;
        }

        .sidebar-logo {
            width:42px;
            height:42px;
            border-radius:12px;
            display:flex;
            align-items:center;
            justify-content:center;
            background:linear-gradient(135deg,#2f80ed 0%,#37c9a5 100%);
            font-size:20px;
            font-weight:800;
            box-shadow:0 8px 20px rgba(0,0,0,.18);
        }

        .sidebar-brand-title {
            font-size:17px;
            font-weight:800;
            line-height:1.15;
        }

        .sidebar-brand-sub {
            font-size:11px;
            color:#a8b6ca !important;
            margin-top:3px;
        }

        .sidebar-section-label {
            color:#7183a0 !important;
            font-size:10px;
            font-weight:800;
            letter-spacing:.10em;
            text-transform:uppercase;
            margin:8px 0 6px 8px;
        }

        /* Navegación */
        [data-testid="stSidebar"] div[role="radiogroup"] {
            gap:4px;
        }

        [data-testid="stSidebar"] div[role="radiogroup"] label {
            border-radius:11px;
            padding:8px 10px;
            transition:background .15s ease, transform .15s ease;
            border:1px solid transparent;
        }

        [data-testid="stSidebar"] div[role="radiogroup"] label:hover {
            background:rgba(255,255,255,.06);
        }

        [data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
            background:linear-gradient(90deg, rgba(47,128,237,.32), rgba(55,201,165,.14));
            border:1px solid rgba(93,163,255,.22);
            box-shadow:inset 3px 0 0 #53d4b3;
        }

        [data-testid="stSidebar"] div[role="radiogroup"] label p {
            font-size:13px;
            font-weight:650;
        }

        /* Tarjeta de actualización */
        .sidebar-status-card {
            margin-top:10px;
            padding:14px;
            border-radius:14px;
            background:linear-gradient(135deg, rgba(26,106,112,.38), rgba(14,65,88,.52));
            border:1px solid rgba(85,214,173,.14);
        }

        .sidebar-status-top {
            display:flex;
            align-items:center;
            gap:7px;
            font-size:12px;
            font-weight:700;
        }

        .sidebar-status-dot {
            width:8px;
            height:8px;
            border-radius:50%;
            background:#45d19a;
            box-shadow:0 0 0 4px rgba(69,209,154,.10);
        }

        .sidebar-status-date {
            font-size:13px;
            font-weight:800;
            margin-top:10px;
        }

        .sidebar-status-time {
            color:#8fa1ba !important;
            font-size:10px;
            margin-top:2px;
        }

        /* Perfil */
        .sidebar-profile {
            display:flex;
            align-items:center;
            gap:10px;
            padding:12px 8px;
            margin-top:6px;
        }

        .sidebar-avatar {
            width:38px;
            height:38px;
            border-radius:50%;
            display:flex;
            align-items:center;
            justify-content:center;
            background:linear-gradient(135deg,#5a67d8,#805ad5);
            font-weight:800;
            font-size:13px;
        }

        .sidebar-profile-name {
            font-size:13px;
            font-weight:800;
        }

        .sidebar-profile-role {
            color:#8fa1ba !important;
            font-size:10px;
            margin-top:2px;
        }

        .sidebar-version {
            margin:12px 0 4px 0;
            padding:9px 11px;
            border-radius:10px;
            background:rgba(255,255,255,.04);
            border:1px solid rgba(255,255,255,.06);
            display:flex;
            justify-content:space-between;
            align-items:center;
            font-size:10px;
            color:#8fa1ba !important;
        }

        .sidebar-version-badge {
            background:rgba(69,209,154,.14);
            color:#6ee7b7 !important;
            border-radius:999px;
            padding:3px 7px;
            font-weight:700;
        }

        [data-testid="stSidebar"] hr {
            border-color:rgba(255,255,255,.08);
            margin:.75rem 0;
        }

        .gen-header {
            padding: 8px 0 18px 0;
        }

        .gen-title {
            font-size: 30px;
            font-weight: 800;
            margin: 0;
        }

        .gen-subtitle {
            color: #667085;
            font-size: 15px;
            margin-top: 2px;
        }

        .metric-card {
            background: white;
            border: 1px solid #e6eaf0;
            border-radius: 14px;
            padding: 20px;
            min-height: 145px;
            box-shadow: 0 2px 8px rgba(16,24,40,.05);
        }

        .metric-label {
            color: #667085;
            font-size: 13px;
            margin-bottom: 8px;
        }

        .metric-value {
            color: #101828;
            font-size: 28px;
            font-weight: 800;
        }

        .metric-detail {
            color: #667085;
            font-size: 12px;
            margin-top: 8px;
        }

        .status-box {
            background: #f8fafc;
            border: 1px solid #e6eaf0;
            border-radius: 14px;
            padding: 20px;
        }

        .hero-card {
            background: linear-gradient(135deg, #172a4a 0%, #24456f 100%);
            color: white;
            border-radius: 18px;
            padding: 22px 24px;
            margin-bottom: 18px;
            box-shadow: 0 6px 18px rgba(16,24,40,.10);
        }

        .hero-title {
            font-size: 24px;
            font-weight: 800;
            margin-bottom: 4px;
        }

        .hero-subtitle {
            font-size: 13px;
            opacity: .86;
        }

        .kpi-card {
            background: white;
            border: 1px solid #e8edf3;
            border-radius: 16px;
            padding: 18px;
            min-height: 132px;
            box-shadow: 0 3px 10px rgba(16,24,40,.05);
        }

        .kpi-title {
            color: #667085;
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: .04em;
        }

        .kpi-value {
            color: #101828;
            font-size: 28px;
            font-weight: 800;
            margin-top: 6px;
        }

        .kpi-foot {
            color: #667085;
            font-size: 12px;
            margin-top: 8px;
        }

        .section-title {
            font-size: 20px;
            font-weight: 800;
            margin-top: 12px;
            margin-bottom: 8px;
        }

        .soft-card {
            background: #ffffff;
            border: 1px solid #e8edf3;
            border-radius: 14px;
            padding: 16px;
        }


        /* ===== MENSAJES DIARIOS V32 ===== */

        .daily-panel {
            background: linear-gradient(135deg, #102846 0%, #214e7d 100%);
            color: white;
            border-radius: 18px;
            padding: 20px 24px;
            margin-bottom: 16px;
            box-shadow: 0 8px 22px rgba(16,24,40,.10);
        }

        .daily-panel-title {
            font-size: 23px;
            font-weight: 800;
            margin-bottom: 4px;
        }

        .daily-panel-sub {
            font-size: 13px;
            opacity: .88;
        }

        .section-chip {
            display: inline-block;
            background: #eef4ff;
            color: #24456f;
            border-radius: 999px;
            padding: 5px 10px;
            font-size: 12px;
            font-weight: 700;
            margin-bottom: 8px;
        }

        div[data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #e7ebf0;
            padding: 12px 14px;
            border-radius: 12px;
        }

        div[data-testid="stExpander"] {
            border-radius: 12px;
        }


        /* ===== TARJETAS DE OPERADORES V53 ===== */

        .operator-card-head {
            display:flex;
            justify-content:space-between;
            align-items:flex-start;
            gap:12px;
            margin-bottom:10px;
        }

        .operator-card-name {
            font-size:21px;
            font-weight:800;
            color:#101828;
            line-height:1.2;
        }

        .operator-status-pill {
            display:inline-flex;
            align-items:center;
            border-radius:999px;
            padding:5px 10px;
            font-size:12px;
            font-weight:700;
            white-space:nowrap;
        }

        .status-red {
            background:#fff1f3;
            color:#c01048;
        }

        .status-orange {
            background:#fff6ed;
            color:#b54708;
        }

        .status-yellow {
            background:#fffaeb;
            color:#b54708;
        }

        .status-green {
            background:#ecfdf3;
            color:#067647;
        }

        .operator-meta-line {
            font-size:12px;
            color:#667085;
            margin-top:-2px;
            margin-bottom:10px;
        }

        .operator-progress-label {
            display:flex;
            justify-content:space-between;
            align-items:center;
            font-size:11px;
            color:#667085;
            margin-top:7px;
            margin-bottom:2px;
        }

        .operator-divider {
            height:1px;
            background:#eef1f5;
            margin:10px 0 8px 0;
        }


        .messages-summary {
            background:#ffffff;
            border:1px solid #e6eaf0;
            border-radius:16px;
            padding:14px 18px;
            margin:8px 0 14px 0;
        }

        .operator-daily-box {
            background:#f4f8ff;
            border:1px solid #cfe0ff;
            border-radius:10px;
            padding:9px 12px;
            margin:8px 0 10px 0;
            color:#24456f;
            font-size:12px;
            font-weight:700;
        }

        .operator-small-line {
            color:#667085;
            font-size:11px;
            margin-top:4px;
        }

        .operator-channel {
            color:#667085;
            font-size:11px;
            margin-top:3px;
        }


        /* ===== MENSAJES INDIVIDUALES V59 ===== */

        .messages-title-wrap {
            display:flex;
            align-items:center;
            gap:12px;
            margin-bottom:4px;
        }

        .messages-title-icon {
            width:42px;
            height:42px;
            border-radius:13px;
            display:flex;
            align-items:center;
            justify-content:center;
            background:#f1edff;
            color:#6c4ff8;
            font-size:22px;
            font-weight:800;
        }

        .messages-title-text {
            font-size:28px;
            font-weight:800;
            color:#101828;
            line-height:1.1;
        }

        .messages-subtitle-text {
            color:#667085;
            font-size:13px;
            margin-bottom:16px;
        }

        .summary-tile {
            background:#ffffff;
            border:1px solid #e6eaf0;
            border-radius:14px;
            padding:14px 15px;
            min-height:94px;
            box-shadow:0 2px 8px rgba(16,24,40,.04);
        }

        .summary-tile-label {
            color:#667085;
            font-size:11px;
            font-weight:700;
            text-transform:uppercase;
            letter-spacing:.04em;
        }

        .summary-tile-value {
            color:#101828;
            font-size:24px;
            font-weight:800;
            margin-top:5px;
        }

        .summary-tile-foot {
            color:#667085;
            font-size:11px;
            margin-top:3px;
        }

        .operator-head-v59 {
            display:flex;
            justify-content:space-between;
            align-items:flex-start;
            gap:12px;
            margin-bottom:10px;
        }

        .operator-id-wrap-v59 {
            display:flex;
            align-items:center;
            gap:10px;
            min-width:0;
        }

        .operator-avatar-v59 {
            min-width:44px;
            width:44px;
            height:44px;
            border-radius:50%;
            display:flex;
            align-items:center;
            justify-content:center;
            background:#f4ecff;
            color:#6c4ff8;
            font-size:14px;
            font-weight:800;
        }

        .operator-name-v59 {
            color:#101828;
            font-size:18px;
            font-weight:800;
            line-height:1.15;
        }

        .operator-mail-v59 {
            color:#667085;
            font-size:11px;
            margin-top:4px;
        }

        .operator-status-wrap-v59 {
            text-align:right;
            flex-shrink:0;
        }

        .operator-status-note-v59 {
            color:#667085;
            font-size:10px;
            margin-top:5px;
        }

        .daily-target-v59 {
            display:flex;
            align-items:center;
            justify-content:center;
            gap:10px;
            background:#f4f8ff;
            border:1px solid #cfe0ff;
            color:#24456f;
            border-radius:10px;
            padding:10px 12px;
            margin:8px 0 10px 0;
            font-size:12px;
            font-weight:800;
        }

        .toolbar-note-v59 {
            color:#667085;
            font-size:11px;
            margin-top:4px;
        }

        .operator-metric-caption-v59 {
            color:#667085;
            font-size:11px;
            margin-top:4px;
        }


        /* ===== TARJETAS COMPACTAS V61 ===== */
        .operator-head-v59 {
            margin-bottom:4px !important;
        }

        .operator-avatar-v59 {
            min-width:36px !important;
            width:36px !important;
            height:36px !important;
            font-size:12px !important;
        }

        .operator-name-v59 {
            font-size:16px !important;
        }

        .operator-mail-v59,
        .operator-status-note-v59 {
            margin-top:2px !important;
        }

        .daily-target-v59 {
            padding:6px 10px !important;
            margin:4px 0 6px 0 !important;
            font-size:11px !important;
            min-height:0 !important;
        }

        /* Reduce padding de contenedores con borde dentro del área principal */
        [data-testid="stMainBlockContainer"] div[data-testid="stVerticalBlockBorderWrapper"] > div {
            padding-top:8px;
            padding-bottom:8px;
        }

        /* Métricas más compactas manteniendo números legibles */
        [data-testid="stMetric"] {
            padding:4px 8px !important;
        }

        [data-testid="stMetricLabel"] {
            margin-bottom:0 !important;
        }

        [data-testid="stMetricLabel"] p {
            font-size:10px !important;
        }

        [data-testid="stMetricValue"] {
            font-size:22px !important;
            line-height:1.05 !important;
        }

        [data-testid="stMetricDelta"] {
            font-size:10px !important;
        }

        /* Barras y captions más juntos */
        [data-testid="stProgress"] {
            margin-top:-5px !important;
            margin-bottom:-7px !important;
        }

        [data-testid="stCaptionContainer"] {
            margin-top:-2px !important;
            margin-bottom:-4px !important;
        }

        [data-testid="stCaptionContainer"] p {
            font-size:10px !important;
        }

        /* Botones inferiores menos altos */
        [data-testid="stBaseButton-secondary"],
        [data-testid="stLinkButton"] a {
            min-height:32px !important;
            padding-top:4px !important;
            padding-bottom:4px !important;
        }


        /* ===== PRIORIZACIÓN VISUAL V62 ===== */

        .priority-chip-v62 {
            display:inline-flex;
            align-items:center;
            gap:5px;
            border-radius:999px;
            padding:4px 8px;
            font-size:10px;
            font-weight:800;
            margin-top:5px;
        }

        .priority-red-v62 {
            background:#fff1f3;
            color:#c01048;
        }

        .priority-orange-v62 {
            background:#fff6ed;
            color:#b54708;
        }

        .priority-green-v62 {
            background:#ecfdf3;
            color:#067647;
        }

        .channel-mini-v62 {
            display:flex;
            align-items:center;
            gap:10px;
            color:#667085;
            font-size:10px;
            margin-top:4px;
            flex-wrap:wrap;
        }

        .metric-box-v62 {
            background:#ffffff;
            border:1px solid #e7ebf0;
            border-radius:12px;
            padding:8px 9px 7px 9px;
            min-height:112px;
        }

        .metric-label-v62 {
            color:#667085;
            font-size:9px;
            font-weight:800;
            letter-spacing:.04em;
            text-transform:uppercase;
        }

        .metric-value-v62 {
            color:#101828;
            font-size:20px;
            font-weight:800;
            line-height:1.05;
            margin-top:5px;
            white-space:nowrap;
            overflow:hidden;
            text-overflow:ellipsis;
        }

        .metric-sub-v62 {
            color:#667085;
            font-size:10px;
            margin-top:3px;
            white-space:nowrap;
            overflow:hidden;
            text-overflow:ellipsis;
        }

        .metric-bar-bg-v62 {
            width:100%;
            height:7px;
            background:#eef1f4;
            border-radius:999px;
            margin-top:8px;
            overflow:hidden;
        }

        .metric-bar-fill-v62 {
            height:100%;
            border-radius:999px;
        }

        .bar-red-v62 {
            background:#e5484d;
        }

        .bar-orange-v62 {
            background:#f59e0b;
        }

        .bar-green-v62 {
            background:#22a447;
        }

        .metric-foot-v62 {
            color:#667085;
            font-size:9px;
            margin-top:6px;
        }

        .today-mini-v62 {
            color:#667085;
            font-size:10px;
            font-weight:700;
            margin:6px 0 7px 2px;
        }

        /* ===== CONTROL OPERATIVO V63 ===== */

        .status-summary-v63 {
            background:#ffffff;
            border:1px solid #e6eaf0;
            border-radius:14px;
            padding:11px 13px;
            min-height:74px;
        }

        .status-summary-label-v63 {
            color:#667085;
            font-size:10px;
            font-weight:800;
            text-transform:uppercase;
            letter-spacing:.04em;
        }

        .status-summary-value-v63 {
            color:#101828;
            font-size:22px;
            font-weight:800;
            margin-top:3px;
        }

        .status-summary-foot-v63 {
            color:#667085;
            font-size:10px;
            margin-top:2px;
        }

        .expected-note-v63 {
            display:flex;
            align-items:center;
            justify-content:space-between;
            gap:10px;
            background:#f8fafc;
            border:1px solid #e7ebf0;
            border-radius:10px;
            padding:8px 10px;
            margin:6px 0 10px 0;
            font-size:10px;
            color:#475467;
        }

        .expected-note-v63 strong {
            color:#101828;
        }

        .operator-alert-v63 {
            margin-top:4px;
            font-size:10px;
            font-weight:700;
        }

        .operator-alert-red-v63 {
            color:#c01048;
        }

        .operator-alert-orange-v63 {
            color:#b54708;
        }

        .operator-alert-green-v63 {
            color:#067647;
        }

        /* ===== FASE VISUAL V64 ===== */

        .top-action-row-v64 {
            display:flex;
            justify-content:flex-end;
            gap:10px;
            margin:2px 0 10px 0;
        }

        .color-kpi-v64 {
            border-radius:14px;
            padding:13px 14px;
            min-height:86px;
            border:1px solid;
            box-shadow:0 2px 8px rgba(16,24,40,.04);
        }

        .kpi-purple-v64 {
            background:#f6f3ff;
            border-color:#dfd6ff;
        }

        .kpi-blue-v64 {
            background:#eef7ff;
            border-color:#cfe6ff;
        }

        .kpi-green-v64 {
            background:#effcf4;
            border-color:#ccefd8;
        }

        .kpi-orange-v64 {
            background:#fff7ed;
            border-color:#fed7aa;
        }

        .kpi-red-v64 {
            background:#fff1f3;
            border-color:#fecdd3;
        }

        .kpi-value-color-v64 {
            font-size:24px;
            font-weight:800;
            color:#101828;
            margin-top:4px;
        }

        .kpi-label-color-v64 {
            font-size:10px;
            font-weight:800;
            letter-spacing:.04em;
            text-transform:uppercase;
        }

        .kpi-foot-color-v64 {
            font-size:10px;
            color:#667085;
            margin-top:3px;
        }

        .kpi-icon-v64 {
            font-size:20px;
            margin-bottom:2px;
        }

        .operator-card-accent-v64 {
            position:relative;
        }

        .operator-card-accent-v64::before {
            content:"";
            position:absolute;
            left:-1px;
            top:12px;
            bottom:12px;
            width:4px;
            border-radius:999px;
            background:#d0d5dd;
        }

        .channel-ok-v64 {
            color:#067647;
            font-weight:700;
        }

        .channel-pending-v64 {
            color:#b54708;
            font-weight:700;
        }

        .gap-badge-v64 {
            display:inline-flex;
            align-items:center;
            gap:4px;
            border-radius:999px;
            padding:4px 8px;
            font-size:10px;
            font-weight:800;
        }

        .gap-red-v64 {
            background:#fff1f3;
            color:#c01048;
        }

        .gap-orange-v64 {
            background:#fff6ed;
            color:#b54708;
        }

        .gap-green-v64 {
            background:#ecfdf3;
            color:#067647;
        }

        .recovery-focus-v64 {
            color:#b54708;
            font-weight:800;
        }

        .toolbar-shell-v64 {
            background:#ffffff;
            border:1px solid #e6eaf0;
            border-radius:14px;
            padding:10px 12px 2px 12px;
            margin:8px 0 10px 0;
        }

        .mini-chip-v64 {
            display:inline-flex;
            align-items:center;
            gap:5px;
            border-radius:999px;
            padding:4px 8px;
            background:#f2f4f7;
            color:#475467;
            font-size:10px;
            font-weight:700;
            margin-right:6px;
        }

        /* ===== FASE V66 · CONTROL DEL DÍA ===== */

        .hello-v66 {
            display:flex;
            justify-content:space-between;
            align-items:flex-start;
            gap:16px;
            margin-bottom:12px;
        }

        .hello-title-v66 {
            font-size:27px;
            font-weight:850;
            color:#101828;
            line-height:1.05;
        }

        .hello-sub-v66 {
            color:#667085;
            font-size:12px;
            margin-top:5px;
        }

        .kpi-v66 {
            border-radius:15px;
            padding:13px 14px;
            min-height:92px;
            border:1px solid #e5e9ef;
            box-shadow:0 2px 8px rgba(16,24,40,.04);
            background:#fff;
        }

        .kpi-v66-purple {background:linear-gradient(135deg,#f7f3ff,#fff);border-color:#e4d8ff;}
        .kpi-v66-blue   {background:linear-gradient(135deg,#edf7ff,#fff);border-color:#cde6ff;}
        .kpi-v66-green  {background:linear-gradient(135deg,#eefcf4,#fff);border-color:#ccefd8;}
        .kpi-v66-orange {background:linear-gradient(135deg,#fff7ed,#fff);border-color:#fed7aa;}
        .kpi-v66-red    {background:linear-gradient(135deg,#fff1f3,#fff);border-color:#fecdd3;}

        .kpi-label-v66 {
            color:#667085;
            font-size:9px;
            font-weight:850;
            letter-spacing:.05em;
            text-transform:uppercase;
        }

        .kpi-value-v66 {
            color:#101828;
            font-size:23px;
            font-weight:850;
            margin-top:5px;
        }

        .kpi-foot-v66 {
            color:#667085;
            font-size:10px;
            margin-top:4px;
        }

        .day-shell-v66 {
            background:#fff;
            border:1px solid #e5e9ef;
            border-radius:16px;
            padding:14px;
            margin:10px 0 12px 0;
            box-shadow:0 2px 10px rgba(16,24,40,.04);
        }

        .day-title-v66 {
            color:#101828;
            font-size:15px;
            font-weight:850;
            margin-bottom:10px;
        }

        .day-grid-v66 {
            display:grid;
            grid-template-columns:1fr 1.6fr 1.6fr;
            gap:12px;
        }

        .day-card-v66 {
            border:1px solid #e7ebf0;
            border-radius:13px;
            padding:12px;
            background:#fbfcfe;
        }

        .day-card-blue-v66 {
            background:#f2f7ff;
            border-color:#d4e4ff;
        }

        .day-card-green-v66 {
            background:#f1fbf5;
            border-color:#d2efdc;
        }

        .day-card-label-v66 {
            color:#667085;
            font-size:9px;
            font-weight:850;
            text-transform:uppercase;
            letter-spacing:.05em;
        }

        .day-main-v66 {
            color:#101828;
            font-size:24px;
            font-weight:850;
            margin-top:5px;
        }

        .day-detail-v66 {
            color:#667085;
            font-size:10px;
            margin-top:4px;
        }

        .day-delta-red-v66 {
            color:#c01048;
            font-weight:850;
        }

        .day-delta-green-v66 {
            color:#067647;
            font-weight:850;
        }

        .day-progress-bg-v66 {
            height:8px;
            border-radius:999px;
            overflow:hidden;
            background:#e9edf2;
            margin-top:9px;
        }

        .day-progress-fill-v66 {
            height:100%;
            border-radius:999px;
        }

        .operator-today-shell-v66 {
            border-radius:11px;
            padding:9px 10px;
            margin:6px 0 7px 0;
            border:1px solid #e7ebf0;
            background:#f8fafc;
        }

        .operator-today-title-v66 {
            font-size:9px;
            font-weight:850;
            color:#667085;
            text-transform:uppercase;
            letter-spacing:.04em;
            margin-bottom:7px;
        }

        .operator-today-grid-v66 {
            display:grid;
            grid-template-columns:1fr 1fr;
            gap:8px;
        }

        .operator-today-item-v66 {
            background:#fff;
            border:1px solid #e8ecf1;
            border-radius:9px;
            padding:7px 8px;
        }

        .operator-today-value-v66 {
            font-size:16px;
            font-weight:850;
            color:#101828;
        }

        .operator-today-sub-v66 {
            font-size:9px;
            color:#667085;
            margin-top:2px;
        }

        .monthly-strip-v66 {
            display:grid;
            grid-template-columns:1fr 1fr 1.2fr;
            gap:6px;
            margin-top:7px;
        }

        .monthly-item-v66 {
            border-top:1px solid #eef1f4;
            padding-top:6px;
        }

        .monthly-label-v66 {
            color:#98a2b3;
            font-size:8px;
            font-weight:800;
            text-transform:uppercase;
        }

        .monthly-value-v66 {
            color:#344054;
            font-size:11px;
            font-weight:750;
            margin-top:2px;
        }

        .status-critical-v66 {
            background:#fff1f3;
            border-color:#fecdd3 !important;
        }

        .status-attention-v66 {
            background:#fffaf2;
            border-color:#fed7aa !important;
        }

        .status-good-v66 {
            background:#f3fbf6;
            border-color:#ccefd8 !important;
        }

        .legend-v66 {
            background:#f8fafc;
            border:1px solid #e7ebf0;
            border-radius:11px;
            padding:8px 10px;
            margin-top:10px;
            color:#667085;
            font-size:10px;
        }

        /* ===== V71 · TARJETAS OPERATIVAS REFINADAS ===== */

        .op-head-v71 {
            display:flex;
            justify-content:space-between;
            gap:10px;
            align-items:flex-start;
            margin-bottom:6px;
        }

        .op-name-v71 {
            color:#101828;
            font-size:17px;
            font-weight:850;
            line-height:1.15;
        }

        .op-contact-v71 {
            color:#667085;
            font-size:10px;
            margin-top:3px;
        }

        .op-state-v71 {
            display:inline-flex;
            align-items:center;
            border-radius:999px;
            padding:4px 8px;
            font-size:10px;
            font-weight:850;
        }

        .op-red-v71 {
            color:#c01048;
            background:#fff1f3;
        }

        .op-orange-v71 {
            color:#b54708;
            background:#fff6ed;
        }

        .op-green-v71 {
            color:#067647;
            background:#ecfdf3;
        }

        .op-gray-v71 {
            color:#475467;
            background:#f2f4f7;
        }

        .schedule-v71 {
            color:#667085;
            font-size:10px;
            padding:6px 8px;
            background:#f8fafc;
            border:1px solid #e7ebf0;
            border-radius:9px;
            margin-bottom:7px;
        }

        .today-label-v71 {
            color:#667085;
            font-size:9px;
            font-weight:850;
            text-transform:uppercase;
            letter-spacing:.04em;
            margin:3px 0 4px 0;
        }

        .month-bar-v71 {
            border-top:1px solid #eef1f4;
            margin-top:7px;
            padding-top:6px;
        }

        .legend-v71 {
            background:#f8fafc;
            border:1px solid #e7ebf0;
            border-radius:11px;
            padding:8px 10px;
            color:#667085;
            font-size:10px;
            margin-top:8px;
        }

        /* Menos aire vertical dentro de las tarjetas */
        [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMetric"] {
            padding:5px 8px !important;
        }

        [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMetricValue"] {
            font-size:22px !important;
        }

        [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMetricLabel"] p {
            font-size:10px !important;
        }

        [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMetricDelta"] {
            font-size:10px !important;
        }

        /* ===== V72 · GRID 4 COLUMNAS ===== */
        .op-title-v72{
            font-size:15px;
            font-weight:850;
            color:#101828;
            line-height:1.15;
        }
        .op-meta-v72{
            font-size:9px;
            color:#667085;
            margin-top:3px;
        }
        .op-status-v72{
            display:inline-flex;
            padding:3px 7px;
            border-radius:999px;
            font-size:9px;
            font-weight:850;
        }
        .op-red-v72{background:#fff1f3;color:#c01048;}
        .op-orange-v72{background:#fff6ed;color:#b54708;}
        .op-green-v72{background:#ecfdf3;color:#067647;}
        .op-gray-v72{background:#f2f4f7;color:#475467;}
        .schedule-v72{
            font-size:9px;
            color:#667085;
            margin:4px 0 6px 0;
        }
        .month-line-v72{
            font-size:9px;
            color:#667085;
            margin-top:5px;
            padding-top:5px;
            border-top:1px solid #eef1f4;
        }
        .month-strong-v72{
            color:#344054;
            font-weight:800;
        }

        /* compactar métricas dentro de tarjetas */
        [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMetric"]{
            padding:3px 5px !important;
        }
        [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMetricValue"]{
            font-size:18px !important;
            line-height:1.05 !important;
        }
        [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMetricLabel"] p{
            font-size:9px !important;
        }
        [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMetricDelta"]{
            font-size:9px !important;
        }
        [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stCaptionContainer"] p{
            font-size:9px !important;
        }

        /* ===== V73 · VISUAL OPERATIVA MEJORADA ===== */

        .op-card-v73 {
            border-radius:14px;
            padding:0;
        }

        .op-head-wrap-v73 {
            display:flex;
            justify-content:space-between;
            align-items:flex-start;
            gap:8px;
            margin-bottom:5px;
        }

        .op-title-v73 {
            font-size:15px;
            font-weight:850;
            color:#101828;
            line-height:1.15;
        }

        .op-sub-v73 {
            font-size:9px;
            color:#667085;
            margin-top:3px;
            line-height:1.25;
        }

        .status-pill-v73 {
            display:inline-flex;
            align-items:center;
            gap:4px;
            padding:3px 7px;
            border-radius:999px;
            font-size:9px;
            font-weight:850;
            white-space:nowrap;
        }

        .status-red-v73 {
            background:#fff1f3;
            color:#c01048;
        }

        .status-orange-v73 {
            background:#fff6ed;
            color:#b54708;
        }

        .status-green-v73 {
            background:#ecfdf3;
            color:#067647;
        }

        .status-gray-v73 {
            background:#f2f4f7;
            color:#475467;
        }

        .schedule-row-v73 {
            background:#f8fafc;
            border:1px solid #eef1f4;
            border-radius:8px;
            padding:5px 7px;
            font-size:9px;
            color:#667085;
            margin:4px 0 6px 0;
        }

        .today-kicker-v73 {
            font-size:8px;
            color:#98a2b3;
            text-transform:uppercase;
            letter-spacing:.06em;
            font-weight:850;
            margin:2px 0 4px 0;
        }

        .progress-mini-v73 {
            height:5px;
            background:#eef1f4;
            border-radius:999px;
            overflow:hidden;
            margin-top:5px;
        }

        .progress-mini-fill-v73 {
            height:100%;
            border-radius:999px;
        }

        .fill-red-v73 {background:#e5484d;}
        .fill-orange-v73 {background:#f59e0b;}
        .fill-green-v73 {background:#22a447;}

        .month-summary-v73 {
            display:flex;
            justify-content:space-between;
            align-items:center;
            gap:6px;
            margin-top:6px;
            padding-top:6px;
            border-top:1px solid #eef1f4;
            font-size:9px;
            color:#667085;
        }

        .month-summary-v73 strong {
            color:#344054;
        }

        .focus-note-v73 {
            border-radius:8px;
            padding:5px 7px;
            margin-top:5px;
            font-size:9px;
            font-weight:800;
        }

        .focus-red-v73 {
            background:#fff1f3;
            color:#c01048;
        }

        .focus-orange-v73 {
            background:#fff6ed;
            color:#b54708;
        }

        .focus-green-v73 {
            background:#ecfdf3;
            color:#067647;
        }

        /* tarjetas algo más altas pero mejor balanceadas */
        [data-testid="stVerticalBlockBorderWrapper"] {
            border-radius:14px !important;
        }

        [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMetric"]{
            padding:3px 4px !important;
        }

        [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMetricValue"]{
            font-size:19px !important;
        }

        [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMetricLabel"] p{
            font-size:9px !important;
            font-weight:700 !important;
        }

        [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMetricDelta"]{
            font-size:9px !important;
        }

        [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stCaptionContainer"] p{
            font-size:8px !important;
        }

        /* Botones más discretos */
        [data-testid="stVerticalBlockBorderWrapper"] button,
        [data-testid="stVerticalBlockBorderWrapper"] a[data-testid="stBaseButton-secondary"]{
            min-height:30px !important;
            font-size:10px !important;
        }

        /* ===== V74 · TARJETAS 3 COLUMNAS / MÁS LEGIBLES ===== */

        .op-head-v74{
            display:flex;
            justify-content:space-between;
            gap:10px;
            align-items:flex-start;
            margin-bottom:6px;
        }

        .op-name-v74{
            font-size:16px;
            line-height:1.15;
            font-weight:850;
            color:#101828;
        }

        .op-contact-v74{
            margin-top:3px;
            font-size:10px;
            color:#667085;
        }

        .status-v74{
            display:inline-flex;
            align-items:center;
            padding:4px 8px;
            border-radius:999px;
            font-size:10px;
            font-weight:850;
            white-space:nowrap;
        }

        .v74-red{background:#fff1f3;color:#c01048;}
        .v74-orange{background:#fff6ed;color:#b54708;}
        .v74-green{background:#ecfdf3;color:#067647;}
        .v74-gray{background:#f2f4f7;color:#475467;}

        .schedule-v74{
            background:#f8fafc;
            border:1px solid #e7ebf0;
            border-radius:9px;
            padding:6px 8px;
            font-size:10px;
            color:#667085;
            margin-bottom:7px;
        }

        .kicker-v74{
            color:#98a2b3;
            font-size:9px;
            font-weight:850;
            letter-spacing:.05em;
            text-transform:uppercase;
            margin:2px 0 5px 0;
        }

        .mini-progress-v74{
            height:6px;
            border-radius:999px;
            background:#edf0f4;
            overflow:hidden;
            margin-top:5px;
        }

        .mini-fill-v74{
            height:100%;
            border-radius:999px;
        }

        .mini-red-v74{background:#e5484d;}
        .mini-orange-v74{background:#f59e0b;}
        .mini-green-v74{background:#22a447;}

        .action-v74{
            border-radius:9px;
            padding:7px 9px;
            margin:7px 0 6px 0;
            font-size:10px;
            font-weight:800;
        }

        .action-red-v74{background:#fff1f3;color:#c01048;}
        .action-orange-v74{background:#fff6ed;color:#b54708;}
        .action-green-v74{background:#ecfdf3;color:#067647;}
        .action-gray-v74{background:#f2f4f7;color:#475467;}

        .monthly-v74{
            border-top:1px solid #eef1f4;
            margin-top:7px;
            padding-top:6px;
            display:flex;
            justify-content:space-between;
            gap:8px;
            font-size:10px;
            color:#667085;
        }

        .monthly-v74 strong{
            color:#344054;
        }

        /* Métricas más cómodas que V73 */
        [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMetric"]{
            padding:5px 6px !important;
        }

        [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMetricValue"]{
            font-size:21px !important;
            line-height:1.05 !important;
        }

        [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMetricLabel"] p{
            font-size:10px !important;
            font-weight:700 !important;
        }

        [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMetricDelta"]{
            font-size:10px !important;
        }

        [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stCaptionContainer"] p{
            font-size:9px !important;
        }

        [data-testid="stVerticalBlockBorderWrapper"] button{
            min-height:32px !important;
            font-size:10px !important;
        }

        /* ===== V77 · ALERTAS COMPACTAS ===== */

        .alert-summary-v77 {
            border:1px solid #f4d7a2;
            background:linear-gradient(135deg,#fffaf0,#fffef8);
            border-radius:14px;
            padding:12px 14px;
            margin-top:8px;
        }

        .alert-summary-title-v77 {
            font-size:13px;
            font-weight:850;
            color:#7a4b00;
        }

        .alert-summary-sub-v77 {
            font-size:10px;
            color:#8a6b2d;
            margin-top:3px;
        }

        .alert-row-v77 {
            display:flex;
            justify-content:space-between;
            gap:10px;
            align-items:center;
            padding:6px 0;
            border-bottom:1px solid rgba(122,75,0,.08);
            font-size:10px;
        }

        .alert-row-v77:last-child {
            border-bottom:none;
        }

        .alert-name-v77 {
            color:#344054;
            font-weight:750;
        }

        .alert-value-v77 {
            color:#b54708;
            font-weight:850;
            white-space:nowrap;
        }

        .leader-strip-v77 {
            border-radius:11px;
            padding:8px 10px;
            font-size:10px;
            font-weight:750;
            min-height:42px;
            display:flex;
            align-items:center;
        }

        .leader-green-v77 {
            background:#ecfdf3;
            color:#067647;
            border:1px solid #ccefd8;
        }

        .leader-orange-v77 {
            background:#fff7ed;
            color:#b54708;
            border:1px solid #fed7aa;
        }

        /* ===== V79 · RESUMEN EJECUTIVO ===== */

        .team-state-v79{
            border-radius:14px;
            padding:12px 14px;
            margin:8px 0 12px 0;
            border:1px solid;
            display:flex;
            justify-content:space-between;
            align-items:center;
            gap:14px;
        }

        .team-state-red-v79{
            background:#fff1f3;
            border-color:#fecdd3;
            color:#9f1239;
        }

        .team-state-orange-v79{
            background:#fff7ed;
            border-color:#fed7aa;
            color:#9a3412;
        }

        .team-state-green-v79{
            background:#ecfdf3;
            border-color:#bbf7d0;
            color:#166534;
        }

        .team-state-title-v79{
            font-size:15px;
            font-weight:850;
        }

        .team-state-sub-v79{
            font-size:10px;
            margin-top:3px;
            opacity:.82;
        }

        .team-focus-v79{
            font-size:11px;
            font-weight:800;
            white-space:nowrap;
        }

        .kpi-card-v79{
            border:1px solid #e7ebf0;
            border-radius:14px;
            padding:12px 13px;
            min-height:112px;
            background:#fff;
            box-shadow:0 2px 8px rgba(16,24,40,.04);
        }

        .kpi-card-blue-v79{
            background:linear-gradient(135deg,#eef7ff,#ffffff);
            border-color:#cfe6ff;
        }

        .kpi-card-orange-v79{
            background:linear-gradient(135deg,#fff7ed,#ffffff);
            border-color:#fed7aa;
        }

        .kpi-card-green-v79{
            background:linear-gradient(135deg,#ecfdf3,#ffffff);
            border-color:#bbf7d0;
        }

        .kpi-card-purple-v79{
            background:linear-gradient(135deg,#f6f3ff,#ffffff);
            border-color:#ded5ff;
        }

        .kpi-label-v79{
            font-size:9px;
            font-weight:850;
            letter-spacing:.05em;
            text-transform:uppercase;
            color:#667085;
        }

        .kpi-value-v79{
            font-size:24px;
            font-weight:850;
            color:#101828;
            margin-top:5px;
        }

        .kpi-foot-v79{
            font-size:10px;
            color:#667085;
            margin-top:4px;
        }

        .compare-card-v79{
            border:1px solid #e7ebf0;
            border-radius:13px;
            padding:11px 12px;
            background:#fff;
            min-height:118px;
        }

        .compare-title-v79{
            font-size:11px;
            font-weight:850;
            color:#344054;
        }

        .compare-value-v79{
            font-size:21px;
            font-weight:850;
            color:#101828;
            margin-top:4px;
        }

        .compare-sub-v79{
            font-size:10px;
            color:#667085;
            margin-top:3px;
        }

        .compare-gap-red-v79{
            color:#c01048;
            font-weight:850;
        }

        .compare-gap-orange-v79{
            color:#b54708;
            font-weight:850;
        }

        .compare-gap-green-v79{
            color:#067647;
            font-weight:850;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# MENÚ LATERAL
# =========================================================

with st.sidebar:

    st.markdown(
        """
        <div class="sidebar-brand">
            <div class="sidebar-logo">G</div>
            <div>
                <div class="sidebar-brand-title">GEN Control</div>
                <div class="sidebar-brand-sub">Cobranzas Inmobiliarias</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="sidebar-section-label">Navegación</div>',
        unsafe_allow_html=True,
    )

    menu = st.radio(
        "Navegación",
        [
            "🏠 Resumen",
            "📈 Comportamiento diario",
            "✉️ Mensajes diarios",
            "📥 Cargar reportes",
            "🗂️ Histórico",
            "👥 Equipo",
            "⚙️ Configuración",
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")

    ahora_sidebar = (
        st.session_state.get(
            "callcenter_cargado_en"
        )
        or st.session_state.get(
            "promesas_cargado_en"
        )
        or ahora_bolivia()
    )

    ahora_sidebar = (
        datetime_bolivia(ahora_sidebar)
        or ahora_sidebar
    )

    st.markdown(
        f"""
        <div class="sidebar-status-card">
            <div class="sidebar-status-top">
                <span class="sidebar-status-dot"></span>
                Datos actualizados
            </div>
            <div class="sidebar-status-date">
                {ahora_sidebar.strftime('%d/%m/%Y')}
            </div>
            <div class="sidebar-status-time">
                {ahora_sidebar.strftime('%H:%M')} · Hora Bolivia
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    st.markdown(
        """
        <div class="sidebar-profile">
            <div class="sidebar-avatar">JC</div>
            <div>
                <div class="sidebar-profile-name">José Carlos</div>
                <div class="sidebar-profile-role">Coordinador</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="sidebar-version">
            <span>GEN Control</span>
            <span class="sidebar-version-badge">Actualizado</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# ENCABEZADO
# =========================================================

st.markdown(
    f"""
    <div class="gen-header">
        <div class="gen-title">{APP_NAME}</div>
        <div class="gen-subtitle">{APP_SUBTITLE}</div>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# RESUMEN
# =========================================================


def estado_datos_para_seguimiento(resultado=None):
    ahora = datetime.now(ZoneInfo("America/La_Paz"))
    hoy = ahora.date()
    promesas_ok = resultado is not None and not resultado.empty
    promesas_cargado = st.session_state.get("promesas_cargado_en")
    call_df = st.session_state.get("callcenter_df")
    call_ok = call_df is not None and not call_df.empty
    call_cargado = st.session_state.get("callcenter_cargado_en")
    corte = obtener_corte_callcenter(call_df) if call_ok else None
    if hasattr(corte, "to_pydatetime"):
        corte = corte.to_pydatetime()

    minutos_call = None
    if call_cargado is not None:
        try:
            minutos_call = max(int((ahora-call_cargado).total_seconds()//60),0)
        except Exception:
            pass

    fecha_operativa_call = None
    if call_ok:
        col_fecha = buscar_columna(call_df, ["fecha"])
        if col_fecha is not None:
            serie = pd.to_datetime(call_df[col_fecha], dayfirst=True, errors="coerce").dropna()
            if not serie.empty:
                fecha_operativa_call = serie.max().date()

    usuarios_detectados = 0
    if promesas_ok and "Usuario" in resultado.columns:
        usuarios_detectados = int(resultado["Usuario"].astype(str).nunique())

    recuperacion_ok = (
        promesas_ok
        and "Recuperación acumulada" in resultado.columns
        and resultado["Recuperación acumulada"].notna().any()
    )

    bloqueos, avisos = [], []
    if not promesas_ok:
        bloqueos.append("Falta Promesas de Pago")
    if not call_ok:
        bloqueos.append("Falta GEN CallCenter")
    elif fecha_operativa_call is not None and fecha_operativa_call != hoy:
        bloqueos.append(f"CallCenter corresponde al {fecha_operativa_call.strftime('%d/%m/%Y')}")
    if usuarios_detectados and usuarios_detectados < CANTIDAD_OPERADORES:
        avisos.append(f"Solo se identificaron {usuarios_detectados}/{CANTIDAD_OPERADORES} operadores")
    if call_ok and minutos_call is not None and minutos_call > 180:
        avisos.append(f"CallCenter fue cargado hace {minutos_call//60} h {minutos_call%60} min")

    if bloqueos:
        nivel,titulo="rojo","Datos no listos para enviar"
    elif avisos:
        nivel,titulo="naranja","Revisar antes de enviar"
    else:
        nivel,titulo="verde","Datos listos para seguimiento"

    return {
        "nivel":nivel,"titulo":titulo,"promesas_ok":promesas_ok,
        "promesas_cargado":promesas_cargado,"call_ok":call_ok,
        "call_cargado":call_cargado,"corte":corte,"minutos_call":minutos_call,
        "fecha_operativa_call":fecha_operativa_call,
        "usuarios_detectados":usuarios_detectados,"recuperacion_ok":recuperacion_ok,
        "razones_bloqueo":bloqueos,"advertencias":avisos,
        "bloquear_envio":bool(bloqueos),
    }


def operador_habilitado_para_envio(usuario, momento=None):
    """En turno + habilitación individual + habilitación global."""
    return bool(
        operador_en_turno(usuario, momento)
        or st.session_state.get(
            f"override_fuera_turno_{usuario}",
            False,
        )
        or st.session_state.get(
            "permitir_envio_fuera_turno",
            False,
        )
    )


if menu == "🏠 Resumen":

    resultado = st.session_state.resultado_operadores
    jornadas_info = jornadas_configuradas()

    st.markdown(
        f"""
        <div class="hero-card">
            <div style="
                position:relative;z-index:1;
                display:inline-flex;align-items:center;gap:6px;
                padding:5px 9px;border-radius:999px;
                background:rgba(255,255,255,.10);
                color:#CDE7F6;font-size:9px;font-weight:800;
                letter-spacing:.06em;text-transform:uppercase;
                margin-bottom:10px;
            ">
                ● GEN CONTROL · COBRANZAS INMOBILIARIAS
            </div>
            <div class="hero-title">Centro de control operativo</div>
            <div class="hero-subtitle">
                Seguimiento ejecutivo de metas, brechas y recuperación ·
                {fecha_local_actual().strftime("%d/%m/%Y")}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if resultado is None:
        st.info(
            "Carga el reporte de Promesas de Pago para visualizar "
            "el tablero operativo."
        )

    else:
        esperado = jornadas_info["esperado_pct"]

        promedio_gestiones = float(
            resultado["% Gestiones"].mean()
        )
        promedio_compromisos = float(
            resultado["% Compromisos"].mean()
        )
        promedio_recuperacion = float(
            resultado["% Recuperación"].mean()
        )

        total_gestiones = int(
            resultado["Gestiones"].sum()
        )
        total_compromisos = int(
            resultado["Compromisos"].sum()
        )
        total_recuperacion = float(
            resultado["Recuperación acumulada"].sum()
        )

        meta_equipo_gestiones = (
            st.session_state.meta_gestiones_cfg
            * CANTIDAD_OPERADORES
        )
        meta_equipo_compromisos = (
            st.session_state.meta_compromisos_cfg
            * CANTIDAD_OPERADORES
        )
        meta_equipo_recuperacion = (
            st.session_state.meta_recuperacion_cfg
            * CANTIDAD_OPERADORES
        )

        # Estado del equipo según la MAYOR brecha real.
        # No se promedian indicadores distintos para evitar ocultar rezagos.
        brechas_equipo = {
            "Gestiones": promedio_gestiones - esperado,
            "Compromisos": promedio_compromisos - esperado,
            "Recuperación": promedio_recuperacion - esperado,
        }

        indicador_prioritario = min(
            brechas_equipo,
            key=brechas_equipo.get,
        )

        mayor_brecha_equipo = float(
            brechas_equipo[
                indicador_prioritario
            ]
        )

        if mayor_brecha_equipo >= -3:
            estado_general = "🟢 Equipo en ritmo"
            estado_clase_v79 = "team-state-green-v79"
        elif mayor_brecha_equipo >= -10:
            estado_general = "🟠 Equipo en seguimiento"
            estado_clase_v79 = "team-state-orange-v79"
        else:
            estado_general = "🔴 Reforzar ritmo"
            estado_clase_v79 = "team-state-red-v79"

        st.markdown(
            f"""
            <div class="team-state-v79 {estado_clase_v79}">
                <div>
                    <div class="team-state-title-v79">
                        {estado_general}
                    </div>
                    <div class="team-state-sub-v79">
                        Comparación contra el esperado a la fecha:
                        {formato_porcentaje(esperado)}
                    </div>
                </div>
                <div class="team-focus-v79">
                    Prioridad: {indicador_prioritario} ·
                    {formato_porcentaje(abs(mayor_brecha_equipo))} de brecha
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # -------------------------------------------------
        # KPI PRINCIPALES — V79
        # -------------------------------------------------

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            st.markdown(
                f"""
                <div class="kpi-card-v79 kpi-card-blue-v79">
                    <div class="kpi-label-v79">📞 Gestiones</div>
                    <div class="kpi-value-v79">{formato_entero(total_gestiones)}</div>
                    <div class="kpi-foot-v79">
                        {formato_porcentaje(promedio_gestiones)} ·
                        Meta equipo {formato_entero(meta_equipo_gestiones)}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with c2:
            st.markdown(
                f"""
                <div class="kpi-card-v79 kpi-card-orange-v79">
                    <div class="kpi-label-v79">🤝 Compromisos</div>
                    <div class="kpi-value-v79">{formato_entero(total_compromisos)}</div>
                    <div class="kpi-foot-v79">
                        {formato_porcentaje(promedio_compromisos)} ·
                        Meta equipo {formato_entero(meta_equipo_compromisos)}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with c3:
            st.markdown(
                f"""
                <div class="kpi-card-v79 kpi-card-green-v79">
                    <div class="kpi-label-v79">💰 Recuperación</div>
                    <div class="kpi-value-v79">{formato_usd(total_recuperacion)}</div>
                    <div class="kpi-foot-v79">
                        {formato_porcentaje(promedio_recuperacion)} ·
                        Meta equipo {formato_usd(meta_equipo_recuperacion)}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with c4:
            st.markdown(
                f"""
                <div class="kpi-card-v79 kpi-card-purple-v79">
                    <div class="kpi-label-v79">📈 Esperado a la fecha</div>
                    <div class="kpi-value-v79">{formato_porcentaje(esperado)}</div>
                    <div class="kpi-foot-v79">
                        {jornadas_info['disponibles']} jornadas disponibles contando hoy
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.write("")

        # -------------------------------------------------
        # AVANCE VS ESPERADO — V79
        # -------------------------------------------------

        st.markdown("### Avance vs esperado")

        comparativos_v79 = [
            ("Gestiones", promedio_gestiones),
            ("Compromisos", promedio_compromisos),
            ("Recuperación", promedio_recuperacion),
        ]

        cc1, cc2, cc3 = st.columns(3)

        for columna_cmp, (nombre_cmp, valor_cmp) in zip(
            [cc1, cc2, cc3],
            comparativos_v79,
        ):
            brecha_cmp = float(
                valor_cmp - esperado
            )

            if brecha_cmp >= -3:
                clase_gap = "compare-gap-green-v79"
                estado_gap = "En ritmo"
            elif brecha_cmp >= -10:
                clase_gap = "compare-gap-orange-v79"
                estado_gap = "Seguimiento"
            else:
                clase_gap = "compare-gap-red-v79"
                estado_gap = "Prioridad"

            with columna_cmp:
                st.markdown(
                    f"""
                    <div class="compare-card-v79">
                        <div class="compare-title-v79">{nombre_cmp}</div>
                        <div class="compare-value-v79">
                            {formato_porcentaje(valor_cmp)}
                        </div>
                        <div class="compare-sub-v79">
                            Esperado: {formato_porcentaje(esperado)}
                        </div>
                        <div class="compare-sub-v79 {clase_gap}">
                            {estado_gap} ·
                            Brecha {formato_porcentaje(brecha_cmp)}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.write("")

        # -------------------------------------------------
        # RANKING SIMPLIFICADO
        # -------------------------------------------------

        st.markdown("### Ranking de operadores")
        st.caption(
            "El orden y el estado corresponden al indicador seleccionado."
        )

        ranking = resultado.copy()

        c1, c2 = st.columns([3, 1])

        with c1:
            criterio = st.selectbox(
                "Ranking por",
                [
                    "Recuperación",
                    "Gestiones",
                    "Compromisos",
                ],
                key="ranking_simple_v76",
            )

        with c2:
            menor_primero = st.checkbox(
                "Menor primero",
                value=False,
                key="ranking_menor_v76",
            )

        mapa_criterio = {
            "Recuperación": "% Recuperación",
            "Gestiones": "% Gestiones",
            "Compromisos": "% Compromisos",
        }

        columna_orden = mapa_criterio[criterio]

        ranking["Estado"] = ranking[columna_orden].apply(
            lambda x: clasificar_avance(
                float(x),
                esperado,
            )
        )

        ranking = ranking.sort_values(
            columna_orden,
            ascending=menor_primero,
            kind="stable",
        ).reset_index(drop=True)

        ranking["Posición"] = ranking.index + 1

        vista = pd.DataFrame(
            {
                "#": ranking["Posición"],
                "Operador": ranking["Operador"],
                "Gestiones": ranking.apply(
                    lambda r: (
                        f"{formato_entero(r['Gestiones'])} · "
                        f"{formato_porcentaje(r['% Gestiones'])}"
                    ),
                    axis=1,
                ),
                "Compromisos": ranking.apply(
                    lambda r: (
                        f"{formato_entero(r['Compromisos'])} · "
                        f"{formato_porcentaje(r['% Compromisos'])}"
                    ),
                    axis=1,
                ),
                "Recuperación": ranking.apply(
                    lambda r: (
                        f"{formato_usd(r['Recuperación acumulada'])} · "
                        f"{formato_porcentaje(r['% Recuperación'])}"
                    ),
                    axis=1,
                ),
                "Estado": ranking["Estado"],
            }
        )

        st.dataframe(
            vista,
            use_container_width=True,
            hide_index=True,
        )

        if not ranking.empty:
            lider = ranking.iloc[0]
            seguimiento = ranking.iloc[-1]

            r1, r2 = st.columns(2)

            with r1:
                st.markdown(
                    f"""
                    <div class="leader-strip-v77 leader-green-v77">
                        🏆 <strong>Líder en {criterio.lower()}:</strong>&nbsp;
                        {lider['Operador']} ·
                        {formato_porcentaje(lider[columna_orden])}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with r2:
                st.markdown(
                    f"""
                    <div class="leader-strip-v77 leader-orange-v77">
                        🎯 <strong>Mayor seguimiento en {criterio.lower()}:</strong>&nbsp;
                        {seguimiento['Operador']} ·
                        {formato_porcentaje(seguimiento[columna_orden])}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.write("")

        # -------------------------------------------------
        # ALERTAS COMPACTAS — V77
        # Responden al indicador seleccionado en el ranking
        # -------------------------------------------------

        st.markdown("### Alertas")

        alertas_df = ranking[
            ranking[columna_orden].astype(float)
            < esperado - 10
        ].copy()

        if alertas_df.empty:
            st.success(
                f"✅ No hay brechas críticas en {criterio.lower()}."
            )

        else:
            # Ordenar del más rezagado al menos rezagado.
            alertas_df = alertas_df.sort_values(
                columna_orden,
                ascending=True,
                kind="stable",
            )

            filas_html = []

            for _, fila_alerta in alertas_df.iterrows():
                valor_alerta = float(
                    fila_alerta[columna_orden]
                )

                brecha_alerta = max(
                    esperado - valor_alerta,
                    0,
                )

                filas_html.append(
                    f"""
                    <div class="alert-row-v77">
                        <span class="alert-name-v77">
                            {fila_alerta['Operador']}
                        </span>
                        <span class="alert-value-v77">
                            {formato_porcentaje(valor_alerta)}
                            · brecha {formato_porcentaje(brecha_alerta)}
                        </span>
                    </div>
                    """
                )

            html_alertas = (
                '<div class="alert-summary-v77">'
                f'<div class="alert-summary-title-v77">⚠️ {len(alertas_df)} operador(es) requieren reforzar {criterio.lower()}</div>'
                '<div class="alert-summary-sub-v77">Ordenados desde la mayor brecha hasta la menor.</div>'
                + "".join(
                    parte.strip().replace("\n", " ")
                    for parte in filas_html
                )
                + '</div>'
            )

            st.markdown(
                html_alertas,
                unsafe_allow_html=True,
            )

# =========================================================
# COMPORTAMIENTO DIARIO
# =========================================================

elif menu == "📈 Comportamiento diario":

    # =====================================================
    # COMPORTAMIENTO DIARIO · DISEÑO EJECUTIVO
    # =====================================================
    st.markdown(
        """
        <style>
        .beh-hero{
            background:linear-gradient(120deg,#102A43 0%,#163A5F 62%,#1A6080 100%);
            border-radius:19px;
            padding:20px 22px;
            margin:0 0 15px 0;
            box-shadow:0 14px 32px rgba(16,42,67,.12);
            position:relative;
            overflow:hidden;
        }
        .beh-hero:after{
            content:"";
            position:absolute;
            width:180px;height:180px;border-radius:50%;
            right:-50px;top:-90px;
            background:rgba(70,214,208,.11);
        }
        .beh-kicker{
            display:inline-block;
            padding:4px 8px;
            border-radius:999px;
            background:rgba(255,255,255,.10);
            color:#C8DCEB;
            font-size:8px;
            font-weight:800;
            letter-spacing:.06em;
            text-transform:uppercase;
            margin-bottom:7px;
        }
        .beh-title{
            color:white;
            font-size:24px;
            line-height:1.1;
            font-weight:850;
            letter-spacing:-.03em;
        }
        .beh-sub{
            color:#BDD0E0;
            font-size:10px;
            margin-top:5px;
        }
        .beh-kpi{
            min-height:124px;
            border:1px solid #E4EBF3;
            border-radius:16px;
            background:#FFFFFF;
            padding:14px 15px 13px;
            box-shadow:0 8px 22px rgba(16,42,67,.045);
        }
        .beh-kpi-label{
            font-size:9px;
            color:#708399;
            font-weight:800;
            text-transform:uppercase;
            letter-spacing:.04em;
        }
        .beh-kpi-value{
            font-size:25px;
            line-height:1.05;
            color:#102A43;
            font-weight:850;
            letter-spacing:-.035em;
            margin:8px 0 5px;
        }
        .beh-kpi-sub{
            color:#71849A;
            font-size:9px;
            line-height:1.35;
        }
        .beh-section{
            margin:18px 0 9px;
            font-size:18px;
            font-weight:830;
            color:#102A43;
            letter-spacing:-.025em;
        }
        .beh-section-sub{
            color:#71849A;
            font-size:9px;
            margin-top:-6px;
            margin-bottom:9px;
        }
        .beh-summary{
            border:1px solid #E4EBF3;
            border-radius:15px;
            background:#FFFFFF;
            padding:13px 15px;
            min-height:136px;
            box-shadow:0 7px 20px rgba(16,42,67,.035);
        }
        .beh-summary-title{
            font-size:11px;
            font-weight:820;
            color:#102A43;
            margin-bottom:9px;
        }
        .beh-row{
            display:flex;
            justify-content:space-between;
            gap:14px;
            padding:5px 0;
            border-bottom:1px solid #F0F3F7;
            font-size:9px;
            color:#65798E;
        }
        .beh-row:last-child{border-bottom:none}
        .beh-row strong{color:#183B5B}
        .beh-good{color:#067647!important}
        .beh-warn{color:#B54708!important}
        .beh-bad{color:#B42318!important}
        .beh-pill{
            display:inline-block;
            border-radius:999px;
            padding:4px 8px;
            background:#EEF6FF;
            color:#245A8D;
            font-size:8px;
            font-weight:800;
        }
        .chart-mini-grid{
            display:grid;
            grid-template-columns:repeat(4,minmax(0,1fr));
            gap:7px;
            margin:8px 0 4px;
        }
        .chart-mini{
            border:1px solid #E7EDF4;
            background:#F8FAFC;
            border-radius:10px;
            padding:8px 9px;
        }
        .chart-mini-label{
            color:#7A8DA1;
            font-size:8px;
            font-weight:750;
            text-transform:uppercase;
            letter-spacing:.03em;
        }
        .chart-mini-value{
            color:#16324F;
            font-size:13px;
            font-weight:850;
            margin-top:2px;
        }
        @media(max-width:950px){
            .chart-mini-grid{grid-template-columns:repeat(2,minmax(0,1fr));}
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="beh-hero">
            <div class="beh-kicker">GEN Control · Analítica operativa</div>
            <div class="beh-title">Comportamiento diario</div>
            <div class="beh-sub">
                Evolución real de gestiones y compromisos, cumplimiento diario y días que requieren atención.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    callcenter = st.session_state.callcenter_df

    if callcenter is None or callcenter.empty:
        st.warning(
            "Carga primero el reporte GEN CallCenter en Cargar reportes."
        )

    else:
        df_cc = callcenter.copy()

        col_fecha = buscar_columna(
            df_cc,
            ["fecha"],
        )
        col_usuario = buscar_columna(
            df_cc,
            ["usuario"],
        )
        col_compromiso = buscar_columna(
            df_cc,
            ["compromiso"],
        )

        if col_fecha is None or col_usuario is None:
            st.error(
                "No se encontraron las columnas Fecha y Usuario "
                "necesarias para el análisis diario."
            )

        else:
            df_cc["Fecha_dt"] = pd.to_datetime(
                df_cc[col_fecha],
                dayfirst=True,
                errors="coerce",
            )
            df_cc = df_cc.dropna(
                subset=["Fecha_dt"]
            )
            df_cc["Fecha_dia"] = (
                df_cc["Fecha_dt"].dt.date
            )

            df_cc["_usuario_norm"] = (
                df_cc[col_usuario]
                .astype(str)
                .apply(normalizar_texto)
            )

            df_cc = df_cc[
                df_cc["_usuario_norm"].isin(
                    list(OPERADORES.keys())
                )
            ].copy()

            if col_compromiso:
                compromiso_txt = (
                    df_cc[col_compromiso]
                    .astype(str)
                    .str.strip()
                )
                df_cc["_tiene_compromiso"] = (
                    df_cc[col_compromiso].notna()
                    & (compromiso_txt != "")
                    & (
                        compromiso_txt.str.lower()
                        != "nan"
                    )
                )
            else:
                df_cc["_tiene_compromiso"] = False

            if df_cc.empty:
                st.warning(
                    "El reporte cargado no contiene registros válidos "
                    "para los operadores configurados."
                )
            else:
                fecha_min = df_cc["Fecha_dia"].min()
                fecha_max = df_cc["Fecha_dia"].max()

                f1, f2 = st.columns([2, 1])

                with f1:
                    rango = st.date_input(
                        "Periodo de análisis",
                        value=(
                            fecha_min,
                            fecha_max,
                        ),
                        min_value=fecha_min,
                        max_value=fecha_max,
                        key="periodo_comportamiento_final",
                    )

                with f2:
                    operador_sel = st.selectbox(
                        "Operador",
                        ["Todos"] + [
                            datos["nombre"]
                            for datos in OPERADORES.values()
                        ],
                        key="operador_comportamiento_final",
                    )

                if (
                    isinstance(rango, tuple)
                    and len(rango) == 2
                ):
                    inicio, fin = rango
                else:
                    inicio = fin = rango

                filtrado = df_cc[
                    (df_cc["Fecha_dia"] >= inicio)
                    & (df_cc["Fecha_dia"] <= fin)
                ].copy()

                usuario_sel = None

                if operador_sel != "Todos":
                    usuario_sel = next(
                        usuario
                        for usuario, datos in OPERADORES.items()
                        if datos["nombre"] == operador_sel
                    )

                    filtrado = filtrado[
                        filtrado["_usuario_norm"]
                        == usuario_sel
                    ].copy()

                diario = (
                    filtrado
                    .groupby("Fecha_dia")
                    .agg(
                        Gestiones=("Fecha_dia", "size"),
                        Compromisos=(
                            "_tiene_compromiso",
                            "sum",
                        ),
                        Operadores_activos=(
                            "_usuario_norm",
                            "nunique",
                        ),
                    )
                    .reset_index()
                    .sort_values("Fecha_dia")
                )

                diario["Compromisos"] = (
                    diario["Compromisos"].astype(int)
                )

                # V5 · Lectura correcta de cumplimiento:
                # no comparar domingos ni el corte parcial de hoy como jornadas completas.
                hoy_bolivia_comp = fecha_local_actual()
                diario["_fecha_ts"] = pd.to_datetime(diario["Fecha_dia"])
                diario["_weekday"] = diario["_fecha_ts"].dt.weekday
                diario["_es_domingo"] = diario["_weekday"].eq(6)
                diario["_es_hoy"] = diario["Fecha_dia"].eq(hoy_bolivia_comp)

                total_gestiones = int(
                    diario["Gestiones"].sum()
                ) if not diario.empty else 0

                total_compromisos = int(
                    diario["Compromisos"].sum()
                ) if not diario.empty else 0

                dias = int(len(diario))

                prom_g = (
                    total_gestiones / dias
                    if dias
                    else 0
                )
                prom_c = (
                    total_compromisos / dias
                    if dias
                    else 0
                )

                conversion = (
                    total_compromisos
                    / total_gestiones
                    * 100
                    if total_gestiones
                    else 0
                )

                # Meta diaria correcta:
                # lunes-sábado tienen meta; domingo no se evalúa.
                # En vista general se usa la cantidad de operadores con registros,
                # pero nunca se asigna meta a domingo.
                if operador_sel == "Todos":
                    diario["Meta_gestiones"] = (
                        diario["Operadores_activos"]
                        * META_DIARIA_GESTIONES
                    )
                    diario["Meta_compromisos"] = (
                        diario["Operadores_activos"]
                        * META_DIARIA_COMPROMISOS
                    )
                else:
                    diario["Meta_gestiones"] = META_DIARIA_GESTIONES
                    diario["Meta_compromisos"] = META_DIARIA_COMPROMISOS

                diario.loc[
                    diario["_es_domingo"],
                    ["Meta_gestiones", "Meta_compromisos"],
                ] = 0

                # Para porcentajes y rankings se consideran únicamente jornadas
                # completas. El día actual se muestra, pero no distorsiona el análisis.
                diario["_jornada_completa"] = (
                    ~diario["_es_domingo"]
                    & ~diario["_es_hoy"]
                )

                diario["Cumplimiento_gestiones"] = (
                    diario["Gestiones"]
                    / diario["Meta_gestiones"].replace(0, pd.NA)
                    * 100
                )
                diario["Cumplimiento_compromisos"] = (
                    diario["Compromisos"]
                    / diario["Meta_compromisos"].replace(0, pd.NA)
                    * 100
                )

                diario["Conversion"] = (
                    diario["Compromisos"]
                    / diario["Gestiones"].replace(0, pd.NA)
                    * 100
                ).fillna(0)

                if not diario.empty:
                    idx_mejor_g = diario["Gestiones"].idxmax()
                    idx_mejor_c = diario["Compromisos"].idxmax()
                    mejor_g = diario.loc[idx_mejor_g]
                    mejor_c = diario.loc[idx_mejor_c]
                else:
                    mejor_g = None
                    mejor_c = None

                # ------------------------------
                # KPIs
                # ------------------------------
                k1, k2, k3, k4, k5 = st.columns(5)

                with k1:
                    st.markdown(
                        f"""
                        <div class="beh-kpi">
                            <div class="beh-kpi-label">📞 Gestiones</div>
                            <div class="beh-kpi-value">{formato_entero(total_gestiones)}</div>
                            <div class="beh-kpi-sub">
                                Promedio diario · <b>{formato_entero(prom_g)}</b>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                with k2:
                    st.markdown(
                        f"""
                        <div class="beh-kpi">
                            <div class="beh-kpi-label">🎯 Compromisos</div>
                            <div class="beh-kpi-value">{formato_entero(total_compromisos)}</div>
                            <div class="beh-kpi-sub">
                                Promedio diario · <b>{formato_entero(prom_c)}</b>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                with k3:
                    fecha_mejor_g = (
                        pd.Timestamp(mejor_g["Fecha_dia"]).strftime("%d/%m/%Y")
                        if mejor_g is not None
                        else "—"
                    )
                    valor_mejor_g = (
                        formato_entero(mejor_g["Gestiones"])
                        if mejor_g is not None
                        else "0"
                    )
                    st.markdown(
                        f"""
                        <div class="beh-kpi">
                            <div class="beh-kpi-label">🏆 Mejor día · Gestiones</div>
                            <div class="beh-kpi-value">{valor_mejor_g}</div>
                            <div class="beh-kpi-sub">{fecha_mejor_g}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                with k4:
                    fecha_mejor_c = (
                        pd.Timestamp(mejor_c["Fecha_dia"]).strftime("%d/%m/%Y")
                        if mejor_c is not None
                        else "—"
                    )
                    valor_mejor_c = (
                        formato_entero(mejor_c["Compromisos"])
                        if mejor_c is not None
                        else "0"
                    )
                    st.markdown(
                        f"""
                        <div class="beh-kpi">
                            <div class="beh-kpi-label">⭐ Mejor día · Compromisos</div>
                            <div class="beh-kpi-value">{valor_mejor_c}</div>
                            <div class="beh-kpi-sub">{fecha_mejor_c}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                with k5:
                    st.markdown(
                        f"""
                        <div class="beh-kpi">
                            <div class="beh-kpi-label">🔄 Conversión</div>
                            <div class="beh-kpi-value">{conversion:.1f}%</div>
                            <div class="beh-kpi-sub">
                                Compromisos / Gestiones
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                if diario.empty:
                    st.info(
                        "No hay información dentro del periodo seleccionado."
                    )

                else:
                    # Cálculos generales usados por gráficos y resumen.
                    diario_eval = diario[
                        diario["_jornada_completa"]
                    ].copy()

                    cumplimiento_g_prom = (
                        diario_eval["Gestiones"].sum()
                        / diario_eval["Meta_gestiones"].sum()
                        * 100
                        if diario_eval["Meta_gestiones"].sum()
                        else 0
                    )

                    cumplimiento_c_prom = (
                        diario_eval["Compromisos"].sum()
                        / diario_eval["Meta_compromisos"].sum()
                        * 100
                        if diario_eval["Meta_compromisos"].sum()
                        else 0
                    )

                    dias_meta_g = int(
                        (
                            diario_eval["Gestiones"]
                            >= diario_eval["Meta_gestiones"]
                        ).sum()
                    )
                    dias_meta_c = int(
                        (
                            diario_eval["Compromisos"]
                            >= diario_eval["Meta_compromisos"]
                        ).sum()
                    )

                    mejores = diario_eval.sort_values(
                        ["Cumplimiento_gestiones", "Gestiones"],
                        ascending=[False, False],
                    ).head(3)

                    peores = diario_eval.sort_values(
                        ["Cumplimiento_gestiones", "Gestiones"],
                        ascending=[True, True],
                    ).head(3)

                    # ------------------------------
                    # GRÁFICOS SEPARADOS
                    # ------------------------------
                    st.markdown(
                        '<div class="beh-section">Evolución diaria</div>',
                        unsafe_allow_html=True,
                    )
                    if bool(diario["_es_hoy"].any()):
                        st.info(
                            "El día de hoy se muestra como avance parcial, pero no se incluye "
                            "en el cumplimiento, brechas, rankings ni tendencias hasta cerrar la jornada."
                        )
                    st.markdown(
                        '<div class="beh-section-sub">Cada indicador utiliza su propia escala para evitar distorsiones.</div>',
                        unsafe_allow_html=True,
                    )

                    # ==================================================
                    # GRÁFICOS EJECUTIVOS
                    # ==================================================
                    graf1, graf2 = st.columns(2)

                    # Métricas útiles para lectura del gráfico
                    dias_evaluados = int(len(diario_eval))
                    dias_sobre_meta_g = int(
                        (diario_eval["Gestiones"] >= diario_eval["Meta_gestiones"]).sum()
                    )
                    dias_bajo_meta_g = dias_evaluados - dias_sobre_meta_g
                    dias_sobre_meta_c = int(
                        (diario_eval["Compromisos"] >= diario_eval["Meta_compromisos"]).sum()
                    )
                    dias_bajo_meta_c = dias_evaluados - dias_sobre_meta_c

                    # Mayor racha consecutiva sobre/bajo meta
                    def mayor_racha(serie_bool, valor_objetivo=True):
                        mejor = 0
                        actual = 0
                        for valor in serie_bool.tolist():
                            if bool(valor) is valor_objetivo:
                                actual += 1
                                mejor = max(mejor, actual)
                            else:
                                actual = 0
                        return mejor

                    racha_sobre_g = mayor_racha(
                        diario_eval["Gestiones"] >= diario_eval["Meta_gestiones"],
                        True,
                    )
                    racha_bajo_g = mayor_racha(
                        diario_eval["Gestiones"] < diario_eval["Meta_gestiones"],
                        True,
                    )
                    racha_sobre_c = mayor_racha(
                        diario_eval["Compromisos"] >= diario_eval["Meta_compromisos"],
                        True,
                    )
                    racha_bajo_c = mayor_racha(
                        diario_eval["Compromisos"] < diario_eval["Meta_compromisos"],
                        True,
                    )

                    chart_base = diario.copy()
                    chart_base["Fecha_plot"] = pd.to_datetime(
                        chart_base["Fecha_dia"]
                    )
                    chart_base["Meta_gestiones_plot"] = (
                        chart_base["Meta_gestiones"]
                        .where(chart_base["_jornada_completa"])
                    )
                    chart_base["Meta_compromisos_plot"] = (
                        chart_base["Meta_compromisos"]
                        .where(chart_base["_jornada_completa"])
                    )

                    def grafico_diario_altair(
                        df_plot,
                        real_col,
                        meta_col,
                        titulo_real,
                        promedio_real,
                    ):
                        base = alt.Chart(df_plot).encode(
                            x=alt.X(
                                "Fecha_plot:T",
                                title=None,
                                axis=alt.Axis(
                                    format="%d %b",
                                    labelAngle=0,
                                    labelOverlap=True,
                                    grid=False,
                                ),
                            )
                        )

                        area = base.mark_area(
                            opacity=0.08,
                            interpolate="monotone",
                        ).encode(
                            y=alt.Y(
                                f"{real_col}:Q",
                                title=None,
                                scale=alt.Scale(zero=True),
                            )
                        )

                        linea_real = base.mark_line(
                            strokeWidth=2.6,
                            interpolate="monotone",
                            point=alt.OverlayMarkDef(
                                size=48,
                                filled=True,
                            ),
                        ).encode(
                            y=alt.Y(
                                f"{real_col}:Q",
                                title=None,
                                scale=alt.Scale(zero=True),
                            ),
                            tooltip=[
                                alt.Tooltip(
                                    "Fecha_plot:T",
                                    title="Fecha",
                                    format="%d/%m/%Y",
                                ),
                                alt.Tooltip(
                                    f"{real_col}:Q",
                                    title=titulo_real,
                                    format=",",
                                ),
                                alt.Tooltip(
                                    f"{meta_col}:Q",
                                    title="Meta",
                                    format=",",
                                ),
                            ],
                        )

                        linea_meta = base.mark_line(
                            strokeDash=[7, 5],
                            strokeWidth=1.8,
                            opacity=0.8,
                        ).encode(
                            y=alt.Y(
                                f"{meta_col}:Q",
                                title=None,
                            )
                        )

                        promedio_df = pd.DataFrame(
                            {"Promedio": [promedio_real]}
                        )
                        linea_prom = alt.Chart(
                            promedio_df
                        ).mark_rule(
                            strokeDash=[2, 4],
                            opacity=0.65,
                        ).encode(
                            y=alt.Y(
                                "Promedio:Q",
                                title=None,
                            )
                        )

                        puntos_destacados = base.transform_filter(
                            alt.datum[real_col] >= alt.datum[meta_col]
                        ).mark_point(
                            size=70,
                            filled=True,
                        ).encode(
                            y=alt.Y(
                                f"{real_col}:Q",
                                title=None,
                            )
                        )

                        return (
                            area
                            + linea_real
                            + linea_meta
                            + linea_prom
                            + puntos_destacados
                        ).properties(
                            height=285
                        ).configure_axis(
                            labelFontSize=10,
                            titleFontSize=10,
                            labelColor="#65798E",
                            gridColor="#EDF1F5",
                        ).configure_view(
                            strokeOpacity=0
                        )

                    with graf1:
                        with st.container(border=True):
                            st.markdown("#### 📞 Gestiones diarias")
                            st.caption(
                                f"Promedio {formato_entero(prom_g)} · "
                                f"Meta promedio {formato_entero(diario['Meta_gestiones'].mean())} · "
                                f"Cumplimiento {cumplimiento_g_prom:.0f}%"
                            )

                            st.markdown(
                                f"""
                                <div class="chart-mini-grid">
                                    <div class="chart-mini">
                                        <div class="chart-mini-label">Días sobre meta</div>
                                        <div class="chart-mini-value">{dias_sobre_meta_g} / {dias_evaluados}</div>
                                    </div>
                                    <div class="chart-mini">
                                        <div class="chart-mini-label">Días bajo meta</div>
                                        <div class="chart-mini-value">{dias_bajo_meta_g} / {dias_evaluados}</div>
                                    </div>
                                    <div class="chart-mini">
                                        <div class="chart-mini-label">Mejor racha</div>
                                        <div class="chart-mini-value">{racha_sobre_g} días</div>
                                    </div>
                                    <div class="chart-mini">
                                        <div class="chart-mini-label">Mayor brecha</div>
                                        <div class="chart-mini-value">{racha_bajo_g} días</div>
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

                            chart_g_final = grafico_diario_altair(
                                chart_base,
                                "Gestiones",
                                "Meta_gestiones_plot",
                                "Gestiones",
                                prom_g,
                            )
                            st.altair_chart(
                                chart_g_final,
                                use_container_width=True,
                            )

                            st.caption(
                                "Línea continua: real · línea segmentada: meta · "
                                "línea punteada: promedio · puntos destacados: días que alcanzaron meta."
                            )

                    with graf2:
                        with st.container(border=True):
                            st.markdown("#### 🎯 Compromisos diarios")
                            st.caption(
                                f"Promedio {formato_entero(prom_c)} · "
                                f"Meta promedio {formato_entero(diario['Meta_compromisos'].mean())} · "
                                f"Cumplimiento {cumplimiento_c_prom:.0f}%"
                            )

                            st.markdown(
                                f"""
                                <div class="chart-mini-grid">
                                    <div class="chart-mini">
                                        <div class="chart-mini-label">Días sobre meta</div>
                                        <div class="chart-mini-value">{dias_sobre_meta_c} / {dias_evaluados}</div>
                                    </div>
                                    <div class="chart-mini">
                                        <div class="chart-mini-label">Días bajo meta</div>
                                        <div class="chart-mini-value">{dias_bajo_meta_c} / {dias_evaluados}</div>
                                    </div>
                                    <div class="chart-mini">
                                        <div class="chart-mini-label">Mejor racha</div>
                                        <div class="chart-mini-value">{racha_sobre_c} días</div>
                                    </div>
                                    <div class="chart-mini">
                                        <div class="chart-mini-label">Mayor brecha</div>
                                        <div class="chart-mini-value">{racha_bajo_c} días</div>
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

                            chart_c_final = grafico_diario_altair(
                                chart_base,
                                "Compromisos",
                                "Meta_compromisos_plot",
                                "Compromisos",
                                prom_c,
                            )
                            st.altair_chart(
                                chart_c_final,
                                use_container_width=True,
                            )

                            st.caption(
                                "Línea continua: real · línea segmentada: meta · "
                                "línea punteada: promedio · puntos destacados: días que alcanzaron meta."
                            )

                    # ------------------------------
                    # RESUMEN EJECUTIVO DEL PERIODO
                    # ------------------------------
                    meta_g_total = int(
                        diario_eval["Meta_gestiones"].sum()
                    )
                    meta_c_total = int(
                        diario_eval["Meta_compromisos"].sum()
                    )

                    gestiones_eval = int(diario_eval["Gestiones"].sum())
                    compromisos_eval = int(diario_eval["Compromisos"].sum())

                    brecha_g_total = (
                        gestiones_eval - meta_g_total
                    )
                    brecha_c_total = (
                        compromisos_eval - meta_c_total
                    )

                    tendencia_g = 0.0
                    tendencia_c = 0.0
                    if len(diario_eval) >= 4:
                        mitad = max(len(diario_eval) // 2, 1)
                        prom_g_1 = diario_eval.iloc[:mitad]["Gestiones"].mean()
                        prom_g_2 = diario_eval.iloc[mitad:]["Gestiones"].mean()
                        prom_c_1 = diario_eval.iloc[:mitad]["Compromisos"].mean()
                        prom_c_2 = diario_eval.iloc[mitad:]["Compromisos"].mean()

                        if prom_g_1:
                            tendencia_g = (
                                (prom_g_2 - prom_g_1)
                                / prom_g_1
                                * 100
                            )
                        if prom_c_1:
                            tendencia_c = (
                                (prom_c_2 - prom_c_1)
                                / prom_c_1
                                * 100
                            )

                    promedio_meta_g = (
                        diario_eval["Meta_gestiones"].mean()
                        if dias
                        else 0
                    )
                    promedio_meta_c = (
                        diario_eval["Meta_compromisos"].mean()
                        if dias
                        else 0
                    )

                    st.markdown(
                        '<div class="beh-section">Lectura ejecutiva del periodo</div>',
                        unsafe_allow_html=True,
                    )
                    st.caption(
                        "Meta acumulada, brecha, tendencia y consistencia diaria."
                    )

                    e1, e2, e3, e4 = st.columns(4)

                    with e1:
                        st.metric(
                            "Meta acumulada · Gestiones",
                            formato_entero(meta_g_total),
                            f"{brecha_g_total:+,} de brecha".replace(",", "."),
                        )

                    with e2:
                        st.metric(
                            "Meta acumulada · Compromisos",
                            formato_entero(meta_c_total),
                            f"{brecha_c_total:+,} de brecha".replace(",", "."),
                        )

                    with e3:
                        st.metric(
                            "Tendencia · Gestiones",
                            f"{tendencia_g:+.1f}%",
                            "2ª mitad vs 1ª mitad",
                        )

                    with e4:
                        st.metric(
                            "Tendencia · Compromisos",
                            f"{tendencia_c:+.1f}%",
                            "2ª mitad vs 1ª mitad",
                        )

                    r1, r2, r3 = st.columns([1.05, 1.35, 1.35])

                    with r1:
                        with st.container(border=True):
                            st.markdown("#### 📌 Resumen del periodo")
                            st.write(f"**Días con información:** {dias}")
                            st.write(
                                f"**Cumplimiento gestiones:** {cumplimiento_g_prom:.0f}%"
                            )
                            st.write(
                                f"**Cumplimiento compromisos:** {cumplimiento_c_prom:.0f}%"
                            )
                            st.write(
                                f"**Días con meta de gestiones:** {dias_meta_g} / {dias}"
                            )
                            st.write(
                                f"**Días con meta de compromisos:** {dias_meta_c} / {dias}"
                            )
                            st.caption(
                                f"Meta diaria promedio observada: "
                                f"{formato_entero(promedio_meta_g)} gestiones · "
                                f"{formato_entero(promedio_meta_c)} compromisos."
                            )

                    with r2:
                        with st.container(border=True):
                            st.markdown("#### 🏆 Días con mayor desempeño")
                            for pos, (_, fila_r) in enumerate(
                                mejores.iterrows(),
                                start=1,
                            ):
                                fecha_txt = pd.Timestamp(
                                    fila_r["Fecha_dia"]
                                ).strftime("%d/%m/%Y")
                                st.markdown(
                                    f"**{pos}. {fecha_txt}**  \n"
                                    f"📞 {formato_entero(fila_r['Gestiones'])} gestiones · "
                                    f"🎯 {formato_entero(fila_r['Compromisos'])} compromisos · "
                                    f"**{fila_r['Cumplimiento_gestiones']:.0f}%** de meta"
                                )

                    with r3:
                        with st.container(border=True):
                            st.markdown("#### ⚠️ Días con menor desempeño")
                            for pos, (_, fila_r) in enumerate(
                                peores.iterrows(),
                                start=1,
                            ):
                                fecha_txt = pd.Timestamp(
                                    fila_r["Fecha_dia"]
                                ).strftime("%d/%m/%Y")
                                brecha_dia = int(
                                    fila_r["Gestiones"]
                                    - fila_r["Meta_gestiones"]
                                )
                                st.markdown(
                                    f"**{pos}. {fecha_txt}**  \n"
                                    f"📞 {formato_entero(fila_r['Gestiones'])} gestiones · "
                                    f"🎯 {formato_entero(fila_r['Compromisos'])} compromisos · "
                                    f"brecha **{brecha_dia:+d}**"
                                )

                    # ------------------------------
                    # INSIGHTS AUTOMÁTICOS
                    # ------------------------------
                    st.markdown(
                        '<div class="beh-section">Qué está pasando</div>',
                        unsafe_allow_html=True,
                    )

                    dias_bajos_g = int(
                        (
                            diario["Cumplimiento_gestiones"] < 100
                        ).sum()
                    )
                    dias_bajos_c = int(
                        (
                            diario["Cumplimiento_compromisos"] < 100
                        ).sum()
                    )

                    mejor_fecha_txt = pd.Timestamp(
                        mejor_g["Fecha_dia"]
                    ).strftime("%d/%m/%Y")

                    peor_fila = peores.iloc[0]
                    peor_fecha_txt = pd.Timestamp(
                        peor_fila["Fecha_dia"]
                    ).strftime("%d/%m/%Y")

                    i1, i2, i3 = st.columns(3)

                    with i1:
                        if brecha_g_total >= 0:
                            st.success(
                                f"Gestiones están {formato_entero(abs(brecha_g_total))} "
                                "por encima de la meta acumulada del periodo."
                            )
                        else:
                            st.warning(
                                f"Gestiones están {formato_entero(abs(brecha_g_total))} "
                                "por debajo de la meta acumulada del periodo."
                            )

                    with i2:
                        st.info(
                            f"{dias_bajos_g} de {dias} días quedaron por debajo de "
                            f"la meta de gestiones y {dias_bajos_c} de {dias} "
                            "por debajo de compromisos."
                        )

                    with i3:
                        st.info(
                            f"Mejor día: {mejor_fecha_txt}. "
                            f"Día que más atención requiere: {peor_fecha_txt}."
                        )

                    # ------------------------------
                    # DETALLE POR FECHA
                    # ------------------------------
                    st.markdown(
                        '<div class="beh-section">Detalle por fecha</div>',
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        '<div class="beh-section-sub">Lectura diaria con meta, cumplimiento y conversión.</div>',
                        unsafe_allow_html=True,
                    )

                    nombres_dia = {
                        0: "Lunes",
                        1: "Martes",
                        2: "Miércoles",
                        3: "Jueves",
                        4: "Viernes",
                        5: "Sábado",
                        6: "Domingo",
                    }

                    detalle = diario.copy()
                    detalle["Fecha"] = pd.to_datetime(
                        detalle["Fecha_dia"]
                    )
                    detalle["Día"] = (
                        detalle["Fecha"]
                        .dt.weekday
                        .map(nombres_dia)
                    )
                    detalle["Estado día"] = detalle.apply(
                        lambda r: (
                            "En curso"
                            if bool(r["_es_hoy"])
                            else (
                                "No laborable"
                                if bool(r["_es_domingo"])
                                else "Cerrado"
                            )
                        ),
                        axis=1,
                    )
                    detalle["Fecha"] = (
                        detalle["Fecha"]
                        .dt.strftime("%d/%m/%Y")
                    )
                    detalle["% Gestiones"] = (
                        detalle["Cumplimiento_gestiones"]
                        / 100
                    )
                    detalle["% Compromisos"] = (
                        detalle["Cumplimiento_compromisos"]
                        / 100
                    )
                    detalle["Conversión"] = (
                        detalle["Conversion"]
                        / 100
                    )

                    detalle["Brecha gestiones"] = (
                        detalle["Gestiones"]
                        - detalle["Meta_gestiones"]
                    )
                    detalle["Brecha compromisos"] = (
                        detalle["Compromisos"]
                        - detalle["Meta_compromisos"]
                    )

                    detalle_tabla = detalle[
                        [
                            "Fecha",
                            "Día",
                            "Estado día",
                            "Gestiones",
                            "Meta_gestiones",
                            "% Gestiones",
                            "Brecha gestiones",
                            "Compromisos",
                            "Meta_compromisos",
                            "% Compromisos",
                            "Brecha compromisos",
                            "Conversión",
                        ]
                    ].rename(
                        columns={
                            "Meta_gestiones": "Meta gestiones",
                            "Meta_compromisos": "Meta compromisos",
                        }
                    )

                    st.dataframe(
                        detalle_tabla.sort_values(
                            "Fecha",
                            ascending=False,
                        ),
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Fecha": st.column_config.TextColumn(
                                "Fecha",
                                width="small",
                            ),
                            "Día": st.column_config.TextColumn(
                                "Día",
                                width="small",
                            ),
                            "Gestiones": st.column_config.NumberColumn(
                                "Gestiones",
                                format="%d",
                            ),
                            "Meta gestiones": st.column_config.NumberColumn(
                                "Meta gestiones",
                                format="%d",
                            ),
                            "% Gestiones": st.column_config.ProgressColumn(
                                "% Gestiones",
                                min_value=0,
                                max_value=1,
                                format="%.0f%%",
                            ),
                            "Brecha gestiones": st.column_config.NumberColumn(
                                "Brecha gestiones",
                                format="%+d",
                            ),
                            "Compromisos": st.column_config.NumberColumn(
                                "Compromisos",
                                format="%d",
                            ),
                            "Meta compromisos": st.column_config.NumberColumn(
                                "Meta compromisos",
                                format="%d",
                            ),
                            "% Compromisos": st.column_config.ProgressColumn(
                                "% Compromisos",
                                min_value=0,
                                max_value=1,
                                format="%.0f%%",
                            ),
                            "Brecha compromisos": st.column_config.NumberColumn(
                                "Brecha compromisos",
                                format="%+d",
                            ),
                            "Conversión": st.column_config.NumberColumn(
                                "Conversión",
                                format="%.1f%%",
                            ),
                        },
                    )

                    # ------------------------------
                    # COMPARACIÓN ENTRE OPERADORES
                    # ------------------------------
                    if operador_sel == "Todos":
                        with st.expander(
                            "👥 Ver comparación acumulada entre operadores",
                            expanded=False,
                        ):
                            comp_op = (
                                filtrado
                                .groupby("_usuario_norm")
                                .agg(
                                    Gestiones=("Fecha_dia", "size"),
                                    Compromisos=(
                                        "_tiene_compromiso",
                                        "sum",
                                    ),
                                    Dias=("Fecha_dia", "nunique"),
                                )
                                .reset_index()
                            )

                            comp_op["Operador"] = comp_op[
                                "_usuario_norm"
                            ].map(
                                {
                                    u: d["nombre"]
                                    for u, d in OPERADORES.items()
                                }
                            )

                            comp_op["Prom. gestiones"] = (
                                comp_op["Gestiones"]
                                / comp_op["Dias"].replace(0, pd.NA)
                            ).fillna(0).round(1)

                            comp_op["Prom. compromisos"] = (
                                comp_op["Compromisos"]
                                / comp_op["Dias"].replace(0, pd.NA)
                            ).fillna(0).round(1)

                            comp_op["Conversión"] = (
                                comp_op["Compromisos"]
                                / comp_op["Gestiones"].replace(0, pd.NA)
                            ).fillna(0)

                            comp_op = controles_ordenamiento(
                                comp_op,
                                [
                                    "Gestiones",
                                    "Compromisos",
                                    "Prom. gestiones",
                                    "Operador",
                                ],
                                key_prefix="comparacion_diaria_final",
                                columna_default="Gestiones",
                                descendente_default=True,
                                etiquetas={
                                    "Gestiones": "Gestiones",
                                    "Compromisos": "Compromisos",
                                    "Prom. gestiones": "Promedio diario",
                                    "Operador": "Operador (A-Z / Z-A)",
                                },
                            )

                            st.dataframe(
                                comp_op[
                                    [
                                        "Operador",
                                        "Gestiones",
                                        "Compromisos",
                                        "Prom. gestiones",
                                        "Prom. compromisos",
                                        "Conversión",
                                    ]
                                ],
                                use_container_width=True,
                                hide_index=True,
                                column_config={
                                    "Conversión": st.column_config.NumberColumn(
                                        "Conversión",
                                        format="%.1f%%",
                                    ),
                                },
                            )


# =========================================================
# MENSAJES DIARIOS
# =========================================================

elif menu == "✉️ Mensajes diarios":

    resultado = st.session_state.resultado_operadores
    jornadas_info = jornadas_configuradas()

    st.markdown("""
    <style>
    .daily-panel{padding:16px 18px!important;border-radius:14px!important;margin-bottom:12px!important;background:linear-gradient(135deg,#f8fbff,#eef5ff)!important;border:1px solid #dbe7f5!important}
    .daily-panel-title{font-size:23px!important;font-weight:800!important;color:#102a43!important}
    .daily-panel-sub{font-size:12px!important;color:#627d98!important;margin-top:2px!important}
    .data-ready-v86{border:1px solid #dbe5ef;border-radius:13px;padding:12px 14px;margin:6px 0 14px;background:#fff}
    .data-ready-head-v86{font-size:14px;font-weight:800;color:#102a43;margin-bottom:9px}
    .data-grid-v86{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:7px}
    .data-item-v86{background:#f7f9fc;border:1px solid #e7edf4;border-radius:9px;padding:8px 9px}
    .data-label-v86{font-size:9px;font-weight:800;color:#829ab1;text-transform:uppercase;letter-spacing:.35px}
    .data-value-v86{font-size:12px;font-weight:700;color:#243b53;margin-top:2px}
    div[data-testid="stMetric"]{background:#fff;border:1px solid #e4eaf1;padding:8px 10px;border-radius:11px}
    div[data-testid="stMetric"] label{font-size:10px!important;color:#627d98!important}
    div[data-testid="stMetricValue"]{font-size:19px!important;font-weight:800!important}
    div[data-testid="stVerticalBlockBorderWrapper"]{border-color:#e1e8f0!important;border-radius:13px!important}
    div[data-testid="stButton"] button{border-radius:9px!important;font-weight:700!important}
    @media(max-width:900px){.data-grid-v86{grid-template-columns:repeat(2,minmax(0,1fr))}}
    </style>
    """, unsafe_allow_html=True)
    st.markdown("""
    <style>
    /* V88 · Tarjetas con semáforo y mejor jerarquía */
    .op-head-v74{align-items:center!important;margin-bottom:8px!important}
    .op-name-v74{font-size:17px!important;line-height:1.12!important;font-weight:800!important}
    .op-contact-v74{font-size:10px!important;color:#7b8794!important;margin-top:4px!important}
    .status-v74{font-size:10px!important;padding:5px 9px!important;border:1px solid transparent!important}
    .v74-red{background:#fff0f1!important;color:#b42318!important;border-color:#fecaca!important}
    .v74-orange{background:#fff7ed!important;color:#b54708!important;border-color:#fed7aa!important}
    .v74-green{background:#ecfdf3!important;color:#067647!important;border-color:#abefc6!important}
    .v74-gray{background:#f3f4f6!important;color:#667085!important;border-color:#e5e7eb!important}
    .schedule-v74{font-size:10px!important;padding:6px 8px!important;background:#f9fbfd!important}
    .kicker-v74{font-size:10px!important;color:#667085!important;margin:7px 0 6px!important}
    .action-v74{font-size:11px!important;padding:8px 10px!important;margin:8px 0!important}
    .monthly-v74{font-size:10px!important;padding-top:7px!important;margin-top:8px!important}
    .monthly-v74 span:first-child{font-weight:800!important;color:#667085!important}
    [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMetricValue"]{
        font-size:24px!important;line-height:1.05!important
    }
    [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMetricLabel"] p{
        font-size:11px!important;font-weight:700!important
    }
    [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMetricDelta"]{
        font-size:11px!important
    }
    [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stCaptionContainer"] p{
        font-size:10px!important;color:#667085!important
    }
    </style>
    """, unsafe_allow_html=True)



    st.markdown("""
    <style>
    /* V92 · Rediseño de Mensajes diarios */
    .daily-panel{
        padding:14px 18px!important;
        border-radius:14px!important;
        margin:0 0 12px 0!important;
        background:#f7faff!important;
        border:1px solid #dce7f3!important;
        box-shadow:none!important;
    }
    .daily-panel-title{font-size:22px!important}
    .daily-panel-sub{font-size:11px!important}

    .data-ready-v86{
        padding:10px 12px!important;
        margin:0 0 10px 0!important;
        border-radius:12px!important;
        background:#ffffff!important;
    }
    .data-ready-head-v86{
        font-size:12px!important;
        margin-bottom:7px!important;
    }
    .data-item-v86{
        padding:7px 9px!important;
        min-height:48px!important;
    }
    .data-label-v86{font-size:8px!important}
    .data-value-v86{font-size:11px!important}

    .control-v92{
        margin:8px 0 12px;
        border:1px solid #dfe7ef;
        border-radius:13px;
        padding:11px 13px;
        background:#fff;
    }
    .control-head-v92{
        display:flex;
        align-items:center;
        justify-content:space-between;
        gap:12px;
        margin-bottom:9px;
    }
    .control-head-v92 b{
        display:block;
        font-size:14px;
        color:#16324f;
    }
    .control-head-v92 span{
        display:block;
        margin-top:1px;
        font-size:9px;
        color:#829ab1;
    }
    .control-time-v92{
        font-size:18px;
        line-height:1;
        font-weight:800;
        color:#16324f;
    }
    .control-grid-v92{
        display:grid;
        grid-template-columns:repeat(5,minmax(0,1fr));
        gap:7px;
    }
    .control-grid-v92>div{
        background:#f8fafc;
        border:1px solid #edf1f5;
        border-radius:9px;
        padding:7px 9px;
    }
    .control-grid-v92 span{
        display:block;
        font-size:8px;
        color:#829ab1;
        text-transform:uppercase;
        letter-spacing:.25px;
    }
    .control-grid-v92 b{
        display:block;
        font-size:13px;
        margin-top:2px;
        color:#243b53;
    }

    /* Expander usados como herramientas secundarias */
    div[data-testid="stExpander"]{
        border:1px solid #e4eaf1!important;
        border-radius:11px!important;
        background:#fff!important;
    }
    div[data-testid="stExpander"] summary{
        font-weight:700!important;
        font-size:12px!important;
    }

    /* Quitar sensación de formulario gigante */
    div[data-testid="stTextInput"] input,
    div[data-testid="stSelectbox"]>div>div{
        min-height:38px!important;
    }

    @media(max-width:1000px){
        .control-grid-v92{grid-template-columns:repeat(3,minmax(0,1fr))}
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <style>
    /* V93: la información técnica se conserva, pero no ocupa media pantalla */
    .data-ready-v86{display:none!important}
    .control-v92{display:none!important}
    .daily-panel{display:none!important}
    .legend-v71{margin-top:8px!important}
    </style>
    """, unsafe_allow_html=True)


    st.markdown(
        """
        <div style="
            background:linear-gradient(120deg,#102A43,#164A6A);
            border-radius:18px;padding:18px 20px;margin:2px 0 14px;
            box-shadow:0 14px 32px rgba(16,42,67,.13);
        ">
            <div style="
                display:inline-block;padding:4px 8px;border-radius:999px;
                background:rgba(255,255,255,.10);color:#BFD7E8;
                font-size:8px;font-weight:800;letter-spacing:.06em;
                text-transform:uppercase;margin-bottom:8px;
            ">Telegram · Seguimiento operativo</div>
            <div style="font-size:23px;font-weight:850;color:#fff;letter-spacing:-.03em;">
                Mensajes diarios
            </div>
            <div style="font-size:10px;color:#BED0E0;margin-top:3px;">
                Seguimiento individual, mensajes libres y comunicación al grupo.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if resultado is None:
        st.warning("Primero carga el reporte de Promesas de Pago.")
    else:
        operadores_db = cargar_operadores_supabase()
        datos_contacto = {}
        if operadores_db is not None and not operadores_db.empty:
            for _, op in operadores_db.iterrows():
                datos_contacto[str(op["usuario"])] = {
                    "correo": str(op.get("correo") or ""),
                    "telefono": str(op.get("telefono") or ""),
                    "telegram_chat_id": str(op.get("telegram_chat_id") or ""),
                    "nombre_mensaje": str(op.get("nombre_mensaje") or op.get("nombre") or ""),
                }

        validacion_v86 = estado_datos_para_seguimiento(resultado)
        icono_v86 = {"verde":"🟢","naranja":"🟠","rojo":"🔴"}[validacion_v86["nivel"]]

        promesas_txt_v86 = "Disponible" if validacion_v86["promesas_ok"] else "No cargado"
        if validacion_v86["promesas_cargado"] is not None:
            promesas_txt_v86 += " · " + validacion_v86["promesas_cargado"].strftime("%H:%M")

        if validacion_v86["call_ok"]:
            corte_v86 = validacion_v86["corte"]
            call_txt_v86 = f"Corte {corte_v86.strftime('%H:%M')}" if corte_v86 else "Cargado"
            if validacion_v86["minutos_call"] is not None:
                call_txt_v86 += f" · hace {validacion_v86['minutos_call']} min"
        else:
            call_txt_v86 = "No cargado"

        operadores_txt_v86 = f"{validacion_v86['usuarios_detectados']}/{CANTIDAD_OPERADORES} identificados"
        rec_txt_v86 = "Disponible" if validacion_v86["recuperacion_ok"] else "No disponible"

        html_v86 = (
            '<div class="data-ready-v86">'
            f'<div class="data-ready-head-v86">{icono_v86} {validacion_v86["titulo"]}</div>'
            '<div class="data-grid-v86">'
            f'<div class="data-item-v86"><div class="data-label-v86">Promesas</div><div class="data-value-v86">{promesas_txt_v86}</div></div>'
            f'<div class="data-item-v86"><div class="data-label-v86">CallCenter</div><div class="data-value-v86">{call_txt_v86}</div></div>'
            f'<div class="data-item-v86"><div class="data-label-v86">Operadores</div><div class="data-value-v86">{operadores_txt_v86}</div></div>'
            f'<div class="data-item-v86"><div class="data-label-v86">Recuperación</div><div class="data-value-v86">{rec_txt_v86}</div></div>'
            '</div></div>'
        )
        st.markdown(html_v86, unsafe_allow_html=True)

        if validacion_v86["razones_bloqueo"]:
            st.error("No se habilitará el envío masivo hasta corregir: " + " · ".join(validacion_v86["razones_bloqueo"]))
        elif validacion_v86["advertencias"]:
            st.warning("Revisión recomendada: " + " · ".join(validacion_v86["advertencias"]))

        # -------------------------------------------------
        # PANEL COMPACTO DE CONTROL — V92
        # -------------------------------------------------
        ahora_seguimiento = ahora_bolivia()
        info_corte = informacion_corte_recomendado(
            ahora_seguimiento
        )

        usuarios_resultado = (
            resultado["Usuario"]
            .astype(str)
            .tolist()
        )

        usuarios_turno_actual = [
            usuario_ctrl
            for usuario_ctrl in usuarios_resultado
            if (
                operador_en_turno(
                    usuario_ctrl,
                    ahora_seguimiento,
                )
                or st.session_state.get(
                    "permitir_envio_fuera_turno",
                    False,
                )
            )
        ]

        recientes_ctrl, listos_ctrl = (
            resumen_frecuencia_seguimiento(
                usuarios_turno_actual,
                ahora_seguimiento,
            )
        )

        proximo_corte_v92 = (
            info_corte["hora"]
            if info_corte["estado"] != "finalizado"
            else "Finalizado"
        )

        completadas_v92 = len(
            [
                d
                for d in jornadas_info["dias"]
                if d < fecha_local_actual()
            ]
        )

        html_control_v92 = (
            '<div class="control-v92">'
            '<div class="control-head-v92">'
            '<div><b>📊 Control del seguimiento</b>'
            '<span>Estado operativo del momento</span></div>'
            f'<div class="control-time-v92">{ahora_seguimiento.strftime("%H:%M")}</div>'
            '</div>'
            '<div class="control-grid-v92">'
            f'<div><span>Próximo corte</span><b>{proximo_corte_v92}</b></div>'
            f'<div><span>En turno</span><b>{len(usuarios_turno_actual)}/{len(resultado)}</b></div>'
            f'<div><span>Seguimiento &lt;60 min</span><b>{len(recientes_ctrl)}</b></div>'
            f'<div><span>Esperado mes</span><b>{formato_porcentaje(jornadas_info["esperado_pct"])}</b></div>'
            f'<div><span>Jornadas</span><b>{completadas_v92}/{jornadas_info["total"]}</b></div>'
            '</div>'
            '</div>'
        )
        st.markdown(
            html_control_v92,
            unsafe_allow_html=True,
        )

        if recientes_ctrl:
            nombres_recientes_v92 = []
            for usuario_rec, minutos_rec in recientes_ctrl:
                nombre_rec = OPERADORES.get(
                    usuario_rec,
                    {},
                ).get(
                    "nombre_mensaje",
                    usuario_rec,
                )
                nombres_recientes_v92.append(
                    f"{nombre_rec} ({minutos_rec} min)"
                )

            with st.expander(
                f"⚠️ {len(recientes_ctrl)} seguimiento(s) reciente(s)",
                expanded=False,
            ):
                st.caption(
                    " · ".join(nombres_recientes_v92)
                    + ". Puedes reenviar si es necesario; GEN Control solo avisa para evitar mensajes demasiado seguidos."
                )


        ahora_v93 = ahora_bolivia()
        corte_v93 = obtener_corte_callcenter(
            st.session_state.get("callcenter_df")
        )

        if corte_v93 is not None and hasattr(
            corte_v93,
            "to_pydatetime",
        ):
            corte_v93 = corte_v93.to_pydatetime()

        corte_txt_v93 = (
            corte_v93.strftime("%H:%M")
            if corte_v93 is not None
            else "--:--"
        )

        usuarios_v93 = resultado["Usuario"].astype(str).tolist()
        en_turno_v93 = sum(
            1
            for usuario_v93 in usuarios_v93
            if operador_en_turno(
                usuario_v93,
                ahora_v93,
            )
        )

        enviados_v93 = sum(
            1
            for usuario_v93 in usuarios_v93
            if envio_ya_realizado_hoy(
                usuario_v93,
                "seguimiento",
            )
        )

        proximo_v93 = informacion_corte_recomendado(
            ahora_v93
        )
        proximo_txt_v93 = (
            proximo_v93.get("hora", "--:--")
            if proximo_v93.get("estado") != "finalizado"
            else "Cierre"
        )

        st.markdown(
            '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin:6px 0 12px;">'
            f'<div style="border:1px solid #e4e9ef;border-radius:10px;padding:9px 11px;"><span style="font-size:8px;color:#8291a3;text-transform:uppercase;">Corte cargado</span><b style="display:block;font-size:16px;color:#1d354d;">{corte_txt_v93}</b></div>'
            f'<div style="border:1px solid #e4e9ef;border-radius:10px;padding:9px 11px;"><span style="font-size:8px;color:#8291a3;text-transform:uppercase;">En turno</span><b style="display:block;font-size:16px;color:#1d354d;">{en_turno_v93}/{len(usuarios_v93)}</b></div>'
            f'<div style="border:1px solid #e4e9ef;border-radius:10px;padding:9px 11px;"><span style="font-size:8px;color:#8291a3;text-transform:uppercase;">Seguimiento hoy</span><b style="display:block;font-size:16px;color:#1d354d;">{enviados_v93}/{len(usuarios_v93)}</b></div>'
            f'<div style="border:1px solid #e4e9ef;border-radius:10px;padding:9px 11px;"><span style="font-size:8px;color:#8291a3;text-transform:uppercase;">Próximo corte</span><b style="display:block;font-size:16px;color:#1d354d;">{proximo_txt_v93}</b></div>'
            '</div>',
            unsafe_allow_html=True,
        )

        st.caption(
            "Los reportes y la hora del último seguimiento quedan guardados en Supabase y se restauran al actualizar la app."
        )

        with st.expander("📣 Grupo y recuperación", expanded=False):
            # -------------------------------------------------
            # AVANCE GENERAL DE RECUPERACIÓN
            # -------------------------------------------------
            meta_individual = float(st.session_state.meta_recuperacion_cfg)
            tabla_general = resultado[["Operador", "Recuperación acumulada", "% Recuperación"]].copy()
            tabla_general["Meta"] = meta_individual
            tabla_general["Falta"] = (meta_individual - tabla_general["Recuperación acumulada"]).clip(lower=0)
            tabla_general = tabla_general.sort_values("% Recuperación", ascending=False, kind="stable").reset_index(drop=True)

            total_recuperacion_equipo = float(tabla_general["Recuperación acumulada"].sum())
            meta_equipo = meta_individual * CANTIDAD_OPERADORES
            pct_equipo = total_recuperacion_equipo / meta_equipo * 100 if meta_equipo else 0
            falta_equipo = max(meta_equipo - total_recuperacion_equipo, 0)

            st.markdown(
                '<span class="section-chip">RECUPERACIÓN DEL EQUIPO</span>',
                unsafe_allow_html=True,
            )
            st.markdown("### Avance general")
            g1, g2, g3 = st.columns(3)
            g1.metric("Recuperación del equipo", formato_usd(total_recuperacion_equipo))
            g2.metric("Cumplimiento", formato_porcentaje(pct_equipo))
            g3.metric("Brecha total", formato_usd(falta_equipo))

            mensaje_general = (
                f"📊 AVANCE DE RECUPERACIÓN – {fecha_local_actual().strftime('%d/%m/%Y')}\n\n"
                f"Buenos días, equipo. Comparto el avance acumulado de recuperación a la fecha, "
                f"considerando una meta mensual de {formato_usd(meta_individual)} por operador.\n\n"
                "Revisemos nuestro porcentaje de cumplimiento y la brecha pendiente. "
                "Mantengamos el enfoque en recuperación para continuar avanzando hacia la meta mensual. 💪"
            )

            with st.expander("Ver mensaje general y tabla de recuperación", expanded=False):
                st.text_area("Mensaje general", value=mensaje_general, height=135, key="mensaje_general_recuperacion_v22", label_visibility="collapsed")
                tabla_compartir = pd.DataFrame({
                    "Operador": tabla_general["Operador"],
                    "Recuperación": tabla_general["Recuperación acumulada"].apply(formato_usd),
                    "Cumplimiento": tabla_general["% Recuperación"].apply(formato_porcentaje),
                    "Falta": tabla_general["Falta"].apply(formato_usd),
                })
                st.dataframe(tabla_compartir, use_container_width=True, hide_index=True)

                imagen_recuperacion = generar_imagen_avance_recuperacion(tabla_general, fecha_local_actual(), meta_individual)
                st.image(imagen_recuperacion, caption="Imagen lista para correo o Telegram", width=760)
                bi1, bi2, bi3 = st.columns(3)
                with bi1:
                    mostrar_boton_copiar_imagen(imagen_recuperacion)
                with bi2:
                    st.download_button("🖼️ Descargar imagen", data=imagen_recuperacion.getvalue(), file_name=f"avance_recuperacion_{fecha_local_actual().isoformat()}.png", mime="image/png", use_container_width=True)
                with bi3:
                    mailto_general = f"mailto:cobranza@gestiona.bo?subject={quote('Avance de recuperación')}&body={quote(mensaje_general)}"
                    st.link_button("✉️ Correo general", mailto_general, use_container_width=True)

            st.divider()

            # -------------------------------------------------
            # ENCABEZADO + CONTROL DEL DÍA — V66
            # -------------------------------------------------
            corte_callcenter_v68 = obtener_corte_callcenter(
                st.session_state.callcenter_df
            )

            ahora_v66 = (
                corte_callcenter_v68.to_pydatetime()
                if hasattr(
                    corte_callcenter_v68,
                    "to_pydatetime",
                )
                else corte_callcenter_v68
            )

            if ahora_v66 is None:
                ahora_v66 = datetime.now(
                    ZoneInfo("America/La_Paz")
                )

            saludo_v66, emoji_v66 = saludo_segun_hora()

            st.markdown(
                textwrap.dedent(f"""
                <div class="hello-v66">
                    <div>
                        <div class="hello-title-v66">
                            {saludo_v66}, José Carlos. {emoji_v66}
                        </div>
                        <div class="hello-sub-v66">
                            {ahora_v66.strftime('%d/%m/%Y')} ·
                            {ahora_v66.strftime('%H:%M')} hrs ·
                            Seguimiento de metas y avance a la hora
                        </div>
                    </div>
                </div>
                """),
                unsafe_allow_html=True,
            )

            top_a1, top_a2, top_a3 = st.columns([5, 1.25, 1.25])

            with top_a2:
                with st.popover(
                    "📄 Mensaje general",
                    use_container_width=True,
                ):
                    st.text_area(
                        "Mensaje general",
                        value=mensaje_general,
                        height=220,
                        disabled=True,
                        label_visibility="collapsed",
                        key="mensaje_general_popover_v66",
                    )

            with top_a3:
                with st.popover(
                    "📊 Tabla recuperación",
                    use_container_width=True,
                ):
                    st.dataframe(
                        tabla_compartir,
                        use_container_width=True,
                        hide_index=True,
                    )

            # -------------------------------------------------
            # KPIs COMPACTOS
            # -------------------------------------------------
            operadores_con_correo = 0
            operadores_con_telegram = 0

            for _, fila_tmp in resultado.iterrows():
                usuario_tmp = fila_tmp["Usuario"]
                contacto_tmp = datos_contacto.get(
                    usuario_tmp,
                    {},
                )

                correo_tmp = (
                    contacto_tmp.get("correo")
                    or str(
                        fila_tmp.get("Correo", "")
                    ).strip()
                )

                telegram_tmp = (
                    normalizar_telegram_chat_id(
                        contacto_tmp.get(
                            "telegram_chat_id",
                            "",
                        )
                    )
                )

                if correo_tmp:
                    operadores_con_correo += 1

                if telegram_tmp:
                    operadores_con_telegram += 1

            promedio_rec_v66 = float(
                resultado["% Recuperación"].mean()
            )

            esperado_resumen = float(
                jornadas_info["esperado_pct"]
            )

            k1, k2, k3, k4, k5, k6 = st.columns(6)

            kpis_v66 = [
                (
                    k1,
                    "kpi-v66-purple",
                    "👥 OPERADORES",
                    str(len(resultado)),
                    "Activos en el reporte",
                ),
                (
                    k2,
                    "kpi-v66-blue",
                    "✉️ CORREOS",
                    str(operadores_con_correo),
                    "Configurados",
                ),
                (
                    k3,
                    "kpi-v66-green",
                    "✈️ TELEGRAM",
                    str(operadores_con_telegram),
                    "Configurados",
                ),
                (
                    k4,
                    "kpi-v66-orange",
                    "🎯 MÍNIMOS",
                    "98 / 25",
                    "Gestiones / compromisos",
                ),
                (
                    k5,
                    "kpi-v66-blue",
                    "📈 ESPERADO MES",
                    formato_porcentaje(esperado_resumen),
                    "Según jornadas transcurridas",
                ),
                (
                    k6,
                    "kpi-v66-purple",
                    "💰 RECUPERACIÓN",
                    formato_porcentaje(promedio_rec_v66),
                    "Promedio mensual",
                ),
            ]

            for columna_kpi, clase_kpi, etiqueta_kpi, valor_kpi, pie_kpi in kpis_v66:
                with columna_kpi:
                    st.markdown(
                        f"""
                        <div class="kpi-v66 {clase_kpi}">
                            <div class="kpi-label-v66">{etiqueta_kpi}</div>
                            <div class="kpi-value-v66">{valor_kpi}</div>
                            <div class="kpi-foot-v66">{pie_kpi}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

        # -------------------------------------------------
        # MENSAJE LIBRE POR TELEGRAM — V90
        # -------------------------------------------------
        with st.expander(
            "💬 Escribir mensaje libre",
            expanded=False,
        ):
            st.caption(
                "Escribe un aviso libre y elige a quién enviarlo. No cuenta como seguimiento."
            )

            opciones_manual_v90 = []
            mapa_manual_v90 = {}

            for _, fila_manual_v90 in resultado.iterrows():
                usuario_manual_v90 = str(
                    fila_manual_v90["Usuario"]
                )
                nombre_manual_v90 = str(
                    fila_manual_v90["Operador"]
                )

                chat_manual_v90 = normalizar_telegram_chat_id(
                    datos_contacto.get(
                        usuario_manual_v90,
                        {},
                    ).get(
                        "telegram_chat_id",
                        "",
                    )
                )

                if not chat_manual_v90:
                    continue

                etiqueta_manual_v90 = (
                    f"{nombre_manual_v90} · @{usuario_manual_v90}"
                )

                opciones_manual_v90.append(
                    etiqueta_manual_v90
                )
                mapa_manual_v90[
                    etiqueta_manual_v90
                ] = {
                    "usuario": usuario_manual_v90,
                    "nombre": nombre_manual_v90,
                    "chat_id": chat_manual_v90,
                }

            tipo_destino_manual_v90 = st.radio(
                "Destinatarios",
                [
                    "Un operador",
                    "Varios operadores",
                    "Todos los operadores de turno",
                ],
                horizontal=True,
                key="tipo_destino_manual_v90",
            )

            destinatarios_manual_v90 = []

            if tipo_destino_manual_v90 == "Un operador":
                seleccion_manual_v90 = st.selectbox(
                    "Seleccionar operador",
                    opciones_manual_v90,
                    index=None,
                    placeholder="Elige un operador...",
                    key="operador_manual_v90",
                )

                if seleccion_manual_v90:
                    destinatarios_manual_v90 = [
                        mapa_manual_v90[
                            seleccion_manual_v90
                        ]
                    ]

            elif tipo_destino_manual_v90 == "Varios operadores":
                seleccion_multiple_manual_v90 = st.multiselect(
                    "Seleccionar operadores",
                    opciones_manual_v90,
                    key="operadores_manual_v90",
                )

                destinatarios_manual_v90 = [
                    mapa_manual_v90[x]
                    for x in seleccion_multiple_manual_v90
                ]

            else:
                ahora_manual_v90 = datetime.now(
                    ZoneInfo("America/La_Paz")
                )

                destinatarios_manual_v90 = [
                    datos_manual_v90
                    for datos_manual_v90 in mapa_manual_v90.values()
                    if operador_en_turno(
                        datos_manual_v90["usuario"],
                        ahora_manual_v90,
                    )
                ]

                st.info(
                    f"Se enviará únicamente a quienes estén de turno ahora: "
                    f"{len(destinatarios_manual_v90)} operador(es)."
                )

            mensaje_manual_v90 = st.text_area(
                "Mensaje",
                placeholder=(
                    "Ejemplo: Por favor, prioricemos los compromisos pendientes "
                    "durante este corte. Gracias."
                ),
                height=130,
                max_chars=3500,
                key="texto_manual_telegram_v90",
            )

            if destinatarios_manual_v90:
                nombres_destino_manual_v90 = ", ".join(
                    x["nombre"]
                    for x in destinatarios_manual_v90
                )

                st.caption(
                    f"Destinatarios: {nombres_destino_manual_v90}"
                )

            confirmar_manual_v90 = st.checkbox(
                "Confirmo que revisé el mensaje y los destinatarios.",
                key="confirmar_manual_v90",
            )

            enviar_manual_v90 = st.button(
                f"✈️ Enviar mensaje personalizado ({len(destinatarios_manual_v90)})",
                use_container_width=True,
                type="primary",
                disabled=(
                    not destinatarios_manual_v90
                    or not mensaje_manual_v90.strip()
                    or not confirmar_manual_v90
                ),
                key="enviar_manual_telegram_v90",
            )

            if enviar_manual_v90:
                enviados_manual_v90 = []
                errores_manual_v90 = []

                for destino_manual_v90 in destinatarios_manual_v90:
                    ok_manual_v90, detalle_manual_v90 = enviar_mensaje_telegram(
                        destino_manual_v90["chat_id"],
                        mensaje_manual_v90.strip(),
                    )

                    if ok_manual_v90:
                        enviados_manual_v90.append(
                            destino_manual_v90["nombre"]
                        )

                        registrar_envio_diario(
                            destino_manual_v90["usuario"],
                            destino_manual_v90["nombre"],
                            canal="telegram",
                            tipo="mensaje_manual",
                            detalle=detalle_manual_v90,
                        )

                    else:
                        errores_manual_v90.append(
                            f"{destino_manual_v90['nombre']}: {detalle_manual_v90}"
                        )

                if enviados_manual_v90:
                    st.success(
                        f"Mensaje enviado correctamente a "
                        f"{len(enviados_manual_v90)} operador(es)."
                    )

                if errores_manual_v90:
                    st.warning(
                        "No se pudo enviar a:\n\n- "
                        + "\n- ".join(
                            errores_manual_v90
                        )
                    )

        # -------------------------------------------------
        # FILTROS + ENVÍO MASIVO
        # -------------------------------------------------
        st.markdown("### Seguimiento individual")
        modo_fuera_final = bool(
            st.session_state.get(
                "permitir_envio_fuera_turno",
                False,
            )
        )
        st.caption(
            "Estado operativo del envío: "
            + (
                "🔓 modo excepcional global activo"
                if modo_fuera_final
                else "🔒 protección de horario activa"
            )
            + " · los desbloqueos individuales se suman al contador real de destinatarios."
        )

        st.markdown(
            """
            <div style="
                margin:10px 0 8px;
                padding:10px 13px;
                border:1px solid #dfe6ee;
                border-radius:11px;
                background:#f8fafc;
            ">
                <div style="font-size:12px;font-weight:800;color:#20364d;">
                    🔐 Control de horario para envíos
                </div>
                <div style="font-size:9px;color:#708195;margin-top:2px;">
                    Normalmente GEN Control bloquea el envío cuando el operador termina su jornada.
                    Activa el modo excepcional solo cuando necesites escribirle después de su salida.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        permitir_fuera_v98 = st.toggle(
            "🔓 Habilitar envío a operadores fuera de turno",
            value=bool(
                st.session_state.get(
                    "permitir_envio_fuera_turno",
                    False,
                )
            ),
            key="permitir_fuera_turno_v98",
        )
        st.session_state.permitir_envio_fuera_turno = permitir_fuera_v98

        if permitir_fuera_v98:
            st.warning(
                "Modo excepcional activo: también puedes enviar a quienes ya finalizaron su jornada.",
                icon="⚠️",
            )
        else:
            st.caption(
                "🔒 Protección activa · los operadores fuera de turno permanecen bloqueados."
            )

        st.caption(
                    "Protección de horario activa."
                )

        st.caption("Aquí está el trabajo principal: avance de hoy, prioridad y envío por operador.")

        f1, f2, f3, f4, f5 = st.columns([2.0, 1.0, 1.1, 1.05, 1])

        with f1:
            buscar_operador = st.text_input(
                "Buscar operador",
                placeholder="Nombre o usuario...",
                key="buscar_operador_mensajes_v63",
            ).strip()

        with f2:
            filtro_estado = st.selectbox(
                "Estado",
                [
                    "Todos",
                    "⚠️ Prioridad",
                    "Reforzar",
                    "Seguimiento",
                    "Buen avance",
                    "Excelente",
                ],
                key="filtro_estado_mensajes_v63",
            )

        with f3:
            filtro_canal = st.selectbox(
                "Telegram",
                [
                    "Todos",
                    "Configurado",
                    "Pendiente",
                ],
                key="filtro_canal_mensajes_v63",
            )

        with f4:
            ordenar_mensajes = st.selectbox(
                "Ordenar por",
                [
                    "Prioridad de hoy",
                    "Mayor prioridad",
                    "Nombre A-Z",
                    "Recuperación mayor",
                    "Recuperación menor",
                    "Gestiones mayor",
                    "Compromisos mayor",
                ],
                key="orden_mensajes_v63",
            )

        with f5:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)

            telegram_configurados_top = [
                usuario
                for usuario in resultado["Usuario"].tolist()
                if normalizar_telegram_chat_id(
                    datos_contacto.get(
                        usuario, {}
                    ).get("telegram_chat_id", "")
                )
            ]

            momento_envio_top = datetime.now(
                ZoneInfo("America/La_Paz")
            )

            telegram_en_turno_top = [
                usuario
                for usuario in telegram_configurados_top
                if operador_en_turno(
                    usuario,
                    momento_envio_top,
                )
            ]

            # V100: lista real usada por contador, botón y envío.
            telegram_pendientes_top = [
                usuario
                for usuario in telegram_configurados_top
                if operador_habilitado_para_envio(
                    usuario,
                    momento_envio_top,
                )
            ]

            telegram_fuera_turno_top = [
                usuario
                for usuario in telegram_configurados_top
                if not operador_en_turno(
                    usuario,
                    momento_envio_top,
                )
            ]

            st.caption(
                f"En turno ahora: {len(telegram_en_turno_top)} · "
                f"Seleccionados para envío: {len(telegram_pendientes_top)} · "
                f"Fuera de turno: {len(telegram_fuera_turno_top)}"
            )

            recientes_masivo, _ = resumen_frecuencia_seguimiento(
                telegram_pendientes_top,
                momento_envio_top,
            )

            if recientes_masivo:
                st.caption(
                    f"⚠️ {len(recientes_masivo)} operador(es) recibieron un avance "
                    "hace menos de 60 minutos. El botón sigue habilitado porque "
                    "el seguimiento puede repetirse durante el turno."
                )

            if st.button(
                f"✈️ Enviar seguimiento seleccionado ({len(telegram_pendientes_top)})",
                use_container_width=True,
                type="primary",
                disabled=(
                    len(telegram_pendientes_top) == 0
                    or validacion_v86["bloquear_envio"]
                ),
                key="enviar_todos_top_v86",
            ):
                enviados_top = []
                errores_top = []

                for _, fila_envio in resultado.iterrows():
                    usuario_envio = fila_envio["Usuario"]

                    chat_id_envio = normalizar_telegram_chat_id(
                        datos_contacto.get(
                            usuario_envio, {}
                        ).get("telegram_chat_id", "")
                    )

                    if not chat_id_envio:
                        continue

                    if not operador_habilitado_para_envio(
                        usuario_envio,
                        momento_envio_top,
                    ):
                        continue

                    # Puede recibir nuevamente mientras siga en turno.
                    # Fuera de horario se bloquea por defecto, salvo habilitación excepcional.
                    calculo_envio = generar_mensaje_operador_actual(
                        usuario_envio,
                        jornadas_info,
                    )

                    if calculo_envio is None:
                        errores_top.append(
                            f"{fila_envio['Operador']}: sin datos actuales."
                        )
                        continue

                    ok_envio, detalle_envio = enviar_mensaje_telegram(
                        chat_id_envio,
                        calculo_envio["mensaje"],
                    )

                    if ok_envio:
                        enviados_top.append(
                            fila_envio["Operador"]
                        )

                        registrar_envio_diario(
                            usuario_envio,
                            fila_envio["Operador"],
                            canal="telegram",
                            tipo="seguimiento",
                            detalle=detalle_envio,
                        )

                        enviar_copia_coordinador(
                            fila_envio["Operador"],
                            calculo_envio["mensaje"],
                            detalle_envio,
                        )
                    else:
                        errores_top.append(
                            f"{fila_envio['Operador']}: {detalle_envio}"
                        )

                if enviados_top:
                    st.success(
                        f"Se enviaron {len(enviados_top)} mensajes individuales."
                    )

                    ok_aviso_grupo, detalle_aviso_grupo = (
                        enviar_aviso_grupo_post_envio(
                            enviados_top,
                        )
                    )

                    if ok_aviso_grupo:
                        st.info(
                            "📣 Se informó al grupo que se realizó el "
                            "seguimiento individual a los operadores de turno."
                        )
                    else:
                        st.warning(
                            "Los mensajes individuales se enviaron, pero no "
                            f"se pudo informar al grupo: {detalle_aviso_grupo}"
                        )

                if errores_top:
                    st.warning(
                        "No se pudieron enviar:\n\n- "
                        + "\n- ".join(errores_top)
                    )

        # -------------------------------------------------
        # FILTRAR Y ORDENAR
        # -------------------------------------------------
        resultado_vista = resultado.copy()

        if buscar_operador:
            termino = normalizar_texto(buscar_operador)

            mascara_busqueda = (
                resultado_vista["Operador"]
                .astype(str)
                .apply(normalizar_texto)
                .str.contains(
                    termino,
                    regex=False,
                )
                |
                resultado_vista["Usuario"]
                .astype(str)
                .apply(normalizar_texto)
                .str.contains(
                    termino,
                    regex=False,
                )
            )

            resultado_vista = resultado_vista[
                mascara_busqueda
            ].copy()

        # Brecha contra el avance esperado a la fecha.
        esperado_v63 = float(jornadas_info["esperado_pct"])

        resultado_vista["_brecha_prioridad"] = resultado_vista.apply(
            lambda r: max(
                esperado_v63 - float(r["% Gestiones"]),
                esperado_v63 - float(r["% Compromisos"]),
                esperado_v63 - float(r["% Recuperación"]),
            ),
            axis=1,
        )

        if ordenar_mensajes == "Prioridad de hoy":
            def prioridad_hoy_sort_v66(row):
                av = calcular_avance_hora_operador(
                    row["Usuario"],
                    st.session_state.callcenter_df,
                )
                if not av.get("disponible"):
                    return 0
                return min(
                    int(av["delta_gestiones"]),
                    int(av["delta_compromisos"]),
                )

            resultado_vista["_prioridad_hoy_v66"] = (
                resultado_vista.apply(
                    prioridad_hoy_sort_v66,
                    axis=1,
                )
            )

            resultado_vista = resultado_vista.sort_values(
                "_prioridad_hoy_v66",
                ascending=True,
                kind="stable",
            )

        elif ordenar_mensajes == "Mayor prioridad":
            resultado_vista = resultado_vista.sort_values(
                "_brecha_prioridad",
                ascending=False,
                kind="stable",
            )
        elif ordenar_mensajes == "Nombre A-Z":
            resultado_vista = resultado_vista.sort_values(
                "Operador",
                ascending=True,
                kind="stable",
            )
        elif ordenar_mensajes == "Recuperación mayor":
            resultado_vista = resultado_vista.sort_values(
                "% Recuperación",
                ascending=False,
                kind="stable",
            )
        elif ordenar_mensajes == "Recuperación menor":
            resultado_vista = resultado_vista.sort_values(
                "% Recuperación",
                ascending=True,
                kind="stable",
            )
        elif ordenar_mensajes == "Gestiones mayor":
            resultado_vista = resultado_vista.sort_values(
                "Gestiones",
                ascending=False,
                kind="stable",
            )
        else:
            resultado_vista = resultado_vista.sort_values(
                "Compromisos",
                ascending=False,
                kind="stable",
            )

        # -------------------------------------------------
        # PREPARAR ESTADO
        # -------------------------------------------------
        filas_preparadas = []

        for _, fila_pre in resultado_vista.iterrows():
            fila_pre = fila_pre.copy()
            usuario_pre = fila_pre["Usuario"]

            contacto_pre = datos_contacto.get(
                usuario_pre,
                {},
            )

            nombre_guardado_pre = str(
                contacto_pre.get(
                    "nombre_mensaje",
                    "",
                )
            ).strip()

            nombre_original_pre = OPERADORES.get(
                usuario_pre,
                {},
            ).get(
                "nombre_mensaje",
                fila_pre["Operador"].split()[0],
            )

            if nombre_guardado_pre:
                OPERADORES[usuario_pre][
                    "nombre_mensaje"
                ] = nombre_guardado_pre

            chat_id_pre = normalizar_telegram_chat_id(
                contacto_pre.get(
                    "telegram_chat_id",
                    "",
                )
            )

            if (
                filtro_canal == "Configurado"
                and not chat_id_pre
            ):
                continue

            if (
                filtro_canal == "Pendiente"
                and chat_id_pre
            ):
                continue

            fila_actual_pre = obtener_fila_operador_actual(
                usuario_pre
            )

            if fila_actual_pre is not None:
                fila_pre = fila_actual_pre

            calculo_pre = generar_mensaje_diario(
                fila_pre,
                jornadas_info,
            )

            OPERADORES[usuario_pre][
                "nombre_mensaje"
            ] = nombre_original_pre

            estados_pre = [
                calculo_pre["estado_gestiones"],
                calculo_pre["estado_compromisos"],
                calculo_pre["estado_recuperacion"],
            ]

            if "Reforzar" in estados_pre:
                estado_pre = "Reforzar"
                clase_pre = "status-red"
            elif "En seguimiento" in estados_pre:
                estado_pre = "Seguimiento"
                clase_pre = "status-orange"
            elif "Buen avance" in estados_pre:
                estado_pre = "Buen avance"
                clase_pre = "status-yellow"
            else:
                estado_pre = "Excelente"
                clase_pre = "status-green"

            if filtro_estado == "⚠️ Prioridad":
                esperado_pre = float(
                    jornadas_info["esperado_pct"]
                )
                brecha_max_pre = max(
                    esperado_pre - float(fila_pre["% Gestiones"]),
                    esperado_pre - float(fila_pre["% Compromisos"]),
                    esperado_pre - float(fila_pre["% Recuperación"]),
                )
                if brecha_max_pre < 15:
                    continue
            elif (
                filtro_estado != "Todos"
                and estado_pre != filtro_estado
            ):
                continue

            filas_preparadas.append(
                (
                    fila_pre,
                    calculo_pre,
                    estado_pre,
                    clase_pre,
                )
            )

        if not filas_preparadas:
            st.info(
                "No hay operadores que coincidan con los filtros seleccionados."
            )

        st.caption(
            "Semáforo: 🔴 requiere seguimiento · 🟠 bajo el ritmo esperado · "
            "🟢 en ritmo o adelantado · ⚪ sin datos o fuera del momento de seguimiento."
        )

        # -------------------------------------------------
        # TARJETAS DE OPERADORES — V88
        # 3 por fila para recuperar legibilidad
        # -------------------------------------------------
        for bloque_inicio in range(
            0,
            len(filas_preparadas),
            3,
        ):
            cols = st.columns(3)

            for pos, item in enumerate(
                filas_preparadas[
                    bloque_inicio:bloque_inicio + 3
                ]
            ):
                fila, calculo, _, _ = item
                usuario = fila["Usuario"]

                contacto = datos_contacto.get(
                    usuario,
                    {},
                )

                correo_actual = (
                    contacto.get("correo")
                    or str(
                        fila.get("Correo", "")
                    ).strip()
                )

                telegram_chat_id = normalizar_telegram_chat_id(
                    contacto.get(
                        "telegram_chat_id",
                        "",
                    )
                )

                avance = calculo.get(
                    "avance_hora",
                    {},
                )

                pct_g_mes = float(
                    fila["% Gestiones"]
                )
                pct_c_mes = float(
                    fila["% Compromisos"]
                )
                pct_r_mes = float(
                    fila["% Recuperación"]
                )

                dg = (
                    int(
                        avance.get(
                            "delta_gestiones",
                            0,
                        )
                    )
                    if avance.get("disponible")
                    else 0
                )

                dc_val = avance.get(
                    "delta_compromisos"
                )

                dc = (
                    int(dc_val)
                    if dc_val is not None
                    else 0
                )

                estado_jornada = avance.get(
                    "estado_jornada",
                    "",
                )

                if not avance.get("disponible"):
                    estado_txt = "⚪ Sin datos"
                    status_cls = "v74-gray"
                    action_cls = "action-gray-v74"
                    action_txt = "Carga CallCenter para habilitar seguimiento"
                elif estado_jornada == "Jornada aún no iniciada":
                    estado_txt = "⚪ Aún no inicia"
                    status_cls = "v74-gray"
                    action_cls = "action-gray-v74"
                    action_txt = "Aún no corresponde seguimiento"
                elif min(dg, dc) <= -10:
                    estado_txt = "🔴 Seguimiento"
                    status_cls = "v74-red"
                    action_cls = "action-red-v74"
                    if dg <= dc:
                        action_txt = f"Recuperar {abs(dg)} gestiones para volver al ritmo"
                    else:
                        action_txt = f"Recuperar {abs(dc)} compromisos para volver al ritmo"
                elif min(dg, dc) < 0:
                    estado_txt = "🟠 Atención"
                    status_cls = "v74-orange"
                    action_cls = "action-orange-v74"
                    if dg < 0:
                        action_txt = f"{abs(dg)} gestiones por debajo del ritmo"
                    else:
                        action_txt = f"{abs(dc)} compromisos por debajo del ritmo"
                elif dg >= 5 and dc >= 2:
                    estado_txt = "🟢 Adelantado"
                    status_cls = "v74-green"
                    action_cls = "action-green-v74"
                    action_txt = "Buen avance · mantener el ritmo"
                else:
                    estado_txt = "🟢 En ritmo"
                    status_cls = "v74-green"
                    action_cls = "action-green-v74"
                    action_txt = "Avance dentro de lo esperado"

                horario = avance.get(
                    "horario"
                ) or {}

                tg_txt = (
                    "Telegram ✓"
                    if telegram_chat_id
                    else "Telegram pendiente"
                )

                if avance.get("disponible"):
                    esperado_g = max(
                        int(
                            avance.get(
                                "esperado_gestiones",
                                0,
                            )
                        ),
                        1,
                    )

                    esperado_c = max(
                        int(
                            avance.get(
                                "esperado_compromisos",
                                0,
                            )
                        ),
                        1,
                    )

                    pct_g_hoy = min(
                        max(
                            avance["gestiones_hoy"]
                            / esperado_g
                            * 100,
                            0,
                        ),
                        100,
                    )

                    pct_c_hoy = min(
                        max(
                            (
                                avance["compromisos_hoy"]
                                / esperado_c
                                * 100
                            )
                            if avance.get(
                                "compromisos_disponibles"
                            )
                            else 0,
                            0,
                        ),
                        100,
                    )

                    barra_g = (
                        "mini-green-v74"
                        if dg >= 0
                        else (
                            "mini-orange-v74"
                            if dg > -10
                            else "mini-red-v74"
                        )
                    )

                    barra_c = (
                        "mini-green-v74"
                        if dc >= 0
                        else (
                            "mini-orange-v74"
                            if dc > -10
                            else "mini-red-v74"
                        )
                    )

                with cols[pos]:
                    with st.container(
                        border=True,
                    ):
                        st.markdown(
                            f"""
                            <div class="op-head-v74">
                                <div>
                                    <div class="op-name-v74">
                                        {fila['Operador']}
                                    </div>
                                    <div class="op-contact-v74">
                                        @{usuario} · ✈ {tg_txt}
                                    </div>
                                </div>
                                <span class="status-v74 {status_cls}">
                                    {estado_txt}
                                </span>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        if horario.get(
                            "horario_configurado"
                        ):
                            st.markdown(
                                f"""
                                <div class="schedule-v74">
                                    🕒 {horario['entrada']}–{horario['salida']}
                                    · ☕ {f"{horario['break_inicio']}–{horario['break_fin']}" if horario.get('break_inicio') and horario.get('break_fin') else "Sin break"}
                                    · 📍 {estado_jornada}
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

                        st.markdown(
                            f'<div class="kicker-v74">HOY · corte {avance.get("hora_corte","--:--")}</div>',
                            unsafe_allow_html=True,
                        )

                        h1, h2 = st.columns(2)

                        with h1:
                            if avance.get(
                                "disponible"
                            ):
                                st.metric(
                                    "📞 Gestiones",
                                    f'{formato_entero(avance["gestiones_hoy"])} / 98',
                                    f"{dg:+d} vs esperado",
                                )

                                st.markdown(
                                    f"""
                                    <div class="mini-progress-v74">
                                        <div class="mini-fill-v74 {barra_g}"
                                             style="width:{pct_g_hoy}%;">
                                        </div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )

                                st.caption(
                                    f'Esperado {formato_entero(avance["esperado_gestiones"])} · '
                                    f'Faltan {formato_entero(avance["faltan_gestiones"])}'
                                )

                        with h2:
                            if avance.get(
                                "compromisos_disponibles"
                            ):
                                st.metric(
                                    "🤝 Compromisos",
                                    f'{formato_entero(avance["compromisos_hoy"])} / 25',
                                    f"{dc:+d} vs esperado",
                                )

                                st.markdown(
                                    f"""
                                    <div class="mini-progress-v74">
                                        <div class="mini-fill-v74 {barra_c}"
                                             style="width:{pct_c_hoy}%;">
                                        </div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )

                                st.caption(
                                    f'Esperado {formato_entero(avance["esperado_compromisos"])} · '
                                    f'Faltan {formato_entero(avance["faltan_compromisos"])}'
                                )
                            else:
                                st.metric(
                                    "🤝 Compromisos",
                                    "Sin dato",
                                )

                        st.markdown(
                            f'<div class="action-v74 {action_cls}">{action_txt}</div>',
                            unsafe_allow_html=True,
                        )

                        st.markdown(
                            f"""
                            <div class="monthly-v74">
                                <span>ACUMULADO</span>
                                <span>
                                    G <strong>{formato_porcentaje(pct_g_mes)}</strong>
                                    · C <strong>{formato_porcentaje(pct_c_mes)}</strong>
                                    · R <strong>{formato_porcentaje(pct_r_mes)}</strong>
                                </span>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        enviado_hoy = envio_ya_realizado_hoy(
                            usuario,
                            "seguimiento",
                        )

                        hora_envio_actual = hora_envio_hoy(
                            usuario,
                            "seguimiento",
                        )

                        minutos_ultimo_envio = minutos_desde_ultimo_envio(
                            usuario
                        )

                        en_turno_actual = operador_en_turno(
                            usuario
                        )

                        fuera_horario = operador_fuera_de_horario(
                            usuario
                        )

                        estado_turno_actual = texto_estado_turno(
                            usuario
                        )

                        if enviado_hoy and en_turno_actual:
                            if (
                                minutos_ultimo_envio is not None
                                and minutos_ultimo_envio
                                < MINUTOS_RECOMENDADOS_ENTRE_SEGUIMIENTOS
                            ):
                                texto_envio_estado = (
                                    "⚠️ Seguimiento reciente (hora Bolivia)"
                                    + (
                                        f" · {hora_envio_actual}"
                                        if hora_envio_actual
                                        else ""
                                    )
                                    + f" · hace {minutos_ultimo_envio} min"
                                    + " · puedes reenviar si es necesario"
                                )
                                st.warning(
                                    texto_envio_estado
                                )
                            else:
                                texto_envio_estado = (
                                    "✅ Ya recibió seguimiento hoy"
                                    + (
                                        f" · último registro {hora_envio_actual}"
                                        if hora_envio_actual
                                        else ""
                                    )
                                    + " · puede recibir otro; fuera de turno requiere habilitación excepcional"
                                )
                                st.success(
                                    texto_envio_estado
                                )

                        elif enviado_hoy and not en_turno_actual:
                            texto_envio_estado = (
                                "✅ Seguimiento realizado"
                                + (
                                    f" · último registro {hora_envio_actual}"
                                    if hora_envio_actual
                                    else ""
                                )
                                + f" · {estado_turno_actual}"
                            )
                            st.info(
                                texto_envio_estado
                            )

                            override_individual = st.toggle(
                                "🔓 Habilitar envío fuera de turno",
                                value=bool(
                                    st.session_state.get(
                                        f"override_fuera_turno_{usuario}",
                                        False,
                                    )
                                ),
                                key=f"toggle_override_fuera_turno_enviado_{usuario}",
                            )
                            st.session_state[
                                f"override_fuera_turno_{usuario}"
                            ] = override_individual

                        elif not en_turno_actual:
                            override_individual = st.toggle(
                                "🔓 Habilitar envío fuera de turno",
                                value=bool(
                                    st.session_state.get(
                                        f"override_fuera_turno_{usuario}",
                                        False,
                                    )
                                ),
                                key=f"toggle_override_fuera_turno_{usuario}",
                            )
                            st.session_state[
                                f"override_fuera_turno_{usuario}"
                            ] = override_individual

                            if (
                                override_individual
                                or st.session_state.get(
                                    "permitir_envio_fuera_turno",
                                    False,
                                )
                            ):
                                st.warning(
                                    f"{estado_turno_actual} · envío excepcional habilitado."
                                )
                            else:
                                st.info(
                                    f"{estado_turno_actual} · envío bloqueado por horario."
                                )

                        a1, a2 = st.columns(2)

                        with a1:
                            if (
                                telegram_chat_id
                                and operador_habilitado_para_envio(
                                    usuario
                                )
                            ):
                                if st.button(
                                    "✈️ Enviar",
                                    use_container_width=True,
                                    key=f"telegram_v74_{usuario}",
                                ):
                                    calculo_actual = generar_mensaje_operador_actual(
                                        usuario,
                                        jornadas_info,
                                    )

                                    if calculo_actual is None:
                                        st.error(
                                            "No se encontraron datos actuales del operador."
                                        )
                                    else:
                                        ok_tg, detalle_tg = enviar_mensaje_telegram(
                                            telegram_chat_id,
                                            calculo_actual["mensaje"],
                                        )

                                        if ok_tg:
                                            minutos_previos_envio = (
                                                minutos_desde_ultimo_envio(
                                                    usuario
                                                )
                                            )

                                            registrar_envio_diario(
                                                usuario,
                                                fila["Operador"],
                                                canal="telegram",
                                                tipo="seguimiento",
                                                detalle=detalle_tg,
                                            )

                                            if (
                                                minutos_previos_envio is not None
                                                and minutos_previos_envio
                                                < MINUTOS_RECOMENDADOS_ENTRE_SEGUIMIENTOS
                                            ):
                                                st.warning(
                                                    "Enviado correctamente. "
                                                    f"El seguimiento anterior había sido "
                                                    f"hace {minutos_previos_envio} min."
                                                )
                                            else:
                                                st.success(
                                                    "Enviado con datos actuales."
                                                )

                                            enviar_copia_coordinador(
                                                fila["Operador"],
                                                calculo_actual["mensaje"],
                                                detalle_tg,
                                            )
                                        else:
                                            st.error(
                                                f"No se pudo enviar: {detalle_tg}"
                                            )
                            elif not en_turno_actual:
                                st.button(
                                    "🔒 Habilita arriba",
                                    disabled=True,
                                    use_container_width=True,
                                    key=f"fuera_turno_v99_{usuario}",
                                )
                            else:
                                st.button(
                                    "✈️ Pendiente",
                                    disabled=True,
                                    use_container_width=True,
                                    key=f"sin_telegram_v81_{usuario}",
                                )

                        with a2:
                            with st.popover(
                                "👁️ Ver mensaje",
                                use_container_width=True,
                            ):
                                calculo_preview = generar_mensaje_operador_actual(
                                    usuario,
                                    jornadas_info,
                                )

                                mensaje_preview = (
                                    calculo_preview["mensaje"]
                                    if calculo_preview is not None
                                    else calculo["mensaje"]
                                )

                                st.text_area(
                                    "Mensaje",
                                    value=mensaje_preview,
                                    height=280,
                                    key=f"msg_v75_{usuario}",
                                    label_visibility="collapsed",
                                )

        st.markdown(
            """
            <div class="legend-v71">
                <strong>Estados del día:</strong>
                🔴 Crítico = brecha importante ·
                🟠 Atención = debajo del esperado ·
                🟢 En ritmo = dentro del esperado ·
                🟢 Adelantado = por encima del esperado ·
                ⚪ Aún no inicia = todavía no comenzó su jornada.
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.expander("📊 Vista previa y envío del ranking", expanded=False):
            coordinador_chat_id = obtener_telegram_coordinador_chat_id()

            if coordinador_chat_id:
                st.success(
                    "✅ Copia al coordinador activa. Recibirás una confirmación "
                    "con el mensaje exacto después de cada envío individual exitoso."
                )
            else:
                st.info(
                    "Agrega TELEGRAM_COORDINADOR_CHAT_ID en Streamlit Secrets "
                    "para recibir copia y confirmación de cada envío."
                )


            telegram_group_chat_id = (
                obtener_telegram_group_chat_id()
            )

            mensaje_grupo = (
                generar_mensaje_grupo_recuperacion(
                    tabla_general,
                    meta_individual,
                )
            )


            # -------------------------------------------------
            # VISTA PREVIA TELEGRAM — NO ENVÍA NADA
            # -------------------------------------------------
            st.markdown("#### 👁️ Vista previa antes de enviar")

            if st.button(
                "👁️ Ver cómo llegará al grupo",
                use_container_width=True,
                key="preview_telegram_grupo",
            ):
                st.session_state["mostrar_preview_telegram"] = True

            if st.session_state.get(
                "mostrar_preview_telegram",
                False,
            ):
                with st.container(border=True):
                    st.caption(
                        "Vista previa local. No se ha enviado nada a Telegram."
                    )

                    st.markdown("**Mensaje de texto**")
                    st.text_area(
                        "Vista previa del mensaje",
                        value=mensaje_grupo,
                        height=235,
                        disabled=True,
                        label_visibility="collapsed",
                        key="preview_texto_telegram",
                    )

                    st.markdown("**Imagen del ranking**")

                    try:
                        imagen_preview = (
                            generar_imagen_recuperacion_telegram(
                                tabla_general,
                                meta_individual,
                            )
                        )

                        st.image(
                            imagen_preview,
                            use_container_width=True,
                        )

                    except Exception as e:
                        st.error(
                            f"No se pudo generar la vista previa: {e}"
                        )

                    if st.button(
                        "✖️ Cerrar vista previa",
                        use_container_width=True,
                        key="cerrar_preview_telegram",
                    ):
                        st.session_state[
                            "mostrar_preview_telegram"
                        ] = False
                        st.rerun()

            st.divider()

            tg_col1, tg_col2 = st.columns(2)

            with tg_col1:
                if st.button(
                    "📤 Enviar ahora al grupo",
                    type="primary",
                    use_container_width=True,
                    disabled=(
                        not bool(
                            telegram_group_chat_id
                        )
                    ),
                    key="enviar_resumen_grupo_telegram",
                ):
                    # 1. Enviar texto general.
                    ok_texto, detalle_texto = (
                        enviar_mensaje_telegram(
                            telegram_group_chat_id,
                            mensaje_grupo,
                        )
                    )

                    if not ok_texto:
                        st.error(
                            f"No se pudo enviar el texto al grupo: {detalle_texto}"
                        )
                    else:
                        # 2. Generar y enviar UNA sola imagen del ranking.
                        imagen_grupo = (
                            generar_imagen_recuperacion_telegram(
                                tabla_general,
                                meta_individual,
                            )
                        )

                        ok_grupo, detalle_grupo = (
                            enviar_foto_telegram(
                                telegram_group_chat_id,
                                imagen_grupo,
                                "🏆 Ranking actualizado de recuperación",
                            )
                        )

                        if ok_grupo:
                            st.success(
                                "Texto + ranking en imagen enviados al grupo."
                            )
                        else:
                            st.error(
                                f"El texto se envió, pero la imagen falló: {detalle_grupo}"
                            )


            with tg_col2:
                estado_grupo = (
                    "Configurado"
                    if telegram_group_chat_id
                    else "Pendiente"
                )
                st.metric(
                    "Grupo Telegram",
                    estado_grupo,
                )

            if not telegram_group_chat_id:
                st.info(
                    "Agrega TELEGRAM_GROUP_CHAT_ID en Streamlit Secrets "
                    "para habilitar el envío al grupo."
                )



# =========================================================
# CARGAR REPORTES
# =========================================================

elif menu == "📥 Cargar reportes":

    st.subheader("📥 Cargar reportes")
    st.caption(
        "Esta sección se usa únicamente para ingresar y validar "
        "los archivos del CRM. Los análisis se muestran en las demás pestañas."
    )

    archivos = st.file_uploader(
        "Seleccionar archivos",
        type=[
            "xls",
            "xlsx",
            "csv",
        ],
        accept_multiple_files=True,
    )

    if not archivos:
        st.info(
            "Carga Promesas de Pago y/o GEN CallCenter. "
            "GEN Control detectará automáticamente cada reporte."
        )

    else:
        resumen_cargas = []
        promesas_procesadas = False
        callcenter_procesado = False

        for archivo in archivos:
            try:
                df = leer_archivo(archivo)
                tipo = detectar_tipo_reporte(df)

                resumen_cargas.append(
                    {
                        "Archivo": archivo.name,
                        "Tipo detectado": tipo,
                        "Registros": len(df),
                        "Estado": "Correcto",
                    }
                )

                guardar_carga_supabase(
                    archivo.name,
                    tipo,
                    len(df),
                )

                if tipo == "PROMESAS":
                    (
                        resultado,
                        monto_sin_usuario,
                        distribucion,
                    ) = procesar_promesas(df)

                    st.session_state.resultado_operadores = (
                        resultado
                    )
                    st.session_state.monto_sin_usuario = (
                        monto_sin_usuario
                    )
                    st.session_state.distribucion_sin_usuario = (
                        distribucion
                    )
                    st.session_state.promesas_cargado_en = datetime.now(
                        ZoneInfo("America/La_Paz")
                    )
                    st.session_state.promesas_nombre_archivo = archivo.name

                    if supabase_disponible():
                        guardar_snapshot_promesas_v93(
                            resultado,
                            monto_sin_usuario,
                            distribucion,
                            archivo.name,
                        )
                        guardar_resultados_supabase(
                            resultado,
                            fecha_local_actual(),
                            archivo.name,
                        )

                    promesas_procesadas = True

                elif tipo == "CALLCENTER":
                    st.session_state.callcenter_df = df.copy()
                    st.session_state.callcenter_cargado_en = datetime.now(
                        ZoneInfo("America/La_Paz")
                    )
                    st.session_state.callcenter_nombre_archivo = archivo.name

                    if supabase_disponible():
                        guardar_snapshot_callcenter_v93(
                            df,
                            archivo.name,
                        )

                    callcenter_procesado = True

            except Exception as e:
                resumen_cargas.append(
                    {
                        "Archivo": archivo.name,
                        "Tipo detectado": "ERROR",
                        "Registros": 0,
                        "Estado": str(e),
                    }
                )

        st.markdown("### Validación")
        st.dataframe(
            pd.DataFrame(resumen_cargas),
            use_container_width=True,
            hide_index=True,
        )

        if promesas_procesadas:
            st.success(
                "Promesas de Pago procesado correctamente. "
                "Los resultados ya están disponibles en Resumen y Mensajes diarios."
            )

        if callcenter_procesado:
            st.success(
                "GEN CallCenter procesado correctamente. "
                "Revisa Comportamiento diario para ver la evolución."
            )

        st.caption(
            "La pestaña Cargar reportes no repite rankings ni análisis "
            "para evitar duplicar información."
        )


# =========================================================
# HISTÓRICO
# =========================================================

elif menu == "🗂️ Histórico":

    st.subheader("🗂️ Histórico")
    st.caption(
        "Consulta los cierres guardados en Supabase y compara fechas."
    )

    if not supabase_disponible():
        st.warning(
            "Supabase debe estar conectado para consultar el histórico."
        )

    else:
        try:
            resp = (
                get_supabase()
                .table("resultados_diarios")
                .select("*")
                .order("fecha", desc=True)
                .execute()
            )

            historico = pd.DataFrame(
                resp.data or []
            )

            if historico.empty:
                st.info(
                    "Todavía no hay cierres guardados."
                )

            else:
                historico["fecha"] = pd.to_datetime(
                    historico["fecha"],
                    errors="coerce",
                ).dt.date

                operadores_hist = [
                    "Todos"
                ] + sorted(
                    historico["operador"]
                    .dropna()
                    .unique()
                    .tolist()
                )

                c1, c2 = st.columns(2)

                with c1:
                    operador_hist = st.selectbox(
                        "Operador",
                        operadores_hist,
                        key="hist_op_v14",
                    )

                with c2:
                    metrica_hist = st.selectbox(
                        "Indicador",
                        [
                            "porcentaje_recuperacion",
                            "recuperacion_acumulada",
                            "gestiones",
                            "compromisos",
                        ],
                        format_func=lambda x: {
                            "porcentaje_recuperacion": "% Recuperación",
                            "recuperacion_acumulada": "Recuperación Bs",
                            "gestiones": "Gestiones",
                            "compromisos": "Compromisos",
                        }[x],
                        key="hist_metrica_v14",
                    )

                vista_hist = historico.copy()

                if operador_hist != "Todos":
                    vista_hist = vista_hist[
                        vista_hist["operador"]
                        == operador_hist
                    ].copy()

                serie = (
                    vista_hist
                    .sort_values("fecha")
                    .groupby("fecha")[
                        metrica_hist
                    ]
                    .mean()
                )

                st.markdown("### Evolución histórica")
                st.line_chart(
                    serie,
                    use_container_width=True,
                )

                st.markdown("### Registros guardados")

                vista_hist = controles_ordenamiento(
                    vista_hist,
                    [
                        "fecha",
                        metrica_hist,
                        "operador",
                    ],
                    key_prefix="historico_v14",
                    columna_default="fecha",
                    descendente_default=True,
                    etiquetas={
                        "fecha": "Fecha",
                        metrica_hist: {
                            "porcentaje_recuperacion": "% Recuperación",
                            "recuperacion_acumulada": "Recuperación Bs",
                            "gestiones": "Gestiones",
                            "compromisos": "Compromisos",
                        }[metrica_hist],
                        "operador": "Operador (A-Z / Z-A)",
                    },
                )

                mostrar = vista_hist[
                    [
                        c for c in [
                            "fecha",
                            "operador",
                            "gestiones",
                            "compromisos",
                            "recuperacion_acumulada",
                            "porcentaje_recuperacion",
                            "archivo_origen",
                        ]
                        if c in vista_hist.columns
                    ]
                ].copy()

                if "recuperacion_acumulada" in mostrar:
                    mostrar[
                        "recuperacion_acumulada"
                    ] = mostrar[
                        "recuperacion_acumulada"
                    ].apply(formato_bs)

                if "porcentaje_recuperacion" in mostrar:
                    mostrar[
                        "porcentaje_recuperacion"
                    ] = mostrar[
                        "porcentaje_recuperacion"
                    ].apply(formato_porcentaje)

                st.dataframe(
                    mostrar,
                    use_container_width=True,
                    hide_index=True,
                )

        except Exception as e:
            st.error(
                f"No se pudo consultar el histórico: {e}"
            )


# =========================================================
# EQUIPO
# =========================================================

elif menu == "👥 Equipo":

    st.subheader("👥 Equipo")
    st.caption(
        "Gestión de operadores, correos y accesos de contacto."
    )

    if st.session_state.operador_guardado_ok:
        st.success(
            "Datos del operador actualizados correctamente."
        )
        st.session_state.operador_guardado_ok = False

    operadores_db = cargar_operadores_supabase()

    if operadores_db is None or operadores_db.empty:
        sincronizar_operadores_base()
        operadores_db = cargar_operadores_supabase()

    if operadores_db is None or operadores_db.empty:
        st.warning(
            "No se pudieron cargar los operadores desde Supabase."
        )

    else:
        operadores_db = operadores_db.copy()

        operadores_db = controles_ordenamiento(
            operadores_db,
            [
                "nombre",
                "usuario",
                "correo",
                "telefono",
                "telegram_chat_id",
            ],
            key_prefix="equipo_v24",
            columna_default="nombre",
            descendente_default=False,
        )

        mostrar = operadores_db[
            [
                "nombre",
                "usuario",
                "correo",
                "telefono",
                "telegram_chat_id",
                "activo",
            ]
        ].copy()

        mostrar["telegram_chat_id"] = mostrar[
            "telegram_chat_id"
        ].apply(normalizar_telegram_chat_id)

        mostrar.columns = [
            "Operador",
            "Usuario CRM",
            "Correo",
            "Teléfono",
            "Telegram Chat ID",
            "Activo",
        ]

        st.dataframe(
            mostrar,
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("### 🕒 Horarios operativos")

        horarios_v70 = []
        nombres_dias_v94 = {
            0: "Lunes",
            1: "Martes",
            2: "Miércoles",
            3: "Jueves",
            4: "Viernes",
            5: "Sábado",
        }

        for usuario_h, horarios_dia_h in HORARIOS_OPERADORES.items():
            operador_h = OPERADORES.get(
                usuario_h,
                {},
            )

            for dia_h, datos_h in horarios_dia_h.items():
                break_h = (
                    f"{datos_h['break_inicio']}–{datos_h['break_fin']}"
                    if datos_h.get("break_inicio")
                    and datos_h.get("break_fin")
                    else "Sin break"
                )

                horarios_v70.append(
                    {
                        "Operador": operador_h.get(
                            "nombre",
                            usuario_h,
                        ),
                        "Día": nombres_dias_v94.get(
                            dia_h,
                            str(dia_h),
                        ),
                        "Entrada": datos_h["entrada"],
                        "Break": break_h,
                        "Salida": datos_h["salida"],
                    }
                )

        st.dataframe(
            pd.DataFrame(
                horarios_v70
            ),
            use_container_width=True,
            hide_index=True,
        )

        st.caption(
            "El esperado a la hora se calcula con el horario individual. "
            "Durante el break el esperado se congela."
        )

        st.caption(
            "Los cambios guardados se reflejan inmediatamente "
            "en esta tabla y en Mensajes diarios. Los datos editados "
            "ya no se sobrescriben al recargar la aplicación."
        )

        st.divider()

        st.markdown("### ✈️ Detectar IDs de Telegram")
        st.caption(
            "Cada operador debe abrir el bot y enviar /start una sola vez. "
            "Luego pulsa el botón para ver su Chat ID. Esto no envía mensajes."
        )

        if st.button(
            "🔎 Buscar operadores que escribieron al bot",
            use_container_width=True,
            key="buscar_ids_telegram",
        ):
            usuarios_tg, error_tg = obtener_usuarios_telegram_bot()

            if error_tg:
                st.info(error_tg)

            if usuarios_tg:
                st.success(
                    f"Se encontraron {len(usuarios_tg)} chats privados."
                )

                tabla_ids = pd.DataFrame(
                    [
                        {
                            "Nombre Telegram": u["nombre"],
                            "Usuario Telegram": u["username"],
                            "Chat ID": u["chat_id"],
                        }
                        for u in usuarios_tg
                    ]
                )

                st.dataframe(
                    tabla_ids,
                    use_container_width=True,
                    hide_index=True,
                )

                st.session_state[
                    "usuarios_telegram_detectados"
                ] = usuarios_tg

        st.divider()
        st.markdown("### Editar operador")

        seleccion = st.selectbox(
            "Selecciona un operador",
            operadores_db["usuario"].tolist(),
            format_func=lambda u: operadores_db.loc[
                operadores_db["usuario"] == u,
                "nombre",
            ].iloc[0],
        )

        fila_op = operadores_db[
            operadores_db["usuario"] == seleccion
        ].iloc[0]

        c1, c2, c3 = st.columns(3)

        with c1:
            nombre_op = st.text_input(
                "Nombre",
                value=str(
                    fila_op.get("nombre") or ""
                ),
            )

            nombre_mensaje_op = st.text_input(
                "Nombre corto para mensajes",
                value=str(
                    fila_op.get("nombre_mensaje") or ""
                ),
            )

        with c2:
            correo_op = st.text_input(
                "Correo corporativo",
                value=str(
                    fila_op.get("correo") or ""
                ),
            )

            telefono_op = st.text_input(
                "Teléfono",
                value=str(
                    fila_op.get("telefono") or ""
                ),
            )

        with c3:
            telegram_chat_id_op = st.text_input(
                "Telegram Chat ID",
                value=normalizar_telegram_chat_id(
                    fila_op.get("telegram_chat_id")
                ),
                help=(
                    "El operador debe iniciar primero el bot. "
                    "Después guarda aquí su Chat ID numérico."
                ),
            )

            ok_bot, detalle_bot = probar_conexion_telegram()

            if ok_bot:
                st.success(detalle_bot)
            else:
                st.caption(
                    f"Telegram: {detalle_bot}"
                )

        activo_op = st.checkbox(
            "Operador activo",
            value=bool(
                fila_op.get("activo", True)
            ),
        )

        if st.button(
            "💾 Guardar operador",
            type="primary",
        ):
            telefono_normalizado = (
                normalizar_telefono_whatsapp(
                    telefono_op
                )
            )

            payload = {
                "usuario": seleccion,
                "nombre": nombre_op.strip(),
                "nombre_mensaje": nombre_mensaje_op.strip(),
                "correo": correo_op.strip(),
                "telefono": telefono_normalizado,
                "telegram_chat_id": normalizar_telegram_chat_id(
                    telegram_chat_id_op
                ),
                "activo": bool(activo_op),
                "updated_at": datetime.now(
                    ZoneInfo("America/La_Paz")
                ).isoformat(),
            }

            ok, mensaje = guardar_operador_supabase(
                payload
            )

            if ok:
                st.session_state.operadores_supabase_cargados = False
                st.session_state.operador_guardado_ok = True
                st.rerun()
            else:
                st.error(
                    f"No se pudo guardar: {mensaje}"
                )


# =========================================================
# CONFIGURACIÓN
# =========================================================

elif menu == "⚙️ Configuración":

    st.subheader("⚙️ Configuración y metas")
    st.caption(
        "Administración de metas y calendario operativo."
    )

    supa_ok, supa_msg = diagnostico_supabase()

    if supa_ok:
        st.success(
            "● Supabase conectado · cambios e históricos se guardan permanentemente."
        )
    else:
        st.error(
            "● Supabase no conectado."
        )
        st.caption(
            f"Diagnóstico: {supa_msg}"
        )
        st.info(
            "GEN Control seguirá funcionando en modo temporal "
            "hasta corregir la conexión."
        )

    if st.button(
        "🔄 Reintentar conexión Supabase",
        key="retry_supabase",
    ):
        get_supabase.clear()
        st.session_state["_supabase_error"] = ""
        st.rerun()

    # -----------------------------------------------------
    # ACCESO SOLO COORDINADOR
    # -----------------------------------------------------

    if not st.session_state.config_desbloqueada:

        st.info(
            "La configuración está protegida. "
            "Ingresa la clave de administrador para modificarla."
        )

        clave = st.text_input(
            "Clave de administrador",
            type="password",
            key="clave_admin_input",
        )

        if st.button(
            "Desbloquear configuración",
            type="primary",
        ):
            try:
                clave_correcta = st.secrets[
                    "ADMIN_PASSWORD"
                ]
            except Exception:
                clave_correcta = "GEN2026"

            if clave == clave_correcta:
                st.session_state.config_desbloqueada = True
                st.success(
                    "Configuración desbloqueada."
                )
                st.rerun()
            else:
                st.error(
                    "Clave incorrecta."
                )

    else:

        col_logout, _ = st.columns([1, 4])

        with col_logout:
            if st.button("🔒 Bloquear"):
                st.session_state.config_desbloqueada = False
                st.rerun()

        # -------------------------------------------------
        # METAS
        # -------------------------------------------------

        st.markdown("### Metas mensuales")

        c1, c2, c3 = st.columns(3)

        with c1:
            nueva_meta_g = st.number_input(
                "Meta mensual de gestiones",
                min_value=1,
                value=int(
                    st.session_state.meta_gestiones_cfg
                ),
                step=50,
            )

        with c2:
            nueva_meta_c = st.number_input(
                "Meta mensual de compromisos",
                min_value=1,
                value=int(
                    st.session_state.meta_compromisos_cfg
                ),
                step=10,
            )

        with c3:
            nueva_meta_r = st.number_input(
                "Meta mensual de recuperación por operador (USD)",
                min_value=1,
                value=int(
                    st.session_state.meta_recuperacion_cfg
                ),
                step=1000,
            )

        nueva_meta_diaria_c = st.number_input(
            "Mínimo diario de compromisos",
            min_value=0,
            value=int(
                st.session_state.meta_diaria_compromisos_cfg
            ),
            step=1,
        )

        if st.button(
            "💾 Guardar metas",
            type="primary",
        ):
            st.session_state.meta_gestiones_cfg = int(
                nueva_meta_g
            )
            st.session_state.meta_compromisos_cfg = int(
                nueva_meta_c
            )
            st.session_state.meta_recuperacion_cfg = float(
                nueva_meta_r
            )
            st.session_state.meta_diaria_compromisos_cfg = int(
                nueva_meta_diaria_c
            )

            if supabase_disponible():
                ok, mensaje = guardar_configuracion_supabase()

                if ok:
                    st.success(
                        "Metas actualizadas y guardadas permanentemente."
                    )
                else:
                    st.warning(
                        f"Metas actualizadas en esta sesión. "
                        f"No se pudo guardar en Supabase: {mensaje}"
                    )
            else:
                st.success(
                    "Metas actualizadas para esta sesión."
                )

        st.divider()

        # -------------------------------------------------
        # CALENDARIO OPERATIVO
        # -------------------------------------------------

        st.markdown("### 📅 Calendario operativo")
        st.caption(
            "Marca los días que realmente cuentan como jornada laboral. "
            "Esto modifica automáticamente la meta diaria necesaria."
        )

        hoy = fecha_local_actual()

        meses = {
            1: "Enero",
            2: "Febrero",
            3: "Marzo",
            4: "Abril",
            5: "Mayo",
            6: "Junio",
            7: "Julio",
            8: "Agosto",
            9: "Septiembre",
            10: "Octubre",
            11: "Noviembre",
            12: "Diciembre",
        }

        col_mes, col_anio = st.columns(2)

        with col_mes:
            mes_sel = st.selectbox(
                "Mes",
                options=list(meses.keys()),
                format_func=lambda m: meses[m],
                index=hoy.month - 1,
            )

        with col_anio:
            anio_sel = st.number_input(
                "Año",
                min_value=2024,
                max_value=2035,
                value=hoy.year,
                step=1,
            )

        fecha_mes = date(
            int(anio_sel),
            int(mes_sel),
            1,
        )

        clave_mes = inicializar_calendario_mes(
            fecha_mes
        )

        calendario_mes = st.session_state.calendario_laboral[
            clave_mes
        ]

        if supabase_disponible():
            calendario_guardado = cargar_calendario_supabase(
                int(anio_sel),
                int(mes_sel),
            )

            if calendario_guardado:
                calendario_mes.update(
                    calendario_guardado
                )

        dias_mes = calendar.monthrange(
            int(anio_sel),
            int(mes_sel),
        )[1]

        nombres_dia = [
            "Lun",
            "Mar",
            "Mié",
            "Jue",
            "Vie",
            "Sáb",
            "Dom",
        ]

        st.markdown(
            "**Calendario laboral del mes**"
        )
        st.caption(
            "Activa únicamente los días que cuentan como jornada laboral. "
            "Los domingos vienen desmarcados por defecto."
        )

        encabezado = st.columns(7)
        for idx, nombre_dia in enumerate(
            ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
        ):
            with encabezado[idx]:
                st.markdown(
                    f"<div style='text-align:center;font-weight:700;'>{nombre_dia}</div>",
                    unsafe_allow_html=True,
                )

        cal = calendar.Calendar(firstweekday=0)
        semanas = cal.monthdayscalendar(
            int(anio_sel),
            int(mes_sel),
        )

        for semana in semanas:
            columnas = st.columns(7)

            for idx, dia in enumerate(semana):
                with columnas[idx]:
                    if dia == 0:
                        st.markdown("&nbsp;", unsafe_allow_html=True)
                        continue

                    fecha_dia = date(
                        int(anio_sel),
                        int(mes_sel),
                        dia,
                    )

                    es_hoy = fecha_dia == fecha_local_actual()
                    etiqueta = (
                        f"⭐ {dia}"
                        if es_hoy
                        else str(dia)
                    )

                    valor = st.checkbox(
                        etiqueta,
                        value=calendario_mes.get(
                            dia,
                            fecha_dia.weekday() != 6,
                        ),
                        key=(
                            f"cal_{anio_sel}_{mes_sel}_{dia}"
                        ),
                        help=(
                            fecha_dia.strftime("%d/%m/%Y")
                        ),
                    )

                    calendario_mes[dia] = valor

        if st.button(
            "💾 Guardar calendario laboral",
            type="primary",
        ):
            if supabase_disponible():
                ok, mensaje = guardar_calendario_supabase(
                    int(anio_sel),
                    int(mes_sel),
                    calendario_mes,
                )

                if ok:
                    st.success(
                        "Calendario laboral guardado permanentemente."
                    )
                else:
                    st.error(
                        f"No se pudo guardar el calendario: {mensaje}"
                    )
            else:
                st.success(
                    "Calendario actualizado para esta sesión."
                )

        # -------------------------------------------------
        # CÁLCULO DE META DIARIA
        # -------------------------------------------------

        st.divider()
        st.markdown("### Meta diaria necesaria")

        fecha_calculo = (
            hoy
            if (
                int(anio_sel) == hoy.year
                and int(mes_sel) == hoy.month
            )
            else fecha_mes
        )

        jornadas = jornadas_configuradas(
            fecha_calculo
        )

        resultado = st.session_state.resultado_operadores

        hoy_es_laboral = (
            hoy in jornadas["dias"]
        )

        jornadas_antes_hoy = len(
            [d for d in jornadas["dias"] if d < hoy]
        )

        jornadas_despues_hoy = len(
            [d for d in jornadas["dias"] if d > hoy]
        )

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            st.metric(
                "Jornadas del mes",
                jornadas["total"],
            )

        with c2:
            st.metric(
                "Completadas antes de hoy",
                jornadas_antes_hoy,
            )

        with c3:
            st.metric(
                "Hoy",
                "Laboral" if hoy_es_laboral else "No laboral",
            )

        with c4:
            st.metric(
                "Pendientes después de hoy",
                jornadas_despues_hoy,
            )

        st.info(
            f"Para calcular la meta de cierre de hoy se consideran "
            f"{jornadas['disponibles']} jornadas disponibles contando hoy. "
            f"Después de hoy quedan {jornadas_despues_hoy}."
        )

        if resultado is not None and not resultado.empty:

            promedio_g = float(
                resultado["Gestiones"].mean()
            )
            promedio_c = float(
                resultado["Compromisos"].mean()
            )
            promedio_r = float(
                resultado["Recuperación acumulada"].mean()
            )

            faltante_g = max(
                st.session_state.meta_gestiones_cfg
                - promedio_g,
                0,
            )

            faltante_c = max(
                st.session_state.meta_compromisos_cfg
                - promedio_c,
                0,
            )

            faltante_r = max(
                st.session_state.meta_recuperacion_cfg
                - promedio_r,
                0,
            )

            disponibles = max(
                jornadas["disponibles"],
                1,
            )

            meta_diaria_g = math.ceil(
                faltante_g / disponibles
            )

            meta_diaria_c = max(
                st.session_state.meta_diaria_compromisos_cfg,
                math.ceil(
                    faltante_c / disponibles
                ),
            ) if faltante_c > 0 else 0

            meta_diaria_r = (
                faltante_r / disponibles
            )

            d1, d2, d3 = st.columns(3)

            with d1:
                st.metric(
                    "Gestiones necesarias por día",
                    formato_entero(
                        meta_diaria_g
                    ),
                )

            with d2:
                st.metric(
                    "Compromisos necesarios por día",
                    formato_entero(
                        meta_diaria_c
                    ),
                )

            with d3:
                st.metric(
                    "Recuperación necesaria por día",
                    formato_bs(
                        meta_diaria_r
                    ),
                )

            st.caption(
                "La meta diaria se recalcula automáticamente "
                "según el avance acumulado y los días laborales pendientes."
            )

        else:
            st.info(
                "Carga el reporte de Promesas de Pago para calcular "
                "la meta diaria real según el avance acumulado."
            )

        st.divider()

        # -------------------------------------------------
        # REGLA DE RECUPERACIÓN
        # -------------------------------------------------

        st.markdown("### Regla de recuperación")

        st.success(
            "Recuperación ajustada = recuperación individual "
            "+ (monto Sin usuario ÷ 8 operadores)."
        )

        st.info(
            "El porcentaje se calcula contra la meta mensual en USD "
            "de recuperación definida arriba."
        )

        st.warning(
            "La fórmula de distribución Sin usuario ÷ 8 "
            "se mantiene fija para evitar errores."
        )
