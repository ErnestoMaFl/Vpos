from typing import Optional, Dict, Any, List
from app.logic.state_manager import state_manager, VPosState
from app.logic.ai_helpers import ai_helpers
import uuid
import re

# Mock config for commands
COMMANDS_CONFIG = {
    "interrupcion": ["cancelar", "olvídalo", "parar", "detener", "salir"],
    "confirmacion": ["sí", "si", "correcto", "confirmar", "dale", "ok", "yes", "va"],
    "negacion": ["no", "incorrecto", "corregir", "espera", "cancela"],
    "cobrar": ["cobrar", "finalizar", "cerrar cuenta", "pagar"],
}

AVAILABLE_TABLES = ["vpos_productos", "vpos_ventas", "vpos_clientes", "vpos_proveedores"]

# Config for required fields per action/table
REQUIRED_FIELDS = {
    "vpos_ventas": ["producto", "cantidad"],
    "vpos_billing": ["producto"], # Cart needs at least a product to ADD
    "vpos_productos": ["nombre"], # Example for creation
    "vpos_clientes": ["nombre"],
}

class CommandAnalyzer:
    def _check_completion(self, state: VPosState) -> Dict[str, Any]:
        """
        Checks if the state has all required data.
        Returns a dict with 'is_complete' (bool) and 'missing_field' (str) or 'message' (str).
        """
        # Determine table from context or collected data (simplistic mapping)
        # In a real app, state should have 'target_table' explicitly.
        # For now, we rely on the command_origin or context being descriptive,
        # but better to store 'table' in VPosState. Let's infer from 'valor_retorno_esperado'.
        
        table = state.valor_retorno_esperado.replace("campos_para_", "")
        required = REQUIRED_FIELDS.get(table, [])
        
        if table == "vpos_billing":
             items = state.datos_recolectados.get("items") or state.datos_recolectados.get("productos") or []
             if items:
                 desc = ", ".join([f"{i.get('cantidad', 1)}x {i.get('producto')}" for i in items])
                 return {"is_complete": True, "message": f"Agregar {desc} al carrito?", "missing": []}
                 
             # If no items list, check for single product
             if state.datos_recolectados.get("producto"):
                  return {"is_complete": True, "message": f"Agregar {state.datos_recolectados.get('cantidad', 1)} {state.datos_recolectados.get('producto')} al carrito?", "missing": []}
        
        missing = []
        for field in required:
            if field not in state.datos_recolectados:
                missing.append(field)
        
        if not missing:
            return {"is_complete": True, "message": f"Listo para registrar en {table}. ¿Confirmar?", "missing": []}
        
        # Friendly Prompts
        if table == "vpos_billing":
             if missing[0] == "producto" and "items" not in state.datos_recolectados and "productos" not in state.datos_recolectados:
                 return {"is_complete": False, "missing": ["producto"], "message": "Carrito iniciado. ¿Qué producto deseas agregar?"}
             # If we have items but flag says incomplete? Should not happen if logic above catches it.
             
        return {"is_complete": False, "missing": missing[0], "message": f"¿Cuál es el valor para {missing[0]}?"}

    async def _execute_action(self, state: VPosState) -> Dict[str, Any]:
        """
        Executes the action defined in the state.
        Example: Insert into vpos_ventas
        """
        print(f"[DEBUG - ExecuteAction]: Starting execution for state {state.id} (Table: {state.valor_retorno_esperado})")
        try:
            table = state.valor_retorno_esperado.replace("campos_para_", "")
            data = state.datos_recolectados
            
            print(f"[DEBUG - ExecuteAction]: Data collected so far: {data}")
            
            if table == "vpos_billing":
                # ADD TO CART LOGIC
                # ADD TO CART LOGIC
                # Normalize input to list of items
                items_to_process = []
                
                # Case 1: List Validation from LLM (items=[...])
                if data.get("items"):
                    items_to_process = data.get("items")
                elif data.get("productos"):
                     items_to_process = data.get("productos")
                
                # Case 2: Standard Single Item
                elif data.get("producto"):
                    items_to_process = [{"producto": data.get("producto"), "cantidad": data.get("cantidad", 1)}]
                
                # Case 3: Flat Keys (producto1, cantidad1, producto2...)
                # Sometimes LLM returns this format
                elif any(k.startswith("producto") and k[8:].isdigit() for k in data.keys()):
                    i = 1
                    while f"producto{i}" in data:
                        p = data[f"producto{i}"]
                        c = data.get(f"cantidad{i}", 1)
                        if p:
                            items_to_process.append({"producto": p, "cantidad": c})
                        i += 1
                
                # Case 4: Arbitrary Keys (e.g. {galletas: 3, pepsi: 5})
                # If we are here, it means we have data but no standard structure.
                # We assume keys are product names if they are not metadata.
                else:
                    ignored_keys = {"cart", "total", "items", "productos", "producto", "cantidad", "_ambiguity_candidates"}
                    for k, v in data.items():
                        if k not in ignored_keys and isinstance(v, (int, float, str)):
                             # Simple heuristic: if value is number or numeric string, treat as quantity
                             qty = 1
                             try:
                                 qty = float(v)
                             except:
                                 pass
                             items_to_process.append({"producto": k, "cantidad": qty})
                
                if not items_to_process:
                     print("[DEBUG] No items found to process in ExecuteAction")
                     return {"action": "INFO", "message": "No detecté productos para agregar."}
                
                added_msgs = []
                current_cart = state.datos_recolectados.get("cart", [])
                
                from app.services.search_service import search_service
                
                for item in items_to_process:
                    prod_name = item.get("producto")
                    qty = item.get("cantidad", 1)
                    
                    if not prod_name:
                        print(f"[DEBUG] Skipping item with no product name: {item}")
                        continue
                        
                    # 1. Search Product
                    print(f"[DEBUG] Searching for '{prod_name}'...")
                    search_res = await search_service.search_product(prod_name, context=state.valor_retorno_esperado)
                    winner = search_res.get("ganador")

                    if not winner:
                        if search_res.get("method") == "ambiguous":
                            # For ambiguity, we currently stop and ask. 
                            # Future Improvement: Add successful items and only ambiguous for the specific one.
                            # For now, return immediate ambiguity for simplicity.
                            # Save ambiguity context to state so we can resolve it next turn
                            state_manager.update_active_state_data(state.user_id, {
                                "_ambiguity_candidates": search_res.get("candidates"),
                                "producto": prod_name # Store which product caused ambiguity
                            })
                            
                            candidates_str = ", ".join([c["nombre"] for c in search_res.get("candidates", [])[:3]])
                            return {
                                "action": "AMBIGUITY_DETECTED", 
                                "message": f"Encontré varias opciones para '{prod_name}': {candidates_str}. ¿Cuál necesitas?",
                                "candidates": search_res.get("candidates")
                            }
                        
                        # Partial Success Logic:
                        # Log error but CONTINUE to allow other items to be added.
                        print(f"[DEBUG] Failed to find '{prod_name}'")
                        added_msgs.append(f"❌ '{prod_name}' no encontrado")
                        continue

                    # Construct Line Item
                    line_item = {
                        "producto_id": winner.get("id"),
                        "nombre_producto": winner.get("nombre"),
                        "cantidad": int(qty),
                        "precio_unitario": float(winner.get("precio_venta", 0)),
                        "subtotal": int(qty) * float(winner.get("precio_venta", 0))
                    }
                    
                    current_cart.append(line_item)
                    added_msgs.append(f"{line_item['cantidad']}x {line_item['nombre_producto']}")
                
                # Only if using local state update; if returning RESULT, frontend sees it.
                # Update State with new Cart Item
                # Clear "current item" fields to allow next entry, but KEEP cart
                new_data = {"cart": current_cart} 
                # Note: We overwrite datos_recolectados to clear 'producto'/'cantidad'/'items'/'productos' for the next loop
                state_manager.update_active_state_data(state.user_id, new_data, overwrite=True)
                
                total = sum(item["subtotal"] for item in current_cart)
                msg_str = ", ".join(added_msgs)
                
                return {
                    "action": "CART_UPDATE",
                    "message": f"Agregado: {msg_str}. Total al momento: ${total}",
                    "data": {"cart": current_cart, "total": total}
                }

            if table == "vpos_ventas":
                # Special logic for sales: Lookup product validation and price
                product_name = data.get("producto")
                print(f"[DEBUG - ExecuteAction]: Validating product '{product_name}' for sale")
                
                # Import here to avoid circular dependency
                from app.services.search_service import search_service
                
                search_res = await search_service.search_product(product_name)
                winner = search_res.get("ganador")
                
                if not winner:
                    print(f"[DEBUG - ExecuteAction]: Validation failed. Winner is None. Res: {search_res.get('method')}")
                    if search_res.get("method") == "ambiguous":
                        state_manager.update_active_state_data(state.user_id, {
                            "_ambiguity_candidates": search_res.get("candidates"),
                            "producto": product_name
                        })
                        
                        candidates_str = ", ".join([c["nombre"] for c in search_res.get("candidates", [])[:3]])
                        return {
                            "action": "AMBIGUITY_DETECTED", 
                            "message": f"Encontré varias opciones: {candidates_str}. ¿Cuál necesitas?",
                            "candidates": search_res.get("candidates")
                        }
                    return {"action": "ERROR", "message": f"No se pudo encontrar el producto '{product_name}' para concretar la venta."}
                
                # Prepare record
                print(f"[DEBUG - ExecuteAction]: Winner found: {winner.get('nombre')} (ID: {winner.get('id')})")
                sale_data = {
                    "producto_id": winner.get("id"), 
                    "nombre_producto": winner.get("nombre", product_name), 
                    "cantidad": int(data.get("cantidad", 1)),
                    "precio_unitario": float(winner.get("precio_venta", 0)),
                    "total": int(data.get("cantidad", 1)) * float(winner.get("precio_venta", 0)),
                    "user_id": state.user_id,
                    "estado_origen_id": state.id
                }
                
                print(f"[DEBUG - ExecuteAction]: Inserting sale record: {sale_data}")
                
                # Insert into DB
                db_res = state_manager.supabase.table("vpos_ventas").insert(sale_data).execute()
                print(f"[DEBUG - ExecuteAction]: DB Response code: {db_res}")
                
                return {
                    "action": "COMPLETED", 
                    "message": f"Venta registrada: {sale_data['cantidad']}x {sale_data['nombre_producto']} por ${sale_data['total']}"
                }
                
            # Fallback for other tables (generic insert)
            print(f"[DEBUG - ExecuteAction]: Generic insert into {table}")
            state_manager.supabase.table(table).insert(data).execute()
            return {"action": "COMPLETED", "message": f"Registro creado en {table}."}
            
        except Exception as e:
            print(f"[DEBUG - ExecuteAction ERROR]: {str(e)}")
            return {"action": "ERROR", "message": f"Error al ejecutar la acción: {str(e)}"}

    async def analyze(self, user_id: str, text: str, state_id: Optional[str] = None) -> Dict[str, Any]:
        text_lower = text.lower().strip()
        print(f"[DEBUG - Analyze] Processing text: '{text}' for user: {user_id}, state_id: {state_id}")
        
        # 1. Global Interruptions
        if any(trigger in text_lower for trigger in COMMANDS_CONFIG["interrupcion"]):
            active = state_manager.get_active_state(user_id)
            if active:
                state_manager.pop_state(user_id)
                return {"action": "CANCEL_STATE", "message": "Operación cancelada."}
            return {"action": "INFO", "message": "No hay operación activa para cancelar."}

        # 2. Intent Detection (PRE-ANALYSIS)
        # We run this early to decide if the user is shifting context
        intent_res = await ai_helpers.determine_intent(text, AVAILABLE_TABLES)
        action_type = (intent_res.get("tipo") or intent_res.get("action") or "unknown").lower()
        target_table = intent_res.get("tabla") or intent_res.get("table")
        
        # 3. Active State Management
        active_state = None
        if state_id:
             active_state = state_manager.get_state_by_id(state_id)
        
        if not active_state:
             active_state = state_manager.get_active_state(user_id)

        if active_state:
            print(f"[DEBUG - Analyze] Evaluating active state: {active_state.id}. Context: {active_state.valor_retorno_esperado}")
            
            # Determine if we should consume input for THIS state or let it go to NEW intent
            belongs = False
            
            # Check for direct confirmation (always belongs)
            # Tokenize for meaningful check
            import re
            tokens = set(re.findall(r'\b\w+\b', text_lower))
            
            is_confirmation = any(trigger in tokens for trigger in COMMANDS_CONFIG["confirmacion"])
            is_negation = any(trigger in tokens for trigger in COMMANDS_CONFIG["negacion"])
            # Relaxed check for checkout (handles "cerrar cuenta")
            is_checkout = any(trigger in text_lower for trigger in COMMANDS_CONFIG["cobrar"])
            
            # Explicit Hardcoded Safeguard for main commands
            if text_lower.startswith(("cobrar", "finalizar", "pagar")):
                is_checkout = True
                
            print(f"[DEBUG] is_checkout: {is_checkout} | Text: {text_lower}")
            
            if is_confirmation or is_negation or is_checkout:
                belongs = True
            
            # Context Shift Detection Logic
            if not belongs:
                # If we are in "Selection Mode" (resolving ambiguity)
                if active_state.datos_recolectados.get("_ambiguity_candidates"):
                    # Check if input is likely a new command
                    is_new_command = False
                    
                    # If detected valid intent for different table or query inside sale
                    if action_type in ["consulta", "consultar", "crear", "borrar", "actualizar"] and target_table:
                        current_table = (active_state.valor_retorno_esperado or "").replace("campos_para_", "")
                        
                        # ALLOW exception: If we are resolving ambiguity (checking products) and the new intent is about products, 
                        # it might just be the user describing the product.
                        is_product_resolution = "productos" in target_table and active_state.datos_recolectados.get("_ambiguity_candidates")
                        
                        if target_table != current_table and not is_product_resolution:
                            is_new_command = True
                        elif action_type in ["consulta", "consultar"] and "ventas" in current_table:
                            # Standard query vs sale check, but if we are in ambiguity, we prefer selection
                            if not active_state.datos_recolectados.get("_ambiguity_candidates"):
                                is_new_command = True
                        
                        # NEW RULE: If intent is explicitly CREATING/SELLING, it overrides an ambiguous product selection
                        elif action_type == "crear" and "ventas" in target_table:
                            is_new_command = True
                    
                    if is_new_command:
                        belongs = False
                        print(f"[DEBUG] Ambiguity Break: Detected new command '{action_type}' for '{target_table}'")
                    else:
                        # Otherwise, assume it's a selection answer
                        belongs = True
                else:
                    expected_table = (active_state.valor_retorno_esperado or "").replace("campos_para_", "")
                    
                    # Intent Table Check
                    if target_table == expected_table:
                        belongs = True
                        
                    # EXCEPTION: If current state is BILLING/CART, and intent is "crear" on "ventas", 
                    # IT BELONGS to the cart... UNLESS it's a reset.
                    if "vpos_billing" in expected_table and target_table == "vpos_ventas" and action_type == "crear":
                        # Check if it's a "Venta" (Reset) or "Agregar [Producto]" (Append)
                        filtros = intent_res.get("filtros") or {}
                        
                        # Fix for Flat Dictionary Multi-Items (e.g. {galletas: 3, pepsi: 5})
                        # If filters is NOT empty, we assume it has items, UNLESS explicitly "Nueva Venta" text check below.
                        has_items = bool(filtros) 
                        
                        if has_items:
                            belongs = True
                        else:
                            belongs = False # Force NEW start
                        
                    # EXCEPTION: If the user explicitly says "Venta" or "Nueva Venta", they likely want a FRESH start,
                    # even if we are already in a sales state (stale or not).
                    if action_type == "crear" and target_table == "vpos_ventas" and not belongs:
                        # Already handled above if billing, but kept for other states
                        pass

                    # Minor exception: if intent is just a query but we are in a creation flow
                    if action_type in ["consulta", "consultar"] and ("vpos_ventas" in expected_table or "vpos_billing" in expected_table):
                         # Soft Correction: If user says "5 gansitos", LLM might think it's a query
                         # But if we are in billing, we should assume ADD unless they ask for price.
                         explicit_query_triggers = ["precio", "costo", "cuanto", "cuánto", "vale", "tienes", "hay", "stock"]
                         is_explicit_query = any(t in text_lower for t in explicit_query_triggers)
                         
                         if not is_explicit_query and "vpos_billing" in expected_table:
                             # Assume it's actually an ADD command
                             belongs = True
                             action_type = "crear" # Coerce action
                             target_table = "vpos_ventas" # Coerce table
                         else:
                             # If intent is UNKNOWN/WEAK but we have active state, assume it belongs (user dictating items)
                             if action_type in ["desconocido", "informar_campo"]:
                                 belongs = True
                                 print(f"[DEBUG - Analyze] Weak intent '{action_type}' -> Assuming belongs to context '{active_state.valor_retorno_esperado}'")
                             else:
                                 belongs = False # Context SHIFT detected (Real Query)

                    # FINAL CHECK: If belongs is still False, but intent is Unknown/Weak, assume it belongs to context.
                    if not belongs and action_type in ["desconocido", "informar_campo"]:
                         belongs = True
                         print(f"[DEBUG - Analyze] Weak intent '{action_type}' -> Assuming belongs to context '{active_state.valor_retorno_esperado}'")

            if belongs:
                # -------------------------------------------------------------------
                # PROCESS INSIDE STATE
                # -------------------------------------------------------------------

                # Check for direct confirmation to execute
                if is_confirmation:
                     # Execute Action
                     result = await self._execute_action(active_state)
                     
                     if result.get("action") == "COMPLETED":
                         state_manager.pop_state(user_id)
                     
                     if result.get("action") == "AMBIGUITY_DETECTED":
                         state_manager.update_active_state_data(user_id, {"_ambiguity_candidates": result.get("candidates")})
                         
                     return result

                # CHECKOUT TRIGGER
                if is_checkout and "billing" in (active_state.valor_retorno_esperado or ""):
                    # Finalize Sale
                    cart = active_state.datos_recolectados.get("cart", [])
                    if not cart:
                        return {"action": "INFO", "message": "El carrito está vacío. Agrega productos antes de cobrar."}
                    
                    total = sum(item["subtotal"] for item in cart)

                    # Extract Payment Amount
                    match = re.search(r'(?:con|de|pagar con)\s*\$?(\d+(?:\.\d+)?)', text, re.IGNORECASE)
                    pago = float(match.group(1)) if match else 0
                    
                    cambio = 0
                    if pago > 0:
                        if pago < total:
                             return {"action": "INFO", "message": f"El monto recibido (${pago}) es menor al total (${total}). Faltan ${total - pago}."}
                        cambio = pago - total
                    
                    # Insert Header
                    header_data = {
                        "user_id": user_id,
                        "total": total,
                        "estado_origen_id": active_state.id
                    }
                    res_header = state_manager.supabase.table("vpos_ventas").insert(header_data).execute()
                    if not res_header.data:
                         return {"action": "ERROR", "message": "Error al crear la venta."}
                    
                    sale_id = res_header.data[0]['id']
                    
                    # Insert Details
                    details = []
                    for item in cart:
                        details.append({
                            "venta_id": sale_id,
                            "producto_id": item["producto_id"],
                            "nombre_producto": item["nombre_producto"],
                            "cantidad": item["cantidad"],
                            "precio_unitario": item["precio_unitario"],
                            "subtotal": item["subtotal"]
                        })
                    
                    state_manager.supabase.table("vpos_ventas_detalle").insert(details).execute()
                    state_manager.pop_state(user_id)
                    
                    msg = f"Venta cerrada por ${total}."
                    if pago > 0:
                         msg += f" Recibido: ${pago}. CAMBIO: ${cambio}."
                    else:
                         msg += " Cambio: $0 (No especificado)."

                    return {"action": "COMPLETED", "message": msg}
                
                # Check for selection resolution if in that mode
                if active_state.datos_recolectados.get("_ambiguity_candidates"):
                    selection_res = {}
                    try:
                        print(f"[DEBUG] Resolving ambiguity with input: {text}")
                        candidates = active_state.datos_recolectados["_ambiguity_candidates"]
                        
                        # HEURISTIC: Deterministic Local Match
                        # If the user provides specific keywords that match exactly ONE candidate, pick it.
                        text_micro = text.lower().strip()
                        raw_words = text_micro.split()
                        
                        # IGNORE STOP WORDS (de, del, con...) to prevent "coca de 600" failing on "de"
                        STOP_WORDS = {"de", "del", "la", "el", "los", "las", "con", "y", "en", "para", "mi", "un", "una", "unos", "unas"}
                        input_words = [w for w in raw_words if w not in STOP_WORDS]
                        
                        if not input_words:
                            # Fallback if filtered everything (unlikely, e.g. user said "la de")
                            input_words = raw_words 
                        
                        probable_matches = []
                        for c in candidates:
                            c_name = c["nombre"].lower()
                            c_tokens = c_name.split()
                            
                            match_count = 0
                            for u_word in input_words:
                                # Robust partial match: 'galleta' matches 'galletas'
                                if any(u_word in t_word for t_word in c_tokens):
                                    match_count += 1
                            
                            if match_count >= len(input_words):
                                 probable_matches.append(c)
                                 print(f"[DEBUG] Candidate '{c['nombre']}' matches all tokens. (Score: {match_count}/{len(input_words)})")
                        
                        selection_res = {}
                        if len(probable_matches) == 1:
                            print(f"[DEBUG] Deterministic UNIQUE Match Found: {probable_matches[0]['nombre']}")
                            selection_res = {"ganador_id": probable_matches[0]["id"]}
                        elif len(probable_matches) > 1:
                             # TIE-BREAKER: If multiple matches, check word count closeness?
                             # "Galleta Oreo" matches "Galletas Oreo" (2 words) and "Galletas Oreo Grande" (3 words).
                             # Prefer the one with closest token count.
                             probable_matches.sort(key=lambda x: len(x["nombre"].split()))
                             best = probable_matches[0]
                             print(f"[DEBUG] Deterministic Tie-Breaker (Shortest Name): {best['nombre']}")
                             selection_res = {"ganador_id": best["id"]}
                    except Exception as e:
                        print(f"[ERROR - Ambiguity Resolution] Crash: {str(e)}")
                        # Return ambiguity to avoid 500, user can try again or we fallback
                        return {"action": "INFO", "message": "Ocurrió un error al procesar tu selección. Intenta de nuevo."}
                    
                    if not selection_res.get("ganador_id"):
                         # Fallback to AI only if deterministic failed
                         selection_res = await ai_helpers.resolve_ambiguity(candidates, text, field_context="User selection")
                    
                    if selection_res.get("ganador_id"):
                         winner = next((c for c in candidates if c['id'] == selection_res["ganador_id"]), None)
                         if winner:
                             update_data = {"producto": winner["nombre"], "_ambiguity_candidates": None}
                             
                             # CRITICAL FIX: If we have an "items" list (from a bulk add), we must update the specific item
                             # that caused the ambiguity. We stored the ambiguous name in 'producto' when creating the state.
                             ambiguous_term = active_state.datos_recolectados.get("producto")
                             current_items = active_state.datos_recolectados.get("items", [])
                             
                             if current_items and ambiguous_term:
                                 updated_items = []
                                 for it in current_items:
                                     # normalize check or direct match? Direct match should work as it came from the same source
                                     if it.get("producto") == ambiguous_term:
                                         it["producto"] = winner["nombre"]
                                     updated_items.append(it)
                                 update_data["items"] = updated_items
                             
                             state_manager.update_active_state_data(user_id, update_data)
                             
                             if "productos" in (active_state.valor_retorno_esperado or ""):
                                  msg = f"El precio de {winner['nombre']} es ${winner['precio_venta']}. Stock: {winner['stock_actual']}."
                                  state_manager.pop_state(user_id)
                                  return {"action": "SEARCH_RESULT", "message": msg, "data": winner}

                             # AUTO-EXECUTE if Cart context (Similar to Analyze flow)
                             updated_state = state_manager.get_active_state(user_id)
                             check = self._check_completion(updated_state)
                             is_cart = "vpos_billing" in (updated_state.valor_retorno_esperado or "")
                             
                             if check["is_complete"] and is_cart:
                                 print("[DEBUG - Ambiguity] Auto-Executing after Resolution...")
                                 result = await self._execute_action(updated_state)
                                 if result.get("action") == "COMPLETED":
                                      state_manager.pop_state(user_id)
                                 return result

                             return {
                                 "action": "STATE_UPDATE", "state_id": active_state.id,
                                 "message": f"Seleccionado: {winner['nombre']}. ¿Confirmar?", "data": update_data
                             }
                    return {"action": "INFO", "message": "No entendí cuál opción prefieres. Por favor selecciona una de las opciones."}


                # Try to extract information relevant to the current state
                # REVERT OPTIMIZATION: Always run clean_and_extract because it's more robust for quantities
                # "intent_res" often misses specific fields. 
                extraction = await ai_helpers.clean_and_extract(text, context=active_state.valor_retorno_esperado)
                new_data = {}
                
                # Merge if valid
                if extraction:
                     new_data = extraction
                # Fallback to intent_res if extraction failed but intent had something
                elif intent_res.get("filtros"):
                     new_data = intent_res.get("filtros")
                
                if new_data:
                    state_manager.update_active_state_data(user_id, new_data)
                    active_state = state_manager.get_active_state(user_id)
                    check = self._check_completion(active_state)
                    
                    # AUTO-EXECUTE if Cart is complete (Don't ask to confirm)
                    # "vpos_billing" context with valid items -> Add immediately
                    is_cart = "vpos_billing" in (active_state.valor_retorno_esperado or "")
                    
                    if check["is_complete"] and is_cart:
                         print("[DEBUG - Analyze] Auto-Executing content for Billing/Cart...")
                         result = await self._execute_action(active_state)
                         
                         if result.get("action") == "COMPLETED":
                             state_manager.pop_state(user_id)
                         
                         if result.get("action") == "AMBIGUITY_DETECTED":
                             state_manager.update_active_state_data(user_id, {"_ambiguity_candidates": result.get("candidates")})
                         
                         return result

                    return {
                        "action": "STATE_UPDATE", 
                        "state_id": active_state.id, 
                        "data": active_state.datos_recolectados, 
                        "message": check["message"],
                        "missing_fields": check.get("missing", []),
                        "context": active_state.valor_retorno_esperado
                    }
            else:
                 print(f"[DEBUG - Analyze] Context shift detected! Intent type '{action_type}' for '{target_table}' does not match current state.")

        # 4. New Intent / Transition
        # (Reuse intent_res from start)
        print(f"[DEBUG - Analyze] Handling as NEW command...")
        
        if action_type in ["consulta", "consultar", "crear", "actualizar"]:
            # Special handling for immediate search
            if action_type in ["consulta", "consultar"] and "producto" in intent_res.get("filtros", {}):
                # Import here to avoid circular dependency if possible, or assume global import
                from app.services.search_service import search_service
                product_name = intent_res["filtros"]["producto"]
                print(f"[DEBUG - Analyze] Executing immediate search for: {product_name}")
                search_result = await search_service.search_product(product_name)
                
                winner = search_result.get("ganador")
                if winner:
                    msg = f"Encontré {winner.get('nombre', 'Producto')} a {winner.get('precio_venta', 0)} pesos."
                    return {
                        "action": "SEARCH_RESULT",
                        "intent": action_type,
                        "data": search_result,
                        "message": msg
                    }
                elif search_result.get("method") == "ambiguous":
                    # If ambiguous, we create a temporary state to resolve it
                    # IMPORTANT: Preserve ALL filters (quantity, etc.) from original intent, 
                    # not just the product name.
                    initial_data = intent_res.get("filtros", {})
                    initial_data.update({
                        "producto": product_name,
                        "_ambiguity_candidates": search_result.get("candidates")
                    })
                    
                    new_state = VPosState(
                        user_id=user_id,
                        command_origin=text,
                        valor_retorno_esperado="campos_para_vpos_productos", # Context for search
                        datos_recolectados=initial_data,
                        estado_completado=False
                    )
                    state_manager.push_state(user_id, new_state)
                    
                    candidates_str = ", ".join([c["nombre"] for c in search_result.get("candidates", [])[:3]])
                    return {
                        "action": "AMBIGUITY_DETECTED",
                        "state_id": new_state.id,
                        "message": f"Encontré varias opciones para '{product_name}': {candidates_str}. ¿Cuál buscas?",
                        "candidates": search_result.get("candidates")
                    }
                else:
                    return {
                        "action": "SEARCH_RESULT",
                        "intent": action_type,
                        "data": search_result,
                        "message": "No encontré ese producto."
                    }

            # Redirect 'vpos_ventas' 'crear' to 'vpos_billing' (Cart System)
            final_target_table = target_table
            if target_table == "vpos_ventas" and action_type == "crear":
                final_target_table = "vpos_billing"

            new_state = VPosState(
                user_id=user_id,
                command_origin=text,
                valor_retorno_esperado=f"campos_para_{final_target_table}", 
                datos_recolectados=intent_res.get("filtros", {})
            )
            state_manager.push_state(user_id, new_state)
            
            check = self._check_completion(new_state)
            
            # AUTO-EXECUTE FOR NEW COMMANDS
            # Check configuration parameter (Default: False for Fast Flow)
            requires_conf = new_state.parameters_configurables.get("requires_confirmation", False)
            
            is_billing = final_target_table == "vpos_billing"
            
            if check["is_complete"] and is_billing and not requires_conf:
                 print(f"[DEBUG - Analyze] Auto-Exec New Command: {action_type} on {final_target_table}")
                 result = await self._execute_action(new_state)
                 
                 # Helper to persist ambiguity candidates if returned
                 if result.get("action") == "AMBIGUITY_DETECTED":
                     state_manager.update_active_state_data(user_id, {"_ambiguity_candidates": result.get("candidates")})
                 
                 # If completed, pop state immediately
                 if result.get("action") == "COMPLETED":
                     state_manager.pop_state(user_id)
                 
                 # INJECT STATE ID (Critical for Ambiguity/Flow Continuity)
                 if result.get("action") != "COMPLETED":
                     result["state_id"] = new_state.id
                     
                 return result
            
            # Prepare response data (Standard Flow)
            resp_data = intent_res.get("filtros", {})
            
            # For VPOS BILLING (Cart), explicit empty cart if not executed
            if final_target_table == "vpos_billing":
                resp_data["cart"] = []
                resp_data["total"] = 0
            
            return {
                "action": "NEW_STATE",
                "intent": action_type,
                "table": target_table,
                "state_id": new_state.id,
                "message": check['message'] if final_target_table == "vpos_billing" else f"Iniciando {action_type}. {check['message']}",
                "data": resp_data
            }

        print(f"[DEBUG - Analyze] Action '{action_type}' not handled as state transition.")
        return {"action": "UNKNOWN", "text": text, "details": intent_res}

command_analyzer = CommandAnalyzer()
