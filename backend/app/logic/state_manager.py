from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
import json
from pydantic import BaseModel, Field
from supabase import create_client, Client
from app.core.config import settings

class VPosState(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    command_origin: str
    parameters_configurables: Dict[str, Any] = {}
    valor_retorno_esperado: Optional[str] = None
    datos_recolectados: Dict[str, Any] = {}
    timestamp_creacion: datetime = Field(default_factory=datetime.now)
    timestamp_ultima_actividad: datetime = Field(default_factory=datetime.now)
    estado_completado: bool = False
    procedimientos_finalizacion: List[str] = []
    procedimientos_interrupcion: List[str] = []
    procedimientos_ia: List[str] = []
    procedimientos_programaticos: List[str] = []
    prioridad: int = 1
    parent_estado_id: Optional[str] = None

class StateManager:
    def __init__(self):
        # Initialize Supabase client
        # In production verify URL/KEY exist
        self.supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

    def push_state(self, user_id: str, state: VPosState):
        """
        Push new state to DB. If there is an active state, it becomes the parent.
        """
        try:
            active = self.get_active_state(user_id)
            if active:
                state.parent_estado_id = active.id
            
            # Serialize for DB
            data = state.model_dump()
            data['timestamp_creacion'] = data['timestamp_creacion'].isoformat()
            data['timestamp_ultima_actividad'] = data['timestamp_ultima_actividad'].isoformat()
            
            # Use 'vpos_estados' table
            self.supabase.table("vpos_estados").insert(data).execute()
            print(f"[StateManager] Pushed state {state.id} for user {user_id}")
        except Exception as e:
            print(f"[StateManager] Error pushing state: {e}")

    def get_all_active_states(self, user_id: str) -> List[VPosState]:
        """
        Get ALL uncompleted states for the user, ordered by most recent.
        """
        try:
            response = self.supabase.table("vpos_estados")\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("estado_completado", False)\
                .order("timestamp_creacion", desc=True)\
                .execute()
                
            if response.data:
                return [VPosState(**state) for state in response.data]
            return []
        except Exception as e:
            print(f"[StateManager] Error fetching all active states: {e}")
            return []

    def get_active_state(self, user_id: str) -> Optional[VPosState]:
        """
        Get the most recent UNCOMPLETED state.
        Assuming 'stack' logic: the most recently created uncompleted state is active.
        """
        try:
            response = self.supabase.table("vpos_estados")\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("estado_completado", False)\
                .order("timestamp_creacion", desc=True)\
                .limit(1)\
                .execute()
                
            if response.data:
                # Handle empty strings or nulls if needed, but Pydantic is robust
                return VPosState(**response.data[0])
            return None
        except Exception as e:
            print(f"[StateManager] Error fetching active state: {e}")
            return None

    def pop_state(self, user_id: str) -> Optional[VPosState]:
        """
        Mark current active state as completed.
        Returns the popped state.
        """
        try:
            state = self.get_active_state(user_id)
            if state:
                self.supabase.table("vpos_estados")\
                    .update({"estado_completado": True, "timestamp_ultima_actividad": datetime.now().isoformat()})\
                    .eq("id", state.id)\
                    .execute()
                print(f"[StateManager] Popped state {state.id}")
                return state
            return None
        except Exception as e:
            print(f"[StateManager] Error popping state: {e}")
            return None

    def get_state_by_id(self, state_id: str) -> Optional[VPosState]:
        """
        Get a specific state by ID.
        """
        try:
            response = self.supabase.table("vpos_estados")\
                .select("*")\
                .eq("id", state_id)\
                .execute()
                
            if response.data:
                return VPosState(**response.data[0])
            return None
        except Exception as e:
            print(f"[StateManager] Error fetching state by id: {e}")
            return None

    def update_active_state_data(self, user_id: str, data: Dict[str, Any], overwrite: bool = False):
        """
        Update the 'datos_recolectados' of the active state.
        If overwrite is True, replaces the data entirely.
        Otherwise, merges.
        """
        try:
            state = self.get_active_state(user_id)
            if state:
                if overwrite:
                    updated_data = data
                else:
                    # Merge existing data with new data
                    updated_data = {**state.datos_recolectados, **data}
                
                self.supabase.table("vpos_estados")\
                    .update({
                        "datos_recolectados": updated_data,
                        "timestamp_ultima_actividad": datetime.now().isoformat()
                    })\
                    .eq("id", state.id)\
                    .execute()
                print(f"[StateManager] Updated state {state.id} with {data}")
        except Exception as e:
            print(f"[StateManager] Error updating state data: {e}")

state_manager = StateManager()
