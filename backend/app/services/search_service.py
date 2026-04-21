from typing import List, Dict, Any, Optional
from supabase import create_client, Client
from app.core.config import settings
from app.logic.ai_helpers import ai_helpers
import json

class SearchService:
    def __init__(self):
        self.supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

    def _normalize_query(self, query: str) -> str:
        if not query:
            return ""
        q = query.lower()
        q = q.replace(" y medio", ".5")
        q = q.replace(" medio", ".5")
        q = q.replace(" litros", "l")
        q = q.replace(" litro", "l")
        q = q.replace(" mililitros", "ml")
        q = q.replace(" ml", "ml")
        return q.strip()

    async def search_product(self, query: str, context: str = "general sale") -> Dict[str, Any]:
        """
        Orquestra la búsqueda de productos:
        1. Ejecuta función RPC multi-estrategia en Supabase
        2. Aplica lógica de selección de ganador (Exactitud, Soledad)
        3. Si es necesario, usa IA para desempate
        """
        
        normalized_query = self._normalize_query(query)
        print(f"[DEBUG - Search] Normalized '{query}' -> '{normalized_query}'")
        
        # 1. RPC Call
        try:
            response = self.supabase.rpc("search_products", {"query_text": normalized_query}).execute()
            candidates = response.data
        except Exception as e:
            print(f"Supabase Search Error: {e}")
            return {"error": str(e), "candidates": []}

        if not candidates:
            return {"ganador": None, "candidates": [], "razon": "No se encontraron coinciencias"}

        # 2. Heurística Rápida
        
        # Sort candidates by score
        candidates.sort(key=lambda x: x['score'], reverse=True)
        top_score = candidates[0]['score']
        
        # Criterio Exactitud (>0.9)
        # BUG FIX: Verificar si hay múltiples candidatos con score alto
        high_confidence_matches = [c for c in candidates if c['score'] > 0.9]
        
        if len(high_confidence_matches) == 1:
            return {"ganador": high_confidence_matches[0], "candidates": candidates, "method": "exact_match"}
        elif len(high_confidence_matches) > 1:
            # AMBIGÜEDAD DETECTADA: Múltiples matches perfectos
            # Defer to AI or return ambiguity
            pass 

        # Criterio Soledad (Gap Analysis)
        if len(candidates) >= 2:
            gap = candidates[0]['score'] - candidates[1]['score']
            if gap > 0.3:
                return {"ganador": candidates[0], "candidates": candidates, "method": "significance_gap"}
        elif len(candidates) == 1:
             return {"ganador": candidates[0], "candidates": candidates, "method": "single_candidate"}

        # 3. AI Disambiguation (DISABLED FOR INITIAL SEARCH TO PREVENT HALLUCINATIONS)
        # User feedback: "no elijas por mi". If heuristics fail, ASK based on candidates.
        unique_candidates = list({c['id']: c for c in candidates}.values())[:5]
        
        return {
            "ganador": None, 
            "candidates": unique_candidates, 
            "method": "ambiguous", 
            "razon": "Múltiples opciones similares encontradas.",
            "action_required": "ask_clarification"
        }
        
        # Si la IA tampoco decide (retorna null), retornamos estado de Ambigüedad
        return {
            "ganador": None, 
            "candidates": top_candidates, 
            "method": "ambiguous", 
            "razon": "Múltiples opciones similares encontradas.",
            "action_required": "ask_clarification"
        }

search_service = SearchService()
