import json
import re
import requests
from core.plugin_base import BasePlugin

# ==========================================
# FUNCIONES DE EJECUCIÓN (Devuelven dict)
# ==========================================
def _interpret_weather_code(code: int) -> str:
    codes = {
        0: "cielo despejado", 1: "principalmente despejado", 2: "parcialmente nublado",
        3: "nublado", 45: "niebla", 48: "niebla con escarcha", 51: "llovizna ligera",
        53: "llovizna moderada", 55: "llovizna densa", 61: "lluvia ligera", 63: "lluvia moderada",
        65: "lluvia fuerte", 71: "nevada ligera", 73: "nevada moderada", 75: "nevada fuerte",
        77: "granizo", 80: "chubascos ligeros", 81: "chubascos moderados", 82: "chubascos violentos",
        95: "tormenta", 96: "tormenta con granizo", 99: "tormenta fuerte con granizo"
    }
    return codes.get(code, "condiciones desconocidas")

def get_weather(city: str = "Madrid") -> dict:
    try:
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=es"
        geo_response = requests.get(geo_url, timeout=5)
        geo_data = geo_response.json()
        
        if not geo_data.get('results'):
            return {"action": "weather_error", "success": False, "context": f"No encontré la ciudad '{city}'.", "raw_response": True}
        
        lat = geo_data['results'][0]['latitude']
        lon = geo_data['results'][0]['longitude']
        city_name = geo_data['results'][0]['name']
        
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m&timezone=auto"
        weather_response = requests.get(weather_url, timeout=5)
        weather_data = weather_response.json()
        
        current = weather_data['current']
        temp = current['temperature_2m']
        humidity = current['relative_humidity_2m']
        wind = current['wind_speed_10m']
        weather_code = current['weather_code']
        
        weather_desc = _interpret_weather_code(weather_code)
        context = f"En {city_name} hay {weather_desc.lower()}, con {temp:.0f}°C, humedad del {humidity}% y viento de {wind:.0f} km/h."
        
        return {"action": "weather_fetched", "success": True, "context": context, "raw_response": True}
        
    except requests.exceptions.Timeout:
        return {"action": "weather_error", "success": False, "context": "No pude conectar con el servicio de clima.", "raw_response": True}
    except Exception as e:
        return {"action": "weather_error", "success": False, "context": f"Error consultando el clima: {e}", "raw_response": True}


# ==========================================
# PLUGIN CLIMA
# ==========================================
class WeatherPlugin(BasePlugin):
    name = "Clima"
    description = "Consulta el tiempo meteorológico actual con lenguaje natural y contexto de memoria"
    icon = "cloud"
    priority = 60
    
    def get_intents(self):
        return [{"tag": "weather_detectado", "patterns": ["tiempo", "clima", "temperatura", "llover", "pronóstico", "meteorológico"], "responses": ["..."]}]

    def get_forced_patterns(self):
        return [(["tiempo", "clima", "temperatura", "llover", "pronóstico", "meteorológico", "grados"], "weather_detectado")]

    def can_handle(self, text: str, intent: str, confidence: float) -> bool:
        return intent == "weather_detectado"

    def _parse_with_llm(self, text: str, schema: str, examples: str, llm_engine, user_context: str = "") -> dict:
        if not llm_engine:
            return {}
        
        # Inyectamos el contexto del usuario en el prompt si existe
        context_str = f"\nCONTEXTO DEL USUARIO: {user_context}" if user_context else ""
        
        prompt = f"""Analiza esta frase sobre el clima y extrae la información en JSON estricto.{context_str}
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
            print(f"[WeatherPlugin] Error parseando con LLM: {e}")
            return {}

    def handle(self, text: str, intent: str, context: dict) -> dict:
        lower_text = text.lower()
        brain = context.get('brain')
        llm = brain.llm if brain else None
        
        # 1. OBTENER CONTEXTO DE MEMORIA
        user_context = ""
        if brain:
            from core.memory import memory
            # Buscamos recuerdos que puedan indicar la ciudad
            mems = memory.search("ubicacion") or memory.search("vivo") or memory.search("ciudad")
            
            # Si no hay ubicación explícita, usamos los últimos 3 recuerdos por si dijo "soy de Barcelona" en categoría personal
            if not mems:
                mems = memory.get_all()[-3:]
            
            if mems:
                user_context = "Datos relevantes: " + ", ".join([m['fact'] for m in mems])

        # 2. DEFINIR ESQUEMA Y EJEMPLOS (El ejemplo ahora muestra cómo usar el contexto)
        schema = '{"action": "get_weather", "city": "string|null"}'
        examples = f'''
        - "Qué tiempo hace en Barcelona" -> {{"action": "get_weather", "city": "Barcelona"}}
        - "Va a llover hoy" -> {{"action": "get_weather", "city": "Sevilla"}} (si el CONTEXTO DEL USUARIO dice que vive en Sevilla)
        - "Dime la temperatura" -> {{"action": "get_weather", "city": null}}
        '''
        
        # 3. PARSEAR CON EL CONTEXTO INYECTADO
        command = self._parse_with_llm(lower_text, schema, examples, llm, user_context)
        
        # Si el LLM no encontró ciudad (ni en la frase ni en la memoria), usamos "Madrid" por defecto
        city = command.get("city") or "Madrid"
        
        return get_weather(city)