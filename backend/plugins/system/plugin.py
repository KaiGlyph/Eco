import json
import re
import subprocess
import time
import webbrowser
from core.plugin_base import BasePlugin

# ==========================================
# FUNCIONES DE EJECUCIÓN (Devuelven dict)
# ==========================================
def _set_volume_powershell(percentage: float):
    try:
        subprocess.run([
            'powershell', '-NoProfile', '-WindowStyle', 'Hidden', '-Command',
            '$wshell = New-Object -ComObject WScript.Shell; '
            '1..50 | ForEach-Object { $wshell.SendKeys([char]174) }'
        ], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW, timeout=10)
        
        steps = max(0, min(50, int(percentage / 2)))
        if steps > 0:
            subprocess.run([
                'powershell', '-NoProfile', '-WindowStyle', 'Hidden', '-Command',
                f'$wshell = New-Object -ComObject WScript.Shell; '
                f'1..{steps} | ForEach-Object {{ $wshell.SendKeys([char]175) }}'
            ], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW, timeout=3)
        time.sleep(0.2)
    except Exception as e:
        print(f"[Volumen] Error en PowerShell: {e}")

def get_current_volume() -> float: return 50.0

def set_volume(percentage: float) -> dict:
    _set_volume_powershell(percentage)
    return {"action": "volume_set", "success": True, "context": f"El volumen del sistema se ha establecido al {percentage:.0f}%"}

def change_volume(direction: str, percentage: float, is_absolute: bool = False) -> dict:
    current = get_current_volume()
    if is_absolute and percentage is not None: return set_volume(percentage)
    if percentage is None: percentage = 15.0
    new_volume = min(100, current + percentage) if direction == "up" else max(0, current - percentage)
    _set_volume_powershell(new_volume)
    return {"action": "volume_changed", "success": True, "context": f"El volumen se ha {'subido' if direction == 'up' else 'bajado'} al {new_volume:.0f}%"}

