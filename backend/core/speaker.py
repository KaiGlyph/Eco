import os
import tempfile
import time
import threading
import asyncio
import subprocess
import socket
import sounddevice as sd
import soundfile as sf
import numpy as np
import edge_tts
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

DEFAULT_ASSISTANT_VOLUME = 80.0
AUDIO_DIR = os.path.join(os.path.dirname(__file__), '..', 'audio_files')
os.makedirs(AUDIO_DIR, exist_ok=True)

class Speaker:
    def __init__(self):
        self.engine = None  # pyttsx3 engine (offline)
        self.use_edge_tts = True  # Por defecto usa Edge TTS
        self.edge_voice = "es-ES-AlvaroNeural"  # Voz masculina española
        self.edge_rate = "+10%"  # Un poco más rápido (tipo Jarvis)
        self.assistant_volume = DEFAULT_ASSISTANT_VOLUME
        self.ws_send_func = None
        print(f"[Speaker] Inicializado. Volumen del asistente: {self.assistant_volume:.0f}%")

    def set_ws_send_func(self, func):
        """Establece la función para enviar mensajes WebSocket"""
        self.ws_send_func = func

    def _send_ws(self, msg: dict):
        """Envía un mensaje al frontend via WebSocket"""
        if self.ws_send_func:
            try:
                import main
                asyncio.run_coroutine_threadsafe(self.ws_send_func(msg), main.main_loop)
            except Exception as e:
                print(f"[Speaker] Error enviando WS: {e}")

    # ==========================================
    # MÉTODO PRINCIPAL DE HABLA
    # ==========================================
    def speak(self, text: str):
        """Habla usando el mejor motor disponible, con notificación al frontend"""
        if not text or not text.strip():
            return

        print(f"[Speaker] Preparando audio: {text[:80]}...")
        
        # 1. Notificar que empieza a hablar
        self._send_ws({"type": "state", "state": "speaking"})

        # 2. Generar audio y obtener URL
        audio_url = self._generate_edge_tts(text)
        
        if audio_url:
            # 3. Enviar URL al frontend para que la reproduzca y analice
            self._send_ws({"type": "audio_play", "url": audio_url})
            
            # 4. Reproducir localmente (para que también se escuche por los altavoces)
            self._play_audio_from_url(audio_url)
            
            # 5. Estimar duración para volver a idle (aprox 15 caracteres por segundo)
            estimated_duration = max(2.0, len(text) / 15)
            
            def reset_state():
                time.sleep(estimated_duration)
                self._send_ws({"type": "state", "state": "idle"})
            
            threading.Thread(target=reset_state, daemon=True).start()
        else:
            # Si falla Edge TTS, intentar con pyttsx3
            print("[Speaker] Edge TTS falló, intentando con pyttsx3...")
            self._speak_pyttsx3(text)
            self._send_ws({"type": "state", "state": "idle"})

    def _generate_edge_tts(self, text: str) -> str:
        """Genera audio con Edge TTS y lo guarda en audio_files/"""
        try:
            filename = f"eco_{int(time.time() * 1000)}.mp3"
            file_path = os.path.join(AUDIO_DIR, filename)
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                communicate = edge_tts.Communicate(
                    text=text,
                    voice=self.edge_voice,
                    rate=self.edge_rate,
                )
                loop.run_until_complete(communicate.save(file_path))
            finally:
                loop.close()
            
            return f"http://127.0.0.1:8000/audio/{filename}"
        except Exception as e:
            print(f"[Speaker] Error con Edge TTS: {e}")
            return None

    def _play_audio_from_url(self, url: str):
        """Reproduce el archivo de audio localmente con el volumen de Eco"""
        try:
            filename = url.split("/")[-1]
            file_path = os.path.join(AUDIO_DIR, filename)
            data, sample_rate = sf.read(file_path, dtype='float32')
            
            if data.ndim > 1:
                data = np.mean(data, axis=1)

            sd.play(data, sample_rate)
            # Aplicar volumen de sesión después de iniciar la reproducción
            time.sleep(0.05)
            self._apply_own_session_volume()
            sd.wait()
        except Exception as e:
            print(f"[Speaker] Error reproduciendo audio: {e}")

    def _speak_pyttsx3(self, text: str):
        """Genera y reproduce audio usando pyttsx3 (offline)"""
        try:
            if self.engine is None:
                import pyttsx3
                self.engine = pyttsx3.init()
                voices = self.engine.getProperty('voices')
                
                male_voice = None
                for voice in voices:
                    voice_name = voice.name.lower()
                    if any(name in voice_name for name in ['pablo', 'jorge', 'male', 'hombre']):
                        male_voice = voice.id
                        print(f"[Speaker] Voz masculina encontrada: {voice.name}")
                        break
                
                if not male_voice:
                    for voice in voices:
                        if 'spanish' in voice.name.lower() or 'español' in voice.name.lower():
                            male_voice = voice.id
                            print(f"[Speaker] Usando voz: {voice.name}")
                            break
                
                if male_voice:
                    self.engine.setProperty('voice', male_voice)
                
                self.engine.setProperty('rate', 170)
                self.engine.setProperty('volume', 0.95)
                print("[Speaker] Motor pyttsx3 inicializado.")
            
            self.engine.setProperty('volume', self.assistant_volume / 100.0)
            self.engine.say(text)
            self.engine.runAndWait()
                
        except Exception as e:
            print(f"[Speaker] Error con pyttsx3: {e}")

    # ==========================================
    # VOLUMEN DEL ASISTENTE (Eco)
    # ==========================================
    def get_assistant_volume(self) -> float:
        """Devuelve el volumen actual del asistente"""
        return self.assistant_volume

    def set_assistant_volume(self, percentage: float) -> float:
        """Establece el volumen del asistente (0-100)"""
        self.assistant_volume = max(0.0, min(100.0, percentage))
        print(f"[Speaker] Volumen del asistente ajustado a {self.assistant_volume:.0f}%")
        return self.assistant_volume

    def change_assistant_volume(self, direction: str, step: float = 10.0) -> float:
        """Cambia el volumen del asistente relativamente"""
        if direction == "up":
            new_volume = self.assistant_volume + step
        else:
            new_volume = self.assistant_volume - step
        return self.set_assistant_volume(new_volume)

    def _apply_own_session_volume(self):
        """Ajusta el volumen SOLO de la sesión de audio de Eco (independiente del sistema)."""
        try:
            pid = os.getpid()
            gain = self.assistant_volume / 100.0

            # La sesión se crea al abrir el stream; puede tardar un instante en aparecer
            for _ in range(10):
                sessions = AudioUtilities.GetAllSessions()
                for session in sessions:
                    if session.Process and session.Process.pid == pid:
                        session.SimpleAudioVolume.SetMasterVolume(gain, None)
                        return True
                time.sleep(0.02)
            return False
        except Exception as e:
            print(f"[Speaker] No se pudo ajustar el volumen de sesión: {e}")
            return False

    # ==========================================
    # VOLUMEN DEL SISTEMA
    # ==========================================
    @staticmethod
    def _get_system_volume() -> float:
        """Lee el volumen actual del sistema"""
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            return volume.GetMasterVolumeLevelScalar() * 100
        except Exception:
            return 50.0

    @staticmethod
    def _set_system_volume(percentage: float):
        """Establece el volumen del sistema"""
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            volume.SetMasterVolumeLevelScalar(percentage / 100.0, None)
        except Exception as e:
            print(f"[Speaker] Error ajustando volumen del sistema: {e}")
            Speaker._set_volume_powershell(percentage)

    @staticmethod
    def _set_volume_powershell(percentage: float):
        """Fallback: establece el volumen usando teclas de Windows"""
        try:
            subprocess.run([
                'powershell', '-NoProfile', '-WindowStyle', 'Hidden', '-Command',
                '$wshell = New-Object -ComObject WScript.Shell; '
                '1..50 | ForEach-Object { $wshell.SendKeys([char]174) }'
            ], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW, timeout=3)
            
            steps = max(0, min(50, int(percentage / 2)))
            if steps > 0:
                subprocess.run([
                    'powershell', '-NoProfile', '-WindowStyle', 'Hidden', '-Command',
                    f'$wshell = New-Object -ComObject WScript.Shell; '
                    f'1..{steps} | ForEach-Object {{ $wshell.SendKeys([char]175) }}'
                ], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW, timeout=3)
        except Exception as e:
            print(f"[Speaker] Error en fallback PowerShell: {e}")

    # ==========================================
    # VOLUMEN POR APLICACIÓN
    # ==========================================
    @staticmethod
    def get_app_volume(app_name: str) -> float:
        """Obtiene el volumen de una aplicación específica"""
        try:
            sessions = AudioUtilities.GetAllSessions()
            for session in sessions:
                if session.Process:
                    process_name = session.Process.name().lower()
                    if app_name.lower() in process_name:
                        vol = session.SimpleAudioVolume.GetMasterVolume()
                        return vol * 100
            return -1  # Aplicación no encontrada
        except Exception as e:
            print(f"[Speaker] Error obteniendo volumen de {app_name}: {e}")
            return -1

    @staticmethod
    def set_app_volume(app_name: str, percentage: float) -> str:
        """Establece el volumen de una aplicación específica"""
        try:
            sessions = AudioUtilities.GetAllSessions()
            found = False
            for session in sessions:
                if session.Process:
                    process_name = session.Process.name().lower()
                    if app_name.lower() in process_name:
                        session.SimpleAudioVolume.SetMasterVolume(percentage / 100.0, None)
                        found = True
            if found:
                return f"Volumen de {app_name} establecido al {percentage:.0f}%"
            else:
                return f"No encontré la aplicación '{app_name}' ejecutándose."
        except Exception as e:
            return f"Error ajustando volumen de {app_name}: {e}"

    @staticmethod
    def mute_app(app_name: str) -> str:
        """Silencia una aplicación específica"""
        try:
            sessions = AudioUtilities.GetAllSessions()
            found = False
            for session in sessions:
                if session.Process:
                    process_name = session.Process.name().lower()
                    if app_name.lower() in process_name:
                        session.SimpleAudioVolume.SetMute(1, None)
                        found = True
            if found:
                return f"{app_name} silenciado."
            else:
                return f"No encontré la aplicación '{app_name}' ejecutándose."
        except Exception as e:
            return f"Error silenciando {app_name}: {e}"

    @staticmethod
    def list_audio_sessions() -> list:
        """Lista todas las aplicaciones con sesión de audio activa"""
        try:
            sessions = AudioUtilities.GetAllSessions()
            apps = []
            for session in sessions:
                if session.Process:
                    process_name = session.Process.name()
                    vol = session.SimpleAudioVolume.GetMasterVolume() * 100
                    muted = session.SimpleAudioVolume.GetMute()
                    apps.append({
                        'name': process_name,
                        'volume': vol,
                        'muted': bool(muted)
                    })
            return apps
        except Exception as e:
            print(f"[Speaker] Error listando sesiones: {e}")
            return []

    def set_voice(self, engine: str, voice: str = None):
        """Cambia el motor de voz"""
        if engine == "edge":
            self.use_edge_tts = True
            if voice:
                self.edge_voice = voice
        elif engine == "pyttsx3":
            self.use_edge_tts = False
        print(f"[Speaker] Motor cambiado a: {engine}")


# Instancia global
speaker = Speaker()