from flask import Flask, request, send_file
from flask_cors import CORS
from TTS.api import TTS
import tempfile
import os
import torch

app = Flask(__name__)
CORS(app)

# Configuración
USE_GPU = torch.cuda.is_available()
VOICE_REF = os.path.join(os.path.dirname(__file__), 'backend', 'data', 'my_voice.wav')
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'backend', 'data', 'tts_output')

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Cargar modelo XTTS v2
print("Cargando modelo XTTS v2 (esto puede tardar 1-2 minutos la primera vez)...")
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
if USE_GPU:
    tts.to("cuda")
    print("Modelo cargado en GPU (GTX 1050)")
else:
    print("Modelo cargado en CPU")

@app.route('/tts', methods=['POST'])
def text_to_speech():
    data = request.json
    text = data.get('text', '')
    
    if not text:
        return {'error': 'No text provided'}, 400
    
    if not os.path.exists(VOICE_REF):
        return {'error': 'Voice reference not found'}, 404
    
    output_file = os.path.join(OUTPUT_DIR, 'output.wav')
    
    try:
        tts.tts_to_file(
            text=text,
            speaker_wav=VOICE_REF,
            language="es",
            file_path=output_file
        )
        return send_file(output_file, mimetype='audio/wav')
    except Exception as e:
        return {'error': str(e)}, 500

@app.route('/health', methods=['GET'])
def health():
    return {'status': 'ok', 'gpu': USE_GPU, 'model': 'xtts_v2'}

if __name__ == '__main__':
    print("Servidor TTS iniciado en http://localhost:5000")
    app.run(host='0.0.0.0', port=5000)