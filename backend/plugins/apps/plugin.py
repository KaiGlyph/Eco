import json
import re
import os
import subprocess
import psutil
import ctypes
from ctypes import wintypes
from core.plugin_base import BasePlugin

# ==========================================
# MAPEO DE APLICACIONES COMUNES
# ==========================================
APP_MAP = {
    "spotify": "spotify.exe",
    "chrome": "chrome.exe",
    "navegador": "chrome.exe",
    "edge": "msedge.exe",
    "firefox": "firefox.exe",
    "discord": "Discord.exe",
    "visual studio code": "Code.exe",
    "vscode": "Code.exe",
    "code": "Code.exe",
    "bloc de notas": "notepad.exe",
    "notepad": "notepad.exe",
    "calculadora": "calc.exe",
    "explorador": "explorer.exe",
    "steam": "steam.exe",
    "whatsapp": "WhatsApp.exe",
    "telegram": "Telegram.exe",
    "brave": "brave.exe",
    "brave browser": "brave.exe"
}

# Procesos del sistema que nunca deben mostrarse
SYSTEM_PROCESSES = {
    'system', 'svchost.exe', 'services.exe', 'lsass.exe', 'csrss.exe',
    'wininit.exe', 'winlogon.exe', 'smss.exe', 'fontdrvhost.exe',
    'dwm.exe', 'explorer.exe', 'taskhostw.exe', 'runtimebroker.exe',
    'searchindexer.exe', 'searchprotocolhost.exe', 'searchfilterhost.exe',
    'conhost.exe', 'dllhost.exe', 'wudfhost.exe', 'sihost.exe',
    'ctfmon.exe', 'securityhealthsystray.exe', 'msedgewebview2.exe',
    'registry', 'system idle process'
}

def _resolve_app_name(app_name: str) -> str:
    if not app_name:
        return ""
    lower_name = app_name.lower().strip()
    return APP_MAP.get(lower_name, f"{lower_name}.exe" if not lower_name.endswith(".exe") else lower_name)

def _get_process_name_from_exe(exe_name: str) -> str:
    name_map = {
        "Code.exe": "Visual Studio Code",
        "chrome.exe": "Google Chrome",
        "msedge.exe": "Microsoft Edge",
        "brave.exe": "Brave Browser",
        "notepad.exe": "Bloc de notas",
        "calc.exe": "Calculadora",
        "explorer.exe": "Explorador de archivos",
        "Discord.exe": "Discord",
        "spotify.exe": "Spotify",
        "WhatsApp.exe": "WhatsApp",
        "Telegram.exe": "Telegram"
    }
    return name_map.get(exe_name, exe_name.replace(".exe", "").title())

# ==========================================
# API DE WINDOWS PARA DETECTAR VENTANAS
# ==========================================
user32 = ctypes.windll.user32

WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

def _is_window_visible(hwnd: int) -> bool:
    """Verifica si una ventana es visible y tiene título"""
    if not user32.IsWindowVisible(hwnd):
        return False
    
    length = user32.GetWindowTextLengthW(hwnd)
    if length == 0:
        return False
    
    return True

def _get_windows_with_titles() -> list:
    """Obtiene lista de ventanas visibles con sus títulos y PIDs"""
    windows = []
    
    def enum_callback(hwnd, lParam):
        if _is_window_visible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            buffer = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buffer, length + 1)
            
            title = buffer.value.strip()
            if title:
                # Obtener PID del proceso
                pid = wintypes.DWORD()
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                windows.append({
                    'title': title,
                    'pid': pid.value,
                    'hwnd': hwnd
                })
        return True
    
    user32.EnumWindows(WNDENUMPROC(enum_callback), 0)
    return windows

def _get_process_by_pid(pid: int) -> psutil.Process:
    """Obtiene un proceso por su PID"""
    try:
        return psutil.Process(pid)
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return None

# ==========================================
# FUNCIONES DE EJECUCIÓN
# ==========================================
def open_application(app_name: str) -> dict:
    executable = _resolve_app_name(app_name)
    try:
        os.system(f'start "" "{executable}"')
        return {
            "action": "app_opened",
            "success": True,
            "context": f"Abriendo {app_name}."
        }
    except Exception as e:
        return {"action": "app_open_error", "success": False, "context": f"No pude abrir {app_name}: {e}"}

def close_application(app_name: str) -> dict:
    executable = _resolve_app_name(app_name)
    try:
        result = subprocess.run(
            ["taskkill", "/F", "/IM", executable],
            capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
        )
        if result.returncode == 0:
            return {"action": "app_closed", "success": True, "context": f"{app_name} ha sido cerrado."}
        else:
            return {"action": "app_close_error", "success": False, "context": f"No encontré {app_name} abierto.", "raw_response": True}
    except Exception as e:
        return {"action": "app_close_error", "success": False, "context": f"Error al cerrar {app_name}: {e}"}

