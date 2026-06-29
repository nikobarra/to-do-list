"""frontend/app.py
Interfaz web con Streamlit para la API To-Do.

Antes de ejecutar este script asegúrate de que la API está corriendo:
    uvicorn app.main:app --host 127.0.0.1 --port 8000

Para arrancar el frontend:
    streamlit run frontend/app.py

Características del panel:
    - Tabla con todas las tareas e indicador visual por estado (colores).
    - Formulario para crear tareas (título obligatorio + descripción opcional).
    - Botón para completar tareas (solo en pendientes).
    - Botón para eliminar cada tarea.
    - Resumen: total, pendientes y completadas.
"""
import os
import requests
import streamlit as st


# -----------------------------------------------------------------------------
# Configuración
# -----------------------------------------------------------------------------
# Permite sobreescribir la URL de la API por variable de entorno (útil en tests).
API_BASE = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/api")
TIMEOUT = 5  # segundos


# -----------------------------------------------------------------------------
# Funciones de la API
# -----------------------------------------------------------------------------
def _url(path: str = "") -> str:
    """Devuelve la URL completa a un endpoint de la API."""
    return f"{API_BASE}{path}"


@st.cache_data(show_spinner=False)
def fetch_todos(status_filter: str | None = None) -> list[dict]:
    """Obtiene las tareas desde la API. Si `status_filter` es None,
    devuelve todas. Si no, filtra por estado."""
    params = {"status": status_filter} if status_filter else None
    try:
        resp = requests.get(_url("/todos"), params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as exc:
        st.error(f"Error al conectar con la API: {exc}")
        return []


def create_todo(title: str, description: str) -> bool:
    """Crea una nueva tarea."""
    try:
        resp = requests.post(
            _url("/todos"),
            json={"title": title, "description": description},
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        return True
    except requests.RequestException as exc:
        st.error(f"No se pudo crear la tarea: {exc}")
        return False


def complete_todo(todo_id: int) -> bool:
    """Marca una tarea como completada (PATCH status='done')."""
    try:
        resp = requests.patch(
            _url(f"/todos/{todo_id}"),
            json={"status": "done"},
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        return True
    except requests.RequestException as exc:
        st.error(f"No se pudo completar la tarea: {exc}")
        return False


def delete_todo(todo_id: int) -> bool:
    """Elimina una tarea."""
    try:
        resp = requests.delete(_url(f"/todos/{todo_id}"), timeout=TIMEOUT)
        resp.raise_for_status()
        return True
    except requests.RequestException as exc:
        st.error(f"No se pudo eliminar la tarea: {exc}")
        return False


# -----------------------------------------------------------------------------
# UI
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="To-Do List",
    page_icon="✅",
    layout="wide",
    # Se redefine más abajo según el toggle; este es solo el valor inicial.
    initial_sidebar_state="expanded",
)

st.title("✅ To-Do List")
st.caption(f"Conectado a la API en `{API_BASE}`")


# -----------------------------------------------------------------------------
# Tema claro / oscuro
# -----------------------------------------------------------------------------
# Dos paletas completas que controlan TODOS los colores de la app: fondo de
# pantalla, sidebar, inputs, métricas, alertas, tarjetas y textos. El toggle
# en el cuerpo principal alterna entre ambas.
THEME_LIGHT = {
    # Texto
    "text": "#1f1f1f",
    "text_placeholder": "#777",
    # Fondos de la app
    "app_bg": "#FFFFFF",
    "sidebar_bg": "#F0F2F6",
    "sidebar_text": "#1f1f1f",
    # Inputs / widgets
    "input_bg": "#FFFFFF",
    "input_text": "#1f1f1f",
    "input_border": "#D0D0D0",
    # Tarjetas
    "pending_bg": "#FFF3CD",
    "pending_border": "#FFE69C",
    "done_bg": "#D1E7DD",
    "done_border": "#A3CFBB",
    # Alertas
    "info_bg": "#E7F3FE",
    "info_text": "#1f1f1f",
}

THEME_DARK = {
    "text": "#FAFAFA",
    "text_placeholder": "#9A9A9A",
    "app_bg": "#0E1117",
    "sidebar_bg": "#1B1F27",
    "sidebar_text": "#FAFAFA",
    "input_bg": "#262730",
    "input_text": "#FAFAFA",
    "input_border": "#3A3A45",
    "pending_bg": "#5C4A1A",
    "pending_border": "#8A6F26",
    "done_bg": "#1F4632",
    "done_border": "#2F6B4D",
    "info_bg": "#1B2735",
    "info_text": "#FAFAFA",
}

# Selector de tema en el cuerpo principal (radio horizontal con iconos,
# más confiable visualmente que el slider del toggle nativo de Streamlit).
toggle_col, _ = st.columns([1, 5])
with toggle_col:
    theme_choice = st.radio(
        "Tema",
        options=["☀️ Claro", "🌙 Oscuro"],
        index=0,
        horizontal=True,
        help="Cambia entre tema claro y oscuro en toda la app",
        label_visibility="visible",
    )
    dark_mode = theme_choice == "🌙 Oscuro"

current_theme = THEME_DARK if dark_mode else THEME_LIGHT
TEXT_COLOR = current_theme["text"]
TEXT_PLACEHOLDER = current_theme["text_placeholder"]


# -----------------------------------------------------------------------------
# CSS global que re-pinta TODO en función del tema seleccionado.
# -----------------------------------------------------------------------------
theme_css = f"""
<style>
    /* ====== Fondo general y sidebar ====== */
    .stApp {{ background-color: {current_theme['app_bg']} !important; color: {current_theme['text']} !important; }}
    section[data-testid="stSidebar"] {{
        background-color: {current_theme['sidebar_bg']} !important;
        color: {current_theme['sidebar_text']} !important;
    }}
    section[data-testid="stSidebar"] * {{
        color: {current_theme['sidebar_text']} !important;
    }}

    /* ====== Texto ====== */
    h1, h2, h3, h4, h5, h6, p, label, .stCaption, .stMarkdown,
    .stMarkdown p, .stMarkdown li, .stMarkdown span {{
        color: {current_theme['text']} !important;
    }}

    /* ====== Inputs (text_input, text_area, number_input) ====== */
    input[type="text"], input[type="number"], textarea {{
        background-color: {current_theme['input_bg']} !important;
        color: {current_theme['input_text']} !important;
        border-color: {current_theme['input_border']} !important;
    }}
    input::placeholder, textarea::placeholder {{
        color: {current_theme['text_placeholder']} !important;
    }}

    /* ====== Radio buttons del sidebar ====== */
    section[data-testid="stSidebar"] input[type="radio"] + div,
    section[data-testid="stSidebar"] label {{
        color: {current_theme['sidebar_text']} !important;
    }}

    /* ====== Métricas (st.metric) ====== */
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"] {{
        color: {current_theme['text']} !important;
    }}
    [data-testid="stMetric"] {{
        background-color: {current_theme['sidebar_bg']} !important;
        border: 1px solid {current_theme['input_border']} !important;
        border-radius: 8px;
        padding: 8px;
    }}

    /* ====== Alertas (st.info, st.success, st.warning, st.error) ====== */
    .stAlert, [data-testid="stAlert"] {{
        background-color: {current_theme['info_bg']} !important;
        color: {current_theme['info_text']} !important;
    }}
    .stAlert p, .stAlert span {{ color: {current_theme['info_text']} !important; }}

    /* ====== Botones ====== */
    .stButton > button,
    button[data-testid="baseButton-secondary"],
    button[data-testid="baseButton-primary"],
    button[data-testid="baseButton-secondaryFormSubmit"],
    button[data-testid="baseButton-primaryFormSubmit"] {{
        color: {current_theme['text']} !important;
        background-color: {current_theme['input_bg']} !important;
        border: 1px solid {current_theme['input_border']} !important;
    }}
    .stButton > button:hover {{
        opacity: 0.85;
    }}
    /* Selector genérico de cualquier botón de Streamlit (incluye el
       "Añadir" del formulario, que no está dentro de .stButton) */
    .stForm [data-testid="stFormSubmitButton"] button,
    button[data-testid="baseButton-secondaryFormSubmit"],
    button[data-testid="baseButton-primaryFormSubmit"] {{
        color: {current_theme['text']} !important;
        background-color: {('#2563EB' if not dark_mode else '#3B82F6')} !important;
        border: none !important;
    }}
    .stForm [data-testid="stFormSubmitButton"] button:hover,
    button[data-testid="baseButton-secondaryFormSubmit"]:hover,
    button[data-testid="baseButton-primaryFormSubmit"]:hover {{
        opacity: 0.9;
    }}
    /* Botones secundarios (Eliminar) - fondo más visible en modo claro */
    .stButton > button[kind="secondary"] {{
        background-color: {('#FBE3E4' if not dark_mode else '#5C2828')} !important;
        color: {('#7A1F1F' if not dark_mode else '#F5C2C2')} !important;
        border: 1px solid {('#EBA3A8' if not dark_mode else '#8A4646')} !important;
    }}
    /* Botón primario (Completar) - azul visible en ambos temas */
    .stButton > button[kind="primary"] {{
        background-color: #2563EB !important;
        color: #FFFFFF !important;
        border: none !important;
    }}
    /* Botón deshabilitado (Completada) */
    .stButton > button:disabled {{
        opacity: 0.5 !important;
    }}
</style>
"""
st.markdown(theme_css, unsafe_allow_html=True)


# ------- Sidebar: crear tarea + filtros -------
with st.sidebar:
    st.header("Nueva tarea")
    with st.form("form_create", clear_on_submit=True):
        new_title = st.text_input("Título *", max_chars=200)
        new_description = st.text_area(
            "Descripción (opcional)",
            max_chars=1000,
            height=100,
        )
        submitted = st.form_submit_button("Añadir", use_container_width=True)
        if submitted:
            if not new_title.strip():
                st.warning("El título es obligatorio.")
            else:
                if create_todo(new_title.strip(), new_description.strip()):
                    st.success(f"Tarea «{new_title.strip()}» creada.")
                    # Invalidar la cache para refrescar la tabla
                    fetch_todos.clear()
                    st.rerun()

    st.divider()
    st.header("Filtros")
    filter_option = st.radio(
        "Mostrar",
        options=["Todas", "Pendientes", "Completadas"],
        index=0,
    )

# ------- Cuerpo principal -------
status_filter = (
    None
    if filter_option == "Todas"
    else "pending" if filter_option == "Pendientes" else "done"
)

todos = fetch_todos(status_filter)

# ------- Resumen -------
total = len(fetch_todos(None))  # siempre sin filtro para el conteo
pending = len(fetch_todos("pending"))
done = len(fetch_todos("done"))

col_total, col_pending, col_done = st.columns(3)
col_total.metric("📋 Total", total)
col_pending.metric("⏳ Pendientes", pending)
col_done.metric("✔️ Completadas", done)

st.divider()

# ------- Tabla de tareas -------
st.subheader(
    f"Tareas ({filter_option.lower()})"
    if filter_option != "Todas"
    else "Todas las tareas"
)

if not todos:
    st.info("No hay tareas para mostrar. Crea una desde el panel de la izquierda.")
else:
    for todo in todos:
        is_pending = todo["status"] == "pending"
        # Indicador visual por color (usa el tema activo)
        if is_pending:
            color = current_theme["pending_bg"]
            border = current_theme["pending_border"]
            status_badge = "🟡 Pendiente"
        else:
            color = current_theme["done_bg"]
            border = current_theme["done_border"]
            status_badge = "🟢 Completada"

        description_html = (
            f"<p style='margin:4px 0 0 0; color:{TEXT_COLOR}; font-size:0.9em;'>"
            f"{todo['description']}</p>"
            if todo["description"]
            else f"<p style='margin:4px 0 0 0; color:{TEXT_PLACEHOLDER}; font-size:0.85em; font-style:italic;'>Sin descripción</p>"
        )

        st.markdown(
            f"""
            <div style="
                background-color: {color};
                border-left: 5px solid {border};
                border-radius: 6px;
                padding: 12px 16px;
                margin-bottom: 8px;
                color: {TEXT_COLOR};
            ">
                <div style="display:flex; justify-content:space-between; align-items:center; color: {TEXT_COLOR};">
                    <strong style="font-size:1.05em; color: {TEXT_COLOR};">#{todo['id']} · {todo['title']}</strong>
                    <span style="color: {TEXT_COLOR};">{status_badge}</span>
                </div>
                {description_html}
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Botones de acción en una fila
        btn_cols = st.columns([1, 1, 5])
        with btn_cols[0]:
            if is_pending:
                if st.button(
                    "✔ Completar",
                    key=f"complete_{todo['id']}",
                    type="primary",
                    use_container_width=True,
                ):
                    if complete_todo(todo["id"]):
                        st.success(f"Tarea #{todo['id']} completada.")
                        fetch_todos.clear()
                        st.rerun()
            else:
                # Botón deshabilitado para tareas ya completadas
                st.button(
                    "✔ Completada",
                    key=f"complete_disabled_{todo['id']}",
                    disabled=True,
                    use_container_width=True,
                )
        with btn_cols[1]:
            if st.button(
                "🗑 Eliminar",
                key=f"delete_{todo['id']}",
                type="secondary",
                use_container_width=True,
            ):
                if delete_todo(todo["id"]):
                    st.success(f"Tarea #{todo['id']} eliminada.")
                    fetch_todos.clear()
                    st.rerun()