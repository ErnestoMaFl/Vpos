from typing import Dict, Any, List
from app.services.groq_service import groq_service

class AIHelpers:
    """
    Funciones helper de IA para limpieza, extracción y clasificación de comandos de voz.
    """
    
    @staticmethod
    async def clean_and_extract(text: str, context: str = "general") -> Dict[str, Any]:
        """
        Limpia muletillas y extrae entidades clave.
        Input: "ehhh son 5 coca colas de 600"
        Output: { "cantidad": 5, "producto": "coca cola", "medida": "600ml" }
        """
        print(f"[DEBUG - AIHelpers] Extracting from '{text}' with context '{context}'")
        system_msg = """Eres un experto en extracción de datos para un POS.
        Tu objetivo es completar información faltante basándote en el contexto.
        
        Reglas:
        - Si el contexto es 'campos_para_vpos_ventas' o 'campos_para_vpos_billing' y recibes un número solo, asúmelo como 'cantidad'.
        - Si detectas múltiples productos y cantidades (ej: "dos cocas y tres pepsis"), retorna una lista "items": [ { "producto": "...", "cantidad": ... }, ... ].
        - Si es un solo producto, puedes retornar el JSON plano.
        """
        
        prompt = f"""Texto: "{text}"
        Contexto: {context}
        
        Ejemplos:
        Context: campos_para_vpos_ventas | Text: "5" -> {{ "cantidad": 5 }}
        Context: campos_para_vpos_billing | Text: "2 cocas y 1 gansito" -> {{ "items": [ {{ "producto": "coca", "cantidad": 2 }}, {{ "producto": "gansito", "cantidad": 1 }} ] }}
        Context: campos_para_vpos_ventas | Text: "coca cola" -> {{ "producto": "coca cola" }}
        Context: general | Text: "quiero vender dos" -> {{ "cantidad": 2, "accion": "vender" }}
        
        Respuesta JSON:
        """
        
        response = await groq_service.generate_structured_response(prompt, {}, system_msg)
        print(f"[DEBUG - AIHelpers] Extraction Result: {response}")
        return response

    @staticmethod
    async def pre_filter_query(query: str, table_context: str) -> Dict[str, Any]:
        """
        Ajusta una búsqueda a campos específicos de la BD.
        Input: "proveedor que viene mañana"
        Output: { "campo": "dias_surtir", "valor_semantico": "mañana" }
        """
        system_msg = f"Eres un asistente de base de datos SQL. Contexto de tabla: {table_context}."
        prompt = f"Interpreta la búsqueda: '{query}' y asignala a probables campos de la tabla."
        
        return await groq_service.generate_structured_response(prompt, {}, system_msg)

    @staticmethod
    async def determine_intent(text: str, available_tables: List[str]) -> Dict[str, Any]:
        """
        Genera la intención SQL/Acción del usuario.
        Input: "quiero saber cuantas cocas vendi ayer"
        Output: { "tabla": "ventas", "tipo": "consulta", "filtros": ... }
        """
        print(f"[DEBUG - AIHelpers] Determining intent for: '{text}'")
        system_msg = """Eres el cerebro de un sistema POS. Tu trabajo es traducir lenguaje natural a comandos estructurados.
        IMPORTANTE:
        - "Vender", "Cobrar", "Nueva venta" -> Acción: "crear", Tabla: "vpos_ventas".
        - REGLA DE ORO: Si el usuario menciona cantidades o artículos ("un", "una", "dos", "5", etc.) junto a un producto (ej: "una coca", "3 jabones"), interpreta SIEMPRE como VENTA ("crear").
        - "Buscar", "Precio de", "Hay", "Cuánto cuesta", "A cuánto" -> Acción: "consultar", Tabla: "vpos_productos".
        - "Inventario", "Stock" -> Acción: "consultar", Tabla: "vpos_productos".
        """
        
        prompt = f"""Texto del usuario: "{text}"
        Tablas disponibles: {', '.join(available_tables)}
        
        Ejemplos:
        User: "quiero vender una coca" -> {{ "tipo": "crear", "tabla": "vpos_ventas", "filtros": {{ "producto": "coca" }} }}
        User: "una coca y dos barritas" -> {{ "tipo": "crear", "tabla": "vpos_ventas", "filtros": {{ "items": [ {{ "producto": "coca", "cantidad": 1 }}, {{ "producto": "barritas", "cantidad": 2 }} ] }} }}
        User: "precio del jabon" -> {{ "tipo": "consultar", "tabla": "vpos_productos", "filtros": {{ "producto": "jabon" }} }}
        User: "cancelar" -> {{ "tipo": "desconocido", "tabla": null, "filtros": {{}} }}
        
        Analiza el texto actual y responde en JSON.
        """
        
        schema = {
            "tipo": "string (enum: crear, consultar, actualizar, borrar, desconocido)",
            "tabla": "string (nombre exacto de la tabla o null)",
            "filtros": "object (key-value pairs)",
            "razonamiento": "string (breve explicacion)"
        }
        
        response = await groq_service.generate_structured_response(prompt, schema, system_msg)
        print(f"[DEBUG - AIHelpers] Intent Raw Response: {response}")
        return response

    @staticmethod
    async def resolve_ambiguity(candidates: List[Dict], query: str, field_context: str) -> Dict[str, Any]:
        """
        Selecciona el mejor candidato de una lista de búsqueda difusa usando contexto.
        """
        system_msg = "Eres un juez experto en desambiguar búsquedas de productos/entidades."
        prompt = f"""Query Original: "{query}"
        Contexto: {field_context}
        
        Candidatos encontrados:
        {json.dumps(candidates, indent=2)}
        
        Selecciona el GANADOR. 
        Criterios: Exactitud > Contexto > Fonética.
        
        IMPORTANTE: 
        - Si la query es ambigua (ej: "coca" y hay "Coca 600" y "Coca 2.5L"), y el contexto no aclara cuál quiere, DEBES retornar null.
        - NO adivines. NO uses "mayor tamaño" como criterio de desempate a menos que el contexto lo pida.
        - Si ninguno es razonable, retorna null en 'ganador'.
        """
        
        return await groq_service.generate_structured_response(prompt, {"ganador_id": "int | null", "razon": "string"}, system_msg)

ai_helpers = AIHelpers()
import json
