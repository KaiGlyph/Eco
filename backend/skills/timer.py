import threading
import time
from datetime import datetime, timedelta

# Almacenamiento de temporizadores activos
active_timers = {}
timer_counter = 0

def start_timer(minutes: int, label: str = "") -> str:
    global timer_counter
    timer_counter += 1
    timer_id = timer_counter
    
    seconds = minutes * 60
    
    def timer_task():
        time.sleep(seconds)
        if timer_id in active_timers:
            del active_timers[timer_id]
            print(f"TEMPORIZADOR {timer_id} COMPLETADO: {label or f'{minutes} minutos'}")
    
    thread = threading.Thread(target=timer_task, daemon=True)
    thread.start()
    
    active_timers[timer_id] = {
        'label': label or f"{minutes} minutos",
        'start_time': datetime.now(),
        'end_time': datetime.now() + timedelta(seconds=seconds)
    }
    
    # Singular o plural
    unidad = "minuto" if minutes == 1 else "minutos"
    return f"Temporizador iniciado: {minutes} {unidad}. Te avisaré cuando termine."

def cancel_timer(timer_id: int = None) -> str:
    """Cancela un temporizador específico o el último"""
    if not active_timers:
        return "No hay temporizadores activos."
    
    if timer_id is None:
        timer_id = max(active_timers.keys())
    
    if timer_id in active_timers:
        del active_timers[timer_id]
        return f"Temporizador {timer_id} cancelado."
    
    return f"No encontré el temporizador {timer_id}."

def list_timers() -> str:
    if not active_timers:
        return "No hay ningún temporizador activo ahora mismo."
    
    count = len(active_timers)
    unidad = "temporizador" if count == 1 else "temporizadores"
    return f"Tienes {count} {unidad} activos en este momento."

def set_alarm(hour: int, minute: int, label: str = "") -> str:
    """Programa una alarma para una hora específica"""
    global timer_counter
    timer_counter += 1
    alarm_id = timer_counter
    
    now = datetime.now()
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    # Si la hora ya pasó hoy, la programamos para mañana
    if target <= now:
        target += timedelta(days=1)
        
    delay_seconds = (target - now).total_seconds()
    
    def alarm_task():
        time.sleep(delay_seconds)
        if alarm_id in active_timers:
            del active_timers[alarm_id]
            print(f"ALARMA {alarm_id} SONANDO: {label or f'{hour:02d}:{minute:02d}'}")
    
    thread = threading.Thread(target=alarm_task, daemon=True)
    thread.start()
    
    active_timers[alarm_id] = {
        'label': label or f"Alarma {hour:02d}:{minute:02d}",
        'start_time': now,
        'end_time': target,
        'type': 'alarm'
    }
    
    return f"Alarma programada para las {hour:02d}:{minute:02d}."

def cancel_alarm() -> str:
    """Cancela la última alarma programada"""
    # Buscamos la última alarma en la lista
    for tid in sorted(active_timers.keys(), reverse=True):
        if active_timers[tid].get('type') == 'alarm':
            del active_timers[tid]
            return f"Alarma cancelada."
            
    return "No hay alarmas activas para cancelar."