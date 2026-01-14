import streamlit as st
import json
import os
import base64

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Simulador Máster ORP", layout="wide")

# --- 2. FUNCIONES ---
def get_pdf_viewer(pdf_name, page_num):
    """Muestra PDF usando embed para máxima compatibilidad."""
    pdf_path = os.path.join("static", pdf_name)
    if not os.path.exists(pdf_path):
        return f"<div style='color:red; background:#ffebee; padding:10px;'>⚠️ <b>Error:</b> No encuentro {pdf_name} en la carpeta static/</div>"
    
    try:
        with open(pdf_path, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode('utf-8')
        return f'<embed src="data:application/pdf;base64,{base64_pdf}#page={page_num}" type="application/pdf" width="100%" height="800px" />'
    except:
        return "Error al cargar PDF."

def reset_state():
    """Reinicia el contador al cambiar de asignatura."""
    st.session_state.current_index = 0
    st.session_state.score = 0
    st.session_state.answered = False

# --- 3. BARRA LATERAL (DEBUG Y SELECCIÓN) ---
st.sidebar.title("🎛️ Panel de Control")

# Selector de Asignatura (con callback para resetear)
asignatura = st.sidebar.selectbox(
    "Selecciona Asignatura:", 
    ["Psicosociologia", "Ergonomia"],
    on_change=reset_state 
)

# Verificar rutas (DIAGNÓSTICO AUTOMÁTICO)
data_folder = f"data/{asignatura}/"
if not os.path.exists(data_folder):
    st.error(f"🚨 ¡ALERTA! No encuentro la carpeta: {data_folder}")
    st.stop() # Detiene la app si no hay carpeta

# Cargar archivos JSON
files = sorted([f for f in os.listdir(data_folder) if f.endswith('.json')])
if not files:
    st.sidebar.error(f"❌ La carpeta {data_folder} está vacía. ¡Mete los JSON!")
    st.stop()

# Multiselect para Unidades
selected_files = st.sidebar.multiselect("Selecciona Unidades:", files, default=files)

# Botón de Pánico (Reset manual)
if st.sidebar.button("💀 REINICIAR TODO (Si se traba)"):
    reset_state()
    st.rerun()

# --- 4. LÓGICA PRINCIPAL ---
if not selected_files:
    st.warning("👈 ¡Selecciona algo en la izquierda para empezar, no seas tímido!")
else:
    # Cargar preguntas
    all_questions = []
    for f_name in selected_files:
        try:
            with open(os.path.join(data_folder, f_name), 'r', encoding='utf-8') as f:
                content = json.load(f)
                if isinstance(content, list):
                    all_questions.extend(content)
        except json.JSONDecodeError:
            st.error(f"Error: El archivo {f_name} está mal escrito (error de sintaxis JSON).")

    if not all_questions:
        st.error("No hay preguntas cargadas. Revisa que los JSON no estén vacíos.")
    else:
        # Inicializar sesión si no existe
        if 'current_index' not in st.session_state: reset_state()

        # Control de índice válido
        idx = st.session_state.current_index
        if idx >= len(all_questions):
            st.balloons()
            st.success(f"¡Terminaste! Puntuación: {st.session_state.score}/{len(all_questions)}")
            if st.button("Empezar de nuevo"):
                reset_state()
                st.rerun()
        else:
            q = all_questions[idx]
            
            # --- INTERFAZ DE PREGUNTA ---
            # Usamos columnas: Izquierda (Pregunta) | Derecha (PDF solo si es necesario)
            if st.session_state.answered:
                c1, c2 = st.columns([1, 1])
            else:
                c1, c2 = st.columns([1, 0.01]) # Columna 2 invisible

            with c1:
                st.progress((idx + 1) / len(all_questions))
                st.markdown(f"**Tema:** {q.get('topic', 'General')}")
                st.subheader(f"Pregunta {idx + 1}: {q['question']}")
                
                # Opciones (key dinámica para que no se trabe)
                user_ans = st.radio("Respuesta:", q['options'], key=f"q_{idx}_{asignatura}")
                
                # Botones
                if not st.session_state.answered:
                    if st.button("✅ Validar", use_container_width=True):
                        st.session_state.answered = True
                        if user_ans == q['answer']:
                            st.session_state.score += 1
                        st.rerun()
                else:
                    if user_ans == q['answer']:
                        st.success("¡CORRECTO!")
                    else:
                        st.error(f"INCORRECTO. Era: {q['answer']}")
                    
                    st.info(f"📝 {q.get('explanation', '')}")
                    
                    if st.button("➡️ Siguiente", type="primary", use_container_width=True):
                        st.session_state.current_index += 1
                        st.session_state.answered = False
                        st.rerun()

            # --- VISOR PDF (Derecha) ---
            with c2:
                if st.session_state.answered:
                    pdf_file = q.get('source_file')
                    if pdf_file:
                        st.markdown(f"**Fuente:** `{pdf_file}`")
                        st.markdown(get_pdf_viewer(pdf_file, q.get('page', 1)), unsafe_allow_html=True)