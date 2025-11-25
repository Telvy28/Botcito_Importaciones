# 🚢 Chatbot de Importaciones con IA

Chatbot conversacional para análisis de importaciones usando OpenAI, Supabase y Streamlit.

## 📋 Requisitos

- Python 3.8+
- Cuenta Supabase (con tabla de importaciones)
- API Key de OpenAI

## 🚀 Instalación

1. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

2. **Configurar variables de entorno:**

Edita el archivo `.env` con tus credenciales:

```env
SUPABASE_URL=tu_url_de_supabase
SUPABASE_KEY=tu_key_de_supabase
OPENAI_API_KEY=tu_api_key_de_openai
TABLE_NAME=importaciones
```

**Dónde encontrar las credenciales:**

- **Supabase:** 
  - URL y Key: Settings > API > Project URL y anon/public key
  
- **OpenAI:**
  - API Key: https://platform.openai.com/api-keys

3. **Verificar tabla en Supabase:**

Asegúrate que tu tabla `importaciones` tenga estas columnas:
- ID, DUA, Fecha, RUC, Importador, Embarcador, Pais_origen
- Descripcion, Kg_Neto, Qty_2, Und_2, CIF_Tot, CIF_und
- Marca, Formulacion, Concentracion, Concent_disgregada
- INGREDIENTE_nuevo, CLASE_SIGIA, TIPO, Estado, Presentacion, Via

## ▶️ Ejecutar la aplicación

```bash
streamlit run app.py
```

## 🎯 Funcionalidades

### 💬 Chat IA
- Conversación natural sobre importaciones
- Búsqueda inteligente con múltiples criterios
- Análisis automático de datos
- Function calling para consultas precisas

### 🔍 Búsqueda Avanzada
- Filtros por: importador, país, producto, ingrediente, marca, tipo
- Exportación a CSV
- Vista de todas las importaciones

### 📊 Dashboard
- Estadísticas generales en sidebar
- KPIs: total importaciones, países, importadores, valores CIF
- Visualizaciones (próximamente)

## 📁 Estructura del Proyecto

```
Chatbot_AI_Supabase/
├── app.py                      # Aplicación principal Streamlit
├── requirements.txt            # Dependencias
├── .env                        # Variables de entorno
├── utils/
│   ├── __init__.py
│   ├── supabase_client.py     # Conexión y CRUD con Supabase
│   └── chatbot.py             # Lógica del chatbot con OpenAI
```

## 💡 Ejemplos de Uso

**En el Chat:**
- "¿Cuántas importaciones tenemos de China?"
- "Muéstrame las importaciones del importador XYZ"
- "¿Cuál es el total CIF de las importaciones del 2020?"
- "Busca productos con ingrediente Glifosato"
- "Dame estadísticas generales"

## 🔧 Próximas Mejoras

1. Dashboard con KPIs visuales
2. Gráficos interactivos (top países, importadores, tendencias)
3. Filtros por rango de fechas
4. Análisis predictivo
5. Exportación a Excel con formato

## 🐛 Troubleshooting

**Error de conexión a Supabase:**
- Verifica URL y Key en `.env`
- Confirma que la tabla existe y tiene datos

**Error de OpenAI:**
- Verifica API Key válida
- Revisa saldo en tu cuenta OpenAI

**Módulos no encontrados:**
- Ejecuta: `pip install -r requirements.txt`

## 📞 Soporte

Para problemas o sugerencias, revisar la documentación de:
- Supabase: https://supabase.com/docs
- OpenAI: https://platform.openai.com/docs
- Streamlit: https://docs.streamlit.io
