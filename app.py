import streamlit as st
import json
import os
import base64

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="MASTER_ORP - Entrenamiento Pro", layout="wide")

# Estilo personalizado para botones
st.markdown("""
    <style>
    div.stButton > button:first-child { background-color: #007bff; color: white; }
    div.stButton > button:hover { background-color: #0056b3; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIONES ---
def get_pdf_display(pdf_path, page):
    """Genera el código HTML para embeber el PDF"""
    try:
        with open(pdf_path, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode('utf-8')
        # Añadimos el parámetro de página al final del src
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}#page={page}" width="100%" height="800" type="application/pdf"></iframe>'
        return pdf_display
    except Exception as e:
        return f"Error al cargar el PDF: {e}"

# --- INICIO DE LA APP ---
st.title("🚀 MASTER_ORP: Tu Entrenador Personal")

# Selección de Asignatura en el Sidebar
asignatura = st.sidebar.selectbox("¿Qué vamos a estudiar hoy?", ["Psicosociologia", "Ergonomia"])
data_path = f"data/{asignatura}/"

if os.path.exists(data_path):
    files = sorted([f for f in os.listdir(data_path) if f.endswith('.json')])
    selected_files = st.sidebar.multiselect("Selecciona las unidades:", files, default=files if files else None)
    
    # Cargar todas las preguntas de los archivos seleccionados
    all_questions = []
    for file in selected_files:
        with open(os.path.join(data_path, file), 'r', encoding='utf-8') as f:
            all_questions.extend(json.load(f))

    if not all_questions:
        st.warning("Selecciona al menos una unidad para empezar, carnal.")
    else:
        # Inicializar variables de estado
        if 'current_q' not in st.session_state:
            st.session_state.current_q = 0
            st.session_state.score = 0
            st.session_state.answered = False

        q_idx = st.session_state.current_q
        
        if q_idx < len(all_questions):
            q = all_questions[q_idx]
            
            # Layout: Pregunta a la izquierda, PDF a la derecha (opcional)
            col1, col2 = st.columns([1, 1] if st.session_state.answered else [1, 0.01])
            
            with col1:
                st.markdown(f"**Unidad:** {q.get('topic', 'General')}")
                st.write(f"### Pregunta {q_idx + 1}: {q['question']}")
                
                # Opciones de respuesta
                options = q['options']
                user_ans = st.radio("Selecciona la respuesta correcta:", options, key=f"radio_{q_idx}")
                
                if st.button("Validar Respuesta"):
                    st.session_state.answered = True
                
                if st.session_state.answered:
                    if user_ans == q['answer']:
                        st.success("✅ ¡A huevo! Correcto.")
                    else:
                        st.error(f"❌ ¡Pendejo! Era: {q['answer']}")
                    
                    st.info(f"**Explicación:** {q.get('explanation', 'Revisa la fuente para más detalle.')}")
                    
                    # Verificar si existe el PDF
                    pdf_name = q.get('source_file')
                    page_num = q.get('page', 1)
                    pdf_path = f"static/{pdf_name}"
                    
                    if pdf_name and os.path.exists(pdf_path):
                        st.write(f"📍 Fuente: **{pdf_name}** - Página: **{page_num}**")
                    else:
                        st.warning(f"⚠️ Archivo {pdf_name} no encontrado en /static")

                    if st.button("Siguiente Pregunta ➡️"):
                        st.session_state.current_q += 1
                        st.session_state.answered = False
                        st.rerun()

            with col2:
                # Si ya contestó y el archivo existe, mostramos el visor
                if st.session_state.answered:
                    pdf_name = q.get('source_file')
                    pdf_path = f"static/{pdf_name}"
                    if pdf_name and os.path.exists(pdf_path):
                        st.markdown("### 📖 Evidencia del PDF")
                        pdf_html = get_pdf_display(pdf_path, q.get('page', 1))
                        st.markdown(pdf_html, unsafe_allow_html=True)

        else:
            st.balloons()
            st.success(f"¡Examen terminado! Puntuación: {st.session_state.score} de {len(all_questions)}")
            if st.button("Reiniciar Entrenamiento"):
                st.session_state.current_q = 0
                st.session_state.score = 0
                st.session_state.answered = False
                st.rerun()
else:
    st.error(f"No encontré la carpeta {data_path}. Revisa que en GitHub esté todo en minúsculas.")