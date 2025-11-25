import os
from dotenv import load_dotenv
import json
import pandas as pd

load_dotenv()

class ImportacionesChatbot:
    def __init__(self, supabase_client, provider="groq"):
        """
        Inicializa el chatbot con el provider especificado
        """
        self.db = supabase_client
        self.conversation_history = []
        self.provider = provider
        
        # Configurar cliente según provider
        self._setup_client()
        
        # System prompt OPTIMIZADO Y CLARO
        self.system_prompt = """Eres un analista experto en importaciones de la empresa IQ.
FECHA ACTUAL: Noviembre 2025
BASE DE DATOS: BD_Import_IQ (datos 2020-2025)

📊 REGLAS ESTRICTAS:
1. SIEMPRE usa las herramientas disponibles para obtener datos reales
2. NUNCA inventes información - si no hay datos, dilo claramente
3. Los datos de 2025 SÍ EXISTEN y son válidos
4. Responde SOLO con datos verificados de la base de datos

🛠️ USO DE HERRAMIENTAS:
• "Top marcas" → usa top_n_global con group_column="Marca"
• "Evolución de X" → usa analisis_temporal_entidad 
• "Resumen año X" → usa obtener_por_anio
• "Total histórico" → usa total_historico_entidad
• "Comparar años" → usa comparar_periodos

📝 FORMATO DE RESPUESTA:
- Presenta datos en tablas cuando sea apropiado
- Sé conciso pero preciso
- Incluye unidades (Kg, USD) en los valores
- Una conclusión breve al final (máx 2 líneas)

EJEMPLO:
Usuario: "Top 3 marcas 2024"
Tú: [Ejecutas top_n_global(group_column="Marca", n=3, year=2024)]
Respuesta: 
| Marca | Total Kg |
|-------|----------|
| MARCA1| 50,000   |
| MARCA2| 35,000   |
| MARCA3| 28,000   |

Las 3 principales marcas en 2024 sumaron 113,000 kg importados.
"""
    
    def _setup_client(self):
        """Configura el cliente según el provider - MODELOS ACTUALES DE GROQ"""
        
        if self.provider == "groq":
            try:
                from groq import Groq
                api_key = os.getenv("GROQ_API_KEY")
                if not api_key: 
                    raise ValueError("GROQ_API_KEY no configurada")
                
                self.client = Groq(api_key=api_key)
                
                # MODELOS ACTUALES DE GROQ (según el diagnóstico)
                available_models = [
                    "llama-3.3-70b-versatile",  # El más potente actualmente en Groq
                    "llama-3.1-8b-instant",     # Muy rápido
                    "mixtral-8x7b-32768"        # (Si volviera a estar disponible, o bórralo)
                ]
                
                # Probar modelos en orden
                for model in available_models:
                    try:
                        # Test rápido del modelo
                        test_response = self.client.chat.completions.create(
                            model=model,
                            messages=[{"role": "user", "content": "test"}],
                            max_tokens=5,
                            temperature=0
                        )
                        self.model = model
                        self.provider_name = f"Groq ({model.split('/')[-1]})"
                        print(f"✅ Groq configurado con modelo: {model}")
                        return
                    except Exception as e:
                        print(f"⚠️ Groq modelo {model} no funciona: {e}")
                        continue
                
                # Si ningún modelo funciona, usar OpenAI
                print("⚠️ Ningún modelo Groq funciona, usando OpenAI...")
                self.provider = "openai"
                self._setup_client()
                
            except Exception as e:
                print(f"⚠️ Error Groq: {e}. Usando OpenAI...")
                self.provider = "openai"
                self._setup_client()
        
        elif self.provider == "deepseek":
            try:
                from openai import OpenAI
                api_key = os.getenv("DEEPSEEK_API_KEY")
                if not api_key: 
                    raise ValueError("DEEPSEEK_API_KEY no configurada")
                
                self.client = OpenAI(
                    api_key=api_key,
                    base_url="https://api.deepseek.com"
                )
                self.model = "deepseek-chat"
                self.provider_name = "DeepSeek"
                print("✅ DeepSeek configurado")
                
            except Exception as e:
                print(f"⚠️ Error DeepSeek: {e}. Usando OpenAI...")
                self.provider = "openai"
                self._setup_client()
        
        elif self.provider == "openai":
            try:
                from openai import OpenAI
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key: 
                    raise ValueError("OPENAI_API_KEY no configurada")
                
                self.client = OpenAI(api_key=api_key)
                self.model = "gpt-4o-mini"
                self.provider_name = "OpenAI (GPT-4o-mini)"
                print("✅ OpenAI configurado")
                
            except Exception as e:
                raise Exception(f"Error OpenAI: {e}")

    # ... (el resto de las funciones se mantienen igual)

    def get_available_functions(self):
        return {
            "buscar_importaciones": self.buscar_importaciones,
            "obtener_por_id": self.obtener_por_id,
            "buscar_por_pais": self.buscar_por_pais,
            "buscar_por_importador": self.buscar_por_importador,
            "obtener_estadisticas": self.obtener_estadisticas,
            "obtener_por_anio": self.obtener_por_anio,
            "contar_valores_unicos": self.contar_valores_unicos,
            "agregar_por_anio": self.agregar_por_anio,
            "analisis_temporal_entidad": self.analisis_temporal_entidad,
            "top_n_global": self.top_n_global,
            "total_historico_entidad": self.total_historico_entidad,
            "comparar_periodos": self.comparar_periodos
        }
    
    def get_function_definitions(self):
        return [
            {
                "type": "function", "function": {
                    "name": "buscar_importaciones", "description": "Busca importaciones con filtros múltiples",
                    "parameters": { "type": "object", "properties": { "Importador": {"type": "string"}, "Pais_origen": {"type": "string"}, "Descripcion": {"type": "string"}, "Marca": {"type": "string"} }, "required": [] }
                }
            },
            {
                "type": "function", "function": {
                    "name": "obtener_por_anio", "description": "Resumen de importaciones de un año completo",
                    "parameters": { "type": "object", "properties": { "year": {"type": "integer"} }, "required": ["year"] }
                }
            },
            {
                "type": "function", "function": {
                    "name": "top_n_global", "description": "Obtiene Ranking Top N (marcas, paises, etc)",
                    "parameters": { "type": "object", "properties": { 
                        "group_column": {"type": "string", "enum": ["Marca", "Importador", "Pais_origen"]}, 
                        "agg_column": {"type": "string", "default": "Kg_Neto"}, 
                        "n": {"type": "integer", "default": 10}, 
                        "year": {"type": "integer"} 
                    }, "required": ["group_column"] }
                }
            },
            {
                "type": "function", "function": {
                    "name": "comparar_periodos", "description": "Compara metricas entre dos años",
                    "parameters": { "type": "object", "properties": { "year1": {"type": "integer"}, "year2": {"type": "integer"}, "group_column": {"type": "string"} }, "required": ["year1", "year2", "group_column"] }
                }
            },
            {
                "type": "function", "function": {
                    "name": "analisis_temporal_entidad", "description": "Evolución de una marca/empresa por año",
                    "parameters": { "type": "object", "properties": { "filter_column": {"type": "string"}, "filter_value": {"type": "string"} }, "required": ["filter_column", "filter_value"] }
                }
            },
            {
                "type": "function", "function": {
                    "name": "total_historico_entidad", "description": "Total histórico de una entidad específica",
                    "parameters": { "type": "object", "properties": { "filter_column": {"type": "string"}, "filter_value": {"type": "string"} }, "required": ["filter_column", "filter_value"] }
                }
            }
        ]
    
    # Implementación de funciones (se mantienen igual)
    def buscar_importaciones(self, **kwargs):
        filters = {k: v for k, v in kwargs.items() if v}
        results = self.db.search_importaciones(filters)
        return json.dumps({"total": len(results), "data": results[:5]} if results else {"total": 0})
    
    def obtener_por_id(self, id):
        return json.dumps(self.db.get_importacion_by_id(id) or {"mensaje": "No encontrado"})
    
    def buscar_por_pais(self, pais):
        return json.dumps(self.db.get_importaciones_by_pais(pais)[:5])
        
    def buscar_por_importador(self, importador):
        return json.dumps(self.db.get_importaciones_by_importador(importador)[:5])
        
    def obtener_estadisticas(self):
        return json.dumps(self.db.get_summary_stats())
        
    def obtener_por_anio(self, year):
        results = self.db.get_importaciones_by_year(year)
        if not results: return json.dumps({"year": year, "mensaje": "No hay datos"})
        df = pd.DataFrame(results)
        return json.dumps({
            "year": year,
            "total_registros": len(results),
            "total_kg": float(df['Kg_Neto'].sum()) if 'Kg_Neto' in df else 0,
            "total_cif": float(df['CIF_Tot'].sum()) if 'CIF_Tot' in df else 0
        })
        
    def contar_valores_unicos(self, column, year):
        vals = self.db.get_unique_values_by_year(column, year)
        return json.dumps({"year": year, "column": column, "count": len(vals), "samples": vals[:10]})
        
    def agregar_por_anio(self, year, group_column, agg_column="Kg_Neto", agg_function="sum"):
        res = self.db.get_aggregated_by_year(year, group_column, agg_column, agg_function)
        return json.dumps(res if res else {"mensaje": "Sin datos"})

    def analisis_temporal_entidad(self, filter_column, filter_value, agg_column="Kg_Neto", agg_function="sum"):
        res = self.db.get_time_series_by_entity(filter_column, filter_value, 'year', agg_column, agg_function)
        return json.dumps(res if res else {"mensaje": "Sin datos"})
        
    def top_n_global(self, group_column, agg_column="Kg_Neto", agg_function="sum", n=10, year=None):
        res = self.db.get_top_n_global(group_column, agg_column, agg_function, n, year)
        return json.dumps(res if res else {"mensaje": "Sin datos"})

    def total_historico_entidad(self, filter_column, filter_value, agg_column="Kg_Neto", agg_function="sum"):
        res = self.db.get_entity_total_historico(filter_column, filter_value, agg_column, agg_function)
        return json.dumps(res if res else {"mensaje": "Sin datos"})
        
    def comparar_periodos(self, year1, year2, group_column, agg_column="Kg_Neto"):
        res = self.db.comparar_periodos(year1, year2, group_column, agg_column)
        return json.dumps(res if res else {"mensaje": "Error"})

    def chat(self, user_message):
        """Procesa mensaje con function calling"""
        self.conversation_history.append({"role": "user", "content": user_message})
        
        messages = [{"role": "system", "content": self.system_prompt}] + self.conversation_history
        
# Modifica la lógica de tool_choice para DeepSeek

        try:
            # CAMBIO IMPORTANTE: Usar "auto" para DeepSeek también.
            # Forzar "required" rompe el chat si el usuario solo saluda o pide explicaciones sin datos.
            tool_choice = "auto" 
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.get_function_definitions(),
                tool_choice=tool_choice, # Antes tenías un if para Deepseek aquí, quítalo
                temperature=0,
                max_tokens=500
            )
            
            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls
            
            if tool_calls:
                self.conversation_history.append(response_message)
                available_functions = self.get_available_functions()
                
                for tool_call in tool_calls:
                    fname = tool_call.function.name
                    fargs = json.loads(tool_call.function.arguments)
                    
                    if fname in available_functions:
                        func_result = available_functions[fname](**fargs)
                        
                        self.conversation_history.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": fname,
                            "content": str(func_result)
                        })
                
                second_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "system", "content": self.system_prompt}] + self.conversation_history,
                    temperature=0
                )
                final_text = second_response.choices[0].message.content
            else:
                final_text = response_message.content
            
            self.conversation_history.append({"role": "assistant", "content": final_text})
            return final_text
            
        except Exception as e:
            return f"❌ Error con {self.provider_name}: {str(e)}"