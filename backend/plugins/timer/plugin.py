import re
import threading
import json
from datetime import datetime, timedelta
from core.plugin_base import BasePlugin

# ==========================================
# ESTADO GLOBAL (Temporizadores y Alarmas)
# ==========================================
active_timers = {}

# ==========================================
# FUNCIONES DE EJECUCIÓN (Devuelven dict para respuestas naturales)
# ==========================================
def start_timer(minutes: int, label: str = "Temporizador", custom_message: str = None) -> dict:
    timer_id = len(active_timers) + 1
    end_time = datetime.now() + timedelta(minutes=minutes)
    
    # Si hay un mensaje personalizado (ej: "Recuérdame beber agua"), úsalo
    message_to_speak = custom_message if custom_message else f"¡Tiempo! El {label} ha terminado."
    
    active_timers[timer_id] = {
        'end_time': end_time, 'label': label, 'type': 'timer', 'message': message_to_speak
    }
    
    def timer_callback():
        from core.speaker import speaker
        from core.notifier import send_notification
        
        # 1. Hablar
        speaker.speak(message_to_speak)
        
        # 2. Notificar visualmente
        send_notification(
            title="Eco - Temporizador",
            message=message_to_speak,
            timeout=15
        )
        
        if timer_id in active_timers:
            del active_timers[timer_id]
            
    thread = threading.Timer(minutes * 60, timer_callback)
    thread.start()
    
    time_str = "1 minuto" if minutes == 1 else f"{minutes} minutos"
    return {
        "action": "timer_started",
        "success": True,
        "context": f"Temporizador de {time_str} ({label}) iniciado."
    }

def cancel_timer() -> dict:
    if not active_timers:
        return {"action": "timer_cancel", "success": False, "context": "No hay temporizadores activos."}
    
    # Filtrar solo timers, no alarmas
    timers = {k: v for k, v in active_timers.items() if v['type'] == 'timer'}
    if not timers:
        return {"action": "timer_cancel", "success": False, "context": "No hay temporizadores activos."}
        
    count = len(timers)
    timer_word = "temporizador" if count == 1 else "temporizadores"
    return {
        "action": "timer_cancelled",
        "success": True,
        "context": f"Se ha cancelado {count} {timer_word}." if count == 1 else f"Se han cancelado {count} {timer_word}."
    }

def list_timers() -> dict:
    timers = {k: v for k, v in active_timers.items() if v['type'] == 'timer'}
    if not timers:
        return {"action": "timer_list", "success": True, "context": "No hay temporizadores activos.", "raw_response": True}
    
    timer_word = "temporizador" if len(timers) == 1 else "temporizadores"
    lines = [f"Tienes {len(timers)} {timer_word} activo:"]
    now = datetime.now()
    for tid, info in timers.items():
        remaining = (info['end_time'] - now).total_seconds() / 60
        lines.append(f"  • {info['label']}: {remaining:.1f} minutos restantes")
    
    return {"action": "timer_listed", "success": True, "context": "\n".join(lines), "raw_response": True}

def set_alarm(hour: int, minute: int, custom_message: str = None) -> dict:
    now = datetime.now()
    alarm_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if alarm_time <= now:
        alarm_time += timedelta(days=1)
    
    timer_id = len(active_timers) + 1
    label = f"Alarma {hour:02d}:{minute:02d}"
    
    # Mensaje personalizado para la alarma
    message_to_speak = custom_message if custom_message else f"¡Alarma! Son las {hour}:{minute:02d}."
    
    active_timers[timer_id] = {
        'end_time': alarm_time, 'label': label, 'type': 'alarm', 'message': message_to_speak
    }
    
    def alarm_callback():
        from core.speaker import speaker
        from core.notifier import send_notification
        
        # 1. Hablar
        speaker.speak(message_to_speak)
        
        # 2. Notificar visualmente
        send_notification(
            title="Eco - Alarma",
            message=message_to_speak,
            timeout=20
        )
        
        if timer_id in active_timers:
            del active_timers[timer_id]
            
    seconds_until = (alarm_time - now).total_seconds()
    thread = threading.Timer(seconds_until, alarm_callback)
    thread.start()
    
    return {
        "action": "alarm_set",
        "success": True,
        "context": f"Alarma configurada para las {hour:02d}:{minute:02d}."
    }

def cancel_alarm() -> dict:
    alarms = {k: v for k, v in active_timers.items() if v['type'] == 'alarm'}
    if not alarms:
        return {"action": "alarm_cancel", "success": False, "context": "No hay alarmas configuradas."}
    
    for tid in alarms:
        del active_timers[tid]
        
    return {
        "action": "alarm_cancelled",
        "success": True,
        "context": f"Se han cancelado {len(alarms)} alarma(s)."
    }


