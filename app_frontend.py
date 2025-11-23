import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go

BASE_URL = "http://127.0.0.1:8000"  # Tu backend local

st.set_page_config(page_title="Plataforma de Vinculación TEVO", layout="wide")

# Inicializar token en sesión
if "token" not in st.session_state:
    st.session_state["token"] = None

# ========================
# Función para crear gráfica de araña
# ========================

def create_radar_chart(radar_data):
    """Crear gráfica de araña/radar para visualizar matching"""
    categories = [
        "Habilidades Técnicas",
        "Habilidades Blandas", 
        "Idiomas",
        "Experiencia",
        "Carrera",
        "Semestre",
        "Modalidad"
    ]
    
    fig = go.Figure()
    
    # Línea de requerimientos (100%)
    fig.add_trace(go.Scatterpolar(
        r=[100] * 7,
        theta=categories,
        fill='toself',
        name='Requerido',
        line_color='rgba(0, 128, 255, 0.3)',
        fillcolor='rgba(0, 128, 255, 0.1)'
    ))
    
    # Línea del candidato
    valores = [
        radar_data.get("Habilidades Técnicas", 0),
        radar_data.get("Habilidades Blandas", 0),
        radar_data.get("Idiomas", 0),
        radar_data.get("Experiencia", 0),
        radar_data.get("Carrera", 0),
        radar_data.get("Semestre", 0),
        radar_data.get("Modalidad", 0)
    ]
    
    fig.add_trace(go.Scatterpolar(
        r=valores,
        theta=categories,
        fill='toself',
        name='Candidato',
        line_color='rgb(0, 204, 102)',
        fillcolor='rgba(0, 204, 102, 0.3)'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        showlegend=True,
        height=400
    )
    
    return fig


# ========================
# Barra lateral
# ========================
if st.session_state.get("token"):
    if st.session_state.get("role") == "estudiante":
        menu = ["Inicio", "Perfil", "Vacantes", "Mi Matching"]
    elif st.session_state.get("role") == "empresa":
        menu = ["Inicio", "Gestión Empresa", "Mis Vacantes", "Candidatos Matched"]
    else:  # admin
        menu = ["Inicio", "Vacantes", "Estadísticas"]
else:
    try:
        st.sidebar.image("logo.png", width=100)
    except:
        pass
    menu = ["Inicio", "Registro", "Login"]

choice = st.sidebar.selectbox("Menú", menu)

# Botón de logout si está logueado
if st.session_state.get("token"):
    if st.sidebar.button("🚪 Cerrar Sesión"):
        st.session_state.clear()
        st.rerun()

# ========================
# Página Inicio
# ========================
if choice == "Inicio":
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700;800&display=swap');
    
    @keyframes gradient {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 0.3; }
        50% { opacity: 0.6; }
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .hero-section {
        position: relative;
        min-height: 600px;
        background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 50%, #0f172a 100%);
        padding: 80px 20px;
        overflow: hidden;
        margin: -6rem -1rem 2rem -1rem;
    }
    
    .bg-blur-1 {
        position: absolute;
        top: 20%;
        left: 20%;
        width: 400px;
        height: 400px;
        background: #3b82f6;
        border-radius: 50%;
        filter: blur(100px);
        animation: pulse 3s ease-in-out infinite;
    }
    
    .bg-blur-2 {
        position: absolute;
        bottom: 20%;
        right: 20%;
        width: 400px;
        height: 400px;
        background: #06b6d4;
        border-radius: 50%;
        filter: blur(100px);
        animation: pulse 3s ease-in-out infinite 1.5s;
    }
    
    .hero-content {
        position: relative;
        z-index: 10;
        text-align: center;
        max-width: 1200px;
        margin: 0 auto;
        animation: fadeIn 1s ease-out;
    }
    
    .hero-title {
        font-family: 'Montserrat', sans-serif;
        font-size: 120px;
        font-weight: 800;
        letter-spacing: 20px;
        background: linear-gradient(45deg, #60a5fa, #06b6d4, #3b82f6);
        background-size: 200% 200%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        animation: gradient 3s ease infinite;
        margin: 0;
        line-height: 1.2;
    }
    
    .hero-divider {
        height: 3px;
        width: 200px;
        background: linear-gradient(90deg, transparent, #06b6d4, transparent);
        margin: 20px auto;
        border-radius: 10px;
    }
    
    .hero-subtitle {
        font-size: 28px;
        color: #06b6d4;
        font-weight: 300;
        margin: 20px 0;
        letter-spacing: 2px;
    }
    
    .hero-description {
        font-size: 20px;
        color: #cbd5e1;
        max-width: 800px;
        margin: 30px auto;
        line-height: 1.8;
    }
    
    .cta-buttons {
        display: flex;
        gap: 20px;
        justify-content: center;
        margin-top: 40px;
        flex-wrap: wrap;
    }
    
    .btn-primary {
        padding: 18px 40px;
        background: linear-gradient(90deg, #06b6d4, #3b82f6);
        color: white;
        text-decoration: none;
        border-radius: 50px;
        font-weight: 600;
        font-size: 18px;
        transition: all 0.3s;
        border: none;
        cursor: pointer;
        box-shadow: 0 10px 30px rgba(6, 182, 212, 0.3);
    }
    
    .btn-primary:hover {
        transform: scale(1.05);
        box-shadow: 0 15px 40px rgba(6, 182, 212, 0.5);
    }
    
    .btn-secondary {
        padding: 18px 40px;
        background: transparent;
        color: #06b6d4;
        text-decoration: none;
        border-radius: 50px;
        font-weight: 600;
        font-size: 18px;
        border: 2px solid #06b6d4;
        transition: all 0.3s;
        cursor: pointer;
    }
    
    .btn-secondary:hover {
        background: rgba(6, 182, 212, 0.1);
        transform: scale(1.05);
    }
    
    .features-section {
        padding: 80px 20px;
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
    }
    
    .section-title {
        font-size: 48px;
        font-weight: 700;
        text-align: center;
        background: linear-gradient(90deg, #06b6d4, #3b82f6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 60px;
    }
    
    .features-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 30px;
        max-width: 1200px;
        margin: 0 auto;
    }
    
    .feature-card {
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid rgba(6, 182, 212, 0.3);
        border-radius: 20px;
        padding: 40px;
        transition: all 0.3s;
        backdrop-filter: blur(10px);
    }
    
    .feature-card:hover {
        transform: translateY(-10px);
        border-color: #06b6d4;
        box-shadow: 0 20px 60px rgba(6, 182, 212, 0.3);
        background: rgba(6, 182, 212, 0.1);
    }
    
    .feature-icon {
        font-size: 48px;
        margin-bottom: 20px;
    }
    
    .feature-title {
        font-size: 24px;
        font-weight: 700;
        color: white;
        margin-bottom: 15px;
    }
    
    .feature-description {
        color: #cbd5e1;
        line-height: 1.6;
        font-size: 16px;
    }
    
    .benefits-section {
        padding: 80px 20px;
        background: rgba(15, 23, 42, 0.5);
    }
    
    .benefits-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
        gap: 40px;
        max-width: 1200px;
        margin: 0 auto;
    }
    
    .benefit-card {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(6, 182, 212, 0.1));
        border: 1px solid rgba(59, 130, 246, 0.3);
        border-radius: 20px;
        padding: 40px;
        transition: all 0.3s;
    }
    
    .benefit-card:hover {
        border-color: #06b6d4;
        transform: translateY(-5px);
    }
    
    .benefit-header {
        display: flex;
        align-items: center;
        gap: 15px;
        margin-bottom: 30px;
    }
    
    .benefit-icon {
        font-size: 40px;
    }
    
    .benefit-title {
        font-size: 28px;
        font-weight: 700;
        color: white;
    }
    
    .benefit-list {
        list-style: none;
        padding: 0;
    }
    
    .benefit-item {
        display: flex;
        align-items: flex-start;
        gap: 15px;
        margin-bottom: 20px;
        color: #cbd5e1;
        font-size: 16px;
        line-height: 1.6;
    }
    
    .benefit-check {
        color: #06b6d4;
        font-size: 24px;
        flex-shrink: 0;
    }
    
    .stats-section {
        padding: 80px 20px;
        background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
    }
    
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 30px;
        max-width: 1200px;
        margin: 0 auto;
    }
    
    .stat-card {
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid rgba(100, 116, 139, 0.3);
        border-radius: 15px;
        padding: 30px;
        text-align: center;
        transition: all 0.3s;
    }
    
    .stat-card:hover {
        border-color: #06b6d4;
        transform: translateY(-5px);
    }
    
    .stat-value {
        font-size: 48px;
        font-weight: 700;
        color: #06b6d4;
        margin-bottom: 10px;
    }
    
    .stat-label {
        color: #94a3b8;
        font-size: 16px;
    }
    
    .cta-section {
        padding: 80px 20px;
        background: rgba(15, 23, 42, 0.5);
    }
    
    .cta-box {
        max-width: 900px;
        margin: 0 auto;
        background: linear-gradient(135deg, rgba(6, 182, 212, 0.2), rgba(59, 130, 246, 0.2));
        border: 1px solid rgba(6, 182, 212, 0.3);
        border-radius: 30px;
        padding: 60px 40px;
        text-align: center;
        backdrop-filter: blur(10px);
    }
    
    .cta-title {
        font-size: 42px;
        font-weight: 700;
        color: white;
        margin-bottom: 20px;
    }
    
    .cta-text {
        font-size: 20px;
        color: #cbd5e1;
        margin-bottom: 40px;
    }
    
    @media (max-width: 768px) {
        .hero-title { font-size: 60px; letter-spacing: 10px; }
        .hero-subtitle { font-size: 20px; }
        .hero-description { font-size: 16px; }
        .section-title { font-size: 36px; }
        .benefits-grid { grid-template-columns: 1fr; }
        .cta-title { font-size: 32px; }
    }
    </style>
    
    <div class="hero-section">
        <div class="bg-blur-1"></div>
        <div class="bg-blur-2"></div>
        <div class="hero-content">
            <h1 class="hero-title">TEVO</h1>
            <div class="hero-divider"></div>
            <p class="hero-subtitle">Talento · Empleo · Vinculación · Oportunidad</p>
            <p class="hero-description">
                La plataforma inteligente que conecta estudiantes talentosos con empresas innovadoras 
                mediante inteligencia artificial y análisis predictivo
            </p>
            <div class="cta-buttons">
                <button class="btn-primary">Comenzar Ahora →</button>
                <button class="btn-secondary">Ver Demo</button>
            </div>
        </div>
    </div>
    
    <div class="features-section">
        <h2 class="section-title">¿Cómo Funciona?</h2>
        <div class="features-grid">
            <div class="feature-card">
                <div class="feature-icon">🧠</div>
                <h3 class="feature-title">Inteligencia Artificial</h3>
                <p class="feature-description">
                    Algoritmos avanzados que analizan perfiles y vacantes para encontrar el match perfecto
                </p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">🎯</div>
                <h3 class="feature-title">Matching Preciso</h3>
                <p class="feature-description">
                    Sistema de compatibilidad que evalúa habilidades, experiencia y preferencias
                </p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">⚡</div>
                <h3 class="feature-title">Proceso Rápido</h3>
                <p class="feature-description">
                    Conecta con oportunidades en segundos, no en semanas
                </p>
            </div>
        </div>
    </div>
    
    <div class="benefits-section">
        <h2 class="section-title">Beneficios para Todos</h2>
        <div class="benefits-grid">
            <div class="benefit-card">
                <div class="benefit-header">
                    <span class="benefit-icon">👥</span>
                    <h3 class="benefit-title">Para Estudiantes</h3>
                </div>
                <ul class="benefit-list">
                    <li class="benefit-item">
                        <span class="benefit-check">✓</span>
                        <span>Perfil profesional personalizado</span>
                    </li>
                    <li class="benefit-item">
                        <span class="benefit-check">✓</span>
                        <span>Matching automático con vacantes</span>
                    </li>
                    <li class="benefit-item">
                        <span class="benefit-check">✓</span>
                        <span>Visualización de compatibilidad</span>
                    </li>
                    <li class="benefit-item">
                        <span class="benefit-check">✓</span>
                        <span>Acceso a oportunidades exclusivas</span>
                    </li>
                </ul>
            </div>
            <div class="benefit-card">
                <div class="benefit-header">
                    <span class="benefit-icon">💼</span>
                    <h3 class="benefit-title">Para Empresas</h3>
                </div>
                <ul class="benefit-list">
                    <li class="benefit-item">
                        <span class="benefit-check">✓</span>
                        <span>Acceso a talento calificado</span>
                    </li>
                    <li class="benefit-item">
                        <span class="benefit-check">✓</span>
                        <span>Filtrado inteligente de candidatos</span>
                    </li>
                    <li class="benefit-item">
                        <span class="benefit-check">✓</span>
                        <span>Análisis de compatibilidad detallado</span>
                    </li>
                    <li class="benefit-item">
                        <span class="benefit-check">✓</span>
                        <span>Reducción de tiempo de contratación</span>
                    </li>
                </ul>
            </div>
        </div>
    </div>
    
    <div class="stats-section">
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">95%</div>
                <div class="stat-label">Precisión en Matching</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">500+</div>
                <div class="stat-label">Estudiantes Activos</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">100+</div>
                <div class="stat-label">Empresas Asociadas</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">80%</div>
                <div class="stat-label">Colocación Exitosa</div>
            </div>
        </div>
    </div>
    
    <div class="cta-section">
        <div class="cta-box">
            <h2 class="cta-title">¿Listo para Encontrar tu Match Perfecto?</h2>
            <p class="cta-text">
                Únete a TEVO hoy y descubre un nuevo mundo de oportunidades
            </p>
            <div class="cta-buttons">
                <button class="btn-primary">Registro de Estudiantes</button>
                <button class="btn-primary">Registro de Empresas</button>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ========================
# Registro de usuario
# ========================
elif choice == "Registro":
    st.title("📝 Registro de Usuario")
    email = st.text_input("Email")
    username = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")
    role = st.selectbox("Rol", ["estudiante", "empresa", "admin"])

    if st.button("Registrar"):
        # Registro de usuario
        payload = {"email": email, "username": username, "password": password, "role": role}
        res = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
        
        if res.status_code == 201:
            st.success("✅ Usuario registrado correctamente")
            
            # Login automático después del registro
            login_payload = {"username": username, "password": password}
            login_res = requests.post(f"{BASE_URL}/api/auth/login", data=login_payload)
            
            if login_res.status_code == 200:
                # Guardar token en session_state
                token = login_res.json()["access_token"]
                st.session_state["token"] = token
                st.session_state["role"] = role
                
                
                # Redirigir según el rol
                if role == "estudiante":
                    st.info("🔄 Redirigiendo al formulario de perfil...")
                    choice = "Perfil"
                    st.rerun()
                elif role == "empresa":
                    st.info("🔄 Redirigiendo a gestión de empresa...")
                    choice = "Gestión Empresa"
                    st.rerun()
            else:
                st.warning("⚠️ Usuario registrado pero error en login automático. Por favor, ve a la página de login.")
        else:
            st.error(f"❌ Error en registro: {res.json()}")

# ========================
# Login
# ========================
elif choice == "Login":
    st.title("🔐 Login")
    username = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")

    if st.button("Ingresar"):
        payload = {"username": username, "password": password}
        res = requests.post(f"{BASE_URL}/api/auth/login", data=payload)
        if res.status_code == 200:
            response_data = res.json()
            token = response_data["access_token"]
            st.session_state["token"] = token
            
            # Obtener el rol del usuario
            headers = {"Authorization": f"Bearer {token}"}
            user_res = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
            if user_res.status_code == 200:
                user_data = user_res.json()
                st.session_state["role"] = user_data.get("role")
                st.success("Login exitoso")
                st.rerun()  # Recargar para actualizar el estado
            else:
                st.error("Error al obtener información del usuario")
        else:
            st.error(res.json())

# ========================
# Mi Matching (Estudiante)
# ========================
elif choice == "Mi Matching":
    st.title("🎯 Mi Compatibilidad con Vacantes")
    token = st.session_state.get("token")
    
    if not token:
        st.warning("⚠️ Primero inicia sesión")
    else:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Obtener vacantes disponibles
        vacantes_res = requests.get(f"{BASE_URL}/api/vacancies/public/all", headers=headers)
        
        if vacantes_res.status_code == 200:
            vacantes = vacantes_res.json()
            
            if not vacantes:
                st.info("📭 No hay vacantes disponibles para matching")
            else:
                st.info(f"📊 {len(vacantes)} vacantes disponibles para análisis")
                
                # Selector de vacante
                vacancy_options = {f"{v.get('titulo')} - {v.get('empresa_nombre')}": v.get('_id') for v in vacantes}
                selected_vacancy = st.selectbox("Selecciona una vacante:", list(vacancy_options.keys()))
                
                if selected_vacancy and st.button("🔍 Calcular Compatibilidad"):
                    vacancy_id = vacancy_options[selected_vacancy]
                    
                    with st.spinner("Calculando compatibilidad..."):
                        # Primero obtener perfil del estudiante
                        profile_res = requests.get(f"{BASE_URL}/api/students/profile", headers=headers)
                        
                        if profile_res.status_code == 200:
                            profile = profile_res.json()
                            matricula = profile.get("matricula")
                            
                            # Ejecutar matching (esto debería crear el match en el backend)
                            # Nota: Necesitarás un endpoint específico para estudiantes
                            match_res = requests.post(
                                f"{BASE_URL}/api/matching/student/calculate",
                                json={"vacancy_id": vacancy_id, "student_matricula": matricula},
                                headers=headers
                            )
                            
                            if match_res.status_code in [200, 201]:
                                match_data = match_res.json()
                                
                                # Mostrar resultado
                                porcentaje = match_data.get("porcentaje_match", 0)
                                
                                # Indicador visual
                                col1, col2, col3 = st.columns([1, 2, 1])
                                with col2:
                                    if porcentaje >= 80:
                                        st.success(f"### 🎉 {porcentaje}% Compatible")
                                        st.success("¡Excelente match! Considera aplicar a esta vacante.")
                                    elif porcentaje >= 60:
                                        st.info(f"### ✅ {porcentaje}% Compatible")
                                        st.info("Buen match. Podrías ser un candidato viable.")
                                    else:
                                        st.warning(f"### ⚠️ {porcentaje}% Compatible")
                                        st.warning("Match moderado. Considera mejorar tu perfil.")
                                
                                # Desglose detallado
                                st.subheader("📊 Desglose de Compatibilidad")
                                desglose = match_data.get("desglose", {})
                                
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.metric("Habilidades Técnicas", f"{desglose.get('habilidades_tecnicas', 0)*100:.0f}%")
                                    st.metric("Habilidades Blandas", f"{desglose.get('habilidades_blandas', 0)*100:.0f}%")
                                    st.metric("Idiomas", f"{desglose.get('idiomas', 0)*100:.0f}%")
                                
                                with col2:
                                    st.metric("Experiencia", f"{desglose.get('experiencia', 0)*100:.0f}%")
                                    st.metric("Carrera", f"{desglose.get('carrera', 0)*100:.0f}%")
                                    st.metric("Semestre", f"{desglose.get('semestre', 0)*100:.0f}%")
                                
                                # Gráfica de araña
                                if "radar_chart_data" in match_data:
                                    st.subheader("📈 Visualización de Compatibilidad")
                                    radar_fig = create_radar_chart(match_data["radar_chart_data"])
                                    st.plotly_chart(radar_fig, use_container_width=True)
                                
                            else:
                                st.error("❌ Error al calcular matching. Asegúrate de tener tu perfil completo.")
                        else:
                            st.error("❌ No se pudo obtener tu perfil. Complétalo primero.")
        else:
            st.error("❌ Error al obtener vacantes")

# ========================
# Candidatos Matched (Empresa)
# ========================
elif choice == "Candidatos Matched":
    st.title("📊 Candidatos Compatibles")
    
    token = st.session_state.get("token")
    if not token:
        st.warning("Primero inicia sesión")
    else:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Seleccionar vacante
        vacantes_res = requests.get(f"{BASE_URL}/api/vacancies/my-vacancies", headers=headers)
        
        if vacantes_res.status_code == 200:
            vacantes = vacantes_res.json()
            
            if vacantes:
                vacancy_options = {v['titulo']: v['_id'] for v in vacantes}
                selected_vacancy_title = st.selectbox("Selecciona una vacante", list(vacancy_options.keys()))
                selected_vacancy_id = vacancy_options[selected_vacancy_title]
                
                # Obtener matches de la vacante
                matches_res = requests.get(
                    f"{BASE_URL}/api/matching/vacancy/{selected_vacancy_id}/matches",
                    headers=headers
                )
                
                if matches_res.status_code == 200:
                    matches_data = matches_res.json()
                    
                    st.success(f"✅ {matches_data['total_matches']} candidatos encontrados")
                    
                    for match in matches_data['matches']:
                        with st.expander(f"🎓 Candidato {match['student_matricula']} - {match['porcentaje_match']:.1f}% Compatible"):
                            col1, col2 = st.columns([2, 1])
                            
                            with col1:
                                st.write(f"**Carrera:** {match['carrera']}")
                                st.write(f"**Semestre:** {match['semestre']}")
                                st.write(f"**Modalidad:** {match['modalidad_preferida']}")
                                st.write(f"**Experiencia:** {'Sí' if match['tiene_experiencia'] else 'No'}")
                                
                                st.write("**Habilidades Técnicas:**")
                                st.write(", ".join(match['habilidades_tecnicas']))
                                
                                st.write("**Habilidades Blandas:**")
                                st.write(", ".join(match['habilidades_blandas']))
                                
                                # Idiomas
                                if match['idiomas']:
                                    st.write("**Idiomas:**")
                                    for idioma in match['idiomas']:
                                        st.write(f"- {idioma['idioma']}: {idioma['nivel']}")
                            
                            with col2:
                                # Gráfica de compatibilidad
                                st.write("**Desglose de Match:**")
                                desglose = match['desglose']
                                st.progress(desglose['habilidades_tecnicas'], text=f"Téc: {desglose['habilidades_tecnicas']*100:.0f}%")
                                st.progress(desglose['habilidades_blandas'], text=f"Blandas: {desglose['habilidades_blandas']*100:.0f}%")
                                st.progress(desglose['idiomas'], text=f"Idiomas: {desglose['idiomas']*100:.0f}%")
                                st.progress(desglose['experiencia'], text=f"Exp: {desglose['experiencia']*100:.0f}%")
                            
                            # ⭐ BOTÓN DE SOLICITAR CONTACTO
                            st.write("---")
                            
                            # Verificar si ya existe una solicitud
                            requests_res = requests.get(
                                f"{BASE_URL}/api/contact-requests/my-requests",
                                headers=headers
                            )
                            
                            existing_request = None
                            if requests_res.status_code == 200:
                                all_requests = requests_res.json()['solicitudes']
                                existing_request = next(
                                    (r for r in all_requests 
                                     if r['student_matricula'] == match['student_matricula']),
                                    None
                                )
                            
                            if existing_request:
                                # Ya existe una solicitud
                                estado_colors = {
                                    "pendiente": "🟡",
                                    "aprobada": "🟢",
                                    "rechazada": "🔴"
                                }
                                estado = existing_request['estado']
                                st.info(f"{estado_colors.get(estado, '⚪')} Solicitud {estado}")
                                
                                if estado == "aprobada":
                                    # Mostrar botón para ver contacto
                                    if st.button(f"📞 Ver Información de Contacto", key=f"contact_{match['_id']}"):
                                        contact_res = requests.get(
                                            f"{BASE_URL}/api/contact-requests/student-contact/{existing_request['_id']}",
                                            headers=headers
                                        )
                                        
                                        if contact_res.status_code == 200:
                                            contact_info = contact_res.json()
                                            st.success("✅ Información de Contacto Aprobada")
                                            st.write(f"**Nombre:** {contact_info['nombre_completo']}")
                                            st.write(f"**Email:** {contact_info['email']}")
                                            st.write(f"**Teléfono:** {contact_info['telefono']}")
                                            
                                            if contact_info.get('linkedin'):
                                                st.write(f"**LinkedIn:** {contact_info['linkedin']}")
                                            if contact_info.get('github'):
                                                st.write(f"**GitHub:** {contact_info['github']}")
                                            if contact_info.get('cv_url'):
                                                st.write(f"**CV:** [Descargar]({contact_info['cv_url']})")
                                        else:
                                            st.error("Error al obtener información de contacto")
                                
                                elif estado == "rechazada":
                                    st.error("❌ Solicitud rechazada por el administrador")
                                
                            else:
                                # No existe solicitud, mostrar botón para crear
                                with st.form(key=f"request_form_{match['_id']}"):
                                    motivo = st.text_area(
                                        "Motivo de la solicitud (opcional)",
                                        placeholder="Ej: El perfil del candidato es ideal para nuestro equipo de desarrollo...",
                                        max_chars=500
                                    )
                                    
                                    submitted = st.form_submit_button("🤝 Solicitar Contacto con este Candidato")
                                    
                                    if submitted:
                                        payload = {
                                            "vacancy_id": selected_vacancy_id,
                                            "student_matricula": match['student_matricula'],
                                            "motivo": motivo if motivo else None
                                        }
                                        
                                        create_res = requests.post(
                                            f"{BASE_URL}/api/contact-requests/request",
                                            json=payload,
                                            headers=headers
                                        )
                                        
                                        if create_res.status_code == 201:
                                            st.success("✅ Solicitud enviada al administrador")
                                            st.info("💡 Recibirás notificación cuando sea aprobada")
                                            st.rerun()
                                        else:
                                            st.error(f"Error: {create_res.json().get('detail', 'Error desconocido')}")
                    
                else:
                    st.error("Error al obtener matches")
            else:
                st.info("No tienes vacantes publicadas aún")
        else:
            st.error("Error al obtener vacantes")


# También agrega una nueva sección para ver todas las solicitudes
elif choice == "Mis Solicitudes":
    st.title("📋 Mis Solicitudes de Contacto")
    
    token = st.session_state.get("token")
    if not token:
        st.warning("Primero inicia sesión")
    else:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Filtro de estado
        estado_filter = st.selectbox(
            "Filtrar por estado",
            ["Todas", "pendiente", "aprobada", "rechazada"]
        )
        
        # Obtener solicitudes
        params = {}
        if estado_filter != "Todas":
            params["estado"] = estado_filter
        
        res = requests.get(
            f"{BASE_URL}/api/contact-requests/my-requests",
            headers=headers,
            params=params
        )
        
        if res.status_code == 200:
            data = res.json()
            
            # Mostrar estadísticas
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total", data['total'])
            with col2:
                st.metric("Pendientes", data['pendientes'])
            with col3:
                st.metric("Aprobadas", data['aprobadas'])
            with col4:
                st.metric("Rechazadas", data['rechazadas'])
            
            st.write("---")
            
            # Mostrar solicitudes
            if data['solicitudes']:
                for solicitud in data['solicitudes']:
                    estado_colors = {
                        "pendiente": "🟡",
                        "aprobada": "🟢",
                        "rechazada": "🔴"
                    }
                    
                    with st.expander(f"{estado_colors[solicitud['estado']]} {solicitud['vacancy_titulo']} - {solicitud['student_matricula']}"):
                        st.write(f"**Estado:** {solicitud['estado'].upper()}")
                        st.write(f"**Fecha de solicitud:** {solicitud['fecha_solicitud']}")
                        
                        if solicitud.get('motivo'):
                            st.write(f"**Tu motivo:** {solicitud['motivo']}")
                        
                        if solicitud.get('fecha_respuesta'):
                            st.write(f"**Fecha de respuesta:** {solicitud['fecha_respuesta']}")
                        
                        if solicitud.get('comentario_admin'):
                            st.info(f"💬 Admin: {solicitud['comentario_admin']}")
                        
                        if solicitud['estado'] == 'aprobada':
                            if st.button(f"📞 Ver Contacto", key=f"btn_{solicitud['_id']}"):
                                st.success("Información de contacto disponible arriba")
            else:
                st.info("No tienes solicitudes de contacto aún")
        else:
            st.error("Error al obtener solicitudes")


# ========================
# Estadísticas Admin
# ========================
elif choice == "Estadísticas":
    st.title("📊 Dashboard de Administración")
    token = st.session_state.get("token")
    
    if not token:
        st.warning("⚠️ Primero inicia sesión")
    elif st.session_state.get("role") != "admin":
        st.error("❌ Solo administradores pueden acceder a esta sección")
    else:
        headers = {"Authorization": f"Bearer {token}"}
        
        # ============= MÉTRICAS GENERALES =============
        st.header("📈 Métricas Generales del Sistema")
        
        col1, col2, col3, col4 = st.columns(4)
        
        # Obtener estadísticas de estudiantes
        students_res = requests.get(f"{BASE_URL}/api/students/admin/stats", headers=headers)
        if students_res.status_code == 200:
            students_stats = students_res.json()
            total_students = students_stats.get('total_students', 0)
            students_visible = students_stats.get('students_visible', 0)
            students_complete = students_stats.get('students_with_complete_profile', 0)
        else:
            total_students = 0
            students_visible = 0
            students_complete = 0
        
        # Obtener estadísticas de empresas
        companies_res = requests.get(f"{BASE_URL}/api/companies/admin/stats", headers=headers)
        if companies_res.status_code == 200:
            companies_stats = companies_res.json()
            total_companies = companies_stats.get('total_companies', 0)
            companies_verified = companies_stats.get('companies_verified', 0)
            companies_pending = companies_stats.get('companies_pending', 0)
        else:
            total_companies = 0
            companies_verified = 0
            companies_pending = 0
        
        # Obtener estadísticas de vacantes
        vacancies_res = requests.get(f"{BASE_URL}/api/vacancies/admin/stats", headers=headers)
        if vacancies_res.status_code == 200:
            vacancies_stats = vacancies_res.json()
            total_vacancies = vacancies_stats.get('total_vacancies', 0)
            vacancies_active = vacancies_stats.get('vacancies_active', 0)
        else:
            total_vacancies = 0
            vacancies_active = 0
        
        # Obtener estadísticas de matching
        matching_res = requests.get(f"{BASE_URL}/api/matching/admin/stats", headers=headers)
        if matching_res.status_code == 200:
            matching_stats = matching_res.json()
            total_matches = matching_stats.get('total_matches', 0)
            avg_match = matching_stats.get('porcentaje_promedio', 0)
        else:
            total_matches = 0
            avg_match = 0
        
        # Mostrar métricas principales
        with col1:
            st.metric(
                label="👥 Estudiantes Registrados",
                value=total_students,
                delta=f"{students_complete} perfiles completos"
            )
        
        with col2:
            st.metric(
                label="🏢 Empresas Registradas",
                value=total_companies,
                delta=f"{companies_verified} verificadas"
            )
        
        with col3:
            st.metric(
                label="💼 Vacantes Publicadas",
                value=total_vacancies,
                delta=f"{vacancies_active} activas"
            )
        
        with col4:
            st.metric(
                label="🤝 Matches Realizados",
                value=total_matches,
                delta=f"{avg_match:.1f}% promedio"
            )
        
        st.markdown("---")
        
        # ============= GRÁFICAS Y ANÁLISIS =============
        tab1, tab2, tab3, tab4 = st.tabs(["📚 Estudiantes", "🏢 Empresas", "💼 Vacantes", "🤖 Matching"])
        
        # ========== TAB 1: ESTUDIANTES ==========
        with tab1:
            st.subheader("📊 Análisis de Estudiantes")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Gráfica de estudiantes por estado de perfil
                st.write("**Estado de Perfiles**")
                profile_data = pd.DataFrame({
                    'Estado': ['Completo', 'Incompleto', 'Visible', 'No Visible'],
                    'Cantidad': [
                        students_complete,
                        total_students - students_complete,
                        students_visible,
                        total_students - students_visible
                    ]
                })
                st.bar_chart(profile_data.set_index('Estado'))
            
            with col2:
                # Obtener distribución por carrera
                students_all_res = requests.get(f"{BASE_URL}/api/students/admin/all", headers=headers)
                if students_all_res.status_code == 200:
                    students_all = students_all_res.json()
                    
                    # Contar por carrera
                    carreras = {}
                    for student in students_all:
                        carrera = student.get('carrera', 'Sin carrera')
                        carreras[carrera] = carreras.get(carrera, 0) + 1
                    
                    if carreras:
                        st.write("**Top 5 Carreras**")
                        carreras_sorted = sorted(carreras.items(), key=lambda x: x[1], reverse=True)[:5]
                        carreras_df = pd.DataFrame(carreras_sorted, columns=['Carrera', 'Cantidad'])
                        st.bar_chart(carreras_df.set_index('Carrera'))
            
            st.markdown("---")
            
            # Distribución por semestre
            if students_all_res.status_code == 200:
                semestres = {}
                for student in students_all:
                    semestre = student.get('semestre', 0)
                    if semestre > 0:
                        semestres[f"Semestre {semestre}"] = semestres.get(f"Semestre {semestre}", 0) + 1
                
                if semestres:
                    st.write("**📖 Distribución por Semestre**")
                    semestres_df = pd.DataFrame(list(semestres.items()), columns=['Semestre', 'Cantidad'])
                    st.bar_chart(semestres_df.set_index('Semestre'))
            
            # Habilidades más comunes
            st.markdown("---")
            st.write("**💻 Top 10 Habilidades Técnicas Más Comunes**")
            if students_all_res.status_code == 200:
                all_skills = []
                for student in students_all:
                    skills = student.get('habilidades_tecnicas', [])
                    all_skills.extend(skills)
                
                if all_skills:
                    skills_count = {}
                    for skill in all_skills:
                        skill_lower = skill.lower()
                        skills_count[skill_lower] = skills_count.get(skill_lower, 0) + 1
                    
                    skills_sorted = sorted(skills_count.items(), key=lambda x: x[1], reverse=True)[:10]
                    skills_df = pd.DataFrame(skills_sorted, columns=['Habilidad', 'Cantidad'])
                    st.bar_chart(skills_df.set_index('Habilidad'))
        
        # ========== TAB 2: EMPRESAS ==========
        with tab2:
            st.subheader("📊 Análisis de Empresas")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Estado de verificación
                st.write("**Estado de Verificación**")
                verification_data = pd.DataFrame({
                    'Estado': ['Verificadas', 'Pendientes', 'Rechazadas'],
                    'Cantidad': [
                        companies_verified,
                        companies_pending,
                        total_companies - companies_verified - companies_pending
                    ]
                })
                st.bar_chart(verification_data.set_index('Estado'))
            
            with col2:
                # Empresas por tamaño
                companies_all_res = requests.get(f"{BASE_URL}/api/companies/admin/all", headers=headers)
                if companies_all_res.status_code == 200:
                    companies_all = companies_all_res.json()
                    
                    tamanos = {}
                    for company in companies_all:
                        tamano = company.get('tamano', 'No especificado')
                        tamanos[tamano] = tamanos.get(tamano, 0) + 1
                    
                    if tamanos:
                        st.write("**Distribución por Tamaño**")
                        tamanos_df = pd.DataFrame(list(tamanos.items()), columns=['Tamaño', 'Cantidad'])
                        st.bar_chart(tamanos_df.set_index('Tamaño'))
            
            st.markdown("---")
            
            # Empresas por giro
            if companies_all_res.status_code == 200:
                giros = {}
                for company in companies_all:
                    giro = company.get('giro', 'No especificado')
                    giros[giro] = giros.get(giro, 0) + 1
                
                if giros:
                    st.write("**🏭 Top 5 Giros Empresariales**")
                    giros_sorted = sorted(giros.items(), key=lambda x: x[1], reverse=True)[:5]
                    giros_df = pd.DataFrame(giros_sorted, columns=['Giro', 'Cantidad'])
                    st.bar_chart(giros_df.set_index('Giro'))
            
            # Lista de empresas pendientes
            st.markdown("---")
            st.write("**⏳ Empresas Pendientes de Verificación**")
            if companies_all_res.status_code == 200:
                pending_companies = [c for c in companies_all if not c.get('verificada', False)]
                
                if pending_companies:
                    for company in pending_companies[:5]:
                        with st.expander(f"🏢 {company.get('nombre_empresa', 'N/A')} - {company.get('giro', 'N/A')}"):
                            st.write(f"**RFC:** {company.get('rfc', 'N/A')}")
                            st.write(f"**Tamaño:** {company.get('tamano', 'N/A')}")
                            st.write(f"**Ciudad:** {company.get('ciudad', 'N/A')}")
                            st.write(f"**Email:** {company.get('email_contacto', 'N/A')}")
                            
                            col_v1, col_v2 = st.columns(2)
                            with col_v1:
                                if st.button(f"✅ Verificar", key=f"verify_{company.get('_id')}"):
                                    verify_res = requests.put(
                                        f"{BASE_URL}/api/companies/{company.get('_id')}/verify",
                                        headers=headers,
                                        json={"verificada": True}
                                    )
                                    if verify_res.status_code == 200:
                                        st.success("✅ Empresa verificada")
                                        st.rerun()
                            
                            with col_v2:
                                if st.button(f"❌ Rechazar", key=f"reject_{company.get('_id')}"):
                                    st.warning("Funcionalidad de rechazo pendiente")
                else:
                    st.info("✅ No hay empresas pendientes de verificación")
        
        # ========== TAB 3: VACANTES ==========
        with tab3:
            st.subheader("📊 Análisis de Vacantes")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Vacantes por estado
                st.write("**Estado de Vacantes**")
                if vacancies_res.status_code == 200:
                    vacancy_states = vacancies_stats.get('by_state', {})
                    if vacancy_states:
                        states_df = pd.DataFrame(list(vacancy_states.items()), columns=['Estado', 'Cantidad'])
                        st.bar_chart(states_df.set_index('Estado'))
            
            with col2:
                # Vacantes por tipo de contrato
                st.write("**Tipo de Contrato**")
                vacancies_all_res = requests.get(f"{BASE_URL}/api/vacancies/admin/all", headers=headers)
                if vacancies_all_res.status_code == 200:
                    vacancies_all = vacancies_all_res.json()
                    
                    tipos = {}
                    for vacancy in vacancies_all:
                        tipo = vacancy.get('tipo_contrato', 'No especificado')
                        tipos[tipo] = tipos.get(tipo, 0) + 1
                    
                    if tipos:
                        tipos_df = pd.DataFrame(list(tipos.items()), columns=['Tipo', 'Cantidad'])
                        st.bar_chart(tipos_df.set_index('Tipo'))
            
            st.markdown("---")
            
            # Vacantes por modalidad
            if vacancies_all_res.status_code == 200:
                modalidades = {}
                for vacancy in vacancies_all:
                    modalidad = vacancy.get('modalidad', 'No especificado')
                    modalidades[modalidad] = modalidades.get(modalidad, 0) + 1
                
                if modalidades:
                    st.write("**🏢 Modalidad de Trabajo**")
                    modalidades_df = pd.DataFrame(list(modalidades.items()), columns=['Modalidad', 'Cantidad'])
                    st.bar_chart(modalidades_df.set_index('Modalidad'))
            
            # Áreas más demandadas
            st.markdown("---")
            if vacancies_all_res.status_code == 200:
                areas = {}
                for vacancy in vacancies_all:
                    area = vacancy.get('area', 'No especificado')
                    areas[area] = areas.get(area, 0) + 1
                
                if areas:
                    st.write("**🎯 Top 5 Áreas Más Demandadas**")
                    areas_sorted = sorted(areas.items(), key=lambda x: x[1], reverse=True)[:5]
                    areas_df = pd.DataFrame(areas_sorted, columns=['Área', 'Cantidad'])
                    st.bar_chart(areas_df.set_index('Área'))
            
            # Rango salarial promedio
            st.markdown("---")
            if vacancies_all_res.status_code == 200:
                salarios_min = [v.get('salario_minimo', 0) for v in vacancies_all if v.get('salario_minimo')]
                salarios_max = [v.get('salario_maximo', 0) for v in vacancies_all if v.get('salario_maximo')]
                
                if salarios_min and salarios_max:
                    col_sal1, col_sal2 = st.columns(2)
                    with col_sal1:
                        st.metric("💰 Salario Mínimo Promedio", f"${sum(salarios_min)/len(salarios_min):,.0f}")
                    with col_sal2:
                        st.metric("💰 Salario Máximo Promedio", f"${sum(salarios_max)/len(salarios_max):,.0f}")
        
        # ========== TAB 4: MATCHING ==========
        with tab4:
            st.subheader("📊 Análisis de Matching")
            
            if matching_res.status_code == 200:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("🎯 Total de Matches", total_matches)
                    st.metric("📊 Porcentaje Promedio", f"{avg_match:.1f}%")
                    st.metric("🏆 Porcentaje Máximo", f"{matching_stats.get('porcentaje_maximo', 0):.1f}%")
                
                with col2:
                    st.metric("📉 Porcentaje Mínimo", f"{matching_stats.get('porcentaje_minimo', 0):.1f}%")
                    
                    # Calcular tasa de éxito (matches > 80%)
                    distribucion = matching_stats.get('distribucion', {})
                    excelentes = distribucion.get('Excelente', 0)
                    if total_matches > 0:
                        tasa_exito = (excelentes / total_matches) * 100
                        st.metric("✨ Matches Excelentes (>80%)", f"{tasa_exito:.1f}%")
                
                st.markdown("---")
                
                # Distribución de matches por calidad
                st.write("**📊 Distribución de Matches por Calidad**")
                if distribucion:
                    dist_df = pd.DataFrame(list(distribucion.items()), columns=['Calidad', 'Cantidad'])
                    st.bar_chart(dist_df.set_index('Calidad'))
                
                # Vacantes con más matches
                st.markdown("---")
                st.write("**🏆 Top 5 Vacantes con Más Matches**")
                vacancies_all_res = requests.get(f"{BASE_URL}/api/vacancies/admin/all", headers=headers)
                if vacancies_all_res.status_code == 200:
                    vacancies_all = vacancies_all_res.json()
                    vacancies_with_matches = [(v.get('titulo', 'N/A'), v.get('num_candidatos_matched', 0)) 
                                              for v in vacancies_all]
                    vacancies_sorted = sorted(vacancies_with_matches, key=lambda x: x[1], reverse=True)[:5]
                    
                    if vacancies_sorted:
                        top_vacancies_df = pd.DataFrame(vacancies_sorted, columns=['Vacante', 'Matches'])
                        st.bar_chart(top_vacancies_df.set_index('Vacante'))
            else:
                st.warning("⚠️ No hay datos de matching disponibles")
        
        st.markdown("---")
        
        # ============= ACCIONES RÁPIDAS =============
        st.header("⚡ Acciones Rápidas")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Actualizar Estadísticas"):
                st.rerun()
        
        with col2:
            if st.button("📥 Exportar Reporte"):
                st.info("Funcionalidad de exportación en desarrollo")
        
        with col3:
            if st.button("🧹 Limpiar Datos Antiguos"):
                st.warning("Funcionalidad de limpieza en desarrollo")

# ========================
# Perfil de estudiante
# ========================
elif choice == "Perfil":
    st.title("👤 Perfil del estudiante")
    token = st.session_state.get("token")
    
    if not token:
        st.warning("⚠️ Primero inicia sesión")
    else:
        headers = {"Authorization": f"Bearer {token}"}
        res = requests.get(f"{BASE_URL}/api/students/profile", headers=headers)
        
        if res.status_code == 200:
            profile = res.json()
            # Asegurar que `profile` sea un diccionario para evitar errores al usar .get()
            if not isinstance(profile, dict):
                try:
                    profile = dict(profile)
                except Exception:
                    profile = {}
            
            # Verificar si el perfil existe
            if not profile.get("exists", True):
                st.warning("📋 No tienes un perfil creado aún. Completa el siguiente formulario:")
                
                # Formulario de creación de perfil
                with st.form("create_profile"):
                    st.subheader("Información Básica")
                    matricula = st.text_input("Matrícula*", placeholder="A01234567")
                    nombre_completo = st.text_input("Nombre Completo*", placeholder="Juan Pérez García")
                    carrera = st.text_input("Carrera*", placeholder="Ingeniería en Sistemas")
                    semestre = st.number_input("Semestre*", min_value=1, max_value=8, value=1)
                    promedio = st.number_input("Promedio", min_value=0.0, max_value=10.0, value=0.0, step=0.1)
                    
                    st.subheader("Contacto")
                    telefono = st.text_input("Teléfono", placeholder="5512345678")
                    ciudad = st.text_input("Ciudad", placeholder="Ciudad de México")
                    disponibilidad = st.selectbox(
                        "Disponibilidad*",
                        ["Tiempo completo", "Medio tiempo", "Por proyecto", "Prácticas"]
                    )
                    
                    st.subheader("Habilidades")
                    habilidades_tecnicas = st.text_area(
                        "Habilidades Técnicas* (una por línea, mínimo 3)",
                        placeholder="Python\nJavaScript\nReact"
                    )
                    habilidades_blandas = st.text_area(
                        "Habilidades Blandas (una por línea)",
                        placeholder="Trabajo en equipo\nComunicación\nLiderazgo"
                    )
                    
                    st.subheader("Idiomas")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        idioma = st.text_input("Idioma*", value="Español")
                    with col2:
                        nivel = st.selectbox("Nivel*", ["Basico", "Intermedio", "Avanzado", "Nativo"])
                    with col3:
                        porcentaje = st.text_input("Porcentaje*", value="100%")
                    
                    st.subheader("Preferencias")
                    areas_interes = st.text_area(
                        "Áreas de Interés (una por línea)",
                        placeholder="Desarrollo Web\nInteligencia Artificial"
                    )
                    modalidad_preferida = st.selectbox(
                        "Modalidad Preferida",
                        ["Híbrido", "Presencial", "Remoto"]
                    )
                    salario_esperado = st.number_input("Salario Esperado (opcional)", min_value=0.0, value=0.0)
                    descripcion_breve = st.text_area(
                        "Descripción Breve",
                        placeholder="Estudiante apasionado por el desarrollo de software...",
                        max_chars=500
                    )
                    
                    submitted = st.form_submit_button("Crear Perfil")
                    
                    if submitted:
                        # Validar campos obligatorios
                        if not all([matricula, nombre_completo, carrera, habilidades_tecnicas, idioma]):
                            st.error("❌ Completa todos los campos obligatorios marcados con *")
                        else:
                            # Procesar habilidades
                            skills_tech = [s.strip() for s in habilidades_tecnicas.split("\n") if s.strip()]
                            skills_soft = [s.strip() for s in habilidades_blandas.split("\n") if s.strip()]
                            areas = [a.strip() for a in areas_interes.split("\n") if a.strip()]
                            
                            if len(skills_tech) < 3:
                                st.error("❌ Debes ingresar al menos 3 habilidades técnicas")
                            else:
                                # Crear payload
                                payload = {
                                    "matricula": matricula,
                                    "nombre_completo": nombre_completo,
                                    "carrera": carrera,
                                    "semestre": semestre,
                                    "promedio": promedio if promedio > 0 else None,
                                    "telefono": telefono if telefono else None,
                                    "ciudad": ciudad if ciudad else None,
                                    "disponibilidad": disponibilidad,
                                    "habilidades_tecnicas": skills_tech,
                                    "habilidades_blandas": skills_soft,
                                    "idiomas": [
                                        {
                                            "idioma": idioma,
                                            "nivel": nivel,
                                            "porcentaje": porcentaje
                                        }
                                    ],
                                    "areas_interes": areas,
                                    "modalidad_preferida": modalidad_preferida,
                                    "salario_esperado": salario_esperado if salario_esperado > 0 else None,
                                    "descripcion_breve": descripcion_breve if descripcion_breve else None
                                }
                                
                                # Enviar al backend
                                create_res = requests.post(
                                    f"{BASE_URL}/api/students/profile",
                                    headers=headers,
                                    json=payload
                                )
                                
                                if create_res.status_code == 201:
                                    st.success("✅ ¡Perfil creado exitosamente!")
                                    st.rerun()  # Recargar para mostrar el perfil
                                else:
                                    st.error(f"❌ Error: {create_res.json()}")
            
            else:
                # Perfil existe, mostrarlo
                st.success("✅ Perfil encontrado")
                
                # Mostrar información básica
                st.subheader("📋 Información Básica")
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Matrícula:** {profile.get('matricula', 'N/A')}")
                    st.write(f"**Nombre:** {profile.get('nombre_completo', 'N/A')}")
                    st.write(f"**Carrera:** {profile.get('carrera', 'N/A')}")
                with col2:
                    st.write(f"**Semestre:** {profile.get('semestre', 'N/A')}")
                    st.write(f"**Promedio:** {profile.get('promedio', 'N/A')}")
                    st.write(f"**Ciudad:** {profile.get('ciudad', 'N/A')}")
                
                # Habilidades
                st.subheader("💡 Habilidades")
                st.write("**Técnicas:**", ", ".join(profile.get('habilidades_tecnicas', [])))
                st.write("**Blandas:**", ", ".join(profile.get('habilidades_blandas', [])))
                
                # Idiomas
                if profile.get('idiomas'):
                    st.subheader("🌐 Idiomas")
                    for idioma in profile['idiomas']:
                        st.write(f"- {idioma['idioma']}: {idioma['nivel']} ({idioma.get('porcentaje', 'N/A')})")
                
                # Nota: vista JSON completa eliminada intencionalmente para evitar mostrar
                # los datos crudos del perfil en la interfaz de usuario.

                # Botón para editar perfil
                if st.button("✏️ Editar Perfil"):
                    st.session_state["editing_profile"] = True
                    st.rerun()

                # Formulario de edición (visible solo si se activa la edición)
                if st.session_state.get("editing_profile"):
                    st.subheader("Editar Perfil")
                    matricula = st.text_input("Matrícula*", value=profile.get('matricula', ''))
                    nombre_completo = st.text_input("Nombre Completo*", value=profile.get('nombre_completo', ''))
                    carrera = st.text_input("Carrera*", value=profile.get('carrera', ''))
                    semestre = st.number_input("Semestre*", min_value=1, max_value=12, value=profile.get('semestre', 1))
                    promedio = st.number_input("Promedio", min_value=0.0, max_value=10.0, value=profile.get('promedio') or 0.0, step=0.1)

                    st.subheader("Contacto")
                    telefono = st.text_input("Teléfono", value=profile.get('telefono', '') or '')
                    ciudad = st.text_input("Ciudad", value=profile.get('ciudad', '') or '')
                    disponibilidad_options = ["Tiempo completo", "Medio tiempo", "Por proyecto", "Prácticas"]
                    disponibilidad_current = profile.get('disponibilidad') if profile.get('disponibilidad') in disponibilidad_options else disponibilidad_options[0]
                    disponibilidad = st.selectbox("Disponibilidad*", disponibilidad_options, index=disponibilidad_options.index(disponibilidad_current))

                    st.subheader("Habilidades")
                    habilidades_tecnicas = st.text_area(
                        "Habilidades Técnicas* (una por línea, mínimo 3)",
                        value="\n".join(profile.get('habilidades_tecnicas', []))
                    )
                    habilidades_blandas = st.text_area(
                        "Habilidades Blandas (una por línea)",
                        value="\n".join(profile.get('habilidades_blandas', []))
                    )

                    st.subheader("Idiomas")
                    idioma_val = profile.get('idiomas', [{'idioma': 'Español', 'nivel': 'Basico', 'porcentaje': '100%'}])[0]
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        idioma = st.text_input("Idioma*", value=idioma_val.get('idioma', ''))
                    with col2:
                        nivel_options = ["Basico", "Intermedio", "Avanzado", "Nativo"]
                        nivel_current = idioma_val.get('nivel') if idioma_val.get('nivel') in nivel_options else nivel_options[0]
                        nivel = st.selectbox("Nivel*", nivel_options, index=nivel_options.index(nivel_current))
                    with col3:
                        porcentaje = st.text_input("Porcentaje*", value=idioma_val.get('porcentaje', '100%'))

                    st.subheader("Preferencias")
                    areas_interes = st.text_area(
                        "Áreas de Interés (una por línea)",
                        value="\n".join(profile.get('areas_interes', []))
                    )
                    modalidad_options = ["Híbrido", "Presencial", "Remoto"]
                    modalidad_current = profile.get('modalidad_preferida') if profile.get('modalidad_preferida') in modalidad_options else modalidad_options[0]
                    modalidad_preferida = st.selectbox("Modalidad Preferida", modalidad_options, index=modalidad_options.index(modalidad_current))
                    salario_esperado = st.number_input(
                        "Salario Esperado (opcional)",
                        min_value=0.0,
                        value=float(profile.get('salario_esperado', 0) or 0.0)
                    )
                    descripcion_breve = st.text_area("Descripción Breve", value=profile.get('descripcion_breve', ''))

                    # Botón de envío fuera de un st.form para evitar el error de "Missing Submit Button"
                    if st.button("Guardar cambios"):
                        # Validaciones básicas
                        if not all([matricula, nombre_completo, carrera, habilidades_tecnicas, idioma]):
                            st.error("❌ Completa todos los campos obligatorios marcados con *")
                        else:
                            skills_tech = [s.strip() for s in habilidades_tecnicas.split("\n") if s.strip()]
                            skills_soft = [s.strip() for s in habilidades_blandas.split("\n") if s.strip()]
                            areas = [a.strip() for a in areas_interes.split("\n") if a.strip()]

                            if len(skills_tech) < 3:
                                st.error("❌ Debes ingresar al menos 3 habilidades técnicas")
                            else:
                                payload = {
                                    "matricula": matricula,
                                    "nombre_completo": nombre_completo,
                                    "carrera": carrera,
                                    "semestre": semestre,
                                    "promedio": promedio if promedio > 0 else None,
                                    "telefono": telefono if telefono else None,
                                    "ciudad": ciudad if ciudad else None,
                                    "disponibilidad": disponibilidad,
                                    "habilidades_tecnicas": skills_tech,
                                    "habilidades_blandas": skills_soft,
                                    "idiomas": [
                                        {
                                            "idioma": idioma,
                                            "nivel": nivel,
                                            "porcentaje": porcentaje
                                        }
                                    ],
                                    "areas_interes": areas,
                                    "modalidad_preferida": modalidad_preferida,
                                    "salario_esperado": salario_esperado if salario_esperado > 0 else None,
                                    "descripcion_breve": descripcion_breve if descripcion_breve else None
                                }

                                # Enviar actualización al backend (usar PUT si el endpoint lo soporta)
                                update_res = requests.put(f"{BASE_URL}/api/students/profile", headers=headers, json=payload)
                                if update_res.status_code in (200, 201):
                                    st.success("✅ Perfil actualizado correctamente")
                                    st.session_state["editing_profile"] = False
                                    st.rerun()
                                else:
                                    # Intentar también con POST por compatibilidad
                                    update_res2 = requests.post(f"{BASE_URL}/api/students/profile", headers=headers, json=payload)
                                    if update_res2.status_code in (200, 201, 204):
                                        st.success("✅ Perfil actualizado correctamente")
                                        st.session_state["editing_profile"] = False
                                        st.rerun()
                                    else:
                                        # Mostrar el error retornado por el backend si existe
                                        try:
                                            err = update_res.json()
                                        except Exception:
                                            err = update_res.text
                                        st.error(f"❌ Error al actualizar: {err}")
        
        elif res.status_code == 403:
            st.error("❌ No tienes permisos para ver esta sección")
        else:
            st.error(f"❌ Error al obtener el perfil: {res.json()}")
# ========================
# Vacantes
# ========================
elif choice == "Vacantes":
    st.title("💼 Vacantes disponibles")
    token = st.session_state.get("token")
    
    if not token:
        st.warning("Primero inicia sesión")
    else:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Detectar si es empresa o estudiante
        # Para estudiantes: ver vacantes públicas
        # Para empresas: ver sus propias vacantes
        
        # Primero intentamos obtener vacantes públicas (para estudiantes)
        res = requests.get(f"{BASE_URL}/api/vacancies/public/all", headers=headers)
        
        if res.status_code == 200:
            vacantes = res.json()
            if vacantes:
                # Mostrar de forma más amigable
                for v in vacantes:
                    with st.expander(f"📌 {v.get('titulo', 'Sin título')} - {v.get('empresa_nombre', 'Empresa')}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Área:** {v.get('area', 'N/A')}")
                            st.write(f"**Tipo:** {v.get('tipo_contrato', 'N/A')}")
                            st.write(f"**Modalidad:** {v.get('modalidad', 'N/A')}")
                        with col2:
                            st.write(f"**Ubicación:** {v.get('ubicacion', 'N/A')}")
                            st.write(f"**Salario:** {v.get('salario_rango', 'No especificado')}")
                            st.write(f"**Vacantes:** {v.get('num_vacantes', 1)}")
                        
                        st.write(f"**Descripción:** {v.get('descripcion', 'N/A')}")
                        
                        if v.get('habilidades_requeridas'):
                            st.write("**Habilidades requeridas:**")
                            st.write(", ".join(v['habilidades_requeridas']))
                        
                        if v.get('beneficios'):
                            st.write("**Beneficios:**")
                            st.write(", ".join(v['beneficios']))
            else:
                st.info("No hay vacantes disponibles")
        else:
            st.error(f"Error al obtener vacantes: {res.json()}")

# ========================
# Matching
# ========================
elif choice == "Matching":
    st.title("📊 Matching de compatibilidad")
    token = st.session_state.get("token")
    if token:
        headers = {"Authorization": f"Bearer {token}"}
        res = requests.get(f"{BASE_URL}/api/matching/students", headers=headers)
        if res.status_code == 200:
            matching_data = res.json()
            if matching_data:
                df = pd.DataFrame(matching_data)
                st.bar_chart(df.set_index("vacancy")["score"])
            else:
                st.info("No hay resultados de matching")
        else:
            st.error(res.json())
    else:
        st.warning("Primero inicia sesión")

# Agregar al final del archivo
elif choice == "Gestión Empresa":
    st.title("🏢 Gestión de Empresa")
    token = st.session_state.get("token")
    
    if not token:
        st.warning("Primero inicia sesión")
    else:
        headers = {"Authorization": f"Bearer {token}"}
        
        tab1, tab2 = st.tabs(["Perfil Empresa", "Crear Vacante"])
        
        with tab1:
            st.subheader("Crear Perfil de Empresa")
            with st.form("create_company"):
                nombre = st.text_input("Nombre Empresa*")
                rfc = st.text_input("RFC*")
                giro = st.text_input("Giro*")
                tamano = st.selectbox("Tamaño*", ["Micro", "Pequeña", "Mediana", "Grande"])
                email = st.text_input("Email Contacto*")
                telefono = st.text_input("Teléfono*")
                ciudad = st.text_input("Ciudad*")
                estado = st.text_input("Estado*")
                cp = st.text_input("Código Postal*")
                direccion = st.text_input("Dirección*")
                descripcion = st.text_area("Descripción*")
                
                if st.form_submit_button("Crear Perfil"):
                    payload = {
                        "nombre_empresa": nombre,
                        "rfc": rfc,
                        "giro": giro,
                        "tamano": tamano,
                        "email_contacto": email,
                        "telefono": telefono,
                        "ciudad": ciudad,
                        "estado": estado,
                        "codigo_postal": cp,
                        "direccion": direccion,
                        "descripcion": descripcion,
                        "beneficios": ["Seguro médico", "Home office"]
                    }
                    res = requests.post(f"{BASE_URL}/api/companies/profile", json=payload, headers=headers)
                    if res.status_code == 201:
                        st.success("✅ Perfil creado. Esperando verificación de admin")
                    else:
                        st.error(res.json())
        
        with tab2:
            st.subheader("Crear Vacante")
            with st.form("create_vacancy"):
                titulo = st.text_input("Título del Puesto*")
                area = st.text_input("Área*")
                descripcion_v = st.text_area("Descripción*")
                tipo = st.selectbox("Tipo Contrato*", ["Tiempo completo", "Medio tiempo", "Prácticas"])
                modalidad = st.selectbox("Modalidad*", ["Presencial", "Remoto", "Híbrido"])
                skills = st.text_area("Habilidades Técnicas (una por línea)*")
                salario_min = st.number_input("Salario Mínimo", min_value=0, value=15000)
                salario_max = st.number_input("Salario Máximo", min_value=0, value=25000)
                
                if st.form_submit_button("Publicar Vacante"):
                    payload = {
                        "titulo": titulo,
                        "area": area,
                        "descripcion": descripcion_v,
                        "tipo_contrato": tipo,
                        "modalidad": modalidad,
                        "habilidades_tecnicas_requeridas": [s.strip() for s in skills.split("\n") if s.strip()],
                        "habilidades_blandas_requeridas": ["Trabajo en equipo"],
                        "salario_minimo": salario_min,
                        "salario_maximo": salario_max,
                        "ubicacion_ciudad": "Ciudad de México",
                        "ubicacion_estado": "CDMX",
                        "num_vacantes": 1
                    }
                    res = requests.post(f"{BASE_URL}/api/vacancies/", json=payload, headers=headers)
                    if res.status_code == 201:
                        st.success("✅ Vacante publicada exitosamente")
                    else:
                        st.error(res.json())

# ========================
# Mis Vacantes (para empresas)
# ========================
elif choice == "Mis Vacantes":
    st.title("📋 Mis Vacantes Publicadas")
    token = st.session_state.get("token")
    
    if not token:
        st.warning("⚠️ Primero inicia sesión")
    else:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Obtener vacantes de la empresa
        res = requests.get(f"{BASE_URL}/api/vacancies/my-vacancies", headers=headers)
        
        if res.status_code == 200:
            vacantes = res.json()
            
            if vacantes:
                st.success(f"✅ Tienes {len(vacantes)} vacante(s) publicada(s)")
                
                # Tabs para organizar
                tab1, tab2 = st.tabs(["📊 Lista de Vacantes", "➕ Nueva Vacante"])
                
                with tab1:
                    for v in vacantes:
                        vacancy_id = v.get('_id') or v.get('id')
                        
                        with st.expander(f"📌 {v.get('titulo', 'Sin título')} - {v.get('num_candidatos_matched', 0)} candidatos"):
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.write(f"**📍 Ubicación:** {v.get('ubicacion_ciudad', 'N/A')}, {v.get('ubicacion_estado', 'N/A')}")
                                st.write(f"**💼 Tipo:** {v.get('tipo_contrato', 'N/A')}")
                                st.write(f"**🏢 Modalidad:** {v.get('modalidad', 'N/A')}")
                            
                            with col2:
                                st.write(f"**💰 Salario:** ${v.get('salario_minimo', 0):,} - ${v.get('salario_maximo', 0):,}")
                                st.write(f"**👥 Vacantes:** {v.get('num_vacantes', 1)}")
                                st.write(f"**📅 Publicada:** {v.get('fecha_publicacion', 'N/A')[:10]}")
                            
                            with col3:
                                estado = v.get('estado', 'activa')
                                if estado == 'activa':
                                    st.success("✅ Activa")
                                elif estado == 'pausada':
                                    st.warning("⏸️ Pausada")
                                else:
                                    st.error("❌ Cerrada")
                                
                                st.write(f"**🎯 Candidatos:** {v.get('num_candidatos_matched', 0)}")
                            
                            st.write("---")
                            st.write(f"**📝 Descripción:** {v.get('descripcion', 'N/A')}")
                            
                            if v.get('habilidades_tecnicas_requeridas'):
                                st.write("**💻 Habilidades Técnicas:**")
                                st.write(", ".join(v['habilidades_tecnicas_requeridas']))
                            
                            if v.get('habilidades_blandas_requeridas'):
                                st.write("**🤝 Habilidades Blandas:**")
                                st.write(", ".join(v['habilidades_blandas_requeridas']))
                            
                            if v.get('idiomas_requeridos'):
                                st.write("**🌐 Idiomas:**")
                                for idioma in v['idiomas_requeridos']:
                                    st.write(f"- {idioma.get('idioma', 'N/A')}: {idioma.get('nivel_minimo', 'N/A')}")
                            
                            st.write("---")
                            
                            # Botones de acción
                            col_btn1, col_btn2, col_btn3, col_btn4 = st.columns(4)
                            
                            with col_btn1:
                                if st.button(f"🔍 Ver Candidatos", key=f"ver_{vacancy_id}"):
                                    st.session_state['selected_vacancy'] = vacancy_id
                                    st.rerun()
                            
                            with col_btn2:
                                if st.button(f"🤖 Ejecutar Matching", key=f"match_{vacancy_id}"):
                                    with st.spinner("Ejecutando matching..."):
                                        match_res = requests.post(
                                            f"{BASE_URL}/api/matching/vacancy/{vacancy_id}/run",
                                            headers=headers,
                                            params={"min_match_percentage": 70.0}
                                        )
                                        if match_res.status_code == 200:
                                            result = match_res.json()
                                            st.success(f"✅ Matching completado: {result.get('matches_created', 0)} nuevos candidatos encontrados")
                                            st.rerun()
                                        else:
                                            st.error(f"❌ Error: {match_res.json()}")
                            
                            with col_btn3:
                                if v.get('estado') == 'activa':
                                    if st.button(f"⏸️ Pausar", key=f"pause_{vacancy_id}"):
                                        pause_res = requests.put(
                                            f"{BASE_URL}/api/vacancies/{vacancy_id}/status",
                                            headers=headers,
                                            json={"estado": "pausada"}
                                        )
                                        if pause_res.status_code == 200:
                                            st.success("✅ Vacante pausada")
                                            st.rerun()
                                else:
                                    if st.button(f"▶️ Activar", key=f"activate_{vacancy_id}"):
                                        activate_res = requests.put(
                                            f"{BASE_URL}/api/vacancies/{vacancy_id}/status",
                                            headers=headers,
                                            json={"estado": "activa"}
                                        )
                                        if activate_res.status_code == 200:
                                            st.success("✅ Vacante activada")
                                            st.rerun()
                            
                            with col_btn4:
                                if st.button(f"🗑️ Eliminar", key=f"delete_{vacancy_id}"):
                                    delete_res = requests.delete(
                                        f"{BASE_URL}/api/vacancies/{vacancy_id}",
                                        headers=headers
                                    )
                                    if delete_res.status_code == 200:
                                        st.success("✅ Vacante eliminada")
                                        st.rerun()
                                    else:
                                        st.error("❌ Error al eliminar")
                
                with tab2:
                    st.subheader("➕ Crear Nueva Vacante")
                    with st.form("create_new_vacancy"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            titulo = st.text_input("Título del Puesto*", placeholder="Ej: Desarrollador Full Stack Junior")
                            area = st.text_input("Área*", placeholder="Ej: Tecnología")
                            tipo = st.selectbox("Tipo de Contrato*", ["Tiempo completo", "Medio tiempo", "Prácticas", "Por proyecto"])
                            modalidad = st.selectbox("Modalidad*", ["Presencial", "Remoto", "Híbrido"])
                            num_vacantes = st.number_input("Número de Vacantes*", min_value=1, value=1)
                        
                        with col2:
                            salario_min = st.number_input("Salario Mínimo*", min_value=0, value=15000, step=1000)
                            salario_max = st.number_input("Salario Máximo*", min_value=0, value=25000, step=1000)
                            ciudad = st.text_input("Ciudad*", placeholder="Ciudad de México")
                            estado = st.text_input("Estado*", placeholder="CDMX")
                            semestre_min = st.number_input("Semestre Mínimo", min_value=1, max_value=12, value=5)
                        
                        descripcion_v = st.text_area("Descripción del Puesto*", placeholder="Describe las responsabilidades y requisitos...", height=150)
                        
                        skills_tech = st.text_area(
                            "Habilidades Técnicas Requeridas* (una por línea)",
                            placeholder="Python\nJavaScript\nReact\nFastAPI",
                            height=100
                        )
                        
                        skills_soft = st.text_area(
                            "Habilidades Blandas Requeridas (una por línea)",
                            placeholder="Trabajo en equipo\nComunicación\nLiderazgo",
                            height=80
                        )
                        
                        st.write("**Idiomas Requeridos**")
                        col_idioma1, col_idioma2 = st.columns(2)
                        with col_idioma1:
                            idioma_req = st.text_input("Idioma", value="Inglés")
                        with col_idioma2:
                            nivel_req = st.selectbox("Nivel Mínimo", ["A1", "A2", "B1", "B2", "C1", "C2", "Nativo"])
                        
                        experiencia_min = st.selectbox(
                            "Experiencia Mínima",
                            ["Sin experiencia", "Menos de 1 año", "1-2 años", "2-3 años", "3-5 años", "Más de 5 años"]
                        )
                        
                        beneficios = st.text_area(
                            "Beneficios (uno por línea)",
                            placeholder="Seguro médico\nHome office\nCapacitación continua",
                            height=80
                        )
                        
                        submitted = st.form_submit_button("📤 Publicar Vacante")
                        
                        if submitted:
                            if not all([titulo, area, descripcion_v, skills_tech]):
                                st.error("❌ Completa todos los campos obligatorios marcados con *")
                            else:
                                skills_tech_list = [s.strip() for s in skills_tech.split("\n") if s.strip()]
                                skills_soft_list = [s.strip() for s in skills_soft.split("\n") if s.strip()]
                                beneficios_list = [b.strip() for b in beneficios.split("\n") if b.strip()]
                                
                                payload = {
                                    "titulo": titulo,
                                    "area": area,
                                    "descripcion": descripcion_v,
                                    "tipo_contrato": tipo,
                                    "modalidad": modalidad,
                                    "habilidades_tecnicas_requeridas": skills_tech_list,
                                    "habilidades_blandas_requeridas": skills_soft_list if skills_soft_list else ["Trabajo en equipo"],
                                    "idiomas_requeridos": [{"idioma": idioma_req, "nivel_minimo": nivel_req}] if idioma_req else [],
                                    "experiencia_minima": experiencia_min,
                                    "salario_minimo": salario_min,
                                    "salario_maximo": salario_max,
                                    "ubicacion_ciudad": ciudad,
                                    "ubicacion_estado": estado,
                                    "num_vacantes": num_vacantes,
                                    "semestre_minimo": semestre_min,
                                    "beneficios": beneficios_list if beneficios_list else []
                                }
                                
                                create_res = requests.post(f"{BASE_URL}/api/vacancies/", json=payload, headers=headers)
                                
                                if create_res.status_code == 201:
                                    st.success("✅ ¡Vacante publicada exitosamente!")
                                    st.balloons()
                                    st.rerun()
                                else:
                                    try:
                                        error_detail = create_res.json()
                                        st.error(f"❌ Error: {error_detail}")
                                    except:
                                        st.error(f"❌ Error al publicar vacante: {create_res.text}")
                
                # Mostrar candidatos si se seleccionó una vacante
                if st.session_state.get('selected_vacancy'):
                    st.markdown("---")
                    st.subheader(f"👥 Candidatos para la vacante")
                    
                    vacancy_id = st.session_state['selected_vacancy']
                    
                    # Obtener matches
                    matches_res = requests.get(
                        f"{BASE_URL}/api/matching/vacancy/{vacancy_id}/matches",
                        headers=headers,
                        params={"min_percentage": 0}
                    )
                    
                    if matches_res.status_code == 200:
                        matches_data = matches_res.json()
                        matches = matches_data.get('matches', [])
                        
                        if matches:
                            st.info(f"📊 Total de candidatos: {len(matches)}")
                            
                            # Filtro por porcentaje
                            min_percentage = st.slider("Porcentaje mínimo de compatibilidad", 0, 100, 70)
                            
                            matches_filtered = [m for m in matches if m.get('porcentaje_match', 0) >= min_percentage]
                            
                            for match in matches_filtered:
                                with st.expander(f"🎯 {match.get('porcentaje_match', 0):.1f}% - {match.get('student_matricula', 'N/A')} - {match.get('carrera', 'N/A')}"):
                                    col1, col2 = st.columns(2)
                                    
                                    with col1:
                                        st.write(f"**📚 Carrera:** {match.get('carrera', 'N/A')}")
                                        st.write(f"**📖 Semestre:** {match.get('semestre', 'N/A')}")
                                        st.write(f"**🏢 Modalidad:** {match.get('modalidad_preferida', 'N/A')}")
                                        st.write(f"**💼 Experiencia:** {'Sí' if match.get('tiene_experiencia') else 'No'}")
                                    
                                    with col2:
                                        st.write("**💻 Habilidades Técnicas:**")
                                        st.write(", ".join(match.get('habilidades_tecnicas', [])))
                                        st.write("**🤝 Habilidades Blandas:**")
                                        st.write(", ".join(match.get('habilidades_blandas', [])))
                                    
                                    st.write("**📊 Desglose de Compatibilidad:**")
                                    desglose = match.get('desglose', {})
                                    
                                    cols = st.columns(4)
                                    metrics = [
                                        ("💻 Técnicas", desglose.get('habilidades_tecnicas', 0) * 100),
                                        ("🤝 Blandas", desglose.get('habilidades_blandas', 0) * 100),
                                        ("🌐 Idiomas", desglose.get('idiomas', 0) * 100),
                                        ("📚 Carrera", desglose.get('carrera', 0) * 100)
                                    ]
                                    
                                    for col, (label, value) in zip(cols, metrics):
                                        col.metric(label, f"{value:.0f}%")
                        else:
                            st.warning("⚠️ No hay candidatos para esta vacante. Ejecuta el matching para encontrar candidatos.")
                    else:
                        st.error("❌ Error al obtener candidatos")
                    
                    if st.button("⬅️ Volver a lista de vacantes"):
                        del st.session_state['selected_vacancy']
                        st.rerun()
            
            else:
                st.info("📝 No tienes vacantes publicadas aún. ¡Crea tu primera vacante!")
                
                # Botón para crear primera vacante
                if st.button("➕ Crear mi primera vacante"):
                    st.rerun()
        
        elif res.status_code == 403:
            st.error("❌ No tienes una empresa registrada. Ve a 'Gestión Empresa' para crear tu perfil.")
        else:
            st.error(f"❌ Error al obtener vacantes: {res.text}")