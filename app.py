import streamlit as st
import pandas as pd
import re
import unicodedata
import math
from io import BytesIO
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
from urllib.parse import quote


# =========================================================
# CONFIGURACIÓN GENERAL
# =========================================================

APP_NAME = "GEN Control"
APP_SUBTITLE = "Cobranzas Inmobiliarias"

META_GESTIONES = 2400
META_COMPROMISOS = 600
META_DIARIA_COMPROMISOS = 25

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


st.set_page_config(
    page_title=APP_NAME,
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


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


def objetivo_hoy_gestiones(acumulado, jornadas_disponibles):
    faltante = max(META_GESTIONES - acumulado, 0)

    if faltante <= 0:
        return 0

    if jornadas_disponibles <= 0:
        return int(math.ceil(faltante))

    return int(
        math.ceil(faltante / jornadas_disponibles)
    )


def objetivo_hoy_compromisos(acumulado, jornadas_disponibles):
    faltante = max(META_COMPROMISOS - acumulado, 0)

    if faltante <= 0:
        return 0

    if jornadas_disponibles <= 0:
        return int(math.ceil(faltante))

    recuperacion_diaria = int(
        math.ceil(faltante / jornadas_disponibles)
    )

    # Regla operativa: mantener al menos 25 compromisos diarios
    # mientras la meta mensual aún no esté cumplida.
    return max(
        META_DIARIA_COMPROMISOS,
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
    pct_recuperacion = float(fila["% Recuperación"])

    disponibles = jornadas_info["disponibles"]
    esperado = jornadas_info["esperado_pct"]

    objetivo_g = objetivo_hoy_gestiones(
        gestiones,
        disponibles,
    )
    objetivo_c = objetivo_hoy_compromisos(
        compromisos,
        disponibles,
    )

    faltante_rec = max(
        META_RECUPERACION - recuperacion,
        0,
    )

    pct_g = float(fila["% Gestiones"])
    pct_c = float(fila["% Compromisos"])

    brechas = {
        "gestiones": esperado - pct_g,
        "compromisos": esperado - pct_c,
        "recuperación": esperado - pct_recuperacion,
    }

    principal = max(
        brechas,
        key=brechas.get,
    )

    if (
        pct_g >= esperado
        and pct_c >= esperado
        and pct_recuperacion >= esperado
    ):
        cierre = (
            "Muy buen avance. Mantengamos el ritmo diario "
            "para asegurar el cumplimiento mensual."
        )
    elif principal == "gestiones":
        cierre = (
            "Enfoquémonos hoy en reducir la brecha de gestiones "
            "sin bajar el ritmo en los demás indicadores."
        )
    elif principal == "compromisos":
        cierre = (
            "Hoy reforcemos especialmente la generación de "
            "compromisos para recuperar la brecha."
        )
    else:
        cierre = (
            "Hoy reforcemos la recuperación para acercarnos "
            "a la meta mensual."
        )

    linea_g = (
        f"🔹 Gestiones: {formato_entero(gestiones)} acumuladas"
    )
    if objetivo_g > 0:
        linea_g += (
            f" | realizar {formato_entero(objetivo_g)} hoy"
        )
    else:
        linea_g += " | meta mensual cumplida"

    linea_c = (
        f"🔹 Compromisos: {formato_entero(compromisos)} acumulados"
    )
    if objetivo_c > 0:
        linea_c += (
            f" | generar {formato_entero(objetivo_c)} hoy"
        )
    else:
        linea_c += " | meta mensual cumplida"

    if faltante_rec > 0:
        linea_r = (
            f"🔹 Recuperación: {formato_porcentaje(pct_recuperacion)} "
            f"| {formato_bs(recuperacion)} acumulados "
            f"| faltan {formato_bs(faltante_rec)}"
        )
    else:
        linea_r = (
            f"🔹 Recuperación: {formato_porcentaje(pct_recuperacion)} "
            f"| meta de {formato_bs(META_RECUPERACION)} cumplida"
        )

    mensaje = (
        f"Buenos días, {nombre}. 👋\n\n"
        f"Para mantenernos encaminados a las metas del mes, hoy necesitamos:\n\n"
        f"{linea_g}\n"
        f"{linea_c}\n"
        f"{linea_r}\n\n"
        f"{cierre} ¡Vamos con todo! 💪"
    )

    return {
        "mensaje": mensaje,
        "objetivo_gestiones": objetivo_g,
        "objetivo_compromisos": objetivo_c,
        "faltante_recuperacion": faltante_rec,
        "estado_gestiones": clasificar_avance(
            pct_g,
            esperado,
        ),
        "estado_compromisos": clasificar_avance(
            pct_c,
            esperado,
        ),
        "estado_recuperacion": clasificar_avance(
            pct_recuperacion,
            esperado,
        ),
    }


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
            / META_RECUPERACION
            * 100
        )

        porcentaje_gestiones = (
            gestiones
            / META_GESTIONES
            * 100
            if META_GESTIONES
            else 0
        )

        porcentaje_compromisos = (
            compromisos
            / META_COMPROMISOS
            * 100
            if META_COMPROMISOS
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
            background: #13233f;
        }

        [data-testid="stSidebar"] * {
            color: white;
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

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# MENÚ LATERAL
# =========================================================

with st.sidebar:

    st.markdown("## 📊 GEN Control")
    st.caption("Cobranzas Inmobiliarias")

    st.markdown("---")

    menu = st.radio(
        "Navegación",
        [
            "🏠 Resumen",
            "📊 Comportamiento diario",
            "✉️ Mensajes diarios",
            "📥 Cargar reportes",
            "👥 Equipo",
            "⚙️ Configuración",
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")

    fecha_actual = fecha_local_actual().strftime("%d/%m/%Y")

    st.success(
        f"● Datos actualizados\n\n{fecha_actual}"
    )

    st.markdown("---")

    st.markdown("**José Carlos**")
    st.caption("Coordinador")


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

if menu == "🏠 Resumen":

    st.subheader("Resumen operativo")

    st.caption(
        "Seguimiento general del cumplimiento "
        "mensual del equipo."
    )

    resultado = st.session_state.resultado_operadores

    if resultado is None:

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Gestiones",
                "0",
                f"Meta: {formato_entero(META_GESTIONES)}",
            )

        with col2:
            st.metric(
                "Compromisos",
                "0",
                f"Meta: {formato_entero(META_COMPROMISOS)}",
            )

        with col3:
            st.metric(
                "Recuperación",
                "0,00%",
                f"Meta por operador: {formato_bs(META_RECUPERACION)}",
            )

        st.info(
            "Carga el reporte de Promesas de Pago "
            "para visualizar los resultados reales."
        )

    else:

        promedio_gestiones = resultado[
            "% Gestiones"
        ].mean()

        promedio_compromisos = resultado[
            "% Compromisos"
        ].mean()

        promedio_recuperacion = resultado[
            "% Recuperación"
        ].mean()

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Gestiones · cumplimiento promedio",
                formato_porcentaje(
                    promedio_gestiones
                ),
            )

        with col2:
            st.metric(
                "Compromisos · cumplimiento promedio",
                formato_porcentaje(
                    promedio_compromisos
                ),
            )

        with col3:
            st.metric(
                "Recuperación · cumplimiento promedio",
                formato_porcentaje(
                    promedio_recuperacion
                ),
            )

        st.write("")

        st.subheader("Avance por operador")

        tabla = resultado[
            [
                "Operador",
                "Gestiones",
                "% Gestiones",
                "Compromisos",
                "% Compromisos",
                "Recuperación acumulada",
                "% Recuperación",
            ]
        ].copy()

        tabla["% Gestiones"] = tabla[
            "% Gestiones"
        ].apply(formato_porcentaje)

        tabla["% Compromisos"] = tabla[
            "% Compromisos"
        ].apply(formato_porcentaje)

        tabla["Recuperación acumulada"] = tabla[
            "Recuperación acumulada"
        ].apply(formato_bs)

        tabla["% Recuperación"] = tabla[
            "% Recuperación"
        ].apply(formato_porcentaje)

        st.dataframe(
            tabla,
            use_container_width=True,
            hide_index=True,
        )


# =========================================================
# COMPORTAMIENTO DIARIO
# =========================================================

elif menu == "📊 Comportamiento diario":

    st.subheader("Comportamiento diario")
    st.caption(
        "Evolución real de gestiones y compromisos a partir del reporte GEN CallCenter."
    )

    callcenter = st.session_state.callcenter_df

    if callcenter is None or callcenter.empty:
        st.warning(
            "Primero carga el reporte GEN CallCenter desde la sección Cargar reportes."
        )

    else:
        df_cc = callcenter.copy()

        df_cc["Fecha_dt"] = pd.to_datetime(
            df_cc["Fecha"],
            dayfirst=True,
            errors="coerce",
        )
        df_cc = df_cc.dropna(subset=["Fecha_dt"])
        df_cc["Fecha_dia"] = df_cc["Fecha_dt"].dt.date

        usuarios_oficiales = list(OPERADORES.keys())
        df_cc["_usuario_norm"] = (
            df_cc["Usuario"]
            .astype(str)
            .apply(normalizar_texto)
        )

        df_cc = df_cc[
            df_cc["_usuario_norm"].isin(usuarios_oficiales)
        ].copy()

        if df_cc.empty:
            st.warning(
                "El archivo fue leído, pero no se encontraron registros de los 8 operadores oficiales."
            )
        else:
            fecha_min = df_cc["Fecha_dia"].min()
            fecha_max = df_cc["Fecha_dia"].max()

            col_f1, col_f2 = st.columns([2, 1])

            with col_f1:
                rango = st.date_input(
                    "Rango de fechas",
                    value=(fecha_min, fecha_max),
                    min_value=fecha_min,
                    max_value=fecha_max,
                )

            with col_f2:
                opciones_operadores = ["Todos"] + [
                    datos["nombre"]
                    for datos in OPERADORES.values()
                ]

                operador_sel = st.selectbox(
                    "Operador",
                    opciones_operadores,
                )

            if isinstance(rango, tuple) and len(rango) == 2:
                inicio, fin = rango
            else:
                inicio = fin = rango

            filtrado = df_cc[
                (df_cc["Fecha_dia"] >= inicio)
                & (df_cc["Fecha_dia"] <= fin)
            ].copy()

            if operador_sel != "Todos":
                usuario_sel = next(
                    usuario
                    for usuario, datos in OPERADORES.items()
                    if datos["nombre"] == operador_sel
                )

                filtrado = filtrado[
                    filtrado["_usuario_norm"] == usuario_sel
                ].copy()

            filtrado["_tiene_compromiso"] = (
                filtrado["Compromiso"].notna()
                & (filtrado["Compromiso"].astype(str).str.strip() != "")
                & (filtrado["Compromiso"].astype(str).str.lower() != "nan")
            )

            total_gestiones = len(filtrado)
            total_compromisos = int(filtrado["_tiene_compromiso"].sum())
            dias_con_gestion = int(filtrado["Fecha_dia"].nunique())

            promedio_gestiones = (
                total_gestiones / dias_con_gestion
                if dias_con_gestion
                else 0
            )

            promedio_compromisos = (
                total_compromisos / dias_con_gestion
                if dias_con_gestion
                else 0
            )

            c1, c2, c3, c4 = st.columns(4)

            with c1:
                st.metric(
                    "Gestiones",
                    formato_entero(total_gestiones),
                )

            with c2:
                st.metric(
                    "Compromisos",
                    formato_entero(total_compromisos),
                )

            with c3:
                st.metric(
                    "Promedio gestiones/día",
                    formato_entero(promedio_gestiones),
                )

            with c4:
                st.metric(
                    "Promedio compromisos/día",
                    formato_entero(promedio_compromisos),
                )

            st.write("")
            st.markdown("### Evolución por día")

            diario = (
                filtrado
                .groupby("Fecha_dia")
                .agg(
                    Gestiones=("Fecha_dia", "size"),
                    Compromisos=("_tiene_compromiso", "sum"),
                )
                .reset_index()
                .sort_values("Fecha_dia")
            )

            diario["Compromisos"] = diario["Compromisos"].astype(int)

            st.line_chart(
                diario.set_index("Fecha_dia")[["Gestiones", "Compromisos"]],
                use_container_width=True,
            )

            st.markdown("### Detalle diario")

            st.dataframe(
                diario,
                use_container_width=True,
                hide_index=True,
            )

            if operador_sel == "Todos":
                st.markdown("### Avance acumulado por operador")

                resumen_operador = (
                    filtrado
                    .groupby("_usuario_norm")
                    .agg(
                        Gestiones=("Fecha_dia", "size"),
                        Compromisos=("_tiene_compromiso", "sum"),
                    )
                    .reset_index()
                )

                nombres = {
                    usuario: datos["nombre"]
                    for usuario, datos in OPERADORES.items()
                }

                resumen_operador["Operador"] = resumen_operador[
                    "_usuario_norm"
                ].map(nombres)

                resumen_operador["% Gestiones"] = (
                    resumen_operador["Gestiones"]
                    / META_GESTIONES
                    * 100
                )

                resumen_operador["% Compromisos"] = (
                    resumen_operador["Compromisos"]
                    / META_COMPROMISOS
                    * 100
                )

                resumen_operador = resumen_operador[
                    [
                        "Operador",
                        "Gestiones",
                        "% Gestiones",
                        "Compromisos",
                        "% Compromisos",
                    ]
                ].sort_values(
                    "Gestiones",
                    ascending=False,
                )

                resumen_operador["% Gestiones"] = resumen_operador[
                    "% Gestiones"
                ].apply(formato_porcentaje)

                resumen_operador["% Compromisos"] = resumen_operador[
                    "% Compromisos"
                ].apply(formato_porcentaje)

                st.dataframe(
                    resumen_operador,
                    use_container_width=True,
                    hide_index=True,
                )


# =========================================================
# MENSAJES DIARIOS
# =========================================================

elif menu == "✉️ Mensajes diarios":

    st.subheader("Metas de cierre para hoy")

    jornadas_info = calcular_jornadas()

    st.caption(
        f"{jornadas_info['disponibles']} jornadas disponibles "
        "contando hoy · lunes a sábado"
    )

    resultado = st.session_state.resultado_operadores

    if resultado is None:
        st.warning(
            "Primero carga el reporte de Promesas de Pago."
        )

    else:
        col_a, col_b, col_c = st.columns(3)

        with col_a:
            st.metric(
                "Jornadas del mes",
                jornadas_info["total"],
            )

        with col_b:
            st.metric(
                "Jornadas transcurridas",
                jornadas_info["transcurridas"],
            )

        with col_c:
            st.metric(
                "Avance esperado a la fecha",
                formato_porcentaje(
                    jornadas_info["esperado_pct"]
                ),
            )

        st.write("")

        for _, fila in resultado.iterrows():
            calculo = generar_mensaje_diario(
                fila,
                jornadas_info,
            )

            with st.container(border=True):

                col_nombre, col_estado = st.columns(
                    [4, 1]
                )

                with col_nombre:
                    st.markdown(
                        f"### {fila['Operador']}"
                    )
                    st.caption(fila["Correo"])

                with col_estado:
                    estados = [
                        calculo["estado_gestiones"],
                        calculo["estado_compromisos"],
                        calculo["estado_recuperacion"],
                    ]

                    if "Reforzar" in estados:
                        st.error("Reforzar")
                    elif "En seguimiento" in estados:
                        st.warning("En seguimiento")
                    elif "Buen avance" in estados:
                        st.info("Buen avance")
                    else:
                        st.success("Excelente avance")

                c1, c2, c3 = st.columns(3)

                with c1:
                    st.metric(
                        "Gestiones",
                        formato_entero(
                            fila["Gestiones"]
                        ),
                        (
                            f"Hoy: {formato_entero(calculo['objetivo_gestiones'])}"
                            if calculo["objetivo_gestiones"] > 0
                            else "Meta cumplida"
                        ),
                    )

                with c2:
                    st.metric(
                        "Compromisos",
                        formato_entero(
                            fila["Compromisos"]
                        ),
                        (
                            f"Hoy: {formato_entero(calculo['objetivo_compromisos'])}"
                            if calculo["objetivo_compromisos"] > 0
                            else "Meta cumplida"
                        ),
                    )

                with c3:
                    st.metric(
                        "Recuperación",
                        formato_porcentaje(
                            fila["% Recuperación"]
                        ),
                        (
                            f"{formato_bs(fila['Recuperación acumulada'])} "
                            f"de {formato_bs(META_RECUPERACION)}"
                        ),
                    )

                st.markdown("**Mensaje sugerido**")

                st.code(
                    calculo["mensaje"],
                    language=None,
                )

                asunto = quote(
                    "Seguimiento diario de metas"
                )
                cuerpo = quote(
                    calculo["mensaje"]
                )

                mailto = (
                    f"mailto:{fila['Correo']}"
                    f"?subject={asunto}"
                    f"&body={cuerpo}"
                )

                col_mail, col_whatsapp = st.columns(2)

                with col_mail:
                    st.link_button(
                        "✉️ Enviar por correo",
                        mailto,
                        use_container_width=True,
                    )

                with col_whatsapp:
                    st.link_button(
                        "💬 Abrir WhatsApp Web",
                        "https://web.whatsapp.com/",
                        use_container_width=True,
                    )


# =========================================================
# CARGAR REPORTES
# =========================================================

elif menu == "📥 Cargar reportes":

    st.subheader("Cargar reportes")

    st.caption(
        "Puedes cargar uno o varios archivos. "
        "GEN Control identificará automáticamente "
        "el tipo de reporte."
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

    if archivos:

        resumen_cargas = []

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

                # =========================================
                # PROMESAS
                # =========================================

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

                elif tipo == "CALLCENTER":
                    st.session_state.callcenter_df = df.copy()

                # =========================================
                # CALLCENTER
                # =========================================

                elif tipo == "CALLCENTER":
                    st.session_state.callcenter_df = df.copy()

            except Exception as e:

                resumen_cargas.append(
                    {
                        "Archivo": archivo.name,
                        "Tipo detectado": "ERROR",
                        "Registros": 0,
                        "Estado": str(e),
                    }
                )

        st.write("")

        st.subheader("Validación de archivos")

        st.dataframe(
            pd.DataFrame(resumen_cargas),
            use_container_width=True,
            hide_index=True,
        )

        if st.session_state.callcenter_df is not None:
            st.success(
                "Reporte GEN CallCenter cargado correctamente. "
                "Ya puedes revisar Comportamiento diario."
            )

        if st.session_state.callcenter_df is not None:
            st.success(
                "Reporte GEN CallCenter cargado correctamente. "
                "Ya puedes revisar Comportamiento diario."
            )

        resultado = st.session_state.resultado_operadores

        if resultado is not None:

            st.success(
                "Reporte de Promesas de Pago "
                "procesado correctamente."
            )

            st.markdown(
                "### Cálculo automático de recuperación"
            )

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "Monto sin usuario",
                    formato_bs(
                        st.session_state.monto_sin_usuario
                    ),
                )

            with col2:
                st.metric(
                    "Distribución por operador",
                    formato_bs(
                        st.session_state.distribucion_sin_usuario
                    ),
                    "Sin usuario ÷ 8",
                )

            with col3:
                st.metric(
                    "Meta mensual por operador",
                    formato_bs(
                        META_RECUPERACION
                    ),
                )

            st.info(
                "Regla aplicada: monto sin usuario ÷ 8 "
                "+ recuperación individual. "
                "El resultado se divide entre Bs 170.400 "
                "y se expresa en porcentaje."
            )

            st.markdown(
                "### Resultado por operador"
            )

            vista = resultado[
                [
                    "Operador",
                    "Gestiones",
                    "Compromisos",
                    "Recuperación original",
                    "Distribución sin usuario",
                    "Recuperación acumulada",
                    "% Recuperación",
                ]
            ].copy()

            for columna in [
                "Recuperación original",
                "Distribución sin usuario",
                "Recuperación acumulada",
            ]:
                vista[columna] = vista[
                    columna
                ].apply(formato_bs)

            vista["% Recuperación"] = vista[
                "% Recuperación"
            ].apply(formato_porcentaje)

            st.dataframe(
                vista,
                use_container_width=True,
                hide_index=True,
            )


# =========================================================
# EQUIPO
# =========================================================

elif menu == "👥 Equipo":

    st.subheader("Equipo de Cobranzas Inmobiliarias")

    datos_equipo = []

    for usuario, datos in OPERADORES.items():

        datos_equipo.append(
            {
                "Usuario": usuario,
                "Nombre": datos["nombre"],
                "Correo": datos["correo"],
                "Meta gestiones": META_GESTIONES,
                "Meta compromisos": META_COMPROMISOS,
                "Meta recuperación":
                    formato_bs(META_RECUPERACION),
            }
        )

    st.dataframe(
        pd.DataFrame(datos_equipo),
        use_container_width=True,
        hide_index=True,
    )

    st.caption(
        "8 operadores activos."
    )


# =========================================================
# CONFIGURACIÓN
# =========================================================

elif menu == "⚙️ Configuración":

    st.subheader("Configuración")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.number_input(
            "Meta mensual de gestiones",
            min_value=0,
            value=META_GESTIONES,
            disabled=True,
        )

    with col2:
        st.number_input(
            "Meta mensual de compromisos",
            min_value=0,
            value=META_COMPROMISOS,
            disabled=True,
        )

    with col3:
        st.number_input(
            "Meta mensual de recuperación por operador (Bs)",
            min_value=0,
            value=META_RECUPERACION,
            disabled=True,
        )

    st.markdown("### Regla de objetivo diario")

    st.info(
        f"Gestiones: faltante mensual ÷ jornadas disponibles. "
        f"Compromisos: se mantiene un mínimo de "
        f"{META_DIARIA_COMPROMISOS} por día mientras la meta mensual "
        f"no esté cumplida."
    )

    st.markdown("### Regla de recuperación")

    st.success(
        """
        **Regla oficial actual**

        1. Tomar el monto de Compromisos Cumplidos en $ de
        **Sin usuario**.
        2. Dividirlo entre **8 operadores**.
        3. Sumar ese valor a la recuperación individual.
        4. Dividir el total obtenido entre **Bs 170.400**.
        5. Mostrar el resultado principal en **porcentaje (%)**.
        """
    )

    st.warning(
        "Esta lógica está definida como regla fija del sistema "
        "y no debe modificarse sin autorización."
    )
