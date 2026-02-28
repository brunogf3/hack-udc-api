# LIBRERÍAS
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from pydantic import BaseModel
import uvicorn
from app import api_engine as engine
import pandas as pd
import os


# Creamos el objeto
app = FastAPI(
    title="Twelve Data Financial AI",
    description="API de análisis bursátil con Inteligencia Artificial"
)

# --- CONFIGURACIÓN DE CORS ---
# Añadido para que el navegador no bloquee la conexión con Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MODELOS DE DATOS (Pydantic): TIPO DE DATO "EMPRESA" ---

class RegistroData(BaseModel):
    datetime: str  # Formato "YYYY-MM-DD"
    open: float
    high: float
    low: float
    close: float
    volume: int

class EmpresaManualRequest(BaseModel):
    ticker: str
    datos: List[RegistroData]

# --- ENDPOINTS ---


# GET /STOCK -> ANALIZAR UNA EMPRESA

@app.get("/stock/{symbol}")
async def get_stock(symbol: str):
    data = engine.obtener_datos(symbol.upper())

    if isinstance(data, dict) and "error" in data:
        raise HTTPException(status_code=400, detail=data["error"])

    stats = engine.calcular_estadisticas(data)

    # --- CAMBIO AQUÍ: Forzamos la conversión a datetime al iterar ---
    historial = {
        str(pd.to_datetime(fecha).date()): round(float(precio), 2)
        for fecha, precio in data['close'].tail(15).items()
    }

    return {
        "ticker": symbol.upper(),
        "metricas": stats,
        "historial_cierre": historial
    }


# GET /COMPARE -> COMPARAR DOS EMPRESAS

@app.get("/compare/{symbol1}/{symbol2}")
async def compare_stocks(symbol1: str, symbol2: str):
    resultado = engine.comparar_empresas(symbol1.upper(), symbol2.upper())

    if "error" in resultado:
        raise HTTPException(status_code=400, detail=resultado["error"])

    return resultado


# GET /PREDICT -> PREDECIR EL FUTURO DE LA EMPRESA (IA)

@app.get("/predict/{symbol}")
async def predict(symbol: str):
    df = engine.obtener_datos(symbol.upper())

    if isinstance(df, dict) and "error" in df:
        raise HTTPException(status_code=404, detail=df["error"])

    res = engine.predecir_ia(df)

    # Si la función de IA devuelve un error interno
    if isinstance(res, dict) and "error" in res:
        raise HTTPException(status_code=400, detail=res["error"])

    # Mapeo para que el Dashboard (Archivo Dos) reciba los nombres que espera
    return {
        "ticker": symbol.upper(),
        "ia_forecast": {
            "eficacia": {
                "precision_porcentual": res["metricas"]["precision_porcentual"],
                "error_medio_usd": res["metricas"]["error_medio_usd"],
                "confiabilidad": "Alta" if float(res["metricas"]["precision_porcentual"].replace('%', '')) > 85 else "Media"
            },
            "prediccion_futura": res["predicciones"]
        }
    }


# POST /INSERT-MANUAL -> INTRODUCIR UNA EMPRESA

@app.post("/insert-manual")
async def insert_manual(request: EmpresaManualRequest):
    # Convertimos los objetos Pydantic a diccionarios simples
    datos_dict = [reg.dict() for reg in request.datos]

    resultado = engine.guardar_datos_manuales(request.ticker, datos_dict)

    if "error" in resultado:
        raise HTTPException(status_code=400, detail=resultado["error"])

    return resultado

# FUNCION DE EJECUCIÓN RENDER

if __name__ == "__main__":
    import uvicorn
    # En Render, el puerto lo da la variable de entorno PORT
    port = int(os.environ.get("PORT", 8005))
    uvicorn.run(app, host="0.0.0.0", port=port)