import streamlit as st
import json
import random
import os
import importlib.util

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Plataforma Master ORP", layout="wide", page_icon="🛡️")

# --- ESTILOS CSS ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    h1 { color: #0f172a; }
    .stButton>button { width: 100%; border-radius: 6px; font-weight: 600; }
    div.stButton > button:first-child { background-color: #2563eb; color: white; border: none; }
    div.stButton > button:first-child:hover { background-color: #1d4ed8; }
    
    /* Estilo para la caja de explicación */
    .explanation-box {
        background-color: #fff3cd;
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid #ffc107;
        color: #856404;
        margin-top: 10px;
        margin-bottom: 10px;
    }
    .source-tag {
        font-size: 0.8em;
        color: #6c757d;
        font-style: italic;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ Plataforma Integral - Master ORP")

# --- FUNCIONES DE CARGA ---
def load_tool(tool_name):
    """Carga dinámica de herramientas desde la carpeta tools"""
    tool_path = f"tools/{tool_name}.py"
    if os.path.exists(tool_path):
        spec = importlib.util.spec_from_file_location(tool_name, tool_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    return None

def load_data(base_path, subject, selected_units):
    """Carga las preguntas de los JSON seleccionados"""
    pool = []
    # Mapeo de nombres de archivo a nombres legibles si es necesario
    for unit_file in selected_units:
        path = os.path.join(base_path, subject, unit_file)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Añadimos metadatos a cada pregunta para saber de dónde viene
                for q in data:
                    q['unit_source'] = unit_file.replace('.json', '').replace('_', ' ').title()
                pool.extend(data)
        except Exception as e:
            st.error(f"Error cargando {unit_file}: {e}")
    return pool

# --- BARRA LATERAL (NAVEGACIÓN) ---
st.sidebar.header("🗂️ Navegación")
data_folder = 'data'
if not os.path.exists(data_folder): os.makedirs(data_folder)

# 1. Selector de Asignatura (Ergonomia / Psicosociologia)
subjects = sorted([d for d in os.listdir(data_folder) if os.path.isdir(os.path.join(data_folder, d))])
if not subjects:
    st.error("No hay carpetas en /data. Crea 'Ergonomia' y 'Psicosociologia'.")
    st.stop()

selected_subject = st.sidebar.selectbox("Asignatura:", subjects)
subject_path = os.path.join(data_folder, selected_subject)

# Obtenemos los archivos JSON disponibles en esa asignatura
unit_files = sorted([f for f in os.listdir(subject_path) if f.endswith('.json')])

# 2. Selector de MODO
st.sidebar.markdown("---")
mode = st.sidebar.radio("📍 Selecciona Modo:", 
    ["🎓 Simulador de Proyectos (Casos)", "📝 Zona de Estudio (Quiz)", "🧰 Laboratorio Libre (Herramientas)"])

# ==============================================================================
# MODO 1: SIMULADOR DE PROYECTOS (AEC)
# ==============================================================================
if mode == "🎓 Simulador de Proyectos (Casos)":
    cases_module = load_tool("cases_engine")
    if cases_module:
        cases_module.render_simulator()
    else:
        st.error("⚠️ No se encuentra 'tools/cases_engine.py'.")

# ==============================================================================
# MODO 2: ZONA DE ESTUDIO (QUIZ MEJORADO)
# ==============================================================================
elif mode == "📝 Zona de Estudio (Quiz)":
    st.header(f"📝 Test de {selected_subject}")
    
    # Configuración del Test
    st.sidebar.subheader("⚙️ Configuración")
    use_all = st.sidebar.checkbox("Estudiar TODO (Todas las unidades)", value=True)
    
    target_units = unit_files if use_all else st.sidebar.multiselect("Selecciona Unidades:", unit_files)
    
    if not target_units:
        st.info("👈 Selecciona unidades en el menú lateral para empezar.")
    else:
        # Cargar preguntas
        all_questions = load_data(data_folder, selected_subject, target_units)
        
        if not all_questions:
            st.warning("No se encontraron preguntas en los archivos seleccionados.")
        else:
            qty = st.sidebar.slider("Número de preguntas:", 1, len(all_questions), min(10, len(all_questions)))
            
            # Botón de Inicio
            if st.sidebar.button("▶️ COMENZAR TEST", key="start_quiz"):
                st.session_state.exam = random.sample(all_questions, qty)
                st.session_state.answers = {}
                st.session_state.corrected = False
                st.rerun()

    # Renderizado del Examen
    if 'exam' in st.session_state and st.session_state.exam:
        # Si cambiamos de asignatura, limpiamos el examen para evitar errores
        if 'unit_source' in st.session_state.exam[0]:
            # Chequeo simple para ver si las preguntas actuales coinciden con la asignatura
            pass 

        with st.form("test_form"):
            for i, q in enumerate(st.session_state.exam):
                st.markdown(f"**{i+1}. {q['question']}**")
                
                # Recuperar respuesta previa si existe
                prev_ans = st.session_state.answers.get(i, None)
                st.session_state.answers[i] = st.radio(
                    "Selecciona una opción:", 
                    q['options'], 
                    key=f"q{i}", 
                    index=None if not prev_ans else q['options'].index(prev_ans)
                )
                st.markdown("---")
            
            submit = st.form_submit_button("Corregir Examen")
            if submit:
                st.session_state.corrected = True
                st.rerun()

        # --- PANTALLA DE CORRECCIÓN (AQUÍ ESTÁ LA MEJORA) ---
        if st.session_state.corrected:
            score = 0
            st.markdown("## 📊 Resultados Detallados")
            
            for i, q in enumerate(st.session_state.exam):
                user_ans = st.session_state.answers.get(i)
                correct_ans = q['answer']
                is_correct = (user_ans == correct_ans)
                
                if is_correct:
                    score += 1
                    st.success(f"✅ **Pregunta {i+1}: CORRECTA**")
                else:
                    st.error(f"❌ **Pregunta {i+1}: INCORRECTA**")
                
                # Mostrar la pregunta y respuestas
                st.markdown(f"**P:** {q['question']}")
                st.markdown(f"Your answer: `{user_ans}`")
                st.markdown(f"Correct answer: `{correct_ans}`")
                
                # --- CAJA DE EXPLICACIÓN (PEDAGOGÍA) ---
                explanation_html = f"""
                <div class="explanation-box">
                    <strong>💡 Explicación:</strong><br>
                    {q.get('explanation', 'Sin explicación disponible.')}
                </div>
                """
                st.markdown(explanation_html, unsafe_allow_html=True)
                
                # --- BOTÓN DE FUENTE (PDF) ---
                if 'source_file' in q:
                    pdf_file = q['source_file']
                    pdf_path = os.path.join("static", pdf_file)
                    page_num = q.get('page', '?')
                    
                    col_source, col_btn = st.columns([3, 1])
                    with col_source:
                        st.markdown(f"<p class='source-tag'>📖 Fuente: {pdf_file} (Pág. {page_num})</p>", unsafe_allow_html=True)
                    
                    with col_btn:
                        if os.path.exists(pdf_path):
                            with open(pdf_path, "rb") as f:
                                st.download_button(
                                    label="Abrir PDF",
                                    data=f,
                                    file_name=pdf_file,
                                    mime="application/pdf",
                                    key=f"btn_pdf_{i}"
                                )
                st.markdown("---")

            # Nota final
            final_grade = (score / len(st.session_state.exam)) * 10
            if final_grade >= 5:
                st.balloons()
                st.metric("Nota Final", f"{final_grade:.1f} / 10", "APROBADO")
            else:
                st.metric("Nota Final", f"{final_grade:.1f} / 10", "SUSPENSO", delta_color="inverse")

# ==============================================================================
# MODO 3: LABORATORIO LIBRE
# ==============================================================================
elif mode == "🧰 Laboratorio Libre (Herramientas)":
    # Catálogo de herramientas manuales
    tools_catalog = {
        "Ergonomia": {
            "Selector de Métodos": "selector",
            "Checklist de Riesgos": "checklist",
            "Calculadora Antropométrica": "antropometria",
            "Método LEST": "lest",
        },
        "Psicosociologia": {} # Aquí podríamos añadir herramientas futuras
    }
    
    available = tools_catalog.get(selected_subject, {})
    
    if not available:
        st.info(f"No hay herramientas sueltas para {selected_subject}. Usa el Simulador.")
    else:
        st.sidebar.subheader("Herramientas Disponibles")
        tool_choice = st.sidebar.selectbox("Abrir herramienta:", ["Seleccionar..."] + list(available.keys()))
        
        if tool_choice != "Seleccionar...":
            mod_name = available[tool_choice]
            mod = load_tool(mod_name)
            if mod:
                # Intentamos ejecutar la función de renderizado estándar
                func_name = f"render_{mod_name}_tool"
                if hasattr(mod, func_name):
                    getattr(mod, func_name)()
                elif hasattr(mod, 'main'):
                    mod.main()
                else:
                    st.error(f"La herramienta {mod_name} no tiene función de entrada.")