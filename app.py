import streamlit as st
import json
import os
import base64

# Configuración de página
st.set_page_config(page_title="MASTER_ORP - Tu Pase al Éxito", layout="wide")

def display_pdf(file_path, page):
    """Muestra el PDF embebido en la app"""
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    
    # El parámetro #page=X permite abrir el PDF en la página específica
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}#page={page}" width="100%" height="600" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

# Título y Estilo
st.title("🚀 MASTER_ORP: Entrenamiento Ninja")
st.markdown("---")

# Selección de Asignatura
asignatura = st.sidebar.selectbox("Elige tu veneno:", ["Psicosociologia", "Ergonomia"])
data_path = f"data/{asignatura}/"

# Cargar archivos de la carpeta
if os.path.exists(data_path):
    files = [f for f in os.listdir(data_path) if f.endswith('.json')]
    selected_files = st.sidebar.multiselect("Selecciona Unidades:", files, default=files[0] if files else None)
    
    all_questions = []
    for file in selected_files:
        with open(os.path.join(data_path, file), 'r', encoding='utf-8') as f:
            all_questions.extend(json.load(f))

    if not all_questions:
        st.warning("No hay preguntas en esta selección, ojt!")
    else:
        # Estado del juego
        if 'current_q' not in st.session_state:
            st.session_state.current_q = 0
            st.session_state.score = 0

        q_idx = st.session_state.current_q
        
        if q_idx < len(all_questions):
            q = all_questions[q_idx]
            
            st.subheader(f"Pregunta {q_idx + 1} de {len(all_questions)}")
            st.info(f"**Tópico:** {q.get('topic', 'General')}")
            st.write(f"### {q['question']}")
            
            # Opciones
            ans = st.radio("Cual es la buena?", q['options'], key=f"q_{q_idx}")
            
            if st.button("Revisar respuesta"):
                if ans == q['answer']:
                    st.success("¡A huevo! Estás perro.")
                    st.session_state.score += 1
                else:
                    st.error(f"¡Ni madres! La buena era: {q['answer']}")
                
                # Feedback y Referencias
                st.write(f"**Explicación:** {q.get('explanation', 'No hay explicación, búscala tú.')}")
                
                # BOTÓN MÁGICO PARA EL PDF
                pdf_name = q.get('source_file')
                page_num = q.get('page', 1)
                pdf_path = f"static/{pdf_name}"

                if pdf_name and os.path.exists(pdf_path):
                    st.markdown(f"**Fuente:** {pdf_name} (Pág. {page_num})")
                    if st.button(f"📖 Ver evidencia en {pdf_name}"):
                        display_pdf(pdf_path, page_num)
                else:
                    st.warning(f"⚠️ No encontré el archivo: {pdf_name} en la carpeta static.")

                if st.button("Siguiente pregunta ➡️"):
                    st.session_state.current_q += 1
                    st.rerun()
        else:
            st.balloons()
            st.success(f"¡Terminaste! Sacaste {st.session_state.score} de {len(all_questions)}")
            if st.button("Reiniciar"):
                st.session_state.current_q = 0
                st.session_state.score = 0
                st.rerun()
else:
    st.error(f"No veo la carpeta {data_path}. Checa el pinche GitHub.")