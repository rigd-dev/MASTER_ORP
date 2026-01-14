import streamlit as st
import json
import os
import base64

# ---------------------------------------------------------
# 1. CONFIGURACIÓN INICIAL Y ESTILOS
# ---------------------------------------------------------
st.set_page_config(page_title="Simulador ORP", layout="wide")

# Estilos para que los botones y textos se vean bien
st.markdown("""
    <style>
    .block-container {padding-top: 2rem; padding-bottom: 2rem;}
    div.stButton > button {width: 100%; border-radius: 5px; font-weight: bold;}
    .correct {background-color: #d4edda; padding: 10px; border-radius: 5px; color: #155724; border: 1px solid #c3e6cb;}
    .incorrect {background-color: #f8d7da; padding: 10px; border-radius: 5px; color: #721c24; border: 1px solid #f5c6cb;}
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. GESTIÓN DEL ESTADO (SESSION STATE)
# ---------------------------------------------------------
# Esto es lo que controla que el programa "recuerde" dónde estás
if 'index' not in st.session_state:
    st.session_state.index = 0
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'validated' not in st.session_state:
    st.session_state.validated = False
if 'quiz_data' not in st.session_state:
    st.session_state.quiz_data = []

# Función para reiniciar todo (se usa en el botón Reiniciar y al cambiar tema)
def reset_quiz():
    st.session_state.index = 0
    st.session_state.score = 0
    st.session_state.validated = False

# ---------------------------------------------------------
# 3. FUNCIONES DE CARGA
# ---------------------------------------------------------
def get_pdf_embed(pdf_filename, page):
    """Crea el visor de PDF. Si falla, avisa."""
    path = os.path.join("static", pdf_filename)
    if not os.path.exists(path):
        return f"<div class='incorrect'>⚠️ Error: No encuentro el archivo <b>{pdf_filename}</b> en la carpeta <code>static</code>.</div>"
    
    try:
        with open(path, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode('utf-8')
        # Usamos <embed> que es más agresivo para mostrar el PDF
        return f'<embed src="data:application/pdf;base64,{base64_pdf}#page={page}" width="100%" height="800px" type="application/pdf">'
    except Exception as e:
        return f"Error al leer PDF: {str(e)}"

# ---------------------------------------------------------
# 4. BARRA LATERAL (SELECCIÓN)
# ---------------------------------------------------------
with st.sidebar:
    st.header("🎛️ Configuración")
    
    # Selector de Asignatura
    # on_change=reset_quiz asegura que si cambias de asignatura, todo se reinicia
    asignatura = st.selectbox(
        "Asignatura:", 
        ["Psicosociologia", "Ergonomia"], 
        on_change=reset_quiz
    )
    
    # Cargar archivos disponibles
    base_folder = f"data/{asignatura}"
    if os.path.exists(base_folder):
        files = sorted([f for f in os.listdir(base_folder) if f.endswith(".json")])
        # Selector de Unidades
        selected_files = st.multiselect("Unidades:", files, default=files, on_change=reset_quiz)
    else:
        st.error(f"No existe la carpeta {base_folder}")
        files = []
        selected_files = []

    st.markdown("---")
    
    # Botón de Reinicio Manual
    if st.button("🔄 REINICIAR TEST"):
        reset_quiz()
        st.rerun() # ESTO es lo que faltaba, fuerza a recargar la página

# ---------------------------------------------------------
# 5. LÓGICA DE CARGA DE DATOS
# ---------------------------------------------------------
# Solo cargamos datos si cambiaron las selecciones o si la lista está vacía
current_data = []
if selected_files:
    for file in selected_files:
        path = os.path.join(base_folder, file)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                current_data.extend(data)
        except:
            st.error(f"Error leyendo {file}")

# ---------------------------------------------------------
# 6. INTERFAZ PRINCIPAL DEL EXAMEN
# ---------------------------------------------------------
if not current_data:
    st.info("👈 Selecciona unidades en el menú izquierdo para empezar.")
else:
    # Comprobamos que no nos hayamos pasado del final
    if st.session_state.index >= len(current_data):
        st.balloons()
        st.success(f"¡TERMINASTE! 🏆")
        st.metric("Tu Puntuación Final", f"{st.session_state.score} / {len(current_data)}")
        if st.button("Volver a empezar"):
            reset_quiz()
            st.rerun()
    else:
        # Pregunta actual
        q = current_data[st.session_state.index]
        total = len(current_data)
        
        # Barra de progreso
        st.progress((st.session_state.index) / total)
        st.caption(f"Pregunta {st.session_state.index + 1} de {total}")

        # COLUMNAS: Izquierda (Pregunta) - Derecha (PDF)
        # Si ya validó, la derecha ocupa espacio (1:1). Si no, la derecha es mínima (1:0.01)
        col1_width = 1
        col2_width = 1.5 if st.session_state.validated else 0.01
        c1, c2 = st.columns([col1_width, col2_width])

        with c1:
            st.subheader(q.get("question", "Pregunta sin texto"))
            st.markdown(f"*{q.get('topic', 'General')}*")
            
            # Opciones
            # El key incluye el index para que al cambiar de pregunta se resetee el radio
            opcion = st.radio(
                "Elige la correcta:", 
                q.get("options", []),
                key=f"radio_{st.session_state.index}", 
                disabled=st.session_state.validated
            )

            st.markdown("<br>", unsafe_allow_html=True)

            # BOTONES DE ACCIÓN
            if not st.session_state.validated:
                if st.button("✅ Validar Respuesta"):
                    st.session_state.validated = True
                    if opcion == q.get("answer"):
                        st.session_state.score += 1
                    st.rerun() # Recargar para mostrar resultados y PDF
            else:
                # Mostrar Feedback
                if opcion == q.get("answer"):
                    st.markdown(f"<div class='correct'>✅ <b>¡Correcto!</b></div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='incorrect'>❌ <b>Incorrecto</b>. La respuesta era: {q.get('answer')}</div>", unsafe_allow_html=True)
                
                st.info(f"ℹ️ {q.get('explanation', '')}")

                # Botón Siguiente
                if st.button("➡️ Siguiente Pregunta"):
                    st.session_state.index += 1
                    st.session_state.validated = False
                    st.rerun()

        # VISOR PDF (SOLO SI ESTÁ VALIDADO)
        with c2:
            if st.session_state.validated:
                pdf_file = q.get("source_file")
                page = q.get("page", 1)
                
                if pdf_file:
                    st.markdown(f"#### 📖 Referencia: {pdf_file} (Pág. {page})")
                    # Llamamos al visor
                    html = get_pdf_embed(pdf_file, page)
                    st.markdown(html, unsafe_allow_html=True)