import re
import ctypes
import subprocess
from core.plugin_base import BasePlugin

# ==========================================
# FUNCIONES DE EJECUCIÓN (Devuelven dict)
# ==========================================
# Nota: La velocidad del ratón en Windows va de 1 (lento) a 20 (rápido). 10 es el valor por defecto.
DEFAULT_MOUSE_SPEED = 10

def _get_mouse_speed_registry() -> int:
    """Intenta leer la velocidad del ratón desde el registro de Windows"""
    try:
        result = subprocess.run(
            ['reg', 'query', 'HKEY_CURRENT_USER\\Control Panel\\Mouse', '/v', 'MouseSpeed'],
            capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
        )
        # Simplificación: si no podemos leerlo fácilmente, asumimos el valor por defecto
        return DEFAULT_MOUSE_SPEED
    except Exception:
        return DEFAULT_MOUSE_SPEED

def get_mouse_speed_percentage() -> float:
    """Devuelve la velocidad actual en porcentaje (0-100)"""
    speed = _get_mouse_speed_registry()
    # Mapeamos 1-20 a 0-100%
    percentage = ((speed - 1) / 19) * 100
    return max(0.0, min(100.0, percentage))

def set_mouse_speed_percentage(percentage: float) -> dict:
    """Establece la velocidad del ratón usando ctypes (SystemParametersInfo)"""
    try:
        # Mapeamos 0-100% a 1-20
        speed = max(1, min(20, int((percentage / 100) * 19) + 1))
        
        SPI_SETMOUSESPEED = 0x0071
        ctypes.windll.user32.SystemParametersInfoW(SPI_SETMOUSESPEED, 0, speed, 0)
        
        return {
            "action": "mouse_speed_set",
            "success": True,
            "context": f"Velocidad del ratón ajustada al {percentage:.0f}%."
        }
    except Exception as e:
        return {"action": "mouse_speed_set", "success": False, "context": f"Error al ajustar la velocidad del ratón: {e}"}


# ==========================================
# PLUGIN MOUSE
# ==========================================
class MousePlugin(BasePlugin):
    name = "Ratón"
    description = "Control de la velocidad y configuración del ratón"
    icon = "mouse"
    priority = 50
    
    def get_intents(self):
        return [
            {"tag": "mouse_detectado", "patterns": ["ratón", "mouse", "cursor", "velocidad del ratón"], "responses": ["..."]}
        ]

    def get_forced_patterns(self):
        return [
            (["ratón", "mouse", "cursor", "velocidad del ratón", "velocidad del mouse"], "mouse_detectado")
        ]

    def can_handle(self, text: str, intent: str, confidence: float) -> bool:
        return intent == "mouse_detectado"

    def _parse_with_llm(self, text: str, schema: str, examples: str, llm_engine) -> dict:
        if not llm_engine:
            return {}
        prompt = f"""Analiza esta frase sobre el ratón o cursor y extrae la información en JSON estricto.
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
            print(f"[MousePlugin] Error parseando con LLM: {e}")
            return {}

    def handle(self, text: str, intent: str, context: dict) -> dict:
        lower_text = text.lower()
        brain = context.get('brain')
        llm = brain.llm if brain else None
        
        schema = '{"action": "get_speed"|"set_speed", "value": int|null}'
        examples = '''
        - "¿A qué velocidad está el ratón?" -> {"action": "get_speed", "value": null}
        - "Pon el ratón al 50%" -> {"action": "set_speed", "value": 50}
        - "Acelera el cursor" -> {"action": "set_speed", "value": 75}
        - "Baja la velocidad del ratón" -> {"action": "set_speed", "value": 30}
        - "Pon el mouse al máximo" -> {"action": "set_speed", "value": 100}
        '''
        
        command = self._parse_with_llm(lower_text, schema, examples, llm)
        action = command.get("action", "get_speed")
        
        if action == "get_speed":
            current_speed = get_mouse_speed_percentage()
            return {
                "action": "mouse_speed_get",
                "success": True,
                "context": f"La velocidad actual del ratón es del {current_speed:.0f}%.",
                "raw_response": True
            }
        elif action == "set_speed":
            value = command.get("value", 50)
            return set_mouse_speed_percentage(value)
        
        return {"action": "unknown", "success": False, "context": "No entendí el comando del ratón."}