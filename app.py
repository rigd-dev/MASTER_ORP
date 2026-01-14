import streamlit as st
import json
import os
import base64

# --- CONFIGURACIÓN PROFESIONAL ---
st.set_page_config(page_title="Simulador MASTER_ORP", layout="wide")

def display_pdf(pdf_path, page):
    """Muestra el PDF de forma profesional"""
    if os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode('utf-8')
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}#page={page}" width="100%" height="800" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
    else:
        st.error(f"Archivo de referencia no encontrado: {os.path.basename(pdf_path)}")

# --- INTERFAZ ---
st.title("🎓 Simulador de Examen - Prevención de Riesgos")
st.sidebar.header("Configuración de Estudio")

asignatura = st.sidebar.selectbox("Asignatura:", ["Psicosociologia", "Ergonomia"])
data_path = f"data/{asignatura}/"

if os.path.exists(data_path):
    files = sorted([f for f in os.listdir(data_path) if f.endswith('.json')])
    selected_files = st.sidebar.multiselect("Unidades a evaluar:", files, default=files)
    
    # Carga de preguntas
    all_qs = []
    for f_name in selected_files:
        try:
            with open(os.path.join(data_path, f_name), 'r', encoding='utf-8') as f:
                all_qs.extend(json.load(f))
        except:
            continue

    if not all_qs:
        st.info("Por favor, selecciona al menos una unidad en el menú lateral.")
    else:
        # Control de estado
        if 'idx' not in st.session_state:
            st.session_state.idx = 0
            st.session_state.answered = False
            st.session_state.score = 0

        curr_q = all_qs[st.session_state.idx]
        
        # Área de Pregunta
        st.markdown(f"**Tópico:** {curr_q.get('topic', 'General')}")
        st.subheader(f"Pregunta {st.session_state.idx + 1} de {len(all_qs)}")
        st.write(curr_q['question'])
        
        user_choice = st.radio("Seleccione la respuesta:", curr_q['options'], key=f"r_{st.session_state.idx}")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Validar Respuesta"):
                st.session_state.answered = True
        with col2:
            if st.button("Siguiente Pregunta ➡️"):
                if st.session_state.idx < len(all_qs) - 1:
                    st.session_state.idx += 1
                    st.session_state.answered = False
                    st.rerun()
                else:
                    st.success(f"Cuestionario finalizado. Puntuación: {st.session_state.score}/{len(all_qs)}")

        # Feedback
        if st.session_state.answered:
            st.divider()
            if user_choice == curr_q['answer']:
                st.success(f"✅ Correcto: {curr_q['answer']}")
            else:
                st.error(f"❌ Incorrecto. La respuesta correcta es: {curr_q['answer']}")
            
            st.info(f"**Explicación técnica:** {curr_q.get('explanation', 'Consulte la fuente adjunta.')}")
            
            # Visor de PDF
            pdf_file = curr_q.get('source_file')
            pdf_p = curr_q.get('page', 1)
            if pdf_file:
                st.markdown(f"### 📄 Documento de Referencia: {pdf_file}")
                display_pdf(f"static/{pdf_file}", pdf_p)
else:
    st.error("Error: No se encontró la carpeta de datos.")