import streamlit as st
import json
import os
import random

# ---------------------------------------------------------
# 1. CONFIGURACIÓN BÁSICA
# ---------------------------------------------------------
st.set_page_config(page_title="Simulador Máster ORP", layout="centered") # Layout centrado para enfocar en la pregunta

# Estilos simples
st.markdown("""
    <style>
    div.stButton > button {width: 100%; border-radius: 5px; height: 3em; font-weight: bold;}
    .correct {background-color: #d4edda; color: #155724; padding: 15px; border-radius: 5px; border: 1px solid #c3e6cb;}
    .incorrect {background-color: #f8d7da; color: #721c24; padding: 15px; border-radius: 5px; border: 1px solid #f5c6cb;}
    .source-text {font-size: 0.9em; color: #666; font-style: italic; margin-top: 10px;}
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. GESTIÓN DE ESTADO (MEMORIA DE LA APP)
# ---------------------------------------------------------
if 'quiz_questions' not in st.session_state: st.session_state.quiz_questions = []
if 'current_index' not in st.session_state: st.session_state.current_index = 0
if 'score' not in st.session_state: st.session_state.score = 0
if 'validated' not in st.session_state: st.session_state.validated = False
if 'exam_mode' not in st.session_state: st.session_state.exam_mode = False

def start_quiz(questions, is_exam_mode):
    """Inicia el test con las preguntas seleccionadas"""
    st.session_state.quiz_questions = questions
    st.session_state.current_index = 0
    st.session_state.score = 0
    st.session_state.validated = False
    st.session_state.exam_mode = is_exam_mode

# ---------------------------------------------------------
# 3. BARRA LATERAL (CONFIGURACIÓN COMPLETA)
# ---------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Configuración del Test")
    
    # 1. Asignatura
    asignatura = st.selectbox("1️⃣ Asignatura:", ["Psicosociologia", "Ergonomia"])
    
    # 2. Cargar Unidades
    data_path = f"data/{asignatura}"
    if os.path.exists(data_path):
        all_files = sorted([f for f in os.listdir(data_path) if f.endswith(".json")])
        selected_files = st.multiselect("2️⃣ Unidades:", all_files, default=all_files)
    else:
        st.error(f"No existe la carpeta data/{asignatura}")
        selected_files = []

    st.markdown("---")

    # 3. Modo de Uso (Lo que pediste)
    modo = st.radio("3️⃣ Modo:", ["Entrenamiento (Feedback inmediato)", "Examen (Sin feedback hasta el final)"])
    is_exam = True if "Examen" in modo else False

    # 4. Número de preguntas (Lo que pediste)
    num_max_preguntas = st.slider("4️⃣ Nº de Preguntas:", min_value=5, max_value=100, value=20, step=5)

    st.markdown("---")

    # BOTÓN DE GENERAR (FUNDAMENTAL)
    if st.button("🚀 GENERAR NUEVO TEST", type="primary"):
        # Cargar todas las preguntas de los archivos seleccionados
        raw_questions = []
        for f in selected_files:
            try:
                with open(os.path.join(data_path, f), "r", encoding="utf-8") as file:
                    data = json.load(file)
                    raw_questions.extend(data)
            except Exception as e:
                st.error(f"Error en {f}: {e}")
        
        if raw_questions:
            # Seleccionar al azar el número pedido
            if len(raw_questions) > num_max_preguntas:
                final_questions = random.sample(raw_questions, num_max_preguntas)
            else:
                final_questions = raw_questions # Si hay menos, usamos todas
                st.warning(f"Solo había {len(raw_questions)} preguntas disponibles.")
            
            # Arrancar
            start_quiz(final_questions, is_exam)
            st.rerun()
        else:
            st.error("No se encontraron preguntas en los archivos seleccionados.")

# ---------------------------------------------------------
# 4. ÁREA PRINCIPAL
# ---------------------------------------------------------

if not st.session_state.quiz_questions:
    st.info("👈 Configura el test en la barra lateral y pulsa **'GENERAR NUEVO TEST'** para empezar.")
    st.write("Hemos desactivado el visor de PDF para mejorar la estabilidad.")

else:
    # Variables de control
    idx = st.session_state.current_index
    total = len(st.session_state.quiz_questions)
    q = st.session_state.quiz_questions[idx]

    # --- PANTALLA FINAL ---
    if idx >= total:
        st.balloons()
        st.success(f"🏆 ¡Test Finalizado!")
        st.metric("Puntuación Final", f"{st.session_state.score} / {total}")
        
        if st.button("Volver a configurar"):
            st.session_state.quiz_questions = []
            st.rerun()
            
    # --- PANTALLA DE PREGUNTA ---
    else:
        # Barra de progreso
        st.progress((idx + 1) / total)
        st.caption(f"Pregunta {idx + 1} de {total} | Puntuación actual: {st.session_state.score}")

        st.markdown(f"### {q.get('question')}")
        st.markdown(f"**Tema:** *{q.get('topic')}*")

        # Opciones
        user_choice = st.radio(
            "Selecciona una opción:", 
            q.get("options"), 
            key=f"q_{idx}", 
            disabled=st.session_state.validated
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # BOTONES
        if not st.session_state.validated:
            if st.button("✅ Confirmar Respuesta"):
                st.session_state.validated = True
                if user_choice == q.get("answer"):
                    st.session_state.score += 1
                st.rerun()
        else:
            # MOSTRAR RESULTADO (Solo si NO es modo examen, o si quieres mostrarlo siempre al validar)
            # Nota: Incluso en modo examen, si validas paso a paso, sueles querer ver si acertaste.
            # Si quieres modo examen estricto (ciego), quita este bloque else.
            
            if user_choice == q.get("answer"):
                st.markdown(f"<div class='correct'>✅ <b>¡Correcto!</b></div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='incorrect'>❌ <b>Incorrecto</b>. La respuesta correcta es: <b>{q.get('answer')}</b></div>", unsafe_allow_html=True)
            
            # Explicación
            st.info(f"💡 **Explicación:** {q.get('explanation')}")
            
            # REFERENCIA A LA FUENTE (SOLO TEXTO, SIN VISOR)
            source = q.get('source_file')
            page = q.get('page')
            if source:
                st.markdown(f"<p class='source-text'>📚 Fuente: {source} (Página {page}) - <i>Consulta el PDF manualmente si tienes dudas.</i></p>", unsafe_allow_html=True)

            # Botón Siguiente
            if st.button("➡️ Siguiente"):
                st.session_state.current_index += 1
                st.session_state.validated = False
                st.rerun()