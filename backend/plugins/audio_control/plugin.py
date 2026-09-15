import json
import re
import difflib
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from core.plugin_base import BasePlugin

# ==========================================
# MAPEO DE NOMBRES COMUNES Y VARIACIONES
# ==========================================
APP_NAME_MAP = {
    "spotify": ["spotify"],
    "chrome": ["chrome", "google chrome", "cromo"],
    "navegador": ["chrome", "brave", "firefox", "edge"],
    "brave": ["brave", "brave browser", "verave", "breiv"],
    "firefox": ["firefox", "zorrap", "fox"],
    "edge": ["edge", "microsoft edge", "edy"],
    "discord": ["discord", "discor", "discor"],
    "teams": ["teams", "microsoft teams", "tim"],
    "zoom": ["zoom", "zum"],
    "vlc": ["vlc", "velece"],
    "steam": ["steam", "estim"],
    "whatsapp": ["whatsapp", "guasap", "watsap"],
    "telegram": ["telegram", "telegran"]
}

def _find_best_match(user_input: str, active_apps: list, threshold: float = 0.6) -> str:
    """
    Busca la aplicación más parecida usando fuzzy matching
    Returns: nombre real de la aplicación o None si no hay coincidencia
    """
    if not user_input or not active_apps:
        return None
    
    user_input_lower = user_input.lower().strip()
    
    # 1. Buscar en el mapeo de variaciones
    for app_name, variations in APP_NAME_MAP.items():
        for variation in variations:
            if user_input_lower == variation or user_input_lower in variation or variation in user_input_lower:
                # Verificar si esta app está activa
                for active_app in active_apps:
                    if app_name in active_app.lower() or active_app.lower() in app_name:
                        return active_app
    
    # 2. Búsqueda difusa con difflib
    best_match = None
    best_ratio = 0.0
    
    for active_app in active_apps:
        # Comparar con el nombre de la app
        ratio = difflib.SequenceMatcher(None, user_input_lower, active_app.lower()).ratio()
        
        # También comparar con variaciones conocidas
        for app_name, variations in APP_NAME_MAP.items():
            if app_name in active_app.lower():
                for variation in variations:
                    var_ratio = difflib.SequenceMatcher(None, user_input_lower, variation).ratio()
                    ratio = max(ratio, var_ratio)
        
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = active_app
    
    # Solo devolver si la similitud es suficiente
    if best_ratio >= threshold:
        return best_match
    
    return None

def _get_active_app_names() -> list:
    """Obtiene lista de nombres de aplicaciones con audio activo"""
    active_apps = []
    try:
        for session in AudioUtilities.GetAllSessions():
            if session.Process:
                name = session.Process.name().replace('.exe', '').lower()
                if name not in active_apps:
                    active_apps.append(name)
    except Exception as e:
        print(f"[AudioControl] Error obteniendo sesiones: {e}")
    return active_apps

# ==========================================
# FUNCIONES DE EJECUCIÓN
# ==========================================
def get_app_sessions() -> list:
    """Obtiene todas las sesiones de audio activas"""
    sessions = []
    try:
        for session in AudioUtilities.GetAllSessions():
            if session.Process:
                name = session.Process.name().replace('.exe', '')
                volume = session.SimpleAudioVolume
                if volume:
                    sessions.append({
                        'name': name.lower().replace('.exe', ''),
                        'volume': volume.GetMasterVolume(),
                        'mute': volume.GetMute(),
                        'display_name': name.replace('.exe', '').title()
                    })
    except Exception as e:
        print(f"[AudioControl] Error obteniendo sesiones: {e}")
    return sessions

def list_audio_apps() -> dict:
    """Lista aplicaciones con control de volumen"""
    sessions = get_app_sessions()
    
    if not sessions:
        return {
            "action": "audio_apps_listed",
            "success": True,
            "context": "No hay aplicaciones con control de audio activo.",
            "raw_response": True
        }
    
    lines = [f"Tienes {len(sessions)} aplicación(es) con audio:"]
    for session in sessions[:10]:
        mute_str = " (silenciada)" if session['mute'] else ""
        vol_percent = int(session['volume'] * 100)
        lines.append(f"  • {session['display_name']}: {vol_percent}%{mute_str}")
    
    return {
        "action": "audio_apps_listed",
        "success": True,
        "context": "\n".join(lines),
        "raw_response": True
    }

def set_app_volume(app_name: str, volume: float, mute: bool = False) -> dict:
    """Ajusta el volumen de una aplicación específica con fuzzy matching"""
    active_apps = _get_active_app_names()
    
    # Buscar la mejor coincidencia
    matched_app = _find_best_match(app_name, active_apps)
    
    if not matched_app:
        # Si no hay coincidencia, listar las apps disponibles
        apps_list = ", ".join([app.title() for app in active_apps[:5]])
        return {
            "action": "app_volume_error",
            "success": False,
            "context": f"No encontré '{app_name}'. Aplicaciones activas: {apps_list}",
            "raw_response": True
        }
    
    try:
        for session in AudioUtilities.GetAllSessions():
            if session.Process:
                proc_name = session.Process.name().replace('.exe', '').lower()
                if proc_name == matched_app:
                    volume_interface = session.SimpleAudioVolume
                    if volume_interface:
                        volume_interface.SetMasterVolume(volume / 100.0, None)
                        volume_interface.SetMute(mute, None)
                        
                        action = "silenciada" if mute else f"ajustada al {int(volume)}%"
                        return {
                            "action": "app_volume_set",
                            "success": True,
                            "context": f"Volumen de {matched_app.title()} {action}."
                        }
        
        return {
            "action": "app_volume_error",
            "success": False,
            "context": f"Error ajustando volumen de {matched_app}.",
            "raw_response": True
        }
    except Exception as e:
        return {
            "action": "app_volume_error",
            "success": False,
            "context": f"Error ajustando volumen: {e}",
            "raw_response": True
        }

