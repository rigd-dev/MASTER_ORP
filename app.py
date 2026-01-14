import streamlit as st
import json
import os
import base64

# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Simulador Máster ORP",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. ESTILOS CSS PROFESIONALES ---
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        font-weight: bold;
        border-radius: 8px;
    }
    .info-box {
        padding: 15px;
        background-color: #e1f5fe;
        border-left: 5px solid #039be5;
        border-radius: 4px;
        margin-bottom: 10px;
    }
    .success-text { color: #2e7d32; font-weight: bold; }
    .error-text { color: #c62828; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- 3. FUNCIONES AUXILIARES ---

def load_data(asignatura, selected_units):
    """Carga y combina las preguntas de los JSON seleccionados."""
    base_path = f"data/{asignatura}/"
    questions = []
    
    if os.path.exists(base_path):
        for file_name in selected_units:
            file_path = os.path.join(base_path, file_name)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    questions.extend(json.load(f))
            except Exception as e:
                st.error(f"Error al leer {file_name}: {e}")
    return questions

def get_pdf_viewer(pdf_name, page_num):
    """Genera el visor PDF embebido en base64."""
    pdf_path = os.path.join("static", pdf_name)
    
    if not os.path.exists(pdf_path):
        return f"""
        <div style="padding:20px; background-color:#ffcdd2; border-radius:10px; border:1px solid #ef5350;">
            <h4 style="color:#b71c1c;">⚠️ Archivo no encontrado</h4>
            <p>El archivo <b>{pdf_name}</b> no está en la carpeta <code>static/</code>.</p>
            <p>Por favor, asegúrate de subirlo con ese nombre exacto.</p>
        </div>
        """
    
    try:
        with open(pdf_path, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode('utf-8')
        
        # El parámetro #page=N funciona en la mayoría de visores modernos (Chrome/Edge/Firefox)
        return f'''
            <iframe src="data:application/pdf;base64,{base64_pdf}#page={page_num}" 
            width="100%" height="850px" type="application/pdf" style="border:none;">
            </iframe>
        '''
    except Exception as e:
        return f"Error al procesar el PDF: {e}"

# --- 4. INTERFAZ PRINCIPAL ---

st.title("🎓 Simulador de Examen - Máster ORP")

# --- BARRA LATERAL (Configuración) ---
st.sidebar.header("⚙️ Configuración")

# Selección de Asignatura
asignatura = st.sidebar.selectbox(
    "1️⃣ Selecciona Asignatura:",
    ["Psicosociologia", "Ergonomia"]
)

# Selección de Unidades
data_folder = f"data/{asignatura}/"
if os.path.exists(data_folder):
    available_files = sorted([f for f in os.listdir(data_folder) if f.endswith('.json')])
    selected_files = st.sidebar.multiselect(
        "2️⃣ Selecciona Unidades:", 
        available_files, 
        default=available_files
    )
else:
    st.sidebar.error(f"No existe la carpeta data/{asignatura}")
    selected_files = []

# Botón de Reinicio
if st.sidebar.button("🔄 Reiniciar Test"):
    st.session_state.current_index = 0
    st.session_state.score = 0
    st.session_state.answered = False
    st.rerun()

# --- LÓGICA DEL TEST ---

if not selected_files:
    st.info("👈 Selecciona al menos una unidad en el menú lateral para comenzar.")
else:
    # Cargar preguntas
    all_questions = load_data(asignatura, selected_files)
    total_q = len(all_questions)

    # Inicializar estado de sesión si no existe
    if 'current_index' not in st.session_state:
        st.session_state.current_index = 0
        st.session_state.score = 0
        st.session_state.answered = False

    # Verificar que no nos pasamos del índice
    if st.session_state.current_index >= total_q:
        # PANTALLA FINAL
        st.balloons()
        st.success(f"🎉 ¡Has terminado el entrenamiento!")
        st.metric(label="Puntuación Final", value=f"{st.session_state.score} / {total_q}")
        
        if st.button("Volver a Empezar"):
            st.session_state.current_index = 0
            st.session_state.score = 0
            st.session_state.answered = False
            st.rerun()
    else:
        # OBTENER PREGUNTA ACTUAL
        q = all_questions[st.session_state.current_index]
        
        # BARRA DE PROGRESO
        progress = (st.session_state.current_index + 1) / total_q
        st.progress(progress)
        st.caption(f"Pregunta {st.session_state.current_index + 1} de {total_q}")

        # --- LAYOUT PRINCIPAL (2 Columnas) ---
        # Si ya se respondió, dividimos pantalla. Si no, pantalla completa para la pregunta.
        if st.session_state.answered:
            col_question, col_pdf = st.columns([1, 1.2]) # El PDF un poco más ancho
        else:
            col_question, col_pdf = st.columns([1, 0.01]) # Columna PDF oculta

        with col_question:
            st.markdown(f"### {q['question']}")
            st.markdown(f"**Tema:** *{q.get('topic', 'General')}*")
            
            # Opciones de respuesta
            # Usamos un key único combinando el índice para que no se mezcle
            user_answer = st.radio(
                "Selecciona tu respuesta:", 
                q['options'], 
                key=f"q_{st.session_state.current_index}",
                disabled=st.session_state.answered # Bloquear si ya respondió
            )

            st.markdown("---")

            # BOTONES DE ACCIÓN
            if not st.session_state.answered:
                if st.button("✅ Validar Respuesta"):
                    st.session_state.answered = True
                    if user_answer == q['answer']:
                        st.session_state.score += 1
                    st.rerun() # Recargamos para mostrar el PDF en la otra columna
            else:
                # MOSTRAR FEEDBACK
                if user_answer == q['answer']:
                    st.markdown(f"<div class='success-text'>✅ ¡Correcto!</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='error-text'>❌ Incorrecto</div>", unsafe_allow_html=True)
                    st.markdown(f"**La respuesta correcta era:** {q['answer']}")
                
                st.info(f"💡 **Explicación:** {q.get('explanation', 'Consultar PDF.')}")

                # Botón Siguiente
                if st.button("➡️ Siguiente Pregunta", type="primary"):
                    st.session_state.current_index += 1
                    st.session_state.answered = False
                    st.rerun()

        # COLUMNA DERECHA (VISOR PDF)
        with col_pdf:
            if st.session_state.answered:
                pdf_file = q.get('source_file')
                page_num = q.get('page', 1)
                
                if pdf_file:
                    st.markdown(f"### 📄 Fuente: {pdf_file}")
                    # Renderizar el PDF
                    html_viewer = get_pdf_viewer(pdf_file, page_num)
                    st.markdown(html_viewer, unsafe_allow_html=True)