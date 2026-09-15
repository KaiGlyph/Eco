import os
import re
import json
from datetime import datetime, timedelta
from core.plugin_base import BasePlugin

# ==========================================
# CONFIGURACIÓN Y AUTENTICACIÓN (GOOGLE)
# ==========================================
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), 'credentials.json')
TOKEN_FILE = os.path.join(os.path.dirname(__file__), 'token.json')

def get_google_service():
    """Obtiene el servicio de Google Calendar autenticado"""
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build

        creds = None
        if os.path.exists(TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(TOKEN_FILE)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(CREDENTIALS_FILE):
                    print("[Calendar] ERROR: No se encuentra credentials.json")
                    return None
                flow = InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS_FILE, ['https://www.googleapis.com/auth/calendar'])
                creds = flow.run_local_server(port=0)
            
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())

        return build('calendar', 'v3', credentials=creds)
    except Exception as e:
        print(f"[Calendar] Error de autenticación Google: {e}")
        return None

# ==========================================
# FUNCIONES DE EJECUCIÓN
# ==========================================
def get_today_events() -> dict:
    """Obtiene TODOS los eventos de hoy"""
    service = get_google_service()
    if not service:
        return {"action": "calendar_error", "success": False, "context": "No pude conectar con Google Calendar.", "raw_response": True}

    try:
        # Usar UTC para evitar conflictos de formato en la API de Google
        now = datetime.utcnow()
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=0)
        
        # Formato ISO con 'Z' (UTC) que es el que Google valida correctamente
        time_min = start_of_day.strftime("%Y-%m-%dT%H:%M:%SZ")
        time_max = end_of_day.strftime("%Y-%m-%dT%H:%M:%SZ")

        print(f"[Calendar] Buscando eventos de hoy entre {time_min} y {time_max}")

        events_result = service.events().list(
            calendarId='primary', 
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True, 
            orderBy='startTime'
            # NOTA: No usamos timeZone='Europe/Madrid' aquí para evitar el error 400
        ).execute()
        
        events = events_result.get('items', [])
        
        if not events:
            return {"action": "calendar_empty", "success": True, "context": "No tienes ningún evento programado para hoy.", "raw_response": True}

        # Corrección de singular/plural para que suene natural
        event_word = "evento" if len(events) == 1 else "eventos"
        lines = [f"Tienes {len(events)} {event_word} hoy:"]
        
        for event in events:
            start = event.get('start', {})
            if 'dateTime' in start:
                dt_str = start['dateTime']
                start_time = dt_str.split('T')[1][:5]
            else:
                start_time = "Todo el día"
            lines.append(f"  • {start_time}: {event.get('summary')}")

        return {"action": "calendar_listed", "success": True, "context": "\n".join(lines), "raw_response": True}
        
    except Exception as e:
        print(f"[Calendar] Error: {e}")
        return {"action": "calendar_error", "success": False, "context": "Error al leer el calendario.", "raw_response": True}


def create_event(title: str, date_str: str = None, time_str: str = None, duration_minutes: int = 60) -> dict:
    """Crea un nuevo evento en Google Calendar"""
    service = get_google_service()
    if not service:
        return {"action": "calendar_error", "success": False, "context": "No pude conectar con Google Calendar.", "raw_response": True}

    try:
        # Parsear fecha
        if date_str:
            for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]:
                try:
                    event_date = datetime.strptime(date_str, fmt)
                    break
                except ValueError:
                    continue
            else:
                event_date = datetime.now()
        else:
            event_date = datetime.now()

        # Parsear hora (por defecto 9:00 AM)
        if time_str:
            try:
                start_time = datetime.strptime(time_str, "%H:%M")
                start_dt = event_date.replace(hour=start_time.hour, minute=start_time.minute, second=0, microsecond=0)
            except ValueError:
                start_dt = event_date.replace(hour=9, minute=0, second=0, microsecond=0)
        else:
            start_dt = event_date.replace(hour=9, minute=0, second=0, microsecond=0)

        end_dt = start_dt + timedelta(minutes=duration_minutes)

        event = {
            'summary': title,
            'start': {
                'dateTime': start_dt.isoformat(),
                'timeZone': 'Europe/Madrid',
            },
            'end': {
                'dateTime': end_dt.isoformat(),
                'timeZone': 'Europe/Madrid',
            },
        }

        event = service.events().insert(calendarId='primary', body=event).execute()
        return {
            "action": "event_created",
            "success": True,
            "context": f"Evento '{title}' creado para el {start_dt.strftime('%d/%m a las %H:%M')}."
        }
        
    except Exception as e:
        return {"action": "calendar_error", "success": False, "context": f"Error al crear el evento: {e}", "raw_response": True}

def delete_event(date_str: str, title_filter: str = None) -> dict:
    """Elimina un evento de una fecha específica"""
    service = get_google_service()
    if not service:
        return {"action": "calendar_error", "success": False, "context": "No pude conectar con Google Calendar.", "raw_response": True}

    try:
        # Parsear fecha
        event_date = None
        for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]:
            try:
                event_date = datetime.strptime(date_str, fmt)
                break
            except (ValueError, TypeError):
                continue
        
        if not event_date:
            return {"action": "calendar_error", "success": False, "context": f"No entendí la fecha '{date_str}'.", "raw_response": True}

        # Buscar eventos en ese día usando formato UTC con 'Z'
        time_min = event_date.replace(hour=0, minute=0, second=0, microsecond=0)
        time_max = event_date.replace(hour=23, minute=59, second=59, microsecond=0)
        
        time_min_iso = time_min.strftime("%Y-%m-%dT%H:%M:%SZ")
        time_max_iso = time_max.strftime("%Y-%m-%dT%H:%M:%SZ")

        print(f"[Calendar] Buscando eventos para eliminar entre {time_min_iso} y {time_max_iso}")

        events_result = service.events().list(
            calendarId='primary', 
            timeMin=time_min_iso, 
            timeMax=time_max_iso,
            singleEvents=True, 
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])
        
        if not events:
            return {"action": "calendar_error", "success": False, "context": f"No encontré eventos el {event_date.strftime('%d/%m')}.", "raw_response": True}

        # Si hay filtro de título, buscar el que coincida
        event_to_delete = None
        if title_filter:
            for event in events:
                if title_filter.lower() in event.get('summary', '').lower():
                    event_to_delete = event
                    break
        else:
            # Si no hay filtro, eliminar el primero
            event_to_delete = events[0]

        if not event_to_delete:
            return {"action": "calendar_error", "success": False, "context": f"No encontré un evento con '{title_filter}' el {event_date.strftime('%d/%m')}.", "raw_response": True}

        event_id = event_to_delete['id']
        event_summary = event_to_delete.get('summary', 'Evento')
        
        print(f"[Calendar] Eliminando evento: {event_summary} (ID: {event_id})")

        # Eliminar el evento
        service.events().delete(calendarId='primary', eventId=event_id).execute()

        return {
            "action": "event_deleted",
            "success": True,
            "context": f"Evento '{event_summary}' eliminado del {event_date.strftime('%d/%m')}."
        }
        
    except Exception as e:
        print(f"[Calendar] Error al eliminar evento: {e}")
        return {"action": "calendar_error", "success": False, "context": "Error al eliminar el evento.", "raw_response": True}

def move_event(old_date_str: str, new_date_str: str, new_time_str: str = None) -> dict:
    """Mueve un evento de una fecha/hora a otra"""
    service = get_google_service()
    if not service:
        return {"action": "calendar_error", "success": False, "context": "No pude conectar con Google Calendar.", "raw_response": True}

    try:
        # Parsear fecha antigua
        old_date = None
        for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]:
            try:
                old_date = datetime.strptime(old_date_str, fmt)
                break
            except (ValueError, TypeError):
                continue
        
        if not old_date:
            return {"action": "calendar_error", "success": False, "context": f"No entendí la fecha '{old_date_str}'.", "raw_response": True}

        # Buscar eventos
        time_min = old_date.replace(hour=0, minute=0, second=0, microsecond=0)
        time_max = old_date.replace(hour=23, minute=59, second=59, microsecond=0)
        
        time_min_iso = time_min.strftime("%Y-%m-%dT%H:%M:%S")
        time_max_iso = time_max.strftime("%Y-%m-%dT%H:%M:%S")

        print(f"[Calendar] Buscando eventos entre {time_min_iso} y {time_max_iso}")

        events_result = service.events().list(
            calendarId='primary', 
            timeMin=time_min_iso, 
            timeMax=time_max_iso,
            singleEvents=True, 
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])
        
        if not events:
            return {"action": "calendar_error", "success": False, "context": f"No encontré eventos el {old_date.strftime('%d/%m')}.", "raw_response": True}

        event = events[0]
        event_id = event['id']
        event_summary = event.get('summary', 'Evento')
        
        print(f"[Calendar] Evento encontrado: {event_summary} (ID: {event_id})")
        
        # Parsear nueva fecha
        new_date = None
        if new_date_str:
            for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]:
                try:
                    new_date = datetime.strptime(new_date_str, fmt)
                    break
                except (ValueError, TypeError):
                    continue
        
        if not new_date:
            new_date = old_date  # Misma fecha si no se especifica
        
        # Obtener hora original del evento
        old_start_str = event['start'].get('dateTime', '')
        old_end_str = event['end'].get('dateTime', '')
        
        # Calcular nueva hora de inicio
        if new_time_str:
            try:
                new_time = datetime.strptime(new_time_str, "%H:%M")
                new_start = new_date.replace(hour=new_time.hour, minute=new_time.minute)
            except ValueError:
                new_start = new_date.replace(hour=9, minute=0)
        else:
            # Mantener la hora del evento original
            if 'T' in old_start_str:
                old_hour = int(old_start_str.split('T')[1][:2])
                old_minute = int(old_start_str.split('T')[1][3:5])
                new_start = new_date.replace(hour=old_hour, minute=old_minute)
            else:
                new_start = new_date.replace(hour=9, minute=0)
        
        # Calcular duración del evento original
        duration_minutes = 60
        if 'T' in old_end_str and 'T' in old_start_str:
            old_end_hour = int(old_end_str.split('T')[1][:2])
            old_end_minute = int(old_end_str.split('T')[1][3:5])
            old_start_hour = int(old_start_str.split('T')[1][:2])
            old_start_minute = int(old_start_str.split('T')[1][3:5])
            duration_minutes = (old_end_hour * 60 + old_end_minute) - (old_start_hour * 60 + old_start_minute)
            if duration_minutes <= 0:
                duration_minutes = 60
        
        new_end = new_start + timedelta(minutes=duration_minutes)

        # Actualizar el evento
        event['start'] = {
            'dateTime': new_start.strftime("%Y-%m-%dT%H:%M:%S"),
            'timeZone': 'Europe/Madrid',
        }
        event['end'] = {
            'dateTime': new_end.strftime("%Y-%m-%dT%H:%M:%S"),
            'timeZone': 'Europe/Madrid',
        }

        updated_event = service.events().update(
            calendarId='primary', eventId=event_id, body=event
        ).execute()

        return {
            "action": "event_moved",
            "success": True,
            "context": f"Evento '{event_summary}' movido al {new_start.strftime('%d/%m a las %H:%M')}."
        }
        
    except Exception as e:
        print(f"[Calendar] Error al mover evento: {e}")
        import traceback
        traceback.print_exc()
        return {"action": "calendar_error", "success": False, "context": f"Error al mover el evento: {e}", "raw_response": True}


# ==========================================
# PLUGIN CALENDAR
# ==========================================
class CalendarPlugin(BasePlugin):
    name = "Calendario"
    description = "Gestión de agenda: consultar, crear, mover y eliminar eventos"
    icon = "calendar"
    priority = 85
    
    def get_intents(self):
        return [
            {"tag": "calendar_detectado", "patterns": ["calendario", "agenda", "evento", "cita", "reunión", "tengo hoy", "qué tengo", "tareas"], "responses": ["..."]}
        ]

    def get_forced_patterns(self):
        return [
            (["agenda", "agendar", "calendario", "evento", "cita", "reunión", 
              "tengo hoy", "qué tengo", "qué tengo hoy", "tareas tengo", "qué tareas",
              "dentro de una semana", "la semana que viene", "próxima semana", 
              "mañana", "pasado mañana", "cambia", "mueve", "modifica",
              "elimina", "borra", "quita", "cancela la"], 
             "calendar_detectado")
        ]

    def can_handle(self, text: str, intent: str, confidence: float) -> bool:
        if intent == "calendar_detectado":
            lower_text = text.lower()
            keywords = ["agenda", "agendar", "calendario", "evento", "cita", "reunión", 
                       "tengo hoy", "qué tengo", "tareas", "dentro de", "semana", "mañana",
                       "cambia", "mueve", "modifica", "elimina", "borra", "quita", "cancela"]
            return any(kw in lower_text for kw in keywords)
        return False

    def _parse_with_llm(self, text: str, schema: str, examples: str, llm_engine) -> dict:
        """Parsea con LLM usando un prompt más claro"""
        if not llm_engine:
            return {}
        
        prompt = f"""Eres un asistente que extrae información de frases sobre calendario.

ESQUEMA JSON REQUERIDO:
{schema}

{examples}

FRASE DEL USUARIO: "{text}"

Extrae la información de la frase y devuelve SOLO el JSON con los valores reales (no el esquema). No incluyas texto adicional, solo el JSON."""
        
        try:
            response = llm_engine.chat(prompt, "smart")
            print(f"[Calendar] LLM response: {response}")
            
            # Buscar JSON en la respuesta
            json_match = re.search(r'\{[^}]+\}', response, re.DOTALL)
            if not json_match:
                print(f"[Calendar] No se encontró JSON en la respuesta")
                return {}
            
            json_str = json_match.group()
            
            # Corregir errores comunes
            json_str = json_str.replace("'", '"')
            json_str = re.sub(r',\s*}', '}', json_str)
            json_str = re.sub(r',\s*]', ']', json_str)
            
            return json.loads(json_str)
            
        except json.JSONDecodeError as e:
            print(f"[Calendar] Error de JSON: {e}")
            print(f"[Calendar] JSON intentado: {json_str if 'json_str' in locals() else 'N/A'}")
            return {}
        except Exception as e:
            print(f"[Calendar] Error parseando: {e}")
            return {}

    def _get_day_name_es(self, weekday: int) -> str:
        """Convierte el número de día de la semana a español"""
        days = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
        return days[weekday]

    def handle(self, text: str, intent: str, context: dict) -> dict:
        lower_text = text.lower()
        brain = context.get('brain')
        llm = brain.llm if brain else None
        
        # Obtener fecha actual
        now = datetime.now()
        current_date_str = now.strftime("%Y-%m-%d")
        current_day_name_es = self._get_day_name_es(now.weekday())
        
        # Calcular fechas de referencia
        tomorrow = now + timedelta(days=1)
        next_week = now + timedelta(days=7)
        
        schema = '''{
  "action": "get_events" | "create_event" | "move_event" | "delete_event",
  "title": "string o null",
  "old_date": "YYYY-MM-DD o null",
  "new_date": "YYYY-MM-DD o null",
  "time": "HH:MM o null",
  "duration_minutes": número entero
}'''
        
        examples = f"""HOY ES {current_day_name_es.upper()} {current_date_str}.

EJEMPLOS DE FRASES Y SU JSON:

Frase: "Qué tengo hoy"
JSON: {{"action": "get_events", "title": null, "old_date": null, "new_date": null, "time": null, "duration_minutes": 60}}

Frase: "Qué eventos tengo en el calendario"
JSON: {{"action": "get_events", "title": null, "old_date": null, "new_date": null, "time": null, "duration_minutes": 60}}

Frase: "Qué tareas tengo para hoy"
JSON: {{"action": "get_events", "title": null, "old_date": null, "new_date": null, "time": null, "duration_minutes": 60}}

Frase: "Agenda reunión mañana a las 10"
JSON: {{"action": "create_event", "title": "Reunión", "old_date": null, "new_date": "{tomorrow.strftime('%Y-%m-%d')}", "time": "10:00", "duration_minutes": 60}}

Frase: "Cita dentro de una semana"
JSON: {{"action": "create_event", "title": "Cita", "old_date": null, "new_date": "{next_week.strftime('%Y-%m-%d')}", "time": "09:00", "duration_minutes": 60}}

Frase: "Reunión el 1 de septiembre a las 10"
JSON: {{"action": "create_event", "title": "Reunión", "old_date": null, "new_date": "2026-09-01", "time": "10:00", "duration_minutes": 60}}

Frase: "Cambia la reunión del 1 de septiembre al 31 de agosto a las 10 de la mañana"
JSON: {{"action": "move_event", "title": null, "old_date": "2026-09-01", "new_date": "2026-08-31", "time": "10:00", "duration_minutes": 60}}

Frase: "Muéveme la reunión del día 3 de septiembre al 1 de septiembre y a las 10 de la mañana"
JSON: {{"action": "move_event", "title": null, "old_date": "2026-09-03", "new_date": "2026-09-01", "time": "10:00", "duration_minutes": 60}}

Frase: "Muéveme la reunión del 3 de septiembre a las 10"
JSON: {{"action": "move_event", "title": null, "old_date": "2026-09-03", "new_date": null, "time": "10:00", "duration_minutes": 60}}

Frase: "Eliminarme la reunión de hoy"
JSON: {{"action": "delete_event", "title": "reunión", "old_date": "{current_date_str}", "new_date": null, "time": null, "duration_minutes": 0}}

Frase: "Borra el evento de mañana"
JSON: {{"action": "delete_event", "title": null, "old_date": "{tomorrow.strftime('%Y-%m-%d')}", "new_date": null, "time": null, "duration_minutes": 0}}

Frase: "Cancela la cita del viernes"
JSON: {{"action": "delete_event", "title": "cita", "old_date": null, "new_date": null, "time": null, "duration_minutes": 0}}"""
        
        command = self._parse_with_llm(lower_text, schema, examples, llm)
        
        if not command:
            return {"action": "calendar_error", "success": False, "context": "No entendí el comando de calendario.", "raw_response": True}
        
        action = command.get("action")
        
        if action == "get_events":
            return get_today_events()
        
        elif action == "create_event":
            title = command.get("title", "Evento")
            return create_event(
                title=title,
                date_str=command.get("new_date"),
                time_str=command.get("time"),
                duration_minutes=command.get("duration_minutes", 60)
            )
        
        elif action == "move_event":
            old_date = command.get("old_date")
            new_date = command.get("new_date")
            new_time = command.get("time")
            
            if not new_date and new_time:
                # Cambio de hora en la misma fecha
                return move_event(
                    old_date_str=old_date,
                    new_date_str=old_date,
                    new_time_str=new_time
                )
            elif new_date:
                return move_event(
                    old_date_str=old_date,
                    new_date_str=new_date,
                    new_time_str=new_time
                )
            else:
                return {"action": "calendar_error", "success": False, "context": "No especificaste a cuándo mover el evento.", "raw_response": True}
        
        elif action == "delete_event":
            date_to_delete = command.get("old_date")
            if not date_to_delete:
                # Si no hay fecha, usar hoy
                date_to_delete = current_date_str
            title_filter = command.get("title")
            return delete_event(
                date_str=date_to_delete,
                title_filter=title_filter
            )
        
        return {"action": "unknown", "success": False, "context": "No entendí el comando de calendario."}