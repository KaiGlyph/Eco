import json
import psutil
import re
from core.plugin_base import BasePlugin

# ==========================================
# FUNCIONES DE EJECUCIÓN (Devuelven dict)
# ==========================================
def get_battery_status() -> dict:
    try:
        battery = psutil.sensors_battery()
        if battery:
            status = "cargando" if battery.power_plugged else "descargando"
            return {
                "action": "battery_status",
                "success": True,
                "context": f"Batería al {battery.percent}%, actualmente {status}.",
                "raw_response": True
            }
        return {"action": "battery_status", "success": False, "context": "No se detectó batería (probablemente es un PC de escritorio).", "raw_response": True}
    except Exception as e:
        return {"action": "battery_status", "success": False, "context": f"Error al leer la batería: {e}", "raw_response": True}

def get_cpu_status() -> dict:
    try:
        cpu_percent = psutil.cpu_percent(interval=0.5)
        cores = psutil.cpu_count()
        return {
            "action": "cpu_status",
            "success": True,
            "context": f"El procesador está al {cpu_percent}% de uso. Tienes {cores} núcleos.",
            "raw_response": True
        }
    except Exception as e:
        return {"action": "cpu_status", "success": False, "context": f"Error al leer la CPU: {e}", "raw_response": True}

def get_ram_status() -> dict:
    try:
        ram = psutil.virtual_memory()
        return {
            "action": "ram_status",
            "success": True,
            "context": f"Memoria RAM: {ram.percent}% usada ({ram.used // (1024**3)}GB de {ram.total // (1024**3)}GB).",
            "raw_response": True
        }
    except Exception as e:
        return {"action": "ram_status", "success": False, "context": f"Error al leer la RAM: {e}", "raw_response": True}

def get_disk_status() -> dict:
    try:
        disk = psutil.disk_usage('C:\\')
        free_gb = disk.free // (1024**3)
        return {
            "action": "disk_status",
            "success": True,
            "context": f"Disco C: {disk.percent}% usado. Quedan {free_gb}GB libres.",
            "raw_response": True
        }
    except Exception as e:
        return {"action": "disk_status", "success": False, "context": f"Error al leer el disco: {e}", "raw_response": True}

def get_all_hardware_status() -> dict:
    try:
        cpu = psutil.cpu_percent(interval=0.5)
        ram = psutil.virtual_memory().percent
        disk = psutil.disk_usage('C:\\').percent
        battery = psutil.sensors_battery()
        bat_str = f"Batería: {battery.percent}%" if battery else "Batería: No detectada (Escritorio)"
        
        context = f"Estado del sistema:\n• CPU: {cpu}%\n• RAM: {ram}%\n• Disco: {disk}%\n• {bat_str}"
        return {"action": "all_status", "success": True, "context": context, "raw_response": True}
    except Exception as e:
        return {"action": "all_status", "success": False, "context": f"Error general: {e}", "raw_response": True}


# ==========================================
# PLUGIN HARDWARE
# ==========================================
class HardwarePlugin(BasePlugin):
    name = "Hardware"
    description = "Consulta del estado del hardware del sistema"
    icon = "microchip"
    priority = 50
    
    def get_intents(self):
        return [
            {"tag": "hardware_detectado", "patterns": ["batería", "bateria", "cpu", "procesador", "ram", "memoria", "disco", "hardware", "equipo"], "responses": ["..."]}
        ]

    def get_forced_patterns(self):
        return [
            (["batería", "bateria", "cpu", "procesador", "ram", "memoria", "disco", "hardware", "equipo", "ordenador", "pc"], "hardware_detectado")
        ]

    def can_handle(self, text: str, intent: str, confidence: float) -> bool:
        return intent == "hardware_detectado"

    def _parse_with_llm(self, text: str, schema: str, examples: str, llm_engine) -> dict:
        if not llm_engine:
            return {}
        prompt = f"""Analiza esta frase sobre el hardware del equipo y extrae la información en JSON estricto.
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
            print(f"[HardwarePlugin] Error parseando con LLM: {e}")
            return {}

    def handle(self, text: str, intent: str, context: dict) -> dict:
        lower_text = text.lower()
        brain = context.get('brain')
        llm = brain.llm if brain else None
        
        schema = '{"action": "get_status", "component": "battery"|"cpu"|"ram"|"disk"|"all"}'
        examples = '''
        - "¿Cuánta batería me queda?" -> {"action": "get_status", "component": "battery"}
        - "¿Cómo va el procesador?" -> {"action": "get_status", "component": "cpu"}
        - "¿Tengo mucha memoria RAM usada?" -> {"action": "get_status", "component": "ram"}
        - "¿Cuánto espacio queda en el disco?" -> {"action": "get_status", "component": "disk"}
        - "¿Cómo está el equipo?" -> {"action": "get_status", "component": "all"}
        - "Dime el estado del sistema" -> {"action": "get_status", "component": "all"}
        '''
        
        command = self._parse_with_llm(lower_text, schema, examples, llm)
        component = command.get("component", "all")
        
        if component == "battery":
            return get_battery_status()
        elif component == "cpu":
            return get_cpu_status()
        elif component == "ram":
            return get_ram_status()
        elif component == "disk":
            return get_disk_status()
        else:
            return get_all_hardware_status()