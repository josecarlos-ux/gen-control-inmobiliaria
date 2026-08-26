import streamlit as st
import pandas as pd
import re
import unicodedata
import math
import calendar
from io import BytesIO
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
from urllib.parse import quote
from supabase import create_client


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

    if faltante <= 0:
        return 0

    if jornadas_disponibles <= 0:
        return int(math.ceil(faltante))

    recuperacion_diaria = int(
        math.ceil(faltante / jornadas_disponibles)
    )

    return max(
        minimo_diario,
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
        st.session_state.meta_recuperacion_cfg - recuperacion,
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
            f"| meta de {formato_bs(st.session_state.meta_recuperacion_cfg)} cumplida"
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
# ORDENAMIENTO DE TABLAS
# =========================================================

def controles_ordenamiento(
    df,
    columnas,
    key_prefix,
    columna_default=None,
    descendente_default=True,
):
    columnas_validas = [
        c for c in columnas
        if c in df.columns
    ]

    if not columnas_validas:
        return df

    if columna_default not in columnas_validas:
        columna_default = columnas_validas[0]

    indice_default = columnas_validas.index(
        columna_default
    )

    c1, c2 = st.columns([2, 1])

    with c1:
        columna_orden = st.selectbox(
            "Ordenar por",
            columnas_validas,
            index=indice_default,
            key=f"{key_prefix}_columna",
        )

    with c2:
        sentido = st.radio(
            "Orden",
            ["Mayor a menor", "Menor a mayor"],
            index=0 if descendente_default else 1,
            horizontal=True,
            key=f"{key_prefix}_sentido",
        )

    return df.sort_values(
        columna_orden,
        ascending=(sentido == "Menor a mayor"),
        na_position="last",
    ).reset_index(drop=True)


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
        "updated_at": datetime.now(
            ZoneInfo("America/La_Paz")
        ).isoformat(),
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
    sb = get_supabase()

    if sb is None:
        return

    registros = []

    for usuario, datos in OPERADORES.items():
        registros.append(
            {
                "usuario": usuario,
                "nombre": datos["nombre"],
                "nombre_mensaje": datos.get(
                    "nombre_mensaje",
                    datos["nombre"].split()[0],
                ),
                "correo": datos.get("correo", ""),
                "telefono": datos.get("telefono", ""),
                "activo": True,
            }
        )

    try:
        (
            sb.table("operadores")
            .upsert(
                registros,
                on_conflict="usuario",
            )
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

if "config_desbloqueada" not in st.session_state:
    st.session_state.config_desbloqueada = False

if "meta_gestiones_cfg" not in st.session_state:
    st.session_state.meta_gestiones_cfg = META_GESTIONES

if "meta_compromisos_cfg" not in st.session_state:
    st.session_state.meta_compromisos_cfg = META_COMPROMISOS

if "meta_recuperacion_cfg" not in st.session_state:
    st.session_state.meta_recuperacion_cfg = META_RECUPERACION

if "meta_diaria_compromisos_cfg" not in st.session_state:
    st.session_state.meta_diaria_compromisos_cfg = META_DIARIA_COMPROMISOS

if "calendario_laboral" not in st.session_state:
    st.session_state.calendario_laboral = {}

if "config_supabase_cargada" not in st.session_state:
    st.session_state.config_supabase_cargada = False

if "operadores_supabase_cargados" not in st.session_state:
    st.session_state.operadores_supabase_cargados = False

if not st.session_state.config_supabase_cargada:
    cargar_configuracion_supabase()
    st.session_state.config_supabase_cargada = True

if (
    supabase_disponible()
    and not st.session_state.operadores_supabase_cargados
):
    sincronizar_operadores_base()
    st.session_state.operadores_supabase_cargados = True


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
            "🗂️ Histórico",
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
        "Seguimiento general del cumplimiento mensual del equipo."
    )

    resultado = st.session_state.resultado_operadores
    jornadas_info = jornadas_configuradas()

    if resultado is None:

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Gestiones",
                "0",
                f"Meta por operador: {formato_entero(META_GESTIONES)}",
            )

        with col2:
            st.metric(
                "Compromisos",
                "0",
                f"Meta por operador: {formato_entero(META_COMPROMISOS)}",
            )

        with col3:
            st.metric(
                "Recuperación",
                "0,00%",
                f"Meta por operador: {formato_bs(st.session_state.meta_recuperacion_cfg)}",
            )

        st.info(
            "Carga el reporte de Promesas de Pago "
            "para visualizar los resultados reales."
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
            st.session_state.meta_gestiones_cfg * CANTIDAD_OPERADORES
        )
        meta_equipo_compromisos = (
            st.session_state.meta_compromisos_cfg * CANTIDAD_OPERADORES
        )
        meta_equipo_recuperacion = (
            st.session_state.meta_recuperacion_cfg * CANTIDAD_OPERADORES
        )

        # -------------------------------------------------
        # ESTADO GENERAL
        # -------------------------------------------------

        indicadores_promedio = [
            promedio_gestiones,
            promedio_compromisos,
            promedio_recuperacion,
        ]

        brecha_promedio = (
            sum(indicadores_promedio) / len(indicadores_promedio)
        ) - esperado

        if brecha_promedio >= 3:
            estado_general = "🟢 Equipo adelantado"
        elif brecha_promedio >= -3:
            estado_general = "🟡 Equipo dentro de lo esperado"
        elif brecha_promedio >= -10:
            estado_general = "🟠 Equipo en seguimiento"
        else:
            estado_general = "🔴 Reforzar ritmo del equipo"

        st.markdown(f"### {estado_general}")

        # -------------------------------------------------
        # TARJETAS PRINCIPALES
        # -------------------------------------------------

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            st.metric(
                "Gestiones",
                formato_entero(total_gestiones),
                (
                    f"{formato_porcentaje(promedio_gestiones)} "
                    f"del promedio individual"
                ),
            )
            st.caption(
                f"Meta equipo: {formato_entero(meta_equipo_gestiones)}"
            )

        with c2:
            st.metric(
                "Compromisos",
                formato_entero(total_compromisos),
                (
                    f"{formato_porcentaje(promedio_compromisos)} "
                    f"del promedio individual"
                ),
            )
            st.caption(
                f"Meta equipo: {formato_entero(meta_equipo_compromisos)}"
            )

        with c3:
            st.metric(
                "Recuperación",
                formato_bs(total_recuperacion),
                formato_porcentaje(promedio_recuperacion),
            )
            st.caption(
                f"Meta equipo: {formato_bs(meta_equipo_recuperacion)}"
            )

        with c4:
            st.metric(
                "Avance esperado",
                formato_porcentaje(esperado),
                f"{jornadas_info['transcurridas']} jornadas transcurridas",
            )
            st.caption(
                f"{jornadas_info['disponibles']} jornadas disponibles contando hoy"
            )

        st.write("")

        # -------------------------------------------------
        # COMPARACIÓN REAL VS ESPERADO
        # -------------------------------------------------

        st.markdown("### Real vs esperado a la fecha")

        comparativo = pd.DataFrame(
            {
                "Indicador": [
                    "Gestiones",
                    "Compromisos",
                    "Recuperación",
                ],
                "Real": [
                    promedio_gestiones,
                    promedio_compromisos,
                    promedio_recuperacion,
                ],
                "Esperado": [
                    esperado,
                    esperado,
                    esperado,
                ],
            }
        )

        comparativo["Brecha"] = (
            comparativo["Real"]
            - comparativo["Esperado"]
        )

        vista_comp = comparativo.copy()
        vista_comp["Real"] = vista_comp[
            "Real"
        ].apply(formato_porcentaje)
        vista_comp["Esperado"] = vista_comp[
            "Esperado"
        ].apply(formato_porcentaje)
        vista_comp["Brecha"] = vista_comp[
            "Brecha"
        ].apply(
            lambda x: (
                f"+{formato_porcentaje(x)}"
                if x >= 0
                else formato_porcentaje(x)
            )
        )

        st.dataframe(
            vista_comp,
            use_container_width=True,
            hide_index=True,
        )

        st.write("")

        # -------------------------------------------------
        # RANKING GENERAL
        # -------------------------------------------------

        st.markdown("### Ranking de operadores")

        ranking = resultado.copy()

        ranking["Puntaje"] = (
            ranking["% Gestiones"]
            + ranking["% Compromisos"]
            + ranking["% Recuperación"]
        ) / 3

        ranking["Estado"] = ranking["Puntaje"].apply(
            lambda pct: clasificar_avance(
                pct,
                esperado,
            )
        )

        ranking = ranking.sort_values(
            "Puntaje",
            ascending=False,
        ).reset_index(drop=True)

        ranking["Posición"] = (
            ranking.index + 1
        )

        ranking_vista = ranking[
            [
                "Posición",
                "Operador",
                "Gestiones",
                "% Gestiones",
                "Compromisos",
                "% Compromisos",
                "Recuperación acumulada",
                "% Recuperación",
                "Puntaje",
                "Estado",
            ]
        ].copy()

        ranking_vista = controles_ordenamiento(
            ranking_vista,
            [
                "Puntaje",
                "Gestiones",
                "% Gestiones",
                "Compromisos",
                "% Compromisos",
                "Recuperación acumulada",
                "% Recuperación",
                "Operador",
            ],
            key_prefix="ranking",
            columna_default="Puntaje",
            descendente_default=True,
        )

        ranking_vista["Posición"] = (
            ranking_vista.index + 1
        )

        ranking_vista["% Gestiones"] = ranking_vista[
            "% Gestiones"
        ].apply(formato_porcentaje)

        ranking_vista["% Compromisos"] = ranking_vista[
            "% Compromisos"
        ].apply(formato_porcentaje)

        ranking_vista["Recuperación acumulada"] = ranking_vista[
            "Recuperación acumulada"
        ].apply(formato_bs)

        ranking_vista["% Recuperación"] = ranking_vista[
            "% Recuperación"
        ].apply(formato_porcentaje)

        ranking_vista["Puntaje"] = ranking_vista[
            "Puntaje"
        ].apply(formato_porcentaje)

        st.dataframe(
            ranking_vista,
            use_container_width=True,
            hide_index=True,
        )

        st.write("")

        # -------------------------------------------------
        # SEMÁFORO POR OPERADOR
        # -------------------------------------------------

        st.markdown("### Semáforo por operador")

        semaforo = resultado[
            [
                "Operador",
                "% Gestiones",
                "% Compromisos",
                "% Recuperación",
            ]
        ].copy()

        semaforo["Gestiones"] = semaforo[
            "% Gestiones"
        ].apply(
            lambda x: clasificar_avance(
                float(x),
                esperado,
            )
        )

        semaforo["Compromisos"] = semaforo[
            "% Compromisos"
        ].apply(
            lambda x: clasificar_avance(
                float(x),
                esperado,
            )
        )

        semaforo["Recuperación"] = semaforo[
            "% Recuperación"
        ].apply(
            lambda x: clasificar_avance(
                float(x),
                esperado,
            )
        )

        semaforo = semaforo[
            [
                "Operador",
                "Gestiones",
                "Compromisos",
                "Recuperación",
            ]
        ]

        st.dataframe(
            semaforo,
            use_container_width=True,
            hide_index=True,
        )

        st.write("")

        # -------------------------------------------------
        # AVANCE VISUAL
        # -------------------------------------------------

        st.markdown("### Cumplimiento promedio del equipo")

        grafico = pd.DataFrame(
            {
                "Indicador": [
                    "Gestiones",
                    "Compromisos",
                    "Recuperación",
                ],
                "Cumplimiento": [
                    promedio_gestiones,
                    promedio_compromisos,
                    promedio_recuperacion,
                ],
            }
        ).set_index("Indicador")

        st.bar_chart(
            grafico,
            use_container_width=True,
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
                ]

                resumen_operador = controles_ordenamiento(
                    resumen_operador,
                    [
                        "Gestiones",
                        "% Gestiones",
                        "Compromisos",
                        "% Compromisos",
                        "Operador",
                    ],
                    key_prefix="comportamiento_operador",
                    columna_default="Gestiones",
                    descendente_default=True,
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

    jornadas_info = jornadas_configuradas()

    st.caption(
        f"{jornadas_info['disponibles']} jornadas disponibles contando hoy · "
        "calendario configurado"
    )

    resultado = st.session_state.resultado_operadores

    if resultado is None:
        st.warning(
            "Primero carga el reporte de Promesas de Pago."
        )

    else:
        operadores_db = cargar_operadores_supabase()

        datos_contacto = {}

        if operadores_db is not None and not operadores_db.empty:
            for _, op in operadores_db.iterrows():
                datos_contacto[str(op["usuario"])] = {
                    "correo": str(op.get("correo") or ""),
                    "telefono": str(op.get("telefono") or ""),
                    "nombre_mensaje": str(
                        op.get("nombre_mensaje")
                        or op.get("nombre")
                        or ""
                    ),
                }

        col_a, col_b, col_c = st.columns(3)

        with col_a:
            st.metric(
                "Jornadas del mes",
                jornadas_info["total"],
            )

        with col_b:
            st.metric(
                "Completadas antes de hoy",
                len(
                    [
                        d for d in jornadas_info["dias"]
                        if d < fecha_local_actual()
                    ]
                ),
            )

        with col_c:
            st.metric(
                "Disponibles contando hoy",
                jornadas_info["disponibles"],
            )

        mensajes_todos = []
        correos_todos = []

        for _, fila in resultado.iterrows():
            usuario = fila["Usuario"]

            if usuario in datos_contacto:
                if datos_contacto[usuario]["correo"]:
                    fila["Correo"] = datos_contacto[usuario]["correo"]

                if datos_contacto[usuario]["nombre_mensaje"]:
                    OPERADORES[usuario]["nombre_mensaje"] = (
                        datos_contacto[usuario]["nombre_mensaje"]
                    )

            calculo = generar_mensaje_diario(
                fila,
                jornadas_info,
            )

            mensajes_todos.append(
                f"{fila['Operador']}\n{calculo['mensaje']}"
            )

            correo_actual = str(
                fila.get("Correo", "")
            ).strip()

            if correo_actual:
                correos_todos.append(correo_actual)

            with st.container(border=True):

                col_nombre, col_estado = st.columns(
                    [4, 1]
                )

                with col_nombre:
                    st.markdown(
                        f"### {fila['Operador']}"
                    )
                    st.caption(
                        correo_actual or "Sin correo registrado"
                    )

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
                            f"de {formato_bs(st.session_state.meta_recuperacion_cfg)}"
                        ),
                    )

                st.markdown("**Mensaje sugerido**")

                st.text_area(
                    "Mensaje",
                    value=calculo["mensaje"],
                    height=190,
                    key=f"msg_{usuario}",
                    label_visibility="collapsed",
                )

                asunto = quote(
                    "Seguimiento diario de metas"
                )
                cuerpo = quote(
                    calculo["mensaje"]
                )

                mailto = (
                    f"mailto:{correo_actual}"
                    f"?subject={asunto}"
                    f"&body={cuerpo}"
                )

                telefono = (
                    datos_contacto
                    .get(usuario, {})
                    .get("telefono", "")
                )

                telefono_limpio = re.sub(
                    r"\D",
                    "",
                    str(telefono),
                )

                col_mail, col_whatsapp = st.columns(2)

                with col_mail:
                    if correo_actual:
                        st.link_button(
                            "✉️ Enviar por correo",
                            mailto,
                            use_container_width=True,
                        )
                    else:
                        st.button(
                            "✉️ Sin correo",
                            disabled=True,
                            use_container_width=True,
                            key=f"sinmail_{usuario}",
                        )

                with col_whatsapp:
                    if telefono_limpio:
                        wa_url = (
                            f"https://wa.me/{telefono_limpio}"
                            f"?text={quote(calculo['mensaje'])}"
                        )

                        st.link_button(
                            "💬 WhatsApp",
                            wa_url,
                            use_container_width=True,
                        )
                    else:
                        st.button(
                            "💬 Agregar teléfono",
                            disabled=True,
                            use_container_width=True,
                            key=f"sinwa_{usuario}",
                        )

        st.divider()
        st.markdown("### Acciones para todo el equipo")

        col_todos1, col_todos2 = st.columns(2)

        with col_todos1:
            if correos_todos:
                bcc = ",".join(
                    sorted(set(correos_todos))
                )

                mailto_todos = (
                    f"mailto:?bcc={quote(bcc)}"
                    f"&subject={quote('Seguimiento diario de metas')}"
                )

                st.link_button(
                    f"✉️ Preparar correo para todos ({len(set(correos_todos))})",
                    mailto_todos,
                    use_container_width=True,
                )

        with col_todos2:
            texto_todos = "\n\n--------------------\n\n".join(
                mensajes_todos
            )

            st.download_button(
                "📋 Descargar mensajes de todos",
                data=texto_todos,
                file_name=(
                    f"mensajes_equipo_{fecha_local_actual().isoformat()}.txt"
                ),
                mime="text/plain",
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

                guardar_carga_supabase(
                    archivo.name,
                    tipo,
                    len(df),
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

                    if supabase_disponible():
                        guardar_resultados_supabase(
                            resultado,
                            fecha_local_actual(),
                            archivo.name,
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

            vista = controles_ordenamiento(
                vista,
                [
                    "% Recuperación",
                    "Recuperación acumulada",
                    "Recuperación original",
                    "Gestiones",
                    "Compromisos",
                    "Operador",
                ],
                key_prefix="resultado_carga",
                columna_default="% Recuperación",
                descendente_default=True,
            )

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
# HISTÓRICO
# =========================================================

elif menu == "🗂️ Histórico":

    st.subheader("🗂️ Histórico")
    st.caption(
        "Consulta resultados guardados por fecha y operador."
    )

    if not supabase_disponible():
        st.warning(
            "Conecta Supabase para habilitar el histórico permanente."
        )
    else:
        sb = get_supabase()

        try:
            resp = (
                sb.table("resultados_diarios")
                .select("*")
                .order("fecha", desc=True)
                .execute()
            )

            historico = pd.DataFrame(
                resp.data or []
            )

            if historico.empty:
                st.info(
                    "Todavía no hay resultados guardados."
                )
            else:
                historico["fecha"] = pd.to_datetime(
                    historico["fecha"],
                    errors="coerce",
                ).dt.date

                fecha_min = historico["fecha"].min()
                fecha_max = historico["fecha"].max()

                c1, c2 = st.columns([2, 1])

                with c1:
                    rango_hist = st.date_input(
                        "Rango histórico",
                        value=(
                            fecha_min,
                            fecha_max,
                        ),
                        min_value=fecha_min,
                        max_value=fecha_max,
                        key="historico_rango",
                    )

                with c2:
                    operador_hist = st.selectbox(
                        "Operador",
                        ["Todos"]
                        + sorted(
                            historico[
                                "operador"
                            ].dropna().unique()
                        ),
                        key="historico_operador",
                    )

                if (
                    isinstance(rango_hist, tuple)
                    and len(rango_hist) == 2
                ):
                    inicio_hist, fin_hist = rango_hist
                else:
                    inicio_hist = fin_hist = rango_hist

                vista_hist = historico[
                    (
                        historico["fecha"]
                        >= inicio_hist
                    )
                    & (
                        historico["fecha"]
                        <= fin_hist
                    )
                ].copy()

                if operador_hist != "Todos":
                    vista_hist = vista_hist[
                        vista_hist["operador"]
                        == operador_hist
                    ].copy()

                if vista_hist.empty:
                    st.info(
                        "No hay datos para los filtros seleccionados."
                    )
                else:
                    columnas_orden = [
                        c for c in [
                            "fecha",
                            "porcentaje_recuperacion",
                            "recuperacion_acumulada",
                            "gestiones",
                            "compromisos",
                            "operador",
                        ]
                        if c in vista_hist.columns
                    ]

                    vista_hist = controles_ordenamiento(
                        vista_hist,
                        columnas_orden,
                        key_prefix="historico",
                        columna_default="fecha",
                        descendente_default=True,
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

                    if "recuperacion_acumulada" in mostrar.columns:
                        mostrar[
                            "recuperacion_acumulada"
                        ] = mostrar[
                            "recuperacion_acumulada"
                        ].apply(formato_bs)

                    if "porcentaje_recuperacion" in mostrar.columns:
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

    st.subheader("👥 Equipo de Cobranzas Inmobiliarias")
    st.caption(
        "Datos de contacto y configuración de los 8 operadores."
    )

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
            ],
            key_prefix="equipo_v10",
            columna_default="nombre",
            descendente_default=False,
        )

        mostrar = operadores_db[
            [
                "nombre",
                "usuario",
                "correo",
                "telefono",
                "activo",
            ]
        ].copy()

        mostrar.columns = [
            "Operador",
            "Usuario CRM",
            "Correo",
            "Teléfono",
            "Activo",
        ]

        st.dataframe(
            mostrar,
            use_container_width=True,
            hide_index=True,
        )

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

        c1, c2 = st.columns(2)

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
                "Teléfono / WhatsApp",
                value=str(
                    fila_op.get("telefono") or ""
                ),
                help=(
                    "Usa código de país. Ejemplo Bolivia: 5917XXXXXXX"
                ),
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
            payload = {
                "usuario": seleccion,
                "nombre": nombre_op.strip(),
                "nombre_mensaje": nombre_mensaje_op.strip(),
                "correo": correo_op.strip(),
                "telefono": telefono_op.strip(),
                "activo": bool(activo_op),
                "updated_at": datetime.now(
                    ZoneInfo("America/La_Paz")
                ).isoformat(),
            }

            ok, mensaje = guardar_operador_supabase(
                payload
            )

            if ok:
                st.success(
                    "Datos del operador guardados permanentemente."
                )
                st.session_state.operadores_supabase_cargados = False
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
                "Meta mensual de recuperación por operador (Bs)",
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
            "El porcentaje se calcula contra la meta mensual "
            "de recuperación definida arriba."
        )

        st.warning(
            "La fórmula de distribución Sin usuario ÷ 8 "
            "se mantiene fija para evitar errores."
        )


