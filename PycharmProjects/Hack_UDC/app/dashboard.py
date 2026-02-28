import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import json
from datetime import datetime

# Configuración de la API
API_URL = "https://hack-udc-api-1.onrender.com"

st.set_page_config(page_title="IA de stock - Dashboard", layout="wide", initial_sidebar_state="expanded")

# --- 1. ESTILOS GLOBALES ---
st.markdown("""
    <script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet"/>
    <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0" rel="stylesheet"/>
    <style>
        .stApp { background-color: #102218; color: #fafafa; font-family: 'Inter', sans-serif; }
        [data-testid="stSidebar"] { background-color: #0a1610; border-right: 1px solid #2d4a3e; }
        .stButton>button { background-color: #13ec6d !important; color: #102218 !important; font-weight: 700 !important; border: none !important; border-radius: 6px !important; }
        .stTextInput>div>div>input { background-color: #102218 !important; border: 1px solid #2d4a3e !important; color: white !important; }
        #MainMenu, footer, header {visibility: hidden;}
        .block-container {padding-top: 2rem;}
        .stDataFrame { background-color: #1a2e24; border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. SIDEBAR ---
with st.sidebar:
    st.markdown("""
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 32px; padding: 8px;">
                <div style="background-color: #13ec6d; color: #102218; width: 40px; height: 40px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 20px;">
                    📈
                </div>
                <div style="display: flex; flex-direction: column;">
                    <span style="color: white; font-size: 20px; font-weight: 700; line-height: 1.2;">StudyStock</span>
                    <span style="color: #13ec6d; font-size: 10px; font-weight: 500; text-transform: uppercase; letter-spacing: 1px;">Terminal Pro</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
    st.markdown('<p class="text-xs font-semibold text-gray-500 uppercase tracking-wider px-2 mb-2">Operaciones</p>',
                unsafe_allow_html=True)

    menu = st.radio("Navegación",
                    ["Consultar Ticker", "Comparar Empresas", "Predicción IA", "Cargar Datos Manuales"],
                    label_visibility="collapsed")

    st.markdown("""
        <div class="mt-20 p-4 border-t border-[#2d4a3e]">
            <div class="flex items-center space-x-2 text-xs text-gray-500">
                <span class="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                <span></span>
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- 3. PANTALLA: CONSULTAR TICKER ---
if menu == "Consultar Ticker":
    st.markdown("""
        <div class="mb-8">
            <h2 class="text-3xl font-bold text-white">Análisis de Mercado</h2>
            <p class="text-gray-400 mt-1">Consulta datos de Twelve Data o de tu Base de Datos Local.</p>
        </div>
    """, unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="bg-[#1a2e24] p-6 rounded-xl border border-[#2d4a3e] shadow-lg mb-8">',
                    unsafe_allow_html=True)
        col_input, col_time, col_btn = st.columns([3, 2, 1])
        with col_input:
            ticker = st.text_input("Ticker Symbol", placeholder="Ej: AAPL", key="ticker_cons").upper()

        with col_time:
            intervalo = st.selectbox("Temporalidad", ["Diario (1D)", "Mensual (1M)", "Anual (1A)"], index=0)
            mapa_intervalos = {"Diario (1D)": "1day", "Mensual (1M)": "1month", "Anual (1A)": "1year"}
            api_param = mapa_intervalos[intervalo]

        with col_btn:
            st.write("##")
            btn_consultar = st.button("Analizar", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    if btn_consultar and ticker:
        with st.spinner(f'Buscando {ticker} en intervalo {intervalo}...'):
            try:
                res = requests.get(f"{API_URL}/stock/{ticker}", params={"interval": api_param})

                if res.status_code == 200:
                    data = res.json()
                    met = data["metricas"]
                    hist = data["historial_cierre"]

                    st.markdown(f"""
                        <div class="flex items-baseline justify-between mb-6">
                            <div class="flex items-baseline space-x-4">
                                <h3 class="text-4xl font-black text-white">{ticker}</h3>
                                <span class="px-3 py-1 bg-[#13ec6d]/20 text-[#13ec6d] text-xs font-bold rounded-full border border-[#13ec6d]/30">LIVE DATA</span>
                            </div>
                            <div class="text-gray-400 text-sm font-mono">Vista: {intervalo}</div>
                        </div>
                    """, unsafe_allow_html=True)

                    col1, col2, col3 = st.columns(3)
                    col1.metric("Último Cierre", f"${met['ultimo_cierre']}")
                    col2.metric("Rango Periodo", f"${met['rango_diario']}")
                    col3.metric("Vol. Medio", f"{met['volumen_medio']:,}")

                    # --- GRÁFICA AJUSTABLE CON ZOOM EN EJE Y ---
                    df_hist = pd.DataFrame(list(hist.items()), columns=['Fecha', 'Precio'])
                    df_hist['Fecha'] = pd.to_datetime(df_hist['Fecha'])
                    df_hist = df_hist.sort_values('Fecha')

                    fig = px.area(df_hist, x='Fecha', y='Precio', template="plotly_dark",
                                  title=f"Evolución Histórica - {intervalo}")

                    fig.update_traces(line_color='#13ec6d', fillcolor='rgba(19, 236, 109, 0.15)')

                    # AJUSTE DINÁMICO DEL EJE Y (VARIEDAD VISUAL)
                    fig.update_yaxes(range=[df_hist['Precio'].min() * 0.99, df_hist['Precio'].max() * 1.01],
                                     autorange=False)

                    if api_param == "1day":
                        fig.update_xaxes(dtick="D1", tickformat="%b %d")
                    elif api_param == "1month":
                        fig.update_xaxes(dtick="M1", tickformat="%b %Y")

                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error(f"Error {res.status_code}: No se pudo obtener información.")
            except Exception as e:
                st.error(f"Fallo de conexión: {str(e)}")

# --- 4. PANTALLA: CARGAR DATOS MANUALES ---
elif menu == "Cargar Datos Manuales":
    st.markdown("""
        <div class="mb-8">
            <h2 class="text-3xl font-bold text-white">Inserción Manual</h2>
            <p class="text-gray-400 mt-1">Inyecta datos personalizados en la base de datos local mediante CSV o JSON.</p>
        </div>
    """, unsafe_allow_html=True)

    st.write("### Método de entrada")
    metodo = st.radio("Selecciona formato de carga:", ["Subir Archivo CSV", "Pegar Texto JSON"], horizontal=True)

    with st.container():
        st.markdown('<div class="bg-[#1a2e24] p-6 rounded-xl border border-[#2d4a3e] shadow-lg mb-8">',
                    unsafe_allow_html=True)

        if metodo == "Subir Archivo CSV":
            ticker_manual = st.text_input("Asignar Ticker", placeholder="Ej: MI_EMPRESA").upper()
            uploaded_file = st.file_uploader("Cargar archivo CSV con historial", type="csv")

            if st.button("Guardar CSV en Base de Datos"):
                if uploaded_file and ticker_manual:
                    df_upload = pd.read_csv(uploaded_file)
                    datos_json = df_upload.to_dict(orient="records")
                    payload = {"ticker": ticker_manual, "datos": datos_json}
                    res = requests.post(f"{API_URL}/insert-manual", json=payload)
                    if res.status_code == 200:
                        st.success(f"¡Éxito! {ticker_manual} ya está disponible.")
                    else:
                        st.error(f"Error: {res.json().get('detail', 'Error desconocido')}")
        else:
            json_input = st.text_area("Datos JSON:", height=300, placeholder='{"ticker": "ABC", "datos": [...]}')
            if st.button("Enviar JSON a la API"):
                try:
                    payload = json.loads(json_input)
                    res = requests.post(f"{API_URL}/insert-manual", json=payload)
                    if res.status_code == 200:
                        st.success(f"¡Datos cargados correctamente!")
                    else:
                        st.error(f"Error de API: {res.json().get('detail', 'Estructura incorrecta')}")
                except:
                    st.error("Error: JSON no válido.")
        st.markdown('</div>', unsafe_allow_html=True)

# --- 5. PANTALLA: PREDICCIÓN IA ---
elif menu == "Predicción IA":
    st.markdown("""
        <div class="mb-8">
            <h2 class="text-3xl font-bold text-white tracking-tight">IA Prophet <span class="text-[#13ec6d]">Forecast</span></h2>
            <p class="text-gray-400 mt-1">Entrenamiento y validación de series temporales.</p>
        </div>
    """, unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="bg-[#1a2e24] p-6 rounded-2xl border border-[#13ec6d]/20 shadow-xl mb-8">',
                    unsafe_allow_html=True)
        col_search, col_btn = st.columns([4, 1])
        with col_search:
            ticker_ia = st.text_input("Ticker para IA", placeholder="Ej: MSFT").upper()
        with col_btn:
            st.write("##")
            btn_predecir = st.button("Ejecutar IA", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    if btn_predecir and ticker_ia:
        with st.spinner('Entrenando Prophet...'):
            response = requests.get(f"{API_URL}/predict/{ticker_ia}")
            if response.status_code == 200:
                raw_data = response.json()
                ia_data = raw_data["ia_forecast"]
                eficacia = ia_data["eficacia"]
                preds = ia_data["prediccion_futura"]

                st.markdown(f"""
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
                        <div class="bg-[#1a2e24]/70 p-6 rounded-2xl border-l-4 border-[#13ec6d]">
                            <p class="text-sm text-[#13ec6d] font-medium mb-1">Precisión</p>
                            <div class="text-4xl font-black text-white">{eficacia['precision_porcentual']}</div>
                        </div>
                        <div class="bg-[#1a2e24]/70 p-6 rounded-2xl border-l-4 border-blue-500">
                            <p class="text-sm text-blue-400 font-medium mb-1">MAE (Error Medio)</p>
                            <div class="text-4xl font-black text-white">${eficacia['error_medio_usd']}</div>
                        </div>
                        <div class="bg-[#1a2e24]/70 p-6 rounded-2xl border-l-4 border-yellow-500">
                            <p class="text-sm text-yellow-500 font-medium mb-1">Confiabilidad</p>
                            <div class="text-2xl font-bold text-white">{eficacia['confiabilidad']}</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

                df_pred = pd.DataFrame(list(preds.items()), columns=['Fecha', 'Precio_Estimado'])
                fig_ia = px.area(df_pred, x='Fecha', y='Precio_Estimado', template="plotly_dark",
                                 color_discrete_sequence=['#13ec6d'])
                fig_ia.update_traces(fillcolor='rgba(19, 236, 109, 0.2)', line_width=4)

                # AJUSTE DEL EJE Y PARA PREDICCIÓN
                fig_ia.update_yaxes(
                    range=[df_pred['Precio_Estimado'].min() * 0.98, df_pred['Precio_Estimado'].max() * 1.02],
                    autorange=False)

                st.plotly_chart(fig_ia, use_container_width=True)

# --- 6. PANTALLA: COMPARAR EMPRESAS ---
elif menu == "Comparar Empresas":
    st.markdown('<h1 class="text-3xl font-bold text-white p-8">Comparativa de Rendimiento</h1>', unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="bg-[#1a2e23] p-6 rounded-xl border border-[#2d4a3b] shadow-xl mx-8 mb-8">',
                    unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            t1 = st.text_input("Activo 1 (Ticker)",  placeholder="Ej: TSLA").upper()
        with c2:
            t2 = st.text_input("Activo 2 (Ticker)",  placeholder="Ej: BTC").upper()

        if st.button("Ejecutar Comparativa"):
            with st.spinner(f"Analizando {t1} vs {t2}..."):
                try:
                    response = requests.get(f"{API_URL}/compare/{t1}/{t2}")
                    if response.status_code == 200:
                        res_comp = response.json()
                        lider = res_comp.get('lider-rendimiento')
                        st.markdown(
                            f'<div class="bg-[#13ec6d]/10 border border-[#13ec6d]/30 p-6 rounded-lg mb-8 text-center"><h3 class="text-[#13ec6d] text-4xl font-black">{lider}</h3></div>',
                            unsafe_allow_html=True)

                        col_a, col_b = st.columns(2)
                        for col, ticker in zip([col_a, col_b], [t1, t2]):
                            info = res_comp.get(ticker, {})
                            with col:
                                st.markdown(f"""
                                <div class="bg-[#102218] p-4 rounded-lg border border-[#2d4a3b]">
                                    <h4 class="text-white font-bold">{ticker}</h4>
                                    <p class="text-2xl font-bold text-[#13ec6d]">{info.get('rendimiento_periodo')}</p>
                                    <p class="text-gray-400 text-sm">Precio: ${info.get('ultimo_precio')}</p>
                                    <p class="text-[10px] text-gray-500 mt-2">Origen: {info.get('fuente')}</p>
                                </div>
                                """, unsafe_allow_html=True)
                    else:
                        st.error("Error en la comparativa.")
                except Exception as e:
                    st.error(f"Error: {e}")