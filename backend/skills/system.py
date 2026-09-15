import ctypes
import subprocess
import time
import webbrowser
import pyautogui
import pygetwindow as gw
from urllib.parse import quote
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import screen_brightness_control as sbc

# ==========================================
# CONTROL DE VOLUMEN
# ==========================================
VK_VOLUME_UP = 0xAF
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_MUTE = 0xAD
KEYEVENTF_KEYUP = 0x0002

# Caché local del volumen
_cached_volume = None

def _press_key(key_code: int):
    """Simula la pulsación de una tecla en Windows"""
    ctypes.windll.user32.keybd_event(key_code, 0, 0, 0)
    ctypes.windll.user32.keybd_event(key_code, 0, KEYEVENTF_KEYUP, 0)

def _get_volume_from_powershell() -> float:
    """Lee el volumen actual usando PowerShell (método más fiable)"""
    try:
        import subprocess
        # PowerShell command to get volume - sin popup
        result = subprocess.run(
            ['powershell', '-Command', 
             'Get-Volume | Select-Object -ExpandProperty VolumeLevel'],
            capture_output=True,
            text=True,
            timeout=2,
            creationflags=subprocess.CREATE_NO_WINDOW  # Evita ventanas emergentes
        )
        
        if result.returncode == 0 and result.stdout.strip():
            try:
                volume = float(result.stdout.strip())
                return round(volume, 1)
            except ValueError:
                pass
    except Exception:
        pass
    
    return -1  # Indica que falló

def _get_volume_interface():
    """Obtiene la interfaz de control de volumen de Windows"""
    try:
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        return cast(interface, POINTER(IAudioEndpointVolume))
    except Exception:
        return None

def initialize_volume_cache():
    """Inicializa el caché con el volumen real del sistema"""
    global _cached_volume
    
    # Intento 1: PowerShell (más fiable)
    volume = _get_volume_from_powershell()
    if volume >= 0:
        _cached_volume = volume
        return True
    
    # Intento 2: pycaw
    try:
        volume_interface = _get_volume_interface()
        if volume_interface:
            current = volume_interface.GetMasterVolumeLevelScalar() * 100
            _cached_volume = round(current, 1)
            return True
    except Exception:
        pass
    
    return False

def get_current_volume() -> float:
    """Lee el volumen actual. Siempre intenta leer el valor real primero."""
    global _cached_volume
    
    # Intento 1: PowerShell
    volume = _get_volume_from_powershell()
    if volume >= 0:
        _cached_volume = volume
        return _cached_volume
    
    # Intento 2: pycaw
    try:
        volume_interface = _get_volume_interface()
        if volume_interface:
            current = volume_interface.GetMasterVolumeLevelScalar() * 100
            _cached_volume = round(current, 1)
            return _cached_volume
    except Exception:
        pass
    
    # Si todo falla, usar el caché o 50.0
    if _cached_volume is not None:
        return _cached_volume
    
    return 50.0

def _update_cached_volume(new_value: float):
    """Actualiza el caché local del volumen"""
    global _cached_volume
    _cached_volume = round(max(0, min(100, new_value)), 1)

def set_volume_absolute(percentage: float) -> str:
    """Establece el volumen a un porcentaje exacto"""
    percentage = max(0, min(100, float(percentage)))
    
    # Intentar con pycaw
    try:
        volume_interface = _get_volume_interface()
        if volume_interface:
            volume_level = percentage / 100.0
            volume_interface.SetMasterVolumeLevelScalar(volume_level, None)
            _update_cached_volume(percentage)
            return f"Volumen establecido al {int(percentage)}%."
    except Exception:
        pass
    
    # Fallback: usar teclas
    current = get_current_volume()
    if percentage > current:
        steps = int((percentage - current) / 2)
        for _ in range(steps):
            _press_key(VK_VOLUME_UP)
            time.sleep(0.02)
    elif percentage < current:
        steps = int((current - percentage) / 2)
        for _ in range(steps):
            _press_key(VK_VOLUME_DOWN)
            time.sleep(0.02)
    
    _update_cached_volume(percentage)
    return f"Volumen establecido al {int(percentage)}%."