def mute_volume() -> dict:
    try:
        subprocess.run(['powershell', '-NoProfile', '-WindowStyle', 'Hidden', '-Command', '(New-Object -ComObject WScript.Shell).SendKeys([char]173)'], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        return {"action": "volume_mute", "success": True, "context": "El sistema ha sido silenciado"}
    except Exception as e:
        return {"action": "volume_mute", "success": False, "context": f"Error silenciando: {e}"}

def get_current_brightness() -> float:
    try:
        import wmi
        return float(wmi.WMI(namespace='wmi').WmiMonitorBrightness()[0].CurrentBrightness)
    except Exception: return 75.0

def set_brightness_absolute(percentage: float) -> dict:
    try:
        import wmi
        wmi.WMI(namespace='wmi').WmiMonitorBrightnessMethods()[0].WmiSetBrightness(int(percentage), 0)
        return {"action": "brightness_set", "success": True, "context": f"Brillo establecido al {percentage:.0f}%"}
    except Exception as e:
        return {"action": "brightness_set", "success": False, "context": f"Error ajustando brillo: {e}"}

def change_brightness_relative(direction: str, percentage: float = 10.0) -> dict:
    current = get_current_brightness()
    new_brightness = min(100, current + percentage) if direction == "up" else max(0, current - percentage)
    return set_brightness_absolute(new_brightness)

def lock_pc() -> dict:
    subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"], creationflags=subprocess.CREATE_NO_WINDOW)
    return {"action": "lock", "success": True, "context": "Equipo bloqueado"}

def shutdown_pc(minutes: int = 1) -> dict:
    subprocess.run(["shutdown", "/s", "/t", str(minutes * 60)], creationflags=subprocess.CREATE_NO_WINDOW)
    return {"action": "shutdown", "success": True, "context": f"Equipo se apagará en {minutes} minuto(s)"}

def cancel_shutdown() -> dict:
    subprocess.run(["shutdown", "/a"], creationflags=subprocess.CREATE_NO_WINDOW)
    return {"action": "cancel_shutdown", "success": True, "context": "Apagado cancelado"}

def restart_pc(minutes: int = 1) -> dict:
    subprocess.run(["shutdown", "/r", "/t", str(minutes * 60)], creationflags=subprocess.CREATE_NO_WINDOW)
    return {"action": "restart", "success": True, "context": f"Equipo se reiniciará en {minutes} minuto(s)"}

def suspend_pc() -> dict:
    subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"], creationflags=subprocess.CREATE_NO_WINDOW)
    return {"action": "suspend", "success": True, "context": "Equipo suspendido"}

def search_web(query: str) -> dict:
    webbrowser.open(f"https://www.google.com/search?q={query}")
    return {"action": "web_search", "success": True, "context": f"Buscando '{query}' en Google"}

def close_browser_tab() -> dict:
    try:
        import pyautogui
        pyautogui.hotkey('ctrl', 'w')
        return {"action": "close_tab", "success": True, "context": "Pestaña cerrada"}
    except Exception:
        return {"action": "close_tab", "success": False, "context": "No se pudo cerrar la pestaña"}

def initialize_volume_cache(): pass


# ==========================================
# PLUGIN SYSTEM
# ==========================================
class SystemPlugin(BasePlugin):
    name = "Sistema"
    description = "Control del sistema: volumen, brillo, apagado, bloqueo, búsqueda web"
    icon = "settings"
    priority = 70
    
    def get_intents(self):
        return [
            {"tag": "volumen_detectado", "patterns": ["volumen", "sonido", "audio"], "responses": ["..."]},
            {"tag": "brillo_detectado", "patterns": ["brillo", "luminosidad", "pantalla"], "responses": ["..."]},
            {"tag": "bloquear_pc", "patterns": ["bloquea", "lock"], "responses": ["..."]},
            {"tag": "apagar_pc", "patterns": ["apaga", "shutdown"], "responses": ["..."]},
            {"tag": "reiniciar_pc", "patterns": ["reinicia", "reboot"], "responses": ["..."]},
            {"tag": "suspender_pc", "patterns": ["suspende", "sleep"], "responses": ["..."]},
            {"tag": "cancelar_apagado", "patterns": ["cancela", "no apagues"], "responses": ["..."]},
            {"tag": "web_search", "patterns": ["busca", "google", "internet"], "responses": ["..."]},
            {"tag": "cerrar_pestaña", "patterns": ["cierra", "pestaña", "navegador"], "responses": ["..."]}
        ]

    def get_forced_patterns(self):
        return [
            (["volumen", "sonido", "audio", "sube", "baja", "silencia", "mute", "máximo", "mitad"], "volumen_detectado"),
            (["brillo", "luminosidad", "pantalla"], "brillo_detectado"),
            (["bloquea", "lock"], "bloquear_pc"),
            (["apaga", "shutdown"], "apagar_pc"),
            (["reinicia", "reboot"], "reiniciar_pc"),
            (["suspende", "sleep"], "suspender_pc"),
            (["cancela", "no apagues"], "cancelar_apagado"),
            (["busca", "google", "internet"], "web_search"),
            (["cierra", "pestaña", "navegador"], "cerrar_pestaña")
        ]

    def can_handle(self, text: str, intent: str, confidence: float) -> bool:
        return intent in ["volumen_detectado", "brillo_detectado", "bloquear_pc", "apagar_pc", "reiniciar_pc", "suspender_pc", "cancelar_apagado", "web_search", "cerrar_pestaña"]

    def _parse_with_llm(self, text: str, schema: str, examples: str, llm_engine) -> dict:
        if not llm_engine: return {}
        prompt = f"""Analiza esta frase sobre el sistema y extrae la información en JSON estricto.
Frase: "{text}"
Esquema requerido: {schema}
Ejemplos: {examples}
Responde SOLO con el JSON:"""
        try:
            response = llm_engine.chat(prompt, "fast")
            json_match = re.search(r'\{[^}]+\}', response)
            if json_match: return json.loads(json_match.group())
            return {}
        except Exception as e:
            print(f"[SystemPlugin] Error parseando con LLM: {e}")
            return {}

    def handle(self, text: str, intent: str, context: dict) -> dict:
        lower_text = text.lower()
        brain = context.get('brain')
        llm = brain.llm if brain else None
        
        # 1. VOLUMEN Y BRILLO UNIFICADOS CON LLM
        if intent in ["volumen_detectado", "brillo_detectado"]:
            # Esquema unificado que permite identificar si es volumen o brillo
            schema = '{"action": "set"|"up"|"down"|"mute", "component": "volume"|"brightness", "value": 0-100 o null, "is_absolute": true|false}'
            examples = '''
            - "Pon el volumen al máximo" -> {"action": "set", "component": "volume", "value": 100, "is_absolute": true}
            - "Sube un poco el audio" -> {"action": "up", "component": "volume", "value": 15, "is_absolute": false}
            - "el brillo al 20" -> {"action": "set", "component": "brightness", "value": 20, "is_absolute": true}
            - "Baja el brillo" -> {"action": "down", "component": "brightness", "value": 15, "is_absolute": false}
            - "Silencia" -> {"action": "mute", "component": "volume", "value": null, "is_absolute": false}
            '''
            
            command = self._parse_with_llm(lower_text, schema, examples, llm)
            
            component = command.get("component", "volume")
            action = command.get("action", "up")
            value = command.get("value", 15)
            is_absolute = command.get("is_absolute", False)
            
            # Ejecutar según el componente detectado
            if component == "volume":
                if action == "mute": return mute_volume()
                elif action == "set" and is_absolute: return set_volume(value)
                elif action == "up": return change_volume("up", value, is_absolute)
                elif action == "down": return change_volume("down", value, is_absolute)
            
            elif component == "brightness":
                if action == "set" and is_absolute: return set_brightness_absolute(value)
                elif action in ["up", "down"]: return change_brightness_relative(action, value)
            
            return {"action": "system_error", "success": False, "context": "No entendí el comando del sistema."}

        # 2. ACCIONES DEL SISTEMA (Sin cambios)
        if intent == "bloquear_pc": return lock_pc()
        elif intent == "apagar_pc":
            if "ahora" in lower_text: return shutdown_pc(1)
            if brain: brain.pending_action = "shutdown"
            return {"action": "pending", "success": True, "context": "¿Estás seguro de que quieres apagar el equipo? Di 'sí' para confirmar."}
        elif intent == "reiniciar_pc":
            if "ahora" in lower_text: return restart_pc(1)
            if brain: brain.pending_action = "restart"
            return {"action": "pending", "success": True, "context": "¿Seguro que quieres reiniciar? Confirma con 'sí'."}
        elif intent == "suspender_pc": return suspend_pc()
        elif intent == "cancelar_apagado": return cancel_shutdown()
        elif intent == "web_search":
            query = lower_text
            for prefix in ["busca en google", "busca en internet", "googlea", "busca"]:
                if query.startswith(prefix): query = query[len(prefix):].strip(); break
            return search_web(query)
        elif intent == "cerrar_pestaña": return close_browser_tab()
        
        return {"action": "unknown", "success": False, "context": "No entendí el comando del sistema."}

        # 3. ACCIONES DEL SISTEMA (Lógica directa, no necesitan LLM complejo)
        if intent == "bloquear_pc":
            return lock_pc()
        elif intent == "apagar_pc":
            if "ahora" in lower_text:
                return shutdown_pc(1)
            if brain:
                brain.pending_action = "shutdown"
            return {"action": "pending", "success": True, "context": "¿Estás seguro de que quieres apagar el equipo? Di 'sí' para confirmar."}
        elif intent == "reiniciar_pc":
            if "ahora" in lower_text:
                return restart_pc(1)
            if brain:
                brain.pending_action = "restart"
            return {"action": "pending", "success": True, "context": "¿Seguro que quieres reiniciar? Confirma con 'sí'."}
        elif intent == "suspender_pc":
            return suspend_pc()
        elif intent == "cancelar_apagado":
            return cancel_shutdown()
        elif intent == "web_search":
            query = lower_text
            for prefix in ["busca en google", "busca en internet", "googlea", "busca"]:
                if query.startswith(prefix):
                    query = query[len(prefix):].strip()
                    break
            return search_web(query)
        elif intent == "cerrar_pestaña":
            return close_browser_tab()
        
        return {"action": "unknown", "success": False, "context": "No entendí el comando del sistema."}