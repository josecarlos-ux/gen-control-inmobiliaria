import streamlit as st
from datetime import datetime

# =========================================================
# CONFIGURACIÓN GENERAL
# =========================================================

APP_NAME = "GEN Control"
APP_SUBTITLE = "Cobranzas Inmobiliarias"

st.set_page_config(
    page_title=APP_NAME,
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

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
            box-shadow: 0 2px 8px rgba(16, 24, 40, 0.04);
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

    fecha_actual = datetime.now().strftime("%d/%m/%Y")

    st.success(f"● Datos actualizados\n\n{fecha_actual}")

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

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
            <div class="metric-card">
                <div class="metric-label">GESTIONES</div>
                <div class="metric-value">0</div>
                <div class="metric-detail">
                    Meta mensual pendiente de cargar
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
            <div class="metric-card">
                <div class="metric-label">COMPROMISOS</div>
                <div class="metric-value">0</div>
                <div class="metric-detail">
                    Meta mensual pendiente de cargar
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            """
            <div class="metric-card">
                <div class="metric-label">RECUPERACIONES</div>
                <div class="metric-value">Bs 0</div>
                <div class="metric-detail">
                    Meta mensual del equipo: Bs 170.400
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.write("")

    st.markdown(
        """
        <div class="status-box">
            <b>Estado inicial</b><br><br>
            GEN Control está funcionando correctamente.
            Los indicadores se completarán cuando conectemos
            los reportes y el histórico.
        </div>
        """,
        unsafe_allow_html=True,
    )

# =========================================================
# COMPORTAMIENTO DIARIO
# =========================================================

elif menu == "📊 Comportamiento diario":

    st.subheader("Comportamiento diario")
    st.info(
        "Aquí incorporaremos la evolución diaria de gestiones, "
        "compromisos y recuperaciones."
    )

# =========================================================
# MENSAJES
# =========================================================

elif menu == "✉️ Mensajes diarios":

    st.subheader("Metas de cierre para hoy")

    st.caption(
        "Aquí se generarán automáticamente los mensajes "
        "personalizados para cada operador."
    )

    st.info(
        "Los mensajes diarios se habilitarán cuando carguemos "
        "los datos de los operadores."
    )

# =========================================================
# CARGAR REPORTES
# =========================================================

elif menu == "📥 Cargar reportes":

    st.subheader("Cargar reportes")

    st.caption(
        "Carga los archivos utilizados para actualizar "
        "los indicadores de GEN Control."
    )

    archivo = st.file_uploader(
        "Seleccionar reporte",
        type=["xlsx", "xls", "csv"],
    )

    if archivo is not None:
        st.success(f"Archivo recibido: {archivo.name}")

# =========================================================
# EQUIPO
# =========================================================

elif menu == "👥 Equipo":

    st.subheader("Equipo")

    st.info(
        "Aquí administraremos operadores, correos, teléfonos "
        "y metas individuales."
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
            value=2400,
        )

    with col2:
        st.number_input(
            "Meta mensual de compromisos",
            min_value=0,
            value=600,
        )

    with col3:
        st.number_input(
            "Meta mensual de recuperación (Bs)",
            min_value=0,
            value=170400,
        )

    st.info(
        "En una siguiente fase estas configuraciones "
        "se guardarán permanentemente en Supabase."
    )