def change_volume_relative(action: str, amount: float) -> str:
    """Sube o baja el volumen"""
    current = get_current_volume()
    if action == "up":
        new_vol = min(100, current + amount)
    elif action == "down":
        new_vol = max(0, current - amount)
    else:
        return "Acción no válida."
    
    # Intentar con pycaw
    try:
        volume_interface = _get_volume_interface()
        if volume_interface:
            volume_level = new_vol / 100.0
            volume_interface.SetMasterVolumeLevelScalar(volume_level, None)
            _update_cached_volume(new_vol)
            return f"Volumen ajustado al {int(new_vol)}%."
    except Exception:
        pass
    
    # Fallback con teclas
    diff = new_vol - current
    steps = int(abs(diff) // 2)
    
    if diff > 0:
        for _ in range(steps):
            _press_key(VK_VOLUME_UP)
            time.sleep(0.02)
    elif diff < 0:
        for _ in range(steps):
            _press_key(VK_VOLUME_DOWN)
            time.sleep(0.02)
    
    _update_cached_volume(new_vol)
    return f"Volumen ajustado al {int(new_vol)}%."

def change_volume(action: str, percentage: float = None, is_absolute: bool = False) -> str:
    """Gestiona el cambio de volumen"""
    if percentage is not None:
        if is_absolute:
            return set_volume_absolute(percentage)
        else:
            return change_volume_relative(action, percentage)
    return change_volume_relative(action, 10.0)

def mute_volume() -> str:
    """Silencia o activa el sonido"""
    _press_key(VK_VOLUME_MUTE)
    return "Cambiando estado de silencio."

# ==========================================
# CONTROL DE BRILLO
# ==========================================
def get_current_brightness() -> float:
    """Lee el brillo actual del monitor. Siempre intenta leer el valor real."""
    try:
        brightness_list = sbc.get_brightness()
        if brightness_list and len(brightness_list) > 0:
            # sbc.get_brightness() devuelve una lista, tomamos el primer valor
            real_brightness = float(brightness_list[0])
            return round(real_brightness, 1)
    except Exception:
        pass
    
    # Si falla completamente, devolver 75.0 como último recurso
    return 75.0

def set_brightness_absolute(percentage: float) -> str:
    """Establece el brillo a un porcentaje exacto"""
    try:
        percentage = max(0, min(100, int(percentage)))
        sbc.set_brightness(percentage)
        return f"Brillo establecido al {percentage}%."
    except Exception as e:
        return f"No se pudo ajustar el brillo: {str(e)}"

def change_brightness_relative(action: str, amount: float) -> str:
    """Sube o baja el brillo una cantidad relativa desde el nivel REAL"""
    try:
        # SIEMPRE leer el brillo real antes de calcular
        brightness_list = sbc.get_brightness()
        if not brightness_list or len(brightness_list) == 0:
            return "No se pudo leer el brillo actual."
        
        current = float(brightness_list[0])
        
        if action == "up":
            new_val = min(100, current + amount)
        elif action == "down":
            new_val = max(0, current - amount)
        else:
            return "Acción no válida."
            
        sbc.set_brightness(int(new_val))
        return f"Brillo ajustado al {int(new_val)}%."
    except Exception as e:
        return f"No se pudo ajustar el brillo: {str(e)}"

# ==========================================
# CONTROL DEL SISTEMA
# ==========================================
def lock_pc() -> str:
    """Bloquea el equipo"""
    try:
        subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"], shell=False)
        return "Bloqueando el equipo."
    except Exception as e:
        return f"Error al bloquear: {str(e)}"

def shutdown_pc(minutes: int = 1) -> str:
    """Apaga el equipo"""
    try:
        seconds = minutes * 60
        subprocess.run(f"shutdown /s /t {seconds} /d p:0:0", shell=True)
        return f"Apagando el equipo en {minutes} minuto(s)."
    except Exception as e:
        return f"Error al apagar: {str(e)}"

def cancel_shutdown() -> str:
    """Cancela un apagado programado"""
    try:
        subprocess.run("shutdown /a", shell=True)
        return "Apagado cancelado."
    except Exception as e:
        return f"Error al cancelar: {str(e)}"

def restart_pc(minutes: int = 1) -> str:
    """Reinicia el equipo"""
    try:
        seconds = minutes * 60
        subprocess.run(f"shutdown /r /t {seconds} /d p:0:0", shell=True)
        return f"Reiniciando el equipo en {minutes} minuto(s)."
    except Exception as e:
        return f"Error al reiniciar: {str(e)}"

def suspend_pc() -> str:
    """Suspende el equipo"""
    try:
        subprocess.run("powercfg /hibernate off", shell=True)
        time.sleep(0.5)
        subprocess.run("rundll32.exe powrprof.dll,SetSuspendState 0,1,0", shell=True)
        return "Suspendiendo el equipo."
    except Exception as e:
        return f"Error al suspender: {str(e)}"
    
def search_web(query: str) -> str:
    """Busca en Google"""
    if not query:
        return "¿Qué quieres que busque?"
    
    encoded_query = quote(query)
    url = f"https://www.google.com/search?q={encoded_query}"
    webbrowser.open(url)
    return f"Buscando '{query}' en Google."

def close_browser_tab() -> str:
    """Cierra la pestaña activa del navegador usando Ctrl+W"""
    try:
        import pyautogui
        # Enviar Ctrl+W para cerrar la pestaña activa
        pyautogui.hotkey('ctrl', 'w')
        return "Pestaña cerrada."
    except ImportError:
        # Si no tiene pyautogui, usar subprocess con PowerShell
        try:
            import subprocess
            # Enviar tecla Ctrl+W usando PowerShell
            subprocess.run([
                'powershell', '-Command',
                'Add-Type -AssemblyName System.Windows.Forms; '
                '[System.Windows.Forms.SendKeys]::SendWait("^w")'
            ], capture_output=True)
            return "Pestaña cerrada."
        except Exception as e:
            return f"Error cerrando pestaña: {e}"
    except Exception as e:
        return f"Error cerrando pestaña: {e}"
    """Cierra la pestaña del navegador"""
    try:
        browsers = ["chrome", "msedge", "firefox", "brave", "opera"]
        browser_window = None
        
        for browser in browsers:
            windows = gw.getWindowsWithTitle(browser)
            if windows:
                browser_window = windows[0]
                break
        
        if browser_window:
            browser_window.activate()
            time.sleep(0.3)
            pyautogui.hotkey('ctrl', 'w')
            return "Cerrando la pestaña del navegador."
        else:
            return "No encontré ningún navegador abierto."
    except Exception as e:
        return f"Error al cerrar la pestaña: {str(e)}"