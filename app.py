import streamlit as st
import json
import os
import base64

# ---------------------------------------------------------
# 1. CONFIGURACIÓN
# ---------------------------------------------------------
st.set_page_config(page_title="Simulador Máster ORP", layout="wide")

# Estilos CSS
st.markdown("""
    <style>
    .block-container {padding-top: 1rem; padding-bottom: 5rem;}
    div.stButton > button {width: 100%; border-radius: 6px; font-weight: bold; height: 3em;}
    .correct {background-color: #d4edda; color: #155724; padding: 15px; border-radius: 8px; border: 1px solid #c3e6cb; margin-bottom: 10px;}
    .incorrect {background-color: #f8d7da; color: #721c24; padding: 15px; border-radius: 8px; border: 1px solid #f5c6cb; margin-bottom: 10px;}
    .source-box {background-color: #e3f2fd; padding: 10px; border-radius: 5px; border-left: 5px solid #2196f3;}
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. GESTIÓN DE ESTADO (Para que no se trabe)
# ---------------------------------------------------------
if 'index' not in st.session_state: st.session_state.index = 0
if 'score' not in st.session_state: st.session_state.score = 0
if 'validated' not in st.session_state: st.session_state.validated = False
# Guardamos la asignatura anterior para detectar cambios
if 'last_asignatura' not in st.session_state: st.session_state.last_asignatura = ""

def reset_quiz():
    """Reinicia el contador a 0."""
    st.session_state.index = 0
    st.session_state.score = 0
    st.session_state.validated = False

# ---------------------------------------------------------
# 3. BARRA LATERAL
# ---------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Configuración")
    
    asignatura = st.selectbox("1️⃣ Asignatura:", ["Psicosociologia", "Ergonomia"])
    
    # Detector de cambio de asignatura para reiniciar
    if asignatura != st.session_state.last_asignatura:
        st.session_state.last_asignatura = asignatura
        reset_quiz()
        st.rerun()

    # Cargar Archivos
    data_path = f"data/{asignatura}"
    if os.path.exists(data_path):
        all_files = sorted([f for f in os.listdir(data_path) if f.endswith(".json")])
        selected_files = st.multiselect("2️⃣ Unidades:", all_files, default=all_files)
    else:
        st.error(f"⚠️ No encuentro la carpeta data/{asignatura}")
        selected_files = []

    st.markdown("---")
    st.metric("Puntuación", f"{st.session_state.score}")
    if st.button("🔄 Reiniciar desde Cero"):
        reset_quiz()
        st.rerun()

# ---------------------------------------------------------
# 4. CARGA DE DATOS
# ---------------------------------------------------------
quiz_data = []
if selected_files:
    for f in selected_files:
        try:
            with open(os.path.join(data_path, f), "r", encoding="utf-8") as file:
                quiz_data.extend(json.load(file))
        except:
            st.error(f"Error cargando {f}")

# ---------------------------------------------------------
# 5. ÁREA PRINCIPAL
# ---------------------------------------------------------
if not quiz_data:
    st.info("👈 Selecciona unidades en el menú izquierdo para comenzar.")
else:
    # Asegurar índice válido
    if st.session_state.index >= len(quiz_data):
        st.balloons()
        st.success(f"🎉 ¡Examen Finalizado! Puntuación: {st.session_state.score}/{len(quiz_data)}")
        if st.button("Volver a empezar"):
            reset_quiz()
            st.rerun()
    else:
        q = quiz_data[st.session_state.index]
        
        # Barra de progreso
        st.progress((st.session_state.index + 1) / len(quiz_data))
        st.caption(f"Pregunta {st.session_state.index + 1} de {len(quiz_data)}")

        # --- DISEÑO DE COLUMNAS ---
        # Si ya validamos, mostramos el PDF a la derecha. Si no, pantalla completa para leer bien.
        if st.session_state.validated:
            col1, col2 = st.columns([1, 1.2])
        else:
            col1, col2 = st.columns([1, 0.01])

        with col1:
            st.subheader(q.get("question"))
            st.markdown(f"**Tema:** *{q.get('topic')}*")
            
            # Opciones (Key única para evitar conflictos)
            user_choice = st.radio(
                "Tu respuesta:", 
                q.get("options"), 
                key=f"q_{st.session_state.index}",
                disabled=st.session_state.validated
            )

            st.markdown("<br>", unsafe_allow_html=True)

            if not st.session_state.validated:
                if st.button("✅ Comprobar", type="primary"):
                    st.session_state.validated = True
                    if user_choice == q.get("answer"):
                        st.session_state.score += 1
                    st.rerun()
            else:
                # FEEDBACK
                if user_choice == q.get("answer"):
                    st.markdown(f"<div class='correct'>✅ <b>¡Correcto!</b></div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='incorrect'>❌ <b>Incorrecto</b><br>La correcta era: <b>{q.get('answer')}</b></div>", unsafe_allow_html=True)
                
                with st.expander("💡 Ver Explicación", expanded=True):
                    st.write(q.get("explanation"))

                if st.button("➡️ Siguiente Pregunta", type="primary"):
                    st.session_state.index += 1
                    st.session_state.validated = False
                    st.rerun()

        # --- VISOR PDF (COLUMNA DERECHA) ---
        with col2:
            if st.session_state.validated:
                pdf_name = q.get("source_file")
                page = q.get("page", 1)
                
                if pdf_name:
                    pdf_url = f"app/static/{pdf_name}" # Ruta relativa mágica de Streamlit
                    
                    st.markdown(f"""
                    <div class="source-box">
                        📄 <b>Fuente:</b> {pdf_name} (Pág. {page})
                    </div>
                    """, unsafe_allow_html=True)

                    # INTENTO 1: Visor incrustado ligero
                    # Usamos iframe apuntando a la ruta estática directa
                    pdf_display = f'<iframe src="static/{pdf_name}#page={page}" width="100%" height="700px" style="border:none;"></iframe>'
                    
                    # INTENTO 2: Si el iframe falla, aquí está el botón de rescate
                    st.markdown(pdf_display, unsafe_allow_html=True)
                    
                    st.markdown(f"""
                    <br>
                    <a href="static/{pdf_name}" target="_blank" style="
                        display: inline-block;
                        padding: 10px 20px;
                        background-color: #6c757d;
                        color: white;
                        text-decoration: none;
                        border-radius: 5px;
                        font-weight: bold;
                        text-align: center;
                        width: 100%;">
                        ⚠️ ¿No se ve el PDF? Haz clic aquí para abrirlo
                    </a>
                    """, unsafe_allow_html=True)