# Voice POS (Vpos) 🎙️🛒

Voice POS es un sistema de Punto de Venta (Point of Sale) innovador controlado por voz e impulsado por Inteligencia Artificial. Diseñado para ofrecer una experiencia de usuario rápida y manos libres, permite a los cajeros y vendedores realizar cobros, agregar productos al carrito y consultar inventario simplemente hablando.

## Características Principales

*   **Ventas Rápidas por Voz:** Agrega productos individuales o múltiples al carrito con comandos naturales (ej. *"Véndeme dos cocas y unas galletas"*).
*   **Inteligencia Artificial Integrada:** Utiliza modelos LLM (vía Groq) para extraer intenciones, cantidades y entidades desde el lenguaje natural.
*   **Desambiguación Inteligente:** Si pides "una coca" y existen varios tamaños, el sistema detecta la ambigüedad y te permite elegir la correcta interactuando fluidamente.
*   **Checkout y Cálculo de Cambio Automático:** Comando de cobro inteligente que detecta con cuánto pagó el cliente y calcula el cambio (ej. *"Cobrar con 500"*).
*   **Consultas de Inventario:** Pregunta por precios y existencias al instante (ej. *"¿Cuánto cuesta el jabón Zote?"*).
*   **Context Shifting:** El motor comprende si interrumpes una venta para hacer una consulta y te permite retomar el flujo sin perder datos.

## Arquitectura del Sistema

El proyecto está dividido en dos partes principales:

### Backend (Python / FastAPI)
*   **Framework:** FastAPI
*   **Base de Datos:** Supabase (PostgreSQL)
*   **IA & NLP:** Groq API para el procesamiento de lenguaje natural y extracción estructurada de datos.
*   **Motor de Estados:** Un `StateManager` personalizado que gestiona el contexto de la conversación (ej. manteniendo vivo el carrito de compras en la sesión).

### Frontend (React / Vite)
*   **Framework:** React 19 con TypeScript + Vite.
*   **Estilos:** Tailwind CSS.
*   **Integración de Voz:** Manejo de Web Speech API (o integración de audio) para capturar los comandos de voz y enviarlos al backend.

## 🛠️ Instalación y Configuración Local

### Requisitos Previos
*   Python 3.9+
*   Node.js 18+
*   Cuenta en Supabase y Groq (para las API Keys).

### 1. Clonar el repositorio
```bash
git clone https://github.com/ErnestoMaFl/Vpos.git
cd Vpos
```

### 2. Configurar el Backend
```bash
cd backend
python -m venv venv
# Activar entorno virtual (Windows)
.\venv\Scripts\activate
# Activar entorno virtual (Mac/Linux)
source venv/bin/activate

pip install -r requirements.txt
```

Crea un archivo `.env` en la carpeta `backend/` con tus credenciales:
```env
SUPABASE_URL=tu_supabase_url
SUPABASE_KEY=tu_supabase_key
GROQ_API_KEY=tu_groq_api_key
```

Inicia el servidor Backend:
```bash
python main.py
```

### 3. Configurar el Frontend
Abre una nueva terminal en la raíz del proyecto.
```bash
cd frontend
npm install
npm run dev
```

## 🧪 Testing y Casos de Uso
El sistema soporta flujos complejos. Para ver una lista detallada de todos los escenarios de prueba soportados (ventas múltiples, cobros con cambio, manejo de errores y ambigüedades), revisa la documentación interna del proyecto o el archivo de pruebas generado.

