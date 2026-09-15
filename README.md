# Eco 🟣

Asistente de inteligencia artificial personal para Windows. Combina reconocimiento de voz, visión por computadora y un modelo de lenguaje local para automatizar tareas y mantener conversaciones naturales, **sin depender de APIs externas**.

## ✨ Características

- ️ **Control por voz** con Whisper.cpp (transcripción local)
- ️ **Visión por computadora** con MediaPipe (detección facial, gestos, cámara)
- 🧠 **LLM local** Qwen2.5-1.5B (conversaciones sin internet)
- ️ **Control del sistema**: volumen, brillo, apps, energía
- 📝 **Memoria persistente** y notas por voz
-  **13 plugins modulares** extensibles

## 🛠️ Stack

- **Frontend**: Tauri 2.0 (Rust) + React + TypeScript + Three.js
- **Backend**: Python 3.11 + FastAPI + WebSockets
- **IA**: Whisper.cpp, MediaPipe, Llama.cpp, Scikit-learn
- **Voz**: Edge TTS + pyttsx3

##  Instalación

Descarga el último instalador desde [Releases](link) y ejecútalo. No requiere configuración adicional.

## 🚀 Desarrollo

```bash
# Backend
cd backend
python -m venv venv_final
venv_final\Scripts\activate
pip install -r requirements.txt
python main.py

# Frontend
cd frontend
npm install
cargo tauri dev