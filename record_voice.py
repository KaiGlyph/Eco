import sounddevice as sd
import numpy as np
import soundfile as sf
import os

SAMPLE_RATE = 16000  # XTTS usa 22050 Hz
DURATION = 5        # 15 segundos es suficiente
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), 'backend', 'data', 'my_voice.wav')

def record_voice():
    print(f"Grabando {DURATION} segundos de audio...")
    print("Lee este texto en voz alta y clara, con naturalidad:")
    print("'Hola, soy Eco. Esta es mi voz clonada. Puedo ayudarte con muchas cosas: controlar el volumen, el brillo, " \
    "poner temporizadores, buscar en internet, y mucho más. Estoy aquí para hacer tu vida más fácil.'")
    input("Pulsa ENTER cuando estés listo para grabar...")
    
    print("GRABANDO... Habla ahora.")
    
    audio = sd.rec(
        int(DURATION * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype='float32'
    )
    sd.wait()
    
    print("Grabación terminada.")
    
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    sf.write(OUTPUT_FILE, audio, SAMPLE_RATE)
    print(f"Voz guardada en: {OUTPUT_FILE}")

if __name__ == "__main__":
    record_voice()