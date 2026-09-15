import sys
import os
import threading
import time
import tempfile
import subprocess
import numpy as np
import sounddevice as sd
import soundfile as sf

# Importamos la función maestra de rutas
from core.utils import get_resource_path

# Ahora las rutas apuntan exactamente a donde PyInstaller extrae los archivos
WHISPER_EXE = get_resource_path('whisper-cli.exe')
WHISPER_MODEL = get_resource_path('ggml-base.bin')

print(f"[Whisper] Ruta base detectada: {os.path.dirname(WHISPER_EXE)}")
print(f"[Whisper] EXE existe: {os.path.exists(WHISPER_EXE)}")
print(f"[Whisper] Modelo existe: {os.path.exists(WHISPER_MODEL)}")


class Listener:
    def __init__(self, on_text_received):
        self.on_text_received = on_text_received
        self.listening = False
        self.thread = None
        
        # Configuración de audio
        self.sample_rate = 16000  # Whisper requiere 16kHz
        self.channels = 1
        self.chunk_duration = 0.1  # 100ms por chunk
        
        # Configuración de detección de voz
        self.pause_threshold = 2.0  # Reducido a 2.0s para respuesta más rápida
        self.silence_threshold = 200  # Umbral de energía para detectar voz
        self.min_phrase_duration = 0.5  # Duración mínima de una frase válida
        
        # Verificar que whisper.cpp está disponible
        self._check_whisper()
        
        print(f"Micrófono inicializado (sounddevice). Sample rate: {self.sample_rate}Hz")
        print(f"Tiempo de pausa configurado: {self.pause_threshold} segundos")
        print(f"Umbral de silencio: {self.silence_threshold}")

    def _check_whisper(self):
        """Verifica que whisper.cpp y el modelo estén disponibles"""
        if not os.path.exists(WHISPER_EXE):
            print(f"⚠️  AVISO: No se encontró whisper-cli.exe en: {WHISPER_EXE}")
        else:
            print(f"✅ whisper-cli.exe encontrado")
        
        if not os.path.exists(WHISPER_MODEL):
            print(f"⚠️  AVISO CRÍTICO: No se encontró el modelo en: {WHISPER_MODEL}")
            print("   Descárgalo de: https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin")
        else:
            print(f"✅ Modelo whisper '{os.path.basename(WHISPER_MODEL)}' cargado")

    def _get_audio_energy(self, audio_data: np.ndarray) -> float:
        """Calcula la energía (RMS) de un fragmento de audio"""
        return np.sqrt(np.mean(audio_data.astype(np.float32) ** 2))

    def _listen_loop(self):
        """Bucle principal de escucha usando sounddevice"""
        self.listening = True
        print("🎙️ Eco está escuchando...")
        
        audio_buffer = []
        is_speaking = False
        silence_duration = 0.0
        phrase_duration = 0.0
        
        def audio_callback(indata, frames, time_info, status):
            nonlocal audio_buffer, is_speaking, silence_duration, phrase_duration
            
            # CAMBIO 2: Manejar overflow de sounddevice para evitar que se cuelgue
            if status and status.input_overflow:
                print("[AUDIO] ⚠️ Buffer desbordado (overflow). Reiniciando captura limpia...")
                audio_buffer = []
                is_speaking = False
                silence_duration = 0.0
                phrase_duration = 0.0
                return  # Descartar este chunk corrupto y esperar el siguiente
            
            if status:
                print(f"[AUDIO] Status: {status}")
            
            # Convertir a mono si es necesario
            audio_chunk = indata[:, 0] if indata.ndim > 1 else indata.flatten()
            energy = self._get_audio_energy(audio_chunk)
            
            chunk_duration = len(audio_chunk) / self.sample_rate
            
            if energy > self.silence_threshold:
                # Hay voz
                if not is_speaking:
                    print(f"[AUDIO] Detectada voz (energía: {energy:.0f})")
                is_speaking = True
                silence_duration = 0.0
                phrase_duration += chunk_duration
                audio_buffer.append(audio_chunk.copy())
            else:
                # Silencio
                if is_speaking:
                    silence_duration += chunk_duration
                    audio_buffer.append(audio_chunk.copy())
                    
                    # Si el silencio supera el threshold, procesar la frase
                    if silence_duration >= self.pause_threshold:
                        if phrase_duration >= self.min_phrase_duration:
                            print(f"[AUDIO] Frase detectada ({phrase_duration:.1f}s), procesando...")
                            # Procesar el audio capturado en un hilo separado
                            threading.Thread(
                                target=self._process_audio, 
                                args=(audio_buffer.copy(),), 
                                daemon=True
                            ).start()
                        
                        # Resetear estado
                        audio_buffer = []
                        is_speaking = False
                        silence_duration = 0.0
                        phrase_duration = 0.0
        
        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype='int16',
                blocksize=int(self.sample_rate * self.chunk_duration),
                callback=audio_callback
            ):
                while self.listening:
                    sd.sleep(100)
        except Exception as e:
            print(f"Error en el stream de audio: {e}")
            import traceback
            traceback.print_exc()

    def _process_audio(self, audio_buffer: list):
        """Procesa el audio capturado usando whisper.cpp"""
        tmp_path = None
        try:
            # Concatenar todos los chunks
            audio_data = np.concatenate(audio_buffer)
            
            # Guardar como WAV temporal
            tmp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            tmp_path = tmp_file.name
            tmp_file.close()
            
            sf.write(tmp_path, audio_data, self.sample_rate, subtype='PCM_16')
            
            print("[AUDIO] Procesando con whisper.cpp...")
            
            # CAMBIO 3: Parámetros optimizados para velocidad (modelo base)
            # Eliminamos --best-of y --beam-size porque ralentizan mucho sin aportar valor en comandos cortos
            result = subprocess.run(
                [
                    WHISPER_EXE,
                    "-m", WHISPER_MODEL,
                    "-f", tmp_path,
                    "-l", "es",
                    "-nt",          # Sin timestamps
                    "-t", "4",       # 4 threads (suficiente y rápido)
                    "--prompt", "Eco asistente de voz comandos de sistema"  # Contexto corto
                ],
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=30  # Reducido a 30s. Si tarda más, algo va muy mal.
            )
            
            # Extraer la transcripción
            text = self._parse_whisper_output(result.stdout)
            
            if text:
                print(f"✅ Escuchado: '{text}'")
                self.on_text_received(text)
            else:
                print("[AUDIO] No se pudo entender el audio o estaba vacío")
                if result.stderr and 'error' in result.stderr.lower():
                    print(f"[AUDIO] Error de whisper: {result.stderr[:300]}")
            
        except subprocess.TimeoutExpired:
            print("[AUDIO] ⏱️ whisper.cpp tardó demasiado (>30s), omitiendo.")
        except FileNotFoundError:
            print(f"[AUDIO] ❌ ERROR: No se encontró whisper-cli.exe en: {WHISPER_EXE}")
        except Exception as e:
            print(f"Error inesperado procesando audio: {e}")
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass

    def _parse_whisper_output(self, output: str) -> str:
        """Extrae el texto transcrito de la salida de whisper.cpp"""
        if not output:
            return ""
        
        lines = output.strip().split('\n')
        
        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue
            
            # Si tiene timestamps, extraer solo el texto
            if ']  ' in line or '] ' in line:
                parts = line.split(']  ', 1)
                if len(parts) == 2:
                    text = parts[1].strip()
                    if text and not text.startswith('['):
                        return text
            
            # Si no tiene timestamps, usar la línea directamente
            if not line.startswith('whisper_') and not line.startswith('main:') and not line.startswith('system_info:'):
                if len(line) > 3:
                    return line
        
        return ""

    def start(self):
        """Inicia la escucha en un hilo separado"""
        self.thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.thread.start()

    def stop(self):
        """Detiene la escucha"""
        self.listening = False
        if self.thread:
            self.thread.join(timeout=2)