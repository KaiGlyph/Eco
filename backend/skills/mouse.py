import ctypes

# Constantes de Windows
SPI_GETMOUSESPEED = 112
SPI_SETMOUSESPEED = 113

# Rango de sensibilidad: 1 (mínimo) a 20 (máximo), 10 es el valor por defecto
MOUSE_SPEED_MIN = 1
MOUSE_SPEED_MAX = 20
MOUSE_SPEED_DEFAULT = 10

def get_mouse_speed() -> int:
    """Obtiene la velocidad actual del ratón (1-20)"""
    speed = ctypes.c_int()
    ctypes.windll.user32.SystemParametersInfoA(SPI_GETMOUSESPEED, 0, ctypes.byref(speed), 0)
    return speed.value

def set_mouse_speed(speed: int) -> str:
    """Establece la velocidad del ratón (1-20)"""
    speed = max(MOUSE_SPEED_MIN, min(MOUSE_SPEED_MAX, int(speed)))
    ctypes.windll.user32.SystemParametersInfoA(SPI_SETMOUSESPEED, 0, speed, 0)
    return f"Velocidad del ratón establecida a {speed}."

def change_mouse_speed(action: str, amount: int = 2) -> str:
    """Aumenta o reduce la velocidad del ratón"""
    current = get_mouse_speed()
    
    if action == "up":
        new_speed = min(MOUSE_SPEED_MAX, current + amount)
    elif action == "down":
        new_speed = max(MOUSE_SPEED_MIN, current - amount)
    else:
        return "Acción no válida."
    
    return set_mouse_speed(new_speed)

def set_mouse_speed_absolute(percentage: float) -> str:
    """Establece la velocidad del ratón a un porcentaje (0-100%)"""
    # Convertir porcentaje a escala 1-20
    speed = MOUSE_SPEED_MIN + (percentage / 100.0) * (MOUSE_SPEED_MAX - MOUSE_SPEED_MIN)
    return set_mouse_speed(int(round(speed)))

def get_mouse_speed_percentage() -> float:
    """Obtiene la velocidad del ratón como porcentaje (0-100%)"""
    current = get_mouse_speed()
    # Convertir escala 1-20 a porcentaje 0-100
    percentage = ((current - MOUSE_SPEED_MIN) / (MOUSE_SPEED_MAX - MOUSE_SPEED_MIN)) * 100
    return round(percentage, 1)