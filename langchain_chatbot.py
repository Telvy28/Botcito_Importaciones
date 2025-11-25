"""
LangChain SQL Agent v5.2 - FIX DEEPSEEK
Cambio a estructura ReAct para forzar ejecución
"""
import os
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits import create_sql_agent, SQLDatabaseToolkit
from langchain.agents.agent_types import AgentType

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class LangChainChatbot:
    SUPPORTED_PROVIDERS = ["openai", "deepseek", "groq"] # Agregado Groq
    DEFAULT_TABLE = "BD_Import_IQ"
    
    def __init__(self, provider: str = "openai"):
        self.provider = provider
        self.db = None
        self.llm = None
        self.agent = None
        
        self._connect_database()
        self._setup_llm()
        self._create_agent()
    
    def _connect_database(self):
        connection_string = os.getenv("SUPABASE_CONNECTION_STRING")
        if not connection_string:
            raise ValueError("Falta SUPABASE_CONNECTION_STRING en .env")
            
        try:
            self.db = SQLDatabase.from_uri(
                connection_string,
                include_tables=[os.getenv("TABLE_NAME", self.DEFAULT_TABLE)],
                sample_rows_in_table_info=2
            )
        except Exception as e:
            raise ConnectionError(f"Error conectando DB: {e}")

    def _setup_llm(self):
        # Configuración específica para que DeepSeek no alucine
        if self.provider == "deepseek":
            api_key = os.getenv("DEEPSEEK_API_KEY")
            self.llm = ChatOpenAI(
                model="deepseek-chat",
                temperature=0, # Cero creatividad, solo lógica
                openai_api_key=api_key,
                openai_api_base="https://api.deepseek.com",
                max_tokens=1024
            )
            self.provider_name = "DeepSeek"
            
        elif self.provider == "groq":
            # Groq suele ser mejor siguiendo instrucciones que DeepSeek en SQL
            from langchain_groq import ChatGroq
            api_key = os.getenv("GROQ_API_KEY")
            self.llm = ChatGroq(
                model="llama-3.3-70b-versatile",
                temperature=0,
                api_key=api_key
            )
            self.provider_name = "Groq Llama 3.3"
            
        else: # OpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            self.llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0,
                openai_api_key=api_key
            )
            self.provider_name = "OpenAI"

    def _create_agent(self):
        self.toolkit = SQLDatabaseToolkit(db=self.db, llm=self.llm)
        
        # Configuración específica según provider
        if self.provider == "deepseek":
            # DeepSeek necesita formato más directo
            prefix = self._get_deepseek_prefix()
        else:
            prefix = self._get_system_prefix()
        
        self.agent = create_sql_agent(
            llm=self.llm,
            toolkit=self.toolkit,
            agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=10 if self.provider == "deepseek" else 15,
            prefix=prefix,
            early_stopping_method="generate" if self.provider == "deepseek" else "force"
        )

    def _get_deepseek_prefix(self) -> str:
        """Prefix optimizado para DeepSeek - más directo y simple"""
        return """You are a SQL expert assistant for import data analysis.

DATABASE: PostgreSQL
TABLE: BD_Import_IQ

COLUMNS (use exact names with quotes):
"ID", "DUA", "Fecha", "RUC", "Importador", "Embarcador", "Pais_origen",
"Descripcion", "Kg_Neto", "Qty_2", "Und_2", "CIF_Tot", "CIF_und",
"Marca", "Formulacion", "Concentracion", "Concent_disgregada",
"INGREDIENTE_nuevo", "CLASE_SIGIA", "TIPO", "Estado", "Presentacion", "Via"

CRITICAL RULES:
1. ALWAYS use Action: sql_db_query to execute queries
2. Extract year with: EXTRACT(YEAR FROM "Fecha")
3. Use ILIKE with % for text searches: WHERE "Marca" ILIKE '%TERM%'
4. Column names with capitals need quotes: "Kg_Neto", "CIF_Tot"
5. Respond in Spanish with real data only

EXECUTION FORMAT:
Action: sql_db_query
Action Input: [YOUR SQL QUERY HERE]

Example for "top 5 marcas":
Action: sql_db_query
Action Input: SELECT "Marca", SUM("Kg_Neto") as total FROM "BD_Import_IQ" GROUP BY "Marca" ORDER BY total DESC LIMIT 5

START NOW. Execute queries, don't just write them."""

    def _get_system_prefix(self) -> str:
        """System prompt para el agente SQL"""
        return """Eres un asistente experto en análisis de importaciones y comercio exterior.

Tienes acceso directo a una base de datos PostgreSQL con información de importaciones.

TABLA PRINCIPAL: BD_Import_IQ

COLUMNAS DISPONIBLES (23 columnas):
- ID, DUA, Fecha, RUC, Importador, Embarcador, Pais_origen
- Descripcion, Kg_Neto, Qty_2, Und_2, CIF_Tot, CIF_und
- Marca, Formulacion, Concentracion, Concent_disgregada
- INGREDIENTE_nuevo, CLASE_SIGIA, TIPO, Estado, Presentacion, Via

CAPACIDADES:
- Puedes crear CUALQUIER query SQL que necesites
- Puedes hacer múltiples queries para responder preguntas complejas
- Puedes explorar el schema de la base de datos
- Puedes calcular agregaciones, promedios, porcentajes, rankings
- Puedes hacer JOINs, CTEs, subconsultas si es necesario

⚠️ REGLAS INQUEBRANTABLES ⚠️
1. NO RESPONDAS NADA HASTA TENER DATOS REALES DE LA BASE DE DATOS.
2. SI ESCRIBES CÓDIGO SQL EN EL CHAT PERO NO EJECUTAS LA ACCIÓN, FALLARÁS.
3. SIEMPRE USA LA HERRAMIENTA: sql_db_query
4. FORMATO OBLIGATORIO DE PENSAMIENTO:
   
   Question: la pregunta del usuario
   Thought: debo buscar X en la tabla Y...
   Action: sql_db_query
   Action Input: SELECT ... FROM ...
   Observation: [Resultados de la DB]
   Thought: Ya tengo los datos, la respuesta es...
   Final Answer: La respuesta final al usuario.

5. PARA BÚSQUEDAS DE TEXTO (MARCAS/EMPRESAS):
   - SIEMPRE USA `ILIKE` Y COMODINES `%`.
   - Ejemplo: WHERE "Marca" ILIKE '%DORMEX%'

6. SI LA CONSULTA DEVUELVE VACÍO:
   - Intenta buscar con una palabra más corta (ej: '%DORM%').
   - Verifica los años usando EXTRACT(YEAR FROM "Fecha").

INSTRUCCIONES IMPORTANTES:
1. **Usa SQL estándar de PostgreSQL**
2. **SIEMPRE extrae el año de la columna Fecha con EXTRACT(YEAR FROM "Fecha")**
3. **Los nombres de columnas con mayúsculas van entre comillas dobles**: "Kg_Neto", "CIF_Tot", "Marca"
4. **Para búsquedas de texto usa ILIKE (case-insensitive)**: WHERE "Marca" ILIKE '%MIXHOR%'
5. **Para fechas usa formato 'YYYY-MM-DD'**
6. **Siempre limita resultados grandes con LIMIT**
7. **Presenta datos en formato claro y estructurado**

CONTEXTO DE NEGOCIO:
- "Marca" = Marcas de productos importados
- "Importador" = Empresas que importan
- "Pais_origen" = País de procedencia
- "Kg_Neto" = Peso en kilogramos
- "CIF_Tot" = Valor CIF total en USD
- "INGREDIENTE_nuevo" = Ingredientes activos de productos

EJEMPLOS DE QUERIES:

1. Top 10 marcas históricas:
```sql
SELECT "Marca", SUM("Kg_Neto") as total_kg
FROM "BD_Import_IQ"
GROUP BY "Marca"
ORDER BY total_kg DESC
LIMIT 10;
```

2. Evolución por año:
```sql
SELECT EXTRACT(YEAR FROM "Fecha") as anio, SUM("Kg_Neto") as total_kg
FROM "BD_Import_IQ"
WHERE "Marca" ILIKE '%MIXHOR%'
GROUP BY anio
ORDER BY anio;
```

3. Comparación entre años:
```sql
WITH year_2020 AS (
    SELECT "Marca", SUM("Kg_Neto") as kg_2020
    FROM "BD_Import_IQ"
    WHERE EXTRACT(YEAR FROM "Fecha") = 2020
    GROUP BY "Marca"
),
year_2025 AS (
    SELECT "Marca", SUM("Kg_Neto") as kg_2025
    FROM "BD_Import_IQ"
    WHERE EXTRACT(YEAR FROM "Fecha") = 2025
    GROUP BY "Marca"
)
SELECT 
    COALESCE(y1."Marca", y2."Marca") as marca,
    COALESCE(y1.kg_2020, 0) as kg_2020,
    COALESCE(y2.kg_2025, 0) as kg_2025,
    COALESCE(y2.kg_2025, 0) - COALESCE(y1.kg_2020, 0) as cambio,
    CASE 
        WHEN y1.kg_2020 > 0 THEN 
            ROUND(((COALESCE(y2.kg_2025, 0) - y1.kg_2020) / y1.kg_2020 * 100)::numeric, 2)
        ELSE NULL 
    END as porcentaje_cambio
FROM year_2020 y1
FULL OUTER JOIN year_2025 y2 ON y1."Marca" = y2."Marca"
ORDER BY cambio DESC
LIMIT 20;
```

RECUERDA:
- Si no estás seguro de una query, puedes hacer múltiples queries exploratorias
- Siempre verifica que los nombres de columnas sean correctos
- Presenta los resultados de forma clara y en español
- Si encuentras muchos resultados, muestra solo los más relevantes

¡EMPIEZA AHORA! NO INVENTES DATOS.
"""
    
    def chat(self, user_message: str) -> str:
        if not user_message: 
            return "Por favor, haz una pregunta sobre las importaciones."
        
        try:
            # Para DeepSeek, agregar instrucción específica
            if self.provider == "deepseek":
                # Instrucción clara para ejecutar SQL
                enhanced_message = f"""
                Pregunta del usuario: {user_message}
                
                IMPORTANTE: Debes ejecutar una consulta SQL para responder.
                Usa Action: sql_db_query seguido de la consulta SQL.
                """
                response = self.agent.run(enhanced_message)
            else:
                # Groq y OpenAI funcionan bien con el mensaje directo
                response = self.agent.run(user_message)
            
            # Limpiar respuesta si es muy verbose
            if "Entering new SQL Agent" in response:
                lines = response.split('\n')
                # Buscar la respuesta final
                clean_response = []
                capture = False
                for line in lines:
                    if "Final Answer:" in line:
                        capture = True
                        clean_response.append(line.replace("Final Answer:", "").strip())
                    elif capture and not line.startswith(">"):
                        clean_response.append(line)
                
                if clean_response:
                    return '\n'.join(clean_response).strip()
            
            return response
            
        except Exception as e:
            return self._handle_error(e)
    
    def _handle_error(self, error: Exception) -> str:
        """Maneja errores de forma amigable"""
        error_msg = str(error).lower()
        
        # Errores comunes con mensajes claros
        if "connection" in error_msg or "could not connect" in error_msg:
            logger.error(f"Error de conexión: {error}")
            return "❌ Error de conexión con la base de datos. Verifica tu SUPABASE_CONNECTION_STRING en .env"
        
        elif "password" in error_msg or "authentication" in error_msg:
            logger.error(f"Error de autenticación: {error}")
            return "❌ Error de autenticación. Verifica tu password de Supabase en .env"
        
        elif "table" in error_msg or "column" in error_msg:
            logger.error(f"Error de estructura: {error}")
            return f"❌ Error en la estructura de la tabla. Verifica que la tabla y columnas existan."
        
        elif "timeout" in error_msg:
            logger.error(f"Timeout: {error}")
            return "❌ La consulta tardó demasiado. Intenta con una pregunta más específica."
        
        elif "rate limit" in error_msg or "quota" in error_msg:
            logger.error(f"Rate limit: {error}")
            return "❌ Límite de API alcanzado. Espera unos minutos e intenta nuevamente."
        
        else:
            logger.error(f"Error desconocido: {error}")
            return f"❌ Error al procesar la pregunta: {str(error)[:200]}"
    
    def get_table_info(self) -> str:
        """Obtiene información de la tabla"""
        try:
            return self.db.get_table_info()
        except Exception as e:
            logger.error(f"Error al obtener info de tabla: {e}")
            return f"❌ Error al obtener información de la tabla: {e}"
    