def mute_app(app_name: str) -> dict:
    """Silencia una aplicación específica"""
    return set_app_volume(app_name, 0, mute=True)

def unmute_app(app_name: str) -> dict:
    """Desilencia una aplicación específica"""
    active_apps = _get_active_app_names()
    matched_app = _find_best_match(app_name, active_apps)
    
    if not matched_app:
        apps_list = ", ".join([app.title() for app in active_apps[:5]])
        return {
            "action": "app_unmute_error",
            "success": False,
            "context": f"No encontré '{app_name}'. Aplicaciones activas: {apps_list}",
            "raw_response": True
        }
    
    try:
        for session in AudioUtilities.GetAllSessions():
            if session.Process:
                proc_name = session.Process.name().replace('.exe', '').lower()
                if proc_name == matched_app:
                    volume_interface = session.SimpleAudioVolume
                    if volume_interface:
                        if volume_interface.GetMute():
                            volume_interface.SetMute(0, None)
                            return {
                                "action": "app_unmuted",
                                "success": True,
                                "context": f"{matched_app.title()} ha sido desilenciada."
                            }
                        else:
                            return {
                                "action": "app_unmute_error",
                                "success": False,
                                "context": f"{matched_app.title()} no está silenciada.",
                                "raw_response": True
                            }
        
        return {
            "action": "app_unmute_error",
            "success": False,
            "context": f"Error desilenciando {matched_app}.",
            "raw_response": True
        }
    except Exception as e:
        return {
            "action": "app_unmute_error",
            "success": False,
            "context": f"Error desilenciando: {e}",
            "raw_response": True
        }


# ==========================================
# PLUGIN AUDIO CONTROL
# ==========================================
class AudioControlPlugin(BasePlugin):
    name = "Control de Audio"
    description = "Control granular de volumen por aplicación"
    icon = "volume-high"
    priority = 75
    
    def get_intents(self):
        return [
            {"tag": "audio_control_detectado", "patterns": ["volumen de", "silencia", "baja el volumen", "sube el volumen", "audio de"], "responses": ["..."]}
        ]

    def get_forced_patterns(self):
        return [
            (["volumen de", "silencia", "baja el volumen", "sube el volumen", "audio de", 
              "qué aplicaciones tienen audio", "lista el audio", "aplicaciones con audio"], 
             "audio_control_detectado")
        ]

    def can_handle(self, text: str, intent: str, confidence: float) -> bool:
        if intent == "audio_control_detectado":
            lower_text = text.lower()
            keywords = ["volumen de", "silencia", "baja el volumen", "sube el volumen", 
                       "audio de", "aplicaciones con audio", "lista el audio"]
            return any(kw in lower_text for kw in keywords)
        return False

    def _parse_with_llm(self, text: str, schema: str, examples: str, llm_engine) -> dict:
        if not llm_engine:
            return {}
        prompt = f"""Analiza esta frase sobre control de audio de aplicaciones y extrae la información en JSON estricto.
Frase: "{text}"
Esquema requerido: {schema}
Ejemplos: {examples}
Responde SOLO con el JSON:"""
        try:
            response = llm_engine.chat(prompt, "fast")
            json_match = re.search(r'\{[^}]+\}', response)
            if json_match:
                return json.loads(json_match.group())
            return {}
        except Exception as e:
            print(f"[AudioControl] Error parseando con LLM: {e}")
            return {}

    def handle(self, text: str, intent: str, context: dict) -> dict:
        lower_text = text.lower()
        brain = context.get('brain')
        llm = brain.llm if brain else None
        
        schema = '{"action": "list"|"set_volume"|"mute"|"unmute", "app_name": "string|null", "volume": int|null}'
        examples = '''
        - "Baja el volumen de Spotify al 30%" -> {"action": "set_volume", "app_name": "spotify", "volume": 30}
        - "Silencia Discord" -> {"action": "mute", "app_name": "discord", "volume": null}
        - "Sube el volumen de Chrome" -> {"action": "set_volume", "app_name": "chrome", "volume": 80}
        - "Qué aplicaciones tienen audio" -> {"action": "list", "app_name": null, "volume": null}
        - "Lista el audio de las aplicaciones" -> {"action": "list", "app_name": null, "volume": null}
        - "Desilencia Spotify" -> {"action": "unmute", "app_name": "spotify", "volume": null}
        '''
        
        command = self._parse_with_llm(lower_text, schema, examples, llm)
        action = command.get("action", "list")
        app_name = command.get("app_name")
        volume = command.get("volume")
        
        if action == "list":
            return list_audio_apps()
            
        elif action == "set_volume":
            if not app_name:
                return {"action": "audio_error", "success": False, "context": "No me has dicho qué aplicación.", "raw_response": True}
            if volume is None:
                volume = 50
            return set_app_volume(app_name, volume)
            
        elif action == "mute":
            if not app_name:
                return {"action": "audio_error", "success": False, "context": "No me has dicho qué aplicación silenciar.", "raw_response": True}
            return mute_app(app_name)
            
        elif action == "unmute":
            if not app_name:
                return {"action": "audio_error", "success": False, "context": "No me has dicho qué aplicación desilenciar.", "raw_response": True}
            return unmute_app(app_name)
        
        return {"action": "unknown", "success": False, "context": "No entendí el comando de audio."}