def list_open_apps(verbose: bool = False) -> dict:
    """
    Lista aplicaciones separando ventanas visibles de procesos en segundo plano
    """
    try:
        # 1. Obtener todas las ventanas visibles con sus PIDs
        windows = _get_windows_with_titles()
        
        # 2. Agrupar por PID y obtener nombres de procesos únicos
        apps_with_windows = {}
        for win in windows:
            pid = win['pid']
            proc = _get_process_by_pid(pid)
            
            if proc:
                name = proc.name()
                # Filtrar procesos del sistema
                if name.lower() not in SYSTEM_PROCESSES:
                    display_name = _get_process_name_from_exe(name)
                    if display_name not in apps_with_windows:
                        apps_with_windows[display_name] = {
                            'exe': name,
                            'titles': []
                        }
                    # Añadir título de la ventana (limitar a 2 por app)
                    if len(apps_with_windows[display_name]['titles']) < 2:
                        apps_with_windows[display_name]['titles'].append(win['title'])
        
        # 3. Obtener procesos en segundo plano (solo si verbose=True)
        background_processes = []
        if verbose:
            all_pids_with_windows = {win['pid'] for win in windows}
            
            for proc in psutil.process_iter(['name', 'username']):
                try:
                    if proc.info['username'] and os.getlogin() in proc.info['username']:
                        name = proc.name()
                        if name.lower() not in SYSTEM_PROCESSES and proc.pid not in all_pids_with_windows:
                            display_name = _get_process_name_from_exe(name)
                            if display_name not in background_processes:
                                background_processes.append(display_name)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        
        # 4. Construir respuesta
        if not apps_with_windows and not background_processes:
            return {"action": "apps_listed", "success": True, "context": "No hay aplicaciones abiertas.", "raw_response": True}
        
        lines = []
        if apps_with_windows:
            count = len(apps_with_windows)
            app_word = "aplicación" if count == 1 else "aplicaciones"
            lines.append(f"Tienes {count} {app_word} abiertas:")
            for app_name, info in list(apps_with_windows.items())[:10]:
                lines.append(f"  • {app_name}")
        
        if verbose and background_processes:
            count = len(background_processes)
            proc_word = "proceso" if count == 1 else "procesos"
            lines.append(f"\nY {count} {proc_word} en segundo plano:")
            for proc in background_processes[:10]:
                lines.append(f"  • {proc}")
        
        context = "\n".join(lines)
        return {"action": "apps_listed", "success": True, "context": context, "raw_response": True}
        
    except Exception as e:
        return {"action": "apps_list_error", "success": False, "context": f"Error listando apps: {e}", "raw_response": True}


# ==========================================
# PLUGIN APPS
# ==========================================
class AppsPlugin(BasePlugin):
    name = "Aplicaciones"
    description = "Gestión de aplicaciones: abrir, cerrar y listar"
    icon = "app-window"
    priority = 65
    
    def get_intents(self):
        return [
            {"tag": "apps_detectado", "patterns": ["abre", "cierra", "abrir", "cerrar", "aplicación", "programa", "app", "ventana"], "responses": ["..."]}
        ]

    def get_forced_patterns(self):
        return [
            (["abre", "abrir", "lanza", "inicia", "cierra", "cerrar", "mata", "detén", 
              "qué tengo abierto", "que tengo abierto", "aplicaciones abiertas", "programas abiertos",
              "lista las aplicaciones", "listar aplicaciones", "qué apps", "que apps", 
              "aplicaciones", "programas", "apps", "ventanas abiertas", "qué ventanas", "que ventanas",
              "segundo plano", "procesos", "qué procesos", "que procesos"], "apps_detectado")
        ]

    def can_handle(self, text: str, intent: str, confidence: float) -> bool:
        if intent == "apps_detectado":
            lower_text = text.lower()
            # Usar raíces de palabras para coincidir con plurales y géneros
            app_roots = ["aplicac", "program", "app", "ventan", "abiert", "lista", "listar", 
                        "proceso", "segundo plano", "abre", "cierra", "abrir", "cerrar",
                        "lanza", "inicia", "mata", "detén", "corriendo", "ejecutand"]
            return any(root in lower_text for root in app_roots)
        return False

    def _parse_with_llm(self, text: str, schema: str, examples: str, llm_engine) -> dict:
        if not llm_engine:
            return {}
        prompt = f"""Analiza esta frase sobre aplicaciones del ordenador y extrae la información en JSON estricto.
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
            print(f"[AppsPlugin] Error parseando con LLM: {e}")
            return {}

    def handle(self, text: str, intent: str, context: dict) -> dict:
        lower_text = text.lower()
        brain = context.get('brain')
        llm = brain.llm if brain else None
        
        schema = '{"action": "open"|"close"|"list", "app_name": "string|null", "verbose": true|false}'
        examples = '''
        - "Abre Spotify" -> {"action": "open", "app_name": "spotify", "verbose": false}
        - "Cierra el navegador" -> {"action": "close", "app_name": "navegador", "verbose": false}
        - "Abre Visual Studio Code" -> {"action": "open", "app_name": "visual studio code", "verbose": false}
        - "Qué tengo abierto" -> {"action": "list", "app_name": null, "verbose": false}
        - "Lista las aplicaciones" -> {"action": "list", "app_name": null, "verbose": false}
        - "Qué procesos tengo en segundo plano" -> {"action": "list", "app_name": null, "verbose": true}
        - "Muéstrame todo lo que está corriendo" -> {"action": "list", "app_name": null, "verbose": true}
        - "Cierra Discord" -> {"action": "close", "app_name": "discord", "verbose": false}
        '''
        
        command = self._parse_with_llm(lower_text, schema, examples, llm)
        action = command.get("action", "list")
        app_name = command.get("app_name")
        verbose = command.get("verbose", False)
        
        if action == "open":
            if not app_name:
                return {"action": "app_error", "success": False, "context": "No me has dicho qué aplicación abrir.", "raw_response": True}
            return open_application(app_name)
            
        elif action == "close":
            if not app_name:
                return {"action": "app_error", "success": False, "context": "No me has dicho qué aplicación cerrar.", "raw_response": True}
            return close_application(app_name)
            
        elif action == "list":
            return list_open_apps(verbose=verbose)
        
        return {"action": "unknown", "success": False, "context": "No entendí el comando de aplicaciones."}