"""
Módulo de utilidades para obtener estado del sistema.
Estas funciones son usadas por main.py y los plugins.
"""

import psutil
from datetime import datetime

# Timer global (compartido con plugin timer)
active_timers = {}

def get_mouse_speed_percentage() -> float:
    """Obtiene la velocidad actual del ratón"""
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Mouse")
        value, _ = winreg.QueryValueEx(key, "MouseSensitivity")
        winreg.CloseKey(key)
        # Convertir valor de registro (1-20) a porcentaje (0-100)
        return (value / 20.0) * 100
    except Exception:
        return 50.0

def set_mouse_speed_absolute(percentage: float):
    """Establece la velocidad del ratón (0-100%)"""
    try:
        import winreg
        # Convertir porcentaje (0-100) a valor de registro (1-20)
        registry_value = max(1, min(20, int((percentage / 100.0) * 20)))
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Mouse", 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "MouseSensitivity", 0, winreg.REG_SZ, str(registry_value))
        winreg.CloseKey(key)
        return f"Velocidad del ratón establecida al {percentage:.0f}%"
    except Exception as e:
        return f"Error ajustando velocidad del ratón: {e}"

def change_mouse_speed(direction: str, step: int = 2):
    """Cambia la velocidad del ratón relativamente"""
    current = get_mouse_speed_percentage()
    if direction == "up":
        new_speed = min(100, current + step)
    else:
        new_speed = max(0, current - step)
    set_mouse_speed_absolute(new_speed)
    return f"Velocidad del ratón {'aumentada' if direction == 'up' else 'disminuida'} al {new_speed:.0f}%"

def get_current_volume() -> float:
    """Obtiene el volumen actual del sistema"""
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        return volume.GetMasterVolumeLevelScalar() * 100
    except Exception:
        return 50.0

def get_current_brightness() -> float:
    """Obtiene el brillo actual de la pantalla"""
    try:
        import wmi
        c = wmi.WMI(namespace='wmi')
        results = c.WmiMonitorBrightness()
        if results:
            return float(results[0].CurrentBrightness)
    except Exception:
        pass
    return 75.0  # Valor por defecto

def initialize_volume_cache():
    """Inicializa el caché de volumen (placeholder)"""
    pass

def get_notes_count() -> int:
    """Devuelve el número de notas"""
    try:
        import json
        import os
        notes_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'notes.json')
        if os.path.exists(notes_file):
            with open(notes_file, 'r', encoding='utf-8') as f:
                notes = json.load(f)
                return len(notes)
    except Exception:
        pass
    return 0

def get_recent_notes(limit: int = 3) -> list:
    """Devuelve las notas más recientes"""
    try:
        import json
        import os
        from datetime import datetime
        notes_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'notes.json')
        if os.path.exists(notes_file):
            with open(notes_file, 'r', encoding='utf-8') as f:
                notes = json.load(f)
                recent = notes[-limit:]
                recent.reverse()
                return recent
    except Exception:
        pass
    return []