# ==========================================
# PLUGIN TIMER (El experto en su dominio)
# ==========================================
class TimerPlugin(BasePlugin):
    name = "Temporizadores"
    description = "Gestión de temporizadores, alarmas y recordatorios con lenguaje natural"
    icon = "clock"
    priority = 60
    
    def get_intents(self):
        return [
            {"tag": "timer_detectado", "patterns": ["temporizador", "timer", "avísame en", "cuenta atrás", "recuérdame"], "responses": ["..."]},
            {"tag": "alarm_detectado", "patterns": ["alarma", "despiértame", "avísame a las"], "responses": ["..."]}
        ]

    def get_forced_patterns(self):
        return [
            (["temporizador", "timer", "avísame en", "cuenta atrás", "dentro de", "recuérdame", "recordatorio"], "timer_detectado"),
            (["alarma", "despiértame", "avísame a las", "hora de"], "alarm_detectado")
        ]

    def can_handle(self, text: str, intent: str, confidence: float) -> bool:
        return intent in ["timer_detectado", "alarm_detectado"]

    # ==========================================
    # MÉTODO DE INTERPRETACIÓN CON LLM
    # ==========================================
    def _parse_with_llm(self, text: str, schema: str, examples: str, llm_engine) -> dict:
        if not llm_engine:
            return {}
            
        prompt = f"""Analiza esta frase sobre temporizadores, alarmas o recordatorios y extrae la información en JSON estricto.
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
            print(f"[TimerPlugin] Error parseando con LLM: {e}")
            return {}

    def handle(self, text: str, intent: str, context: dict) -> dict:
        lower_text = text.lower()
        brain = context.get('brain')
        llm = brain.llm if brain else None
        
        # 1. INTERPRETACIÓN DE TEMPORIZADORES Y RECORDATORIOS
        if intent == "timer_detectado":
            schema = '{"action": "start"|"cancel"|"list", "duration_minutes": int|null, "label": "string|null", "custom_message": "string|null"}'
            examples = '''
            - "Pon un temporizador de 20 minutos" -> {"action": "start", "duration_minutes": 20, "label": "Temporizador", "custom_message": null}
            - "Avísame en media hora" -> {"action": "start", "duration_minutes": 30, "label": "Temporizador", "custom_message": null}
            - "Temporizador de 1 hora y 15 minutos para la pasta" -> {"action": "start", "duration_minutes": 75, "label": "Pasta", "custom_message": null}
            - "Recuérdame beber agua en 30 minutos" -> {"action": "start", "duration_minutes": 30, "label": "Recordatorio", "custom_message": "¡Hora de beber agua!"}
            - "Recuérdame llamar a mamá en 1 hora" -> {"action": "start", "duration_minutes": 60, "label": "Recordatorio", "custom_message": "Llamar a mamá"}
            - "Cancela el temporizador" -> {"action": "cancel", "duration_minutes": null, "label": null, "custom_message": null}
            - "Qué temporizadores tengo activos" -> {"action": "list", "duration_minutes": null, "label": null, "custom_message": null}
            '''
            
            command = self._parse_with_llm(lower_text, schema, examples, llm)
            action = command.get("action", "list")
            
            if action == "start":
                mins = command.get("duration_minutes", 10)  # Fallback a 10 min si no lo entiende
                label = command.get("label") or "Temporizador"
                custom_msg = command.get("custom_message")
                return start_timer(mins, label, custom_message=custom_msg)
            elif action == "cancel":
                return cancel_timer()
            else:
                return list_timers()

        # 2. INTERPRETACIÓN DE ALARMAS
        elif intent == "alarm_detectado":
            schema = '{"action": "set"|"cancel"|"list", "hour": int|null, "minute": int|null, "custom_message": "string|null"}'
            examples = '''
            - "Pon una alarma a las 7:30" -> {"action": "set", "hour": 7, "minute": 30, "custom_message": null}
            - "Despiértame a las 8 de la mañana" -> {"action": "set", "hour": 8, "minute": 0, "custom_message": null}
            - "Alarma para las 10 de la noche" -> {"action": "set", "hour": 22, "minute": 0, "custom_message": null}
            - "Pon alarma a las 9 para la reunión" -> {"action": "set", "hour": 9, "minute": 0, "custom_message": "Reunión importante"}
            - "Cancela la alarma" -> {"action": "cancel", "hour": null, "minute": null, "custom_message": null}
            - "Qué alarmas tengo" -> {"action": "list", "hour": null, "minute": null, "custom_message": null}
            '''
            
            command = self._parse_with_llm(lower_text, schema, examples, llm)
            action = command.get("action", "list")
            
            if action == "set":
                hour = command.get("hour")
                minute = command.get("minute", 0)
                custom_msg = command.get("custom_message")
                if hour is not None:
                    return set_alarm(hour, minute, custom_message=custom_msg)
                else:
                    return {"action": "alarm_error", "success": False, "context": "No entendí la hora de la alarma."}
            elif action == "cancel":
                return cancel_alarm()
            else:
                # Listar alarmas
                alarms = {k: v for k, v in active_timers.items() if v['type'] == 'alarm'}
                if not alarms:
                    return {"action": "alarm_list", "success": True, "context": "No hay alarmas configuradas.", "raw_response": True}
                lines = [f"Tienes {len(alarms)} alarma(s):"]
                for tid, info in alarms.items():
                    lines.append(f"  • {info['label']}")
                return {"action": "alarm_listed", "success": True, "context": "\n".join(lines), "raw_response": True}
        
        return {"action": "unknown", "success": False, "context": "No entendí el comando de tiempo."}