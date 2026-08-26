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

    resultado = st.session_state.resultado_operadores
    jornadas_info = jornadas_configuradas()

    st.markdown(
        f"""
        <div class="hero-card">
            <div class="hero-title">Centro de control operativo</div>
            <div class="hero-subtitle">
                Seguimiento de metas y brechas ·
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

        promedio_general = (
            promedio_gestiones
            + promedio_compromisos
            + promedio_recuperacion
        ) / 3

        if promedio_general >= esperado + 5:
            estado_general = "🟢 Equipo adelantado"
        elif promedio_general >= esperado - 3:
            estado_general = "🟡 Dentro de lo esperado"
        elif promedio_general >= esperado - 10:
            estado_general = "🟠 En seguimiento"
        else:
            estado_general = "🔴 Reforzar ritmo"

        st.markdown(f"### {estado_general}")

        # -------------------------------------------------
        # KPI PRINCIPALES
        # -------------------------------------------------

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            st.metric(
                "Gestiones",
                formato_entero(total_gestiones),
                formato_porcentaje(promedio_gestiones),
            )
            st.caption(
                f"Meta equipo: {formato_entero(meta_equipo_gestiones)}"
            )

        with c2:
            st.metric(
                "Compromisos",
                formato_entero(total_compromisos),
                formato_porcentaje(promedio_compromisos),
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
                "Esperado a la fecha",
                formato_porcentaje(esperado),
            )
            st.caption(
                f"{jornadas_info['disponibles']} jornadas disponibles contando hoy"
            )

        st.write("")

        # -------------------------------------------------
        # AVANCE VS ESPERADO SIN REPETIR TABLA + GRÁFICO
        # -------------------------------------------------

        st.markdown("### Avance vs esperado")

        indicadores = [
            ("Gestiones", promedio_gestiones),
            ("Compromisos", promedio_compromisos),
            ("Recuperación", promedio_recuperacion),
        ]

        for nombre_indicador, valor in indicadores:
            brecha = valor - esperado

            c1, c2, c3 = st.columns([2, 1, 1])

            with c1:
                st.progress(
                    min(max(valor / 100, 0), 1),
                    text=(
                        f"{nombre_indicador}: "
                        f"{formato_porcentaje(valor)}"
                    ),
                )

            with c2:
                st.caption(
                    f"Esperado: {formato_porcentaje(esperado)}"
                )

            with c3:
                texto_brecha = (
                    f"+{formato_porcentaje(brecha)}"
                    if brecha >= 0
                    else formato_porcentaje(brecha)
                )
                st.caption(
                    f"Brecha: {texto_brecha}"
                )

        st.write("")

        # -------------------------------------------------
        # RANKING SIMPLIFICADO
        # -------------------------------------------------

        st.markdown("### Ranking de operadores")

        ranking = resultado.copy()

        ranking["Puntaje"] = (
            ranking["% Gestiones"]
            + ranking["% Compromisos"]
            + ranking["% Recuperación"]
        ) / 3

        ranking["Estado"] = ranking["Puntaje"].apply(
            lambda x: clasificar_avance(
                float(x),
                esperado,
            )
        )

        c1, c2 = st.columns([3, 1])

        with c1:
            criterio = st.selectbox(
                "Ranking por",
                [
                    "Recuperación",
                    "Gestiones",
                    "Compromisos",
                    "Cumplimiento general",
                ],
                key="ranking_simple_v15",
            )

        with c2:
            menor_primero = st.checkbox(
                "Menor primero",
                value=False,
                key="ranking_menor_v15",
            )

        mapa_criterio = {
            "Recuperación": "% Recuperación",
            "Gestiones": "% Gestiones",
            "Compromisos": "% Compromisos",
            "Cumplimiento general": "Puntaje",
        }

        columna_orden = mapa_criterio[criterio]

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
                        f"{formato_bs(r['Recuperación acumulada'])} · "
                        f"{formato_porcentaje(r['% Recuperación'])}"
                    ),
                    axis=1,
                ),
                "Cumplimiento": ranking[
                    "Puntaje"
                ].apply(formato_porcentaje),
                "Estado": ranking["Estado"],
            }
        )

        st.dataframe(
            vista,
            use_container_width=True,
            hide_index=True,
        )

        st.write("")

        # -------------------------------------------------
        # ALERTAS: SOLO MOSTRAR SI REALMENTE HAY BRECHAS
        # -------------------------------------------------

        st.markdown("### Alertas")

        alertas = []

        for _, fila in ranking.iterrows():
            problemas = []

            if float(fila["% Gestiones"]) < esperado - 10:
                problemas.append("gestiones")

            if float(fila["% Compromisos"]) < esperado - 10:
                problemas.append("compromisos")

            if float(fila["% Recuperación"]) < esperado - 10:
                problemas.append("recuperación")

            if problemas:
                alertas.append(
                    f"**{fila['Operador']}** · reforzar "
                    + ", ".join(problemas)
                )

        if alertas:
            for alerta in alertas:
                st.warning(alerta)
        else:
            st.success(
                "No hay brechas críticas en el equipo."
            )


# =========================================================
# COMPORTAMIENTO DIARIO
# =========================================================

elif menu == "📈 Comportamiento diario":

    st.subheader("📈 Comportamiento diario")
    st.caption(
        "Aquí se analiza únicamente la evolución por fecha del reporte GEN CallCenter."
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

            fecha_min = df_cc["Fecha_dia"].min()
            fecha_max = df_cc["Fecha_dia"].max()

            c1, c2 = st.columns([2, 1])

            with c1:
                rango = st.date_input(
                    "Periodo",
                    value=(
                        fecha_min,
                        fecha_max,
                    ),
                    min_value=fecha_min,
                    max_value=fecha_max,
                    key="periodo_comportamiento_v14",
                )

            with c2:
                operador_sel = st.selectbox(
                    "Operador",
                    ["Todos"] + [
                        datos["nombre"]
                        for datos in OPERADORES.values()
                    ],
                    key="operador_comportamiento_v14",
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

            total_gestiones = len(filtrado)
            total_compromisos = int(
                filtrado["_tiene_compromiso"].sum()
            )
            dias = int(
                filtrado["Fecha_dia"].nunique()
            )

            c1, c2, c3 = st.columns(3)

            with c1:
                st.metric(
                    "Gestiones del periodo",
                    formato_entero(
                        total_gestiones
                    ),
                )

            with c2:
                st.metric(
                    "Compromisos del periodo",
                    formato_entero(
                        total_compromisos
                    ),
                )

            with c3:
                st.metric(
                    "Promedio de gestiones/día",
                    formato_entero(
                        total_gestiones / dias
                        if dias
                        else 0
                    ),
                )

            diario = (
                filtrado
                .groupby("Fecha_dia")
                .agg(
                    Gestiones=("Fecha_dia", "size"),
                    Compromisos=(
                        "_tiene_compromiso",
                        "sum",
                    ),
                )
                .reset_index()
                .sort_values("Fecha_dia")
            )

            diario["Compromisos"] = (
                diario["Compromisos"].astype(int)
            )

            st.markdown("### Tendencia diaria")
            st.line_chart(
                diario.set_index(
                    "Fecha_dia"
                )[
                    [
                        "Gestiones",
                        "Compromisos",
                    ]
                ],
                use_container_width=True,
            )

            st.markdown("### Detalle por fecha")
            st.dataframe(
                diario,
                use_container_width=True,
                hide_index=True,
            )

            if operador_sel == "Todos":
                st.markdown("### Comparación entre operadores")

                comp_op = (
                    filtrado
                    .groupby("_usuario_norm")
                    .agg(
                        Gestiones=("Fecha_dia", "size"),
                        Compromisos=(
                            "_tiene_compromiso",
                            "sum",
                        ),
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

                comp_op = controles_ordenamiento(
                    comp_op,
                    [
                        "Gestiones",
                        "Compromisos",
                        "Operador",
                    ],
                    key_prefix="comparacion_diaria_v14",
                    columna_default="Gestiones",
                    descendente_default=True,
                    etiquetas={
                        "Gestiones": "Gestiones",
                        "Compromisos": "Compromisos",
                        "Operador": "Operador (A-Z / Z-A)",
                    },
                )

                st.dataframe(
                    comp_op[
                        [
                            "Operador",
                            "Gestiones",
                            "Compromisos",
                        ]
                    ],
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

        # -------------------------------------------------
        # MENSAJE GENERAL DE RECUPERACIÓN
        # -------------------------------------------------

        meta_individual = float(
            st.session_state.meta_recuperacion_cfg
        )

        tabla_general = resultado[
            [
                "Operador",
                "Recuperación acumulada",
                "% Recuperación",
            ]
        ].copy()

        tabla_general["Meta"] = meta_individual
        tabla_general["Falta"] = (
            meta_individual
            - tabla_general["Recuperación acumulada"]
        ).clip(lower=0)

        tabla_general = tabla_general.sort_values(
            "% Recuperación",
            ascending=False,
            kind="stable",
        ).reset_index(drop=True)

        total_recuperacion_equipo = float(
            tabla_general["Recuperación acumulada"].sum()
        )
        meta_equipo = (
            meta_individual
            * CANTIDAD_OPERADORES
        )
        pct_equipo = (
            total_recuperacion_equipo
            / meta_equipo
            * 100
            if meta_equipo
            else 0
        )
        falta_equipo = max(
            meta_equipo
            - total_recuperacion_equipo,
            0,
        )

        mensaje_general = (
            f"📊 AVANCE DE RECUPERACIÓN – "
            f"{fecha_local_actual().strftime('%d/%m/%Y')}\n\n"
            "Buenos días, equipo. Comparto el avance acumulado "
            "de recuperación a la fecha, considerando una meta "
            f"mensual de {formato_bs(meta_individual)} por operador.\n\n"
            "Revisemos nuestro porcentaje de cumplimiento y la "
            "brecha pendiente. Mantengamos el enfoque en recuperación "
            "para continuar avanzando hacia la meta mensual. 💪"
        )

        st.markdown("### 📣 Avance general de recuperación")

        c1, c2, c3 = st.columns(3)

        with c1:
            st.metric(
                "Recuperación del equipo",
                formato_bs(total_recuperacion_equipo),
            )

        with c2:
            st.metric(
                "Cumplimiento equipo",
                formato_porcentaje(pct_equipo),
            )

        with c3:
            st.metric(
                "Brecha total",
                formato_bs(falta_equipo),
            )

        st.text_area(
            "Mensaje general",
            value=mensaje_general,
            height=170,
            key="mensaje_general_recuperacion_v17",
            label_visibility="collapsed",
        )

        st.markdown("#### Tabla para compartir")

        tabla_compartir = pd.DataFrame(
            {
                "Operador": tabla_general["Operador"],
                "Recuperación acumulada": tabla_general[
                    "Recuperación acumulada"
                ].apply(formato_bs),
                "Meta": tabla_general["Meta"].apply(formato_bs),
                "Cumplimiento": tabla_general[
                    "% Recuperación"
                ].apply(formato_porcentaje),
                "Falta": tabla_general["Falta"].apply(formato_bs),
            }
        )

        st.dataframe(
            tabla_compartir,
            use_container_width=True,
            hide_index=True,
        )

        correos_generales = [
            str(c).strip()
            for c in resultado["Correo"].tolist()
            if str(c).strip()
        ]

        cg1, cg2, cg3 = st.columns(3)

        with cg1:
            if correos_generales:
                bcc_general = ",".join(
                    sorted(set(correos_generales))
                )
                mailto_general = (
                    f"mailto:?bcc={quote(bcc_general)}"
                    f"&subject={quote('Avance de recuperación')}"
                    f"&body={quote(mensaje_general)}"
                )
                st.link_button(
                    "✉️ Enviar correo general",
                    mailto_general,
                    use_container_width=True,
                )

        with cg2:
            texto_tabla = tabla_compartir.to_string(
                index=False
            )
            contenido_descarga = (
                mensaje_general
                + "\n\n"
                + texto_tabla
            )
            st.download_button(
                "📋 Descargar mensaje + tabla",
                data=contenido_descarga,
                file_name=(
                    f"avance_recuperacion_"
                    f"{fecha_local_actual().isoformat()}.txt"
                ),
                mime="text/plain",
                use_container_width=True,
            )

        with cg3:
            st.link_button(
                "💬 Abrir WhatsApp Web",
                "https://web.whatsapp.com/",
                use_container_width=True,
            )

        st.divider()
        st.markdown("### Mensajes individuales")

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

                telefono_limpio = (
                    normalizar_telefono_whatsapp(
                        telefono
                    )
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

                    if supabase_disponible():
                        guardar_resultados_supabase(
                            resultado,
                            fecha_local_actual(),
                            archivo.name,
                        )

                    promesas_procesadas = True

                elif tipo == "CALLCENTER":
                    st.session_state.callcenter_df = df.copy()
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

        st.caption(
            "Los cambios guardados se reflejan inmediatamente "
            "en esta tabla y en Mensajes diarios. Los datos editados "
            "ya no se sobrescriben al recargar la aplicación."
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
                    "Puedes escribir 8 dígitos. GEN Control agregará "
                    "automáticamente el código 591 para Bolivia."
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