# Mantener el resto de métodos auxiliares (test_connection, get_stats) igual...
    def test_connection(self):
        try:
            self.db.run("SELECT 1")
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_stats(self) -> Optional[Dict[str, Any]]:
        """Obtiene estadísticas básicas de la base de datos"""
        try:
            queries = {
                "total_records": 'SELECT COUNT(*) FROM "BD_Import_IQ"',
                "date_range": 'SELECT MIN("Fecha"), MAX("Fecha") FROM "BD_Import_IQ"',
                "total_marcas": 'SELECT COUNT(DISTINCT "Marca") FROM "BD_Import_IQ"',
                "total_importadores": 'SELECT COUNT(DISTINCT "Importador") FROM "BD_Import_IQ"'
            }
            
            stats = {}
            for key, query in queries.items():
                result = self.db.run(query)
                stats[key] = result
            
            logger.info("✅ Estadísticas obtenidas")
            return stats
            
        except Exception as e:
            logger.error(f"Error al obtener estadísticas: {e}")
            return None


def test_langchain_agent(provider: str = "openai"):
    """
    Función de prueba del agente
    
    Args:
        provider: Provider a probar ("openai" o "deepseek")
    """
    print("\n" + "="*60)
    print(f"🧪 INICIANDO PRUEBAS - Provider: {provider.upper()}")
    print("="*60)
    
    try:
        # Inicializar chatbot
        chatbot = LangChainChatbot(provider=provider)
        
        # Test 1: Conexión
        print("\n" + "="*60)
        print("🔍 TEST 1: CONEXIÓN A BASE DE DATOS")
        print("="*60)
        test_result = chatbot.test_connection()
        print(f"Resultado: {test_result}")
        
        if not test_result["success"]:
            print("\n❌ Test de conexión falló. Abortando pruebas.")
            return False
        
        # Test 2: Estadísticas
        print("\n" + "="*60)
        print("📊 TEST 2: ESTADÍSTICAS GENERALES")
        print("="*60)
        stats = chatbot.get_stats()
        if stats:
            for key, value in stats.items():
                print(f"  {key}: {value}")
        
        # Test 3: Query simple
        print("\n" + "="*60)
        print("💬 TEST 3: QUERY SIMPLE")
        print("="*60)
        pregunta = "¿Cuántas importaciones hay en total?"
        print(f"Pregunta: {pregunta}")
        response = chatbot.chat(pregunta)
        print(f"Respuesta: {response}")
        
        # Test 4: Query compleja
        print("\n" + "="*60)
        print("💬 TEST 4: QUERY COMPLEJA")
        print("="*60)
        pregunta = "¿Cuáles son las top 5 marcas más importadas?"
        print(f"Pregunta: {pregunta}")
        response = chatbot.chat(pregunta)
        print(f"Respuesta: {response}")
        
        print("\n" + "="*60)
        print("✅ TODAS LAS PRUEBAS COMPLETADAS")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR EN PRUEBAS: {e}")
        logger.exception("Error durante las pruebas")
        return False


if __name__ == "__main__":
    # Ejecutar pruebas
    import sys
    
    provider = sys.argv[1] if len(sys.argv) > 1 else "openai"
    success = test_langchain_agent(provider)
    
    sys.exit(0 if success else 1)