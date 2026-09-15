import psutil
import platform

def get_battery_info() -> str:
    try:
        battery = psutil.sensors_battery()
        if battery is None:
            return "No tienes batería, es un ordenador de escritorio."
        status = "cargando" if battery.power_plugged else "descargando"
        return f"Batería al {battery.percent}% y {status}."
    except Exception as e:
        return f"Error al leer batería: {str(e)}"

def get_ram_info() -> str:
    try:
        ram = psutil.virtual_memory()
        return f"Memoria RAM en uso al {ram.percent}%."
    except Exception as e:
        return f"Error al leer RAM: {str(e)}"

def get_cpu_info() -> str:
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        return f"El procesador está al {cpu_percent}% de uso."
    except Exception as e:
        return f"Error al leer CPU: {str(e)}"

def get_disk_info() -> str:
    try:
        disk = psutil.disk_usage('C:\\')
        return f"Disco duro con {disk.percent}% de espacio usado."
    except Exception as e:
        return f"Error al leer disco: {str(e)}"

def get_system_info() -> str:
    try:
        return f"Sistema operativo Windows y procesador {platform.processor()}."
    except Exception as e:
        return f"Error al leer sistema: {str(e)}"