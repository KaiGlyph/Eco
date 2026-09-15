import webbrowser
import urllib.parse
import pyautogui
import time
import re
import json
import ctypes  # <--- AÑADIDO para control multimedia de Windows
from core.plugin_base import BasePlugin

# ==========================================
# CÓDIGOS DE TECLAS MULTIMEDIA DE WINDOWS
# ==========================================
VK_MEDIA_PLAY_PAUSE = 0xB3
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002

def _send_media_key(vk_code):
    """Envía una tecla multimedia a nivel de sistema (mucho más fiable que pyautogui para navegadores)"""
    try:
        # Simular presión de tecla
        ctypes.windll.user32.keybd_event(vk_code, 0, KEYEVENTF_EXTENDEDKEY, 0)
        time.sleep(0.1)
        # Simular liberación de tecla
        ctypes.windll.user32.keybd_event(vk_code, 0, KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP, 0)
        return True
    except Exception:
        # Fallback a pyautogui por si acaso
        if vk_code == VK_MEDIA_PLAY_PAUSE:
            pyautogui.press('playpause')
        elif vk_code == VK_MEDIA_NEXT_TRACK:
            pyautogui.press('nexttrack')
        elif vk_code == VK_MEDIA_PREV_TRACK:
            pyautogui.press('prevtrack')
        return True

# ==========================================
# FUNCIONES DE EJECUCIÓN
# ==========================================
def search_youtube(query: str) -> dict:
    """Abre YouTube y reproduce el primer resultado"""
    try:
        import requests
        
        # 1. Buscar en YouTube
        encoded_query = urllib.parse.quote(query)
        search_url = f"https://www.youtube.com/results?search_query={encoded_query}"
        
        # 2. Obtener la página de resultados
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'en-US,en;q=0.9'
        }
        response = requests.get(search_url, headers=headers, timeout=10)
        
        # 3. Buscar el primer video ID en el HTML
        video_id_patterns = [
            r'"videoId":"([^"]{11})"',
            r'watch\?v=([^"&]{11})',
            r'/watch\?v=([^"&]{11})'
        ]
        
        video_id = None
        for pattern in video_id_patterns:
            matches = re.findall(pattern, response.text)
            if matches:
                for match in matches:
                    if len(match) == 11 and match not in ['null', 'undefined']:
                        video_id = match
                        break
                if video_id:
                    break
        
        if video_id:
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            webbrowser.open(video_url)
            return {
                "action": "youtube_search",
                "success": True,
                "context": f"Reproduciendo: '{query}'.",
                "raw_response": True
            }
        else:
            webbrowser.open(search_url)
            return {
                "action": "youtube_search",
                "success": True,
                "context": f"Buscando '{query}' en YouTube.",
                "raw_response": True
            }
            
    except Exception as e:
        print(f"[YouTube] Error: {e}")
        webbrowser.open(f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}")
        return {
            "action": "youtube_search",
            "success": True,
            "context": f"Buscando en YouTube: '{query}'.",
            "raw_response": True
        }
        
def play_music() -> dict:
    try:
        _send_media_key(VK_MEDIA_PLAY_PAUSE)
        time.sleep(0.3)
        return {"action": "music_play", "success": True, "context": "Reproducción reanudada.", "raw_response": True}
    except Exception as e:
        return {"action": "music_error", "success": False, "context": f"Error: {e}", "raw_response": True}

def pause_music() -> dict:
    try:
        _send_media_key(VK_MEDIA_PLAY_PAUSE)
        time.sleep(0.3)
        return {"action": "music_pause", "success": True, "context": "Reproducción pausada.", "raw_response": True}
    except Exception as e:
        return {"action": "music_error", "success": False, "context": f"Error: {e}", "raw_response": True}

def next_track() -> dict:
    try:
        _send_media_key(VK_MEDIA_NEXT_TRACK)
        time.sleep(0.3)
        return {"action": "music_next", "success": True, "context": "Siguiente.", "raw_response": True}
    except Exception as e:
        return {"action": "music_error", "success": False, "context": f"Error: {e}", "raw_response": True}

def previous_track() -> dict:
    try:
        _send_media_key(VK_MEDIA_PREV_TRACK)
        time.sleep(0.3)
        return {"action": "music_previous", "success": True, "context": "Anterior.", "raw_response": True}
    except Exception as e:
        return {"action": "music_error", "success": False, "context": f"Error: {e}", "raw_response": True}


