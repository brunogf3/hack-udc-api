
# LIBRERÍAS
import os
import pandas as pd
import numpy as np
from twelvedata import TDClient
from prophet import Prophet
from dotenv import load_dotenv
import logging
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error


# Configuración de logs y entorno
load_dotenv()
logging.getLogger('prophet').setLevel(logging.ERROR)

API_KEY = os.getenv("TWELVE_DATA_KEY") # Para la KEY, basta con registrarse en Twelve Data
td = TDClient(apikey=API_KEY)


# DESCARGAR DATOS DE UNA EMPRESA

def descargar_datos(symbol: str):
    # Descarga el último año de datos diarios usando Twelve Data.
    try:
        if not API_KEY:
            return {"error": "No se encontró TWELVE_DATA_KEY en el archivo .env"}

        # Solicitamos la serie temporal
        ts = td.time_series(
            symbol=symbol,
            interval="1day",
            outputsize=365,  # Un año de datos para la IA
            order="ASC"  # Orden ascendente para Prophet
        )

        df = ts.as_pandas()

        if df is None or df.empty:
            return {"error": f"No se encontraron datos para {symbol}. Revisa el ticker."}

        # Twelve Data devuelve las columnas con mayúscula inicial, las pasamos a minúsculas.
        df.columns = [col.lower() for col in df.columns]
        return df
    except Exception as e:
        if "api key" in str(e).lower():
            return {"error": "API Key inválida o expirada."}
        return {"error": f"Error en Twelve Data: {str(e)}"}

# DESCARGAR HISTORIAL EMPRESA

def obtener_historial_formateado(df: pd.DataFrame, dias: int = 10):

    # Extrae los últimos 'n' días del historial y los formatea para JSON.

    if df is None or df.empty:
        return {}

    # Tomamos los últimos 'n' registros (en este caso 10).
    ultimo_historial = df['close'].tail(dias).to_dict()

    # Formateamos las fechas (que son el índice) a strings YYYY-MM-DD
    return {str(fecha.date()): round(float(valor), 2) for fecha, valor in ultimo_historial.items()}

# ESTADÍSTICAS EMPRESA

def calcular_estadisticas(df: pd.DataFrame):
    # Cálculos financieros básicos.
    return {
        "ultimo_cierre": round(float(df['close'].iloc[-1]), 2),
        "rango_diario": round(float(df['high'].iloc[-1] - df['low'].iloc[-1]), 2),
        "volumen_medio": int(df['volume'].mean())
    }

# COMPARAR DOS EMPRESAS (tanto insertadas en POST como de Twelve Data)

def comparar_empresas(ticker1: str, ticker2: str):
    # Buscamos ambos usando nuestra función "maestra" que ya creamos
    df1 = obtener_datos(ticker1)
    df2 = obtener_datos(ticker2)

    if isinstance(df1, dict) and "error" in df1: return df1
    if isinstance(df2, dict) and "error" in df2: return df2

    # Calculamos el rendimiento porcentual de ambas para comparar
    # (Precio Final / Precio Inicial - 1) * 100
    perf1 = ((df1['close'].iloc[-1] / df1['close'].iloc[0]) - 1) * 100
    perf2 = ((df2['close'].iloc[-1] / df2['close'].iloc[0]) - 1) * 100

    return {  # Ánalisis de cada empresa y mejor opción.
        ticker1: {
            "ultimo_precio": round(float(df1['close'].iloc[-1]), 2),
            "rendimiento_periodo": f"{round(perf1, 2)}%",
            "fuente": "Local" if ticker1 in DB_LOCAL else "Twelve Data"
        },
        ticker2: {
            "ultimo_precio": round(float(df2['close'].iloc[-1]), 2),
            "rendimiento_periodo": f"{round(perf2, 2)}%",
            "fuente": "Local" if ticker2 in DB_LOCAL else "Twelve Data"
        },
        "lider-rendimiento": ticker1 if perf1 > perf2 else ticker2
    }


# PREDCCIÓN FUTURO EMPRESA (IA)

def predecir_ia(df: pd.DataFrame):
    try:
        # Si hay menos de 15 registros de valores en el historial de la empresa, al modelo
        # de IA no le sirve como aprendizaje (muy pocos datos).
        if len(df) < 15:
            return {"error": f"Datos insuficientes ({len(df)}). Se requieren al menos 15."}

        df_p = df.copy()
        # Estandarizar nombres de columnas
        if 'datetime' in df_p.columns:
            df_p = df_p.rename(columns={'datetime': 'ds', 'close': 'y', 'volume': 'volume'})
        else:
            df_p = df_p.reset_index().rename(
                columns={'datetime': 'ds', 'index': 'ds', 'close': 'y', 'volume': 'volume'})

        df_p['ds'] = pd.to_datetime(df_p['ds']).dt.tz_localize(None)
        df_p = df_p.dropna(subset=['ds', 'y', 'volume'])

        # 2. Validación Cruzada (Cálculo del MAE)
        # Dividimos: entrenamos con todo menos los últimos 5 días para testear
        train = df_p.iloc[:-5]
        test = df_p.iloc[-5:]

        m_val = Prophet(daily_seasonality=False, yearly_seasonality=True)
        m_val.add_regressor('volume')
        m_val.fit(train)

        # Predicción sobre el periodo de prueba
        forecast_test = m_val.predict(test[['ds', 'volume']])

        # AQUÍ DEFINIMOS MAE CORRECTAMENTE
        valor_mae = mean_absolute_error(test['y'], forecast_test['yhat'])
        precision = (1 - (valor_mae / test['y'].mean())) * 100

        # 3. Predicción Futura Final
        m_final = Prophet(daily_seasonality=False, yearly_seasonality=True)
        m_final.add_regressor('volume')
        m_final.fit(df_p)

        future = m_final.make_future_dataframe(periods=7)
        vol_medio = df_p['volume'].mean()
        future['volume'] = df_p['volume'].tolist() + [vol_medio] * 7

        forecast_final = m_final.predict(future).tail(7)

        return {
            "status": "success",
            "metricas": {
                "error_medio_usd": round(float(valor_mae), 2),
                "precision_porcentual": f"{round(precision, 2)}%"
            },
            "predicciones": {str(row.ds.date()): round(row.yhat, 2) for row in forecast_final.itertuples()}
        }

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return {"error": f"Fallo en el motor de IA: {str(e)}"}


# INSERTAR UNA EMPRESA

DB_LOCAL = {}  #Nuestro conjunto de empresas intoducidas

def guardar_datos_manuales(ticker: str, registros: list):
    try:
        df = pd.DataFrame(registros)

        columnas_req = ['datetime', 'open', 'high', 'low', 'close', 'volume']
        for col in columnas_req:
            if col not in df.columns:
                return {"error": f"Falta la columna obligatoria: {col}"}

        # Formateamos fechas y tipos
        df['datetime'] = pd.to_datetime(df['datetime'])
        df = df.sort_values('datetime')

        df = df.set_index('datetime')

        DB_LOCAL[ticker.upper()] = df
        return {"mensaje": f"Empresa {ticker} cargada con {len(df)} registros."}
    except Exception as e:
        return {"error": f"Error al procesar los datos: {str(e)}"}


# OBTENER DATOS: ALGORITMO DE ELECCIÓN
# SI ESTÁ EN DB_LOCAL (introducido por POST), lo extraemos de ahí.
# Si no, buscamos en Twelve Data

def obtener_datos(symbol: str):

    ticker = symbol.upper()

    # Comprobar en DB_LOCAL (Datos inyectados por el usuario)
    if ticker in DB_LOCAL:
        print(f"DEBUG: Recuperando {ticker} de la memoria local.")
        return DB_LOCAL[ticker]

    # Si no está, ir a la API externa
    print(f"DEBUG: {ticker} no encontrado en local. Consultando Twelve Data...")
    return descargar_datos(ticker)
