# StudyStock: Terminal de Análisis Financiero con IA 🤖

**StudyStock** es una plataforma avanzada de análisis bursátil diseñada para el ecosistema de trading moderno. Combina la agilidad de una API REST de alto rendimiento con un motor de 
Inteligencia Artificial capaz de predecir tendencias de mercado y un Dashboard interactivo para la visualización de datos complejos.


## Arquitectura y Estructura del Proyecto

El proyecto está organizado siguiendo el patrón de **paquetes de Python**, lo que garantiza un despliegue limpio y profesional en entornos Cloud.

### Directorio de Aplicación (`/app`)
Para facilitar el despliegue en la nube, todo el código fuente reside en la carpeta `/app`.
* **`__init__.py`**: Archivo crítico para el despliegue en **Render**. Su presencia permite que el servidor de producción trate a la carpeta como un paquete, resolviendo errores de importación de módulos internos (`ModuleNotFoundError`).
* **`main.py`**: Punto de entrada de la API (FastAPI). Gestiona los endpoints de consulta de stocks, inserción manual de datos y comparación de activos. Incluye configuración de **CORS** para permitir la comunicación bidireccional con el Dashboard.
* **`api_engine.py`**: El núcleo lógico. Integra la librería **Prophet (de Meta)** para predicciones. Implementa un algoritmo híbrido que prioriza datos locales (inyectados por el usuario) frente a datos globales de la API de **Twelve Data**.

### Archivos de Configuración (Raíz)
* **`requirements.txt`**: Listado detallado de librerías. Incluye `gunicorn` para el entorno de producción y `uvicorn` para desarrollo local.
* **`.gitignore`**: Configurado para excluir entornos virtuales, archivos de caché y el archivo `.env`, protegiendo las credenciales privadas.
* **`dashboard.py`**: Interfaz de usuario construida en **Streamlit**. Se comunica con la API mediante peticiones asíncronas para mostrar gráficos dinámicos de Plotly.



## Motor de Inteligencia Artificial

A diferencia de las consultas tradicionales, StudyStock ofrece un análisis predictivo real:
1.  **Entrenamiento Dinámico**: Al consultar un ticker, el motor entrena un modelo Prophet en tiempo real con los últimos 365 días de mercado.
2.  **Validación de Precisión**: El sistema calcula automáticamente el **MAE (Media de Error Absoluto)** y la **Precisión Porcentual** comparando las predicciones pasadas con los precios reales.
3.  **Análisis de Rendimiento**: Calcula el crecimiento porcentual esperado, ayudando al inversor a tomar decisiones basadas en datos, pudiendo comparar entre opciones.



## Despliegue y Configuración en la Nube (Render)

El proyecto está optimizado para funcionar 24/7 en **Render.com**:

* **Runtime**: Python 3.14.3.
* **Build Command**: `pip install -r requirements.txt`.
* **Start Command**: `gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app`.  (Se utiliza Gunicorn para manejar el tráfico de red de forma eficiente y segura en producción.)
* **Variables de Entorno**: La `TWELVE_DATA_KEY` se configura de forma aislada en el panel de Render, manteniendo la seguridad del repositorio de GitHub.



## Endpoints Principales

* `GET /stock/{symbol}`: Obtiene análisis histórico + predicción IA a 7 días.
* `POST /insert-manual`: Permite al usuario inyectar datos propios (tickers personalizados) que persisten en la memoria del servidor.
* `GET /compare`: Algoritmo de comparación que determina cuál de dos activos tiene un mejor rendimiento proyectado.

---

**Desarrollado para HackUDC 2026 - Una solución escalable para el análisis de mercados financieros.**
