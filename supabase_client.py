import os
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime
import pandas as pd

load_dotenv()

class SupabaseClient:
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        self.table_name = os.getenv("TABLE_NAME", "importaciones")
        self.client: Client = create_client(url, key)
    
    # ========== CRUD OPERATIONS ==========
    
    def get_all_importaciones(self, limit=100):
        """Obtener todas las importaciones"""
        try:
            response = self.client.table(self.table_name).select("*").limit(limit).execute()
            return response.data
        except Exception as e:
            print(f"Error al obtener importaciones: {e}")
            return []
    
    def get_importacion_by_id(self, id_importacion):
        """Obtener una importación por ID"""
        try:
            response = self.client.table(self.table_name).select("*").eq("ID", id_importacion).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error al obtener importación: {e}")
            return None
    
    def search_importaciones(self, filters):
        """
        Buscar importaciones con múltiples filtros
        filters: dict con los campos a filtrar
        """
        try:
            query = self.client.table(self.table_name).select("*")
            
            for field, value in filters.items():
                if value:
                    query = query.ilike(field, f"%{value}%")
            
            response = query.limit(50).execute()
            return response.data
        except Exception as e:
            print(f"Error en búsqueda: {e}")
            return []
    
    def add_importacion(self, data):
        """Agregar nueva importación"""
        try:
            response = self.client.table(self.table_name).insert(data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error al agregar importación: {e}")
            return None
    
    def update_importacion(self, id_importacion, data):
        """Actualizar importación existente"""
        try:
            response = self.client.table(self.table_name).update(data).eq("ID", id_importacion).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error al actualizar importación: {e}")
            return None
    
    def delete_importacion(self, id_importacion):
        """Eliminar importación"""
        try:
            response = self.client.table(self.table_name).delete().eq("ID", id_importacion).execute()
            return True
        except Exception as e:
            print(f"Error al eliminar importación: {e}")
            return False
    
    # ========== ANALYTICS QUERIES ==========
    
    def get_importaciones_by_pais(self, pais):
        """Obtener importaciones por país de origen"""
        try:
            response = self.client.table(self.table_name).select("*").eq("Pais_origen", pais).execute()
            return response.data
        except Exception as e:
            print(f"Error: {e}")
            return []
    
    def get_importaciones_by_importador(self, importador):
        """Obtener importaciones por importador"""
        try:
            response = self.client.table(self.table_name).select("*").ilike("Importador", f"%{importador}%").execute()
            return response.data
        except Exception as e:
            print(f"Error: {e}")
            return []
    
    def get_importaciones_by_date_range(self, fecha_inicio, fecha_fin):
        """Obtener importaciones en rango de fechas"""
        try:
            response = self.client.table(self.table_name).select("*").gte("Fecha", fecha_inicio).lte("Fecha", fecha_fin).execute()
            return response.data
        except Exception as e:
            print(f"Error: {e}")
            return []
    
    def get_summary_stats(self):
        """Obtener estadísticas resumidas"""
        try:
            all_data = self.get_all_importaciones(limit=10000)
            if not all_data:
                return {}
            
            df = pd.DataFrame(all_data)
            
            stats = {
                "total_importaciones": len(df),
                "total_kg": df['Kg_Neto'].sum(),
                "total_cif": df['CIF_Tot'].sum(),
                "paises_unicos": df['Pais_origen'].nunique(),
                "importadores_unicos": df['Importador'].nunique(),
                "promedio_cif": df['CIF_Tot'].mean()
            }
            return stats
        except Exception as e:
            print(f"Error en estadísticas: {e}")
            return {}
    
    def get_importaciones_by_year(self, year):
        """Obtener todas las importaciones de un año específico"""
        try:
            fecha_inicio = f"{year}-01-01"
            fecha_fin = f"{year}-12-31"
            response = self.client.table(self.table_name).select("*").gte("Fecha", fecha_inicio).lte("Fecha", fecha_fin).execute()
            return response.data
        except Exception as e:
            print(f"Error: {e}")
            return []
    
    def get_unique_values_by_year(self, column, year):
        """Obtener valores únicos de una columna para un año específico"""
        try:
            data = self.get_importaciones_by_year(year)
            if not data:
                return []
            
            df = pd.DataFrame(data)
            if column not in df.columns:
                return []
            
            unique_values = df[column].dropna().unique().tolist()
            return unique_values
        except Exception as e:
            print(f"Error: {e}")
            return []
    
    def get_aggregated_by_year(self, year, group_column, agg_column='Kg_Neto', agg_function='sum'):
        """
        Obtener datos agregados por año
        year: año a consultar
        group_column: columna para agrupar (ej: 'Marca', 'Pais_origen')
        agg_column: columna a agregar (ej: 'Kg_Neto', 'CIF_Tot')
        agg_function: 'sum', 'mean', 'count', 'min', 'max'
        """
        try:
            data = self.get_importaciones_by_year(year)
            if not data:
                return {}
            
            df = pd.DataFrame(data)
            
            if group_column not in df.columns or agg_column not in df.columns:
                return {}
            
            if agg_function == 'sum':
                result = df.groupby(group_column)[agg_column].sum().to_dict()
            elif agg_function == 'mean':
                result = df.groupby(group_column)[agg_column].mean().to_dict()
            elif agg_function == 'count':
                result = df.groupby(group_column)[agg_column].count().to_dict()
            elif agg_function == 'min':
                result = df.groupby(group_column)[agg_column].min().to_dict()
            elif agg_function == 'max':
                result = df.groupby(group_column)[agg_column].max().to_dict()
            else:
                result = {}
            
            return result
        except Exception as e:
            print(f"Error: {e}")
            return {}
    
    def get_time_series_by_entity(self, filter_column, filter_value, group_by_time='year', agg_column='Kg_Neto', agg_function='sum'):
        """
        Análisis temporal de una entidad específica (marca, importador, país)
        filter_column: columna para filtrar (ej: 'Marca', 'Importador', 'Pais_origen')
        filter_value: valor a filtrar (ej: 'MIXHOR PLUS', 'BAYER', 'CHINA')
        group_by_time: 'year' o 'month' (solo year por ahora)
        agg_column: columna a agregar
        agg_function: función de agregación
        """
        try:
            # Obtener todos los datos filtrados por la entidad
            response = self.client.table(self.table_name).select("*").ilike(filter_column, f"%{filter_value}%").execute()
            
            if not response.data:
                return {}
            
            df = pd.DataFrame(response.data)
            
            # Convertir Fecha a datetime
            df['Fecha'] = pd.to_datetime(df['Fecha'])
            df['year'] = df['Fecha'].dt.year
            
            # Agrupar por año
            if agg_function == 'sum':
                result = df.groupby('year')[agg_column].sum().to_dict()
            elif agg_function == 'mean':
                result = df.groupby('year')[agg_column].mean().to_dict()
            elif agg_function == 'count':
                result = df.groupby('year')[agg_column].count().to_dict()
            else:
                result = {}
            
            return result
        except Exception as e:
            print(f"Error: {e}")
            return {}
    
    def get_top_n_global(self, group_column, agg_column='Kg_Neto', agg_function='sum', n=10, year=None):
        """
        Obtener el top N de entidades (marcas, importadores, países) a nivel histórico o por año
        group_column: columna para agrupar (ej: 'Marca', 'Importador', 'Pais_origen')
        agg_column: columna a agregar (ej: 'Kg_Neto', 'CIF_Tot')
        agg_function: 'sum', 'mean', 'count'
        n: cantidad de resultados (top N)
        year: opcional, si se especifica filtra por año
        """
        try:
            if year:
                # Filtrar por año
                data = self.get_importaciones_by_year(year)
            else:
                # Obtener todos los datos históricos
                data = self.get_all_importaciones(limit=100000)
            
            if not data:
                return {}
            
            df = pd.DataFrame(data)
            
            if group_column not in df.columns or agg_column not in df.columns:
                return {}
            
            # Agrupar y agregar
            if agg_function == 'sum':
                result = df.groupby(group_column)[agg_column].sum()
            elif agg_function == 'mean':
                result = df.groupby(group_column)[agg_column].mean()
            elif agg_function == 'count':
                result = df.groupby(group_column)[agg_column].count()
            else:
                return {}
            
            # Ordenar y tomar top N
            top_n = result.nlargest(n).to_dict()
            
            return top_n
        except Exception as e:
            print(f"Error: {e}")
            return {}
    
    def get_entity_total_historico(self, filter_column, filter_value, agg_column='Kg_Neto', agg_function='sum'):
        """
        Obtener el total histórico de una entidad específica (todos los años agregados)
        filter_column: columna para filtrar (ej: 'Marca', 'Importador')
        filter_value: valor a buscar
        agg_column: columna a agregar
        agg_function: función de agregación
        """
        try:
            # Obtener todos los datos de la entidad
            response = self.client.table(self.table_name).select("*").ilike(filter_column, f"%{filter_value}%").execute()
            
            if not response.data:
                return {}
            
            df = pd.DataFrame(response.data)
            
            # Calcular total
            if agg_function == 'sum':
                total = df[agg_column].sum()
            elif agg_function == 'mean':
                total = df[agg_column].mean()
            elif agg_function == 'count':
                total = len(df)
            else:
                total = 0
            
            # Estadísticas adicionales
            result = {
                'total': float(total),
                'registros': len(df),
                'promedio': float(df[agg_column].mean()) if agg_column in df.columns else 0,
                'min': float(df[agg_column].min()) if agg_column in df.columns else 0,
                'max': float(df[agg_column].max()) if agg_column in df.columns else 0,
                'anio_inicio': int(pd.to_datetime(df['Fecha']).dt.year.min()) if 'Fecha' in df.columns else None,
                'anio_fin': int(pd.to_datetime(df['Fecha']).dt.year.max()) if 'Fecha' in df.columns else None
            }
            
            return result
        except Exception as e:
            print(f"Error: {e}")
            return {}
    
    def comparar_periodos(self, year1, year2, group_column, agg_column='Kg_Neto'):
        """
        Comparar dos años y calcular cambios
        year1: año base (anterior)
        year2: año a comparar (posterior)
        group_column: columna para agrupar (ej: 'Marca', 'Importador')
        agg_column: columna a agregar
        """
        try:
            # Obtener datos de ambos años
            data_year1 = self.get_importaciones_by_year(year1)
            data_year2 = self.get_importaciones_by_year(year2)
            
            if not data_year1 or not data_year2:
                return {}
            
            df1 = pd.DataFrame(data_year1)
            df2 = pd.DataFrame(data_year2)
            
            # Agrupar por columna
            grouped1 = df1.groupby(group_column)[agg_column].sum()
            grouped2 = df2.groupby(group_column)[agg_column].sum()
            
            # Crear dataframe de comparación
            comparison = pd.DataFrame({
                f'{year1}': grouped1,
                f'{year2}': grouped2
            }).fillna(0)
            
            # Calcular cambios
            comparison['cambio_absoluto'] = comparison[f'{year2}'] - comparison[f'{year1}']
            comparison['cambio_porcentual'] = ((comparison[f'{year2}'] - comparison[f'{year1}']) / comparison[f'{year1}'].replace(0, 1)) * 100
            
            # Identificar entidades nuevas y salientes
            nuevas = set(grouped2.index) - set(grouped1.index)
            salientes = set(grouped1.index) - set(grouped2.index)
            
            # Ordenar por cambio absoluto
            comparison_sorted = comparison.sort_values('cambio_absoluto', ascending=False)
            
            result = {
                'year1': year1,
                'year2': year2,
                'total_year1': float(grouped1.sum()),
                'total_year2': float(grouped2.sum()),
                'cambio_total': float(grouped2.sum() - grouped1.sum()),
                'cambio_porcentual_total': float(((grouped2.sum() - grouped1.sum()) / grouped1.sum()) * 100) if grouped1.sum() > 0 else 0,
                'top_crecimiento': comparison_sorted.head(10)[['cambio_absoluto', 'cambio_porcentual']].to_dict('index'),
                'top_decrecimiento': comparison_sorted.tail(10)[['cambio_absoluto', 'cambio_porcentual']].to_dict('index'),
                'entidades_nuevas': list(nuevas),
                'entidades_salientes': list(salientes),
                'cantidad_entidades_year1': len(grouped1),
                'cantidad_entidades_year2': len(grouped2)
            }
            
            return result
        except Exception as e:
            print(f"Error: {e}")
            return {}
    
    def get_summary_stats_by_year(self, year):
        """
        Obtiene estadísticas resumidas para un año específico
        
        Args:
            year (int): Año a consultar (ej: 2023, 2024, 2025)
            
        Returns:
            dict: Estadísticas del año
        """
        try:
            # Filtrar por año
            response = (
                self.client.table(self.table_name)
                .select("*")
                .gte("Fecha", f"{year}-01-01")
                .lte("Fecha", f"{year}-12-31")
                .execute()
            )
            
            data = response.data
            
            if not data:
                return {
                    'total_importaciones': 0,
                    'total_kg': 0,
                    'total_cif': 0,
                    'promedio_cif': 0,
                    'importadores_unicos': 0,
                    'paises_unicos': 0
                }
            
            df = pd.DataFrame(data)
            
            stats = {
                'total_importaciones': len(df),
                'total_kg': float(df['Kg_Neto'].sum()) if 'Kg_Neto' in df.columns else 0,
                'total_cif': float(df['CIF_Tot'].sum()) if 'CIF_Tot' in df.columns else 0,
                'promedio_cif': float(df['CIF_Tot'].mean()) if 'CIF_Tot' in df.columns else 0,
                'importadores_unicos': df['Importador'].nunique() if 'Importador' in df.columns else 0,
                'paises_unicos': df['Pais_origen'].nunique() if 'Pais_origen' in df.columns else 0
            }
            
            return stats
            
        except Exception as e:
            print(f"Error obteniendo stats de {year}: {e}")
            return {}

    def get_new_brands_count(self, year):
        """
        Cuenta cuántas marcas nuevas aparecieron en un año
        (marcas que no existían en años anteriores)
        
        Args:
            year (int): Año a analizar
            
        Returns:
            int: Número de marcas nuevas
        """
        try:
            # Obtener marcas del año actual
            current_year_response = (
                self.client.table(self.table_name)
                .select("Marca")
                .gte("Fecha", f"{year}-01-01")
                .lte("Fecha", f"{year}-12-31")
                .execute()
            )
            
            current_brands = set([row['Marca'] for row in current_year_response.data if row.get('Marca')])
            
            # Obtener marcas de años anteriores
            previous_years_response = (
                self.client.table(self.table_name)
                .select("Marca")
                .lt("Fecha", f"{year}-01-01")
                .execute()
            )
            
            previous_brands = set([row['Marca'] for row in previous_years_response.data if row.get('Marca')])
            
            # Marcas nuevas = marcas del año actual que NO estaban en años anteriores
            new_brands = current_brands - previous_brands
            
            return len(new_brands)
            
        except Exception as e:
            print(f"Error contando marcas nuevas de {year}: {e}")
            return 0

    def get_year_comparison(self, year1, year2, metric='Kg_Neto'):
        """
        Compara métricas entre dos años
        
        Args:
            year1 (int): Primer año
            year2 (int): Segundo año
            metric (str): Métrica a comparar ('Kg_Neto' o 'CIF_Tot')
            
        Returns:
            dict: Comparación con cambio absoluto y porcentual
        """
        try:
            stats_year1 = self.get_summary_stats_by_year(year1)
            stats_year2 = self.get_summary_stats_by_year(year2)
            
            key = 'total_kg' if metric == 'Kg_Neto' else 'total_cif'
            
            value1 = stats_year1.get(key, 0)
            value2 = stats_year2.get(key, 0)
            
            change = value2 - value1
            percent_change = (change / value1 * 100) if value1 > 0 else 0
            
            return {
                'year1': year1,
                'year2': year2,
                'value1': value1,
                'value2': value2,
                'change': change,
                'percent_change': percent_change
            }
            
        except Exception as e:
            print(f"Error comparando {year1} vs {year2}: {e}")
            return {}