# ==========================================
# PLUGIN MÚSICA (Universal)
# ==========================================
class MusicaPlugin(BasePlugin):
    name = "Música"
    description = "Control universal de música: búsqueda en YouTube y control multimedia"
    icon = "music"
    priority = 75
    
    def get_intents(self):
        return [
            {"tag": "musica_detectado", "patterns": ["música", "musica", "canción", "cancion", "video", "busca", "pon", "reproduce", "pausa"], "responses": ["..."]}
        ]

    def get_forced_patterns(self):
        return [
            (["música", "musica", "canción", "cancion", "video", "busca", "pon", "reproduce", "pausa", 
              "siguiente", "anterior", "play", "pause", "skip", "next", "previous",
              "youtube", "yt", "spotify"], 
             "musica_detectado")
        ]

    def can_handle(self, text: str, intent: str, confidence: float) -> bool:
        if intent == "musica_detectado":
            lower_text = text.lower()
            keywords = ["música", "musica", "canción", "cancion", "video", "busca", "pon", 
                       "reproduce", "pausa", "siguiente", "anterior", "youtube", "yt", "spotify"]
            return any(kw in lower_text for kw in keywords)
        return False

    def _parse_with_llm(self, text: str, schema: str, examples: str, llm_engine) -> dict:
        if not llm_engine:
            return {}
        prompt = f"""Analiza esta frase sobre música y determina si es una búsqueda o un control de reproducción.
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
            print(f"[Musica] Error parseando con LLM: {e}")
            return {}

    def _extract_query_from_text(self, text: str) -> str:
        """Extrae la query de búsqueda limpiando palabras comunes"""
        query = text.lower()
        stop_words = ["busca", "busca la", "busca en", "pon", "pon la", "pon un", 
                     "en youtube", "en yt", "youtube", "yt", "la", "el", "los", "las",
                     "canción", "cancion", "canción de", "cancion de", "video", "video de",
                     "de", "del", "para"]
        
        for word in stop_words:
            query = query.replace(word, " ")
        
        return query.strip()

    def _is_search_intent(self, text: str) -> bool:
        """Detecta si la frase es una búsqueda por palabras clave"""
        lower = text.lower()
        search_keywords = ["busca", "busca en", "pon", "busca la", "busca el", 
                          "quiero escuchar", "ponme", "reproduce", "búscame"]
        return any(kw in lower for kw in search_keywords)

    def handle(self, text: str, intent: str, context: dict) -> dict:
        lower_text = text.lower()
        brain = context.get('brain')
        llm = brain.llm if brain else None
        
        schema = '{"action": "search"|"play"|"pause"|"next"|"previous", "query": "string|null"}'
        examples = '''
        - "Busca la canción de friends en youtube de marshmallow" -> {"action": "search", "query": "friends marshmello"}
        - "Pon un video de gatos en youtube" -> {"action": "search", "query": "gatos"}
        - "Busca en youtube tutorial de python" -> {"action": "search", "query": "tutorial de python"}
        - "Pon música" -> {"action": "play", "query": null}
        - "Pausa la música" -> {"action": "pause", "query": null}
        - "Siguiente canción" -> {"action": "next", "query": null}
        - "Canción anterior" -> {"action": "previous", "query": null}
        - "Reproduce" -> {"action": "play", "query": null}
        '''
        
        command = self._parse_with_llm(lower_text, schema, examples, llm)
        
        # Si el LLM falló, usar heurística basada en palabras clave
        if not command:
            if self._is_search_intent(lower_text):
                query = self._extract_query_from_text(lower_text)
                if query:
                    return search_youtube(query)
                else:
                    return {"action": "music_error", "success": False, "context": "No entendí qué quieres buscar.", "raw_response": True}
            # Si no es búsqueda, detectar control por palabras
            if any(kw in lower_text for kw in ["pausa", "para", "stop", "detén"]):
                return pause_music()
            elif any(kw in lower_text for kw in ["siguiente", "skip", "next", "salta"]):
                return next_track()
            elif any(kw in lower_text for kw in ["anterior", "previous", "atrás", "atras"]):
                return previous_track()
            else:
                return play_music()
        
        action = command.get("action")
        query = command.get("query")
        
        if action == "search":
            if not query:
                query = self._extract_query_from_text(lower_text)
            if not query:
                return {"action": "music_error", "success": False, "context": "No entendí qué quieres buscar.", "raw_response": True}
            return search_youtube(query)
            
        elif action == "play":
            return play_music()
        elif action == "pause":
            return pause_music()
        elif action == "next":
            return next_track()
        elif action == "previous":
            return previous_track()
        
        return {"action": "unknown", "success": False, "context": "No entendí el comando de música."}