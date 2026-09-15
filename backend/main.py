from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import uvicorn
import json
import asyncio
import psutil
import os
import time
from datetime import datetime
from core.listener import Listener
from core.brain import Brain
from core.speaker import speaker
from core.camera import (
    get_available_cameras, capture_snapshot, MotionDetector, 
    PresenceDetector, GestureControl, OverlayWindow, vision_engine, AirDrawing,
)
from plugins.mouse import get_mouse_speed_percentage
from plugins.system import get_current_volume, get_current_brightness, initialize_volume_cache
from plugins.timer import active_timers

app = FastAPI(title="Eco Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir archivos de audio generados
AUDIO_DIR = os.path.join(os.path.dirname(__file__), 'audio_files')
os.makedirs(AUDIO_DIR, exist_ok=True)
app.mount("/audio", StaticFiles(directory=AUDIO_DIR), name="audio_files")

# ==========================================
# SERVIDOR DE ARCHIVOS ESTÁTICOS
# ==========================================

# Carpeta raíz de camera_files
CAMERA_DIR = os.path.join(os.path.dirname(__file__), 'camera_files')
os.makedirs(CAMERA_DIR, exist_ok=True)

# Subcarpeta para fotos explícitas
FOTOS_DIR = os.path.join(CAMERA_DIR, 'fotos')
os.makedirs(FOTOS_DIR, exist_ok=True)
app.mount("/camera/fotos", StaticFiles(directory=FOTOS_DIR), name="camera_fotos")

# Subcarpeta para videos
VIDEOS_DIR = os.path.join(CAMERA_DIR, 'videos')
os.makedirs(VIDEOS_DIR, exist_ok=True)
app.mount("/camera/videos", StaticFiles(directory=VIDEOS_DIR), name="camera_videos")

# Subcarpeta para frames de movimiento (dentro de videos)
MOTION_FRAMES_DIR = os.path.join(VIDEOS_DIR, 'motion_frames')
os.makedirs(MOTION_FRAMES_DIR, exist_ok=True)
app.mount("/camera/videos/motion_frames", StaticFiles(directory=MOTION_FRAMES_DIR), name="motion_frames")

active_connections: list[WebSocket] = []
brain = Brain()
main_loop = None

# Control del estado del chat
chat_is_open = False

# Instancias de opciones camara
motion_detector = MotionDetector(on_motion_detected_callback=None)
presence_detector = PresenceDetector(on_presence_change_callback=None) 
gesture_control = GestureControl()
overlay_window = OverlayWindow()
air_drawing = AirDrawing()

NOTES_FILE = os.path.join(os.path.dirname(__file__), 'data', 'notes.json')

def _load_notes_safe() -> list:
    if not os.path.exists(NOTES_FILE):
        return []
    try:
        with open(NOTES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []

def get_system_state() -> dict:
    try:
        volume = get_current_volume()
    except Exception:
        volume = 50.0
    
    try:
        brightness = get_current_brightness()
    except Exception:
        brightness = 75.0
    
    try:
        mouse_speed = get_mouse_speed_percentage()
    except Exception:
        mouse_speed = 50.0
    
    try:
        hardware = {
            "cpu": psutil.cpu_percent(interval=0.5),
            "ram": psutil.virtual_memory().percent,
            "disk": psutil.disk_usage('C:\\').percent,
            "battery": None
        }
        battery = psutil.sensors_battery()
        if battery:
            hardware["battery"] = battery.percent
    except Exception:
        hardware = {"cpu": 0, "ram": 0, "disk": 0, "battery": None}
    
    try:
        timers_list = []
        now = datetime.now()
        for tid, info in active_timers.items():
            remaining = (info['end_time'] - now).total_seconds()
            if remaining > 0:
                timers_list.append({
                    "id": tid, "label": info.get('label', ''), "type": info.get('type', 'timer'),
                    "remaining_seconds": int(remaining), "end_time": info['end_time'].isoformat()
                })
    except Exception:
        timers_list = []
    
    try:
        notes = _load_notes_safe()
        notes_count = len(notes)
        recent_notes = notes[-3:][::-1]
    except Exception:
        notes_count = 0
        recent_notes = []
    
    return {
        "volume": volume, "brightness": brightness, "mouse_speed": mouse_speed,
        "hardware": hardware, "timers": timers_list, "notes_count": notes_count, "recent_notes": recent_notes
    }

async def send_ws_message(msg: dict):
    """Envía un mensaje a todos los clientes WebSocket conectados"""
    for connection in active_connections[:]:
        try:
            await connection.send_text(json.dumps(msg))
        except Exception:
            if connection in active_connections:
                active_connections.remove(connection)

def handle_chat_state(is_open: bool):
    """Actualiza el estado del chat y controla la escucha de voz"""
    global chat_is_open
    chat_is_open = is_open
    if is_open:
        print("[INFO] Chat abierto - Escucha de voz pausada")
    else:
        print("[INFO] Chat cerrado - Escucha de voz reanudada")


def handle_voice_input(text: str):
    """Procesa la entrada de voz del micrófono"""
    global chat_is_open
    
    if chat_is_open:
        print(f"[INFO] Voz ignorada (chat abierto): {text}")
        return
    
    try:
        print(f"[INFO] Voz recibida: {text}")
        response = brain.process(text)
        print(f"[INFO] Respuesta del brain: {response}")
        
        camera_image_url = None
        response_text = response
        
        if isinstance(response, dict):
            camera_image_url = response.get('camera_image')
            response_text = response.get('context', response)
        
        msg = {
            "type": "conversation", 
            "user": text, 
            "eco": response_text
        }
        
        if camera_image_url:
            msg["camera_image"] = camera_image_url
            print(f"[INFO] Enviando imagen de cámara al frontend: {camera_image_url}")
        
        asyncio.run_coroutine_threadsafe(
            send_ws_message(msg),
            main_loop
        )
    except Exception as e:
        print(f"[ERROR] en handle_voice_input: {e}")

#  Función que se ejecuta cuando el detector ve movimiento
def handle_motion_detected(frame, video_url=None):
    """Se ejecuta cuando el detector de movimiento ve algo"""
    global chat_is_open
    
    if chat_is_open:
        print("[MOTION] Movimiento ignorado (chat abierto)")
        return
    
    print("[MOTION] ¡Movimiento detectado! Ejecutando acción...")
    
    # Pausar detector de presencia temporalmente
    if presence_detector.is_active:
        print("[PRESENCE] Pausado temporalmente por detector de movimiento")
        presence_detector.is_active = False
    
    alert_msg = {
        "type": "motion_alert",
        "message": "He detectado movimiento. Video guardado en la galería.",
        "motion_video": video_url
    }
    
    if main_loop and main_loop.is_running():
        asyncio.run_coroutine_threadsafe(send_ws_message(alert_msg), main_loop)

def handle_camera_request():
    """Busca una cámara y toma una foto"""
    print("[CAMERA] Buscando cámaras disponibles...")
    cameras = get_available_cameras()

     # Reanudar detector de presencia si estaba pausado
    if not presence_detector.is_active and not motion_detector.is_active:
        print("[PRESENCE] Reanudando detector de presencia")
        presence_detector.is_active = True
    
    if not cameras:
        print("[CAMERA] No se detectó ninguna cámara")
        return {"success": False, "message": "No se detectó ninguna cámara conectada."}
    
    print(f"[CAMERA] Cámaras detectadas en índices: {cameras}")
    image_url = capture_snapshot(camera_index=cameras[0])
    
    if image_url:
        print(f"[CAMERA] Foto capturada: {image_url}")
        return {"success": True, "url": image_url, "message": "Cámara activada y foto capturada."}
    else:
        print("[CAMERA] Error al capturar la imagen")
        return {"success": False, "message": "Error al capturar la imagen."}

def handle_presence_actions(present: bool):
    """Ejecuta acciones automáticas basadas en la presencia"""
    print(f"[PRESENCE] Ejecutando acciones: present={present}")
    
    if present:
        # Alguien volvió: restaurar brillo y reanudar música
        try:
            from plugins.system import set_brightness_absolute
            set_brightness_absolute(75)
            print("[PRESENCE] Brillo restaurado al 75%")
        except Exception as e:
            print(f"[PRESENCE] Error al ajustar brillo: {e}")
        
        try:
            from plugins.musica.plugin import play_music
            play_music()
            print("[PRESENCE] Música reanudada")
        except Exception as e:
            print(f"[PRESENCE] Error al reanudar música: {e}")
        
        alert_msg = {
            "type": "presence_alert",
            "message": "Veo que has vuelto. Brillo restaurado y música reanudada.",
            "action": "presence_detected"
        }
    else:
        # Nadie: bajar brillo + pausar música
        try:
            from plugins.system import set_brightness_absolute
            set_brightness_absolute(20)
            print("[PRESENCE] Brillo reducido al 20%")
        except Exception as e:
            print(f"[PRESENCE] Error al ajustar brillo: {e}")
        
        try:
            from plugins.musica.plugin import pause_music
            pause_music()
            print("[PRESENCE] Música pausada a nivel de sistema")
        except Exception as e:
            print(f"[PRESENCE] Error al pausar música: {e}")
        
        alert_msg = {
            "type": "presence_alert",
            "message": "No hay nadie. Brillo reducido y música pausada.",
            "action": "absence_detected"
        }
    
    if main_loop and main_loop.is_running():
        asyncio.run_coroutine_threadsafe(send_ws_message(alert_msg), main_loop)


async def periodic_state_update():
    while True:
        await asyncio.sleep(5)
        if active_connections:
            try:
                state = get_system_state()
                await send_ws_message({"type": "state_update", **state})
            except Exception:
                pass

@app.on_event("startup")
async def startup_event():
    global main_loop
    main_loop = asyncio.get_running_loop()
    
    initialize_volume_cache()
    speaker.set_ws_send_func(send_ws_message)
    
    motion_detector.on_motion_detected_callback = handle_motion_detected
    presence_detector.on_presence_change_callback = handle_presence_actions  # ← Cambiado
    
    # Arrancar detector de presencia automáticamente
    print("[PRESENCE] Arrancando detector de presencia automáticamente...")
    presence_detector.start()
    
    listener = Listener(on_text_received=handle_voice_input)
    listener.start()
    asyncio.create_task(periodic_state_update())


@app.get("/")
async def root():
    return {"message": "Eco está despierta"}

# ==========================================
# ENDPOINTS PARA GALERÍA MULTIMEDIA
# ==========================================

@app.get("/api/gallery/photos")
async def get_gallery_photos():
    """Devuelve lista de todas las fotos explícitas"""
    photos_dir = os.path.join(os.path.dirname(__file__), 'camera_files', 'fotos')  # CAMBIO: fotos
    os.makedirs(photos_dir, exist_ok=True)
    
    photos = []
    for filename in os.listdir(photos_dir):
        if filename.startswith('eco_cam_') and filename.endswith('.jpg'):
            filepath = os.path.join(photos_dir, filename)
            timestamp = os.path.getmtime(filepath)
            photos.append({
                "id": filename,
                "url": f"http://127.0.0.1:8000/camera/fotos/{filename}",  # CAMBIO: /fotos
                "timestamp": datetime.fromtimestamp(timestamp).isoformat(),
                "type": "photo"
            })
    
    photos.sort(key=lambda x: x['timestamp'], reverse=True)
    return {"photos": photos}

@app.get("/api/gallery/videos")
async def get_gallery_videos():
    """Devuelve lista de todos los videos de movimiento"""
    videos_dir = os.path.join(os.path.dirname(__file__), 'camera_files', 'videos')
    os.makedirs(videos_dir, exist_ok=True)
    
    videos = []
    for filename in os.listdir(videos_dir):
        if filename.startswith('eco_motion_') and filename.endswith('.webm'):  # CAMBIO: solo .webm
            filepath = os.path.join(videos_dir, filename)
            timestamp = os.path.getmtime(filepath)
            videos.append({
                "id": filename,
                "url": f"http://127.0.0.1:8000/camera/videos/{filename}",
                "timestamp": datetime.fromtimestamp(timestamp).isoformat(),
                "type": "video"
            })
    
    videos.sort(key=lambda x: x['timestamp'], reverse=True)
    return {"videos": videos}

@app.get("/api/gallery/motion-frames")
async def get_motion_frames():
    """Devuelve lista de todos los frames de movimiento detectado"""
    frames_dir = os.path.join(os.path.dirname(__file__), 'camera_files', 'motion_frames')
    os.makedirs(frames_dir, exist_ok=True)
    
    frames = []
    for filename in os.listdir(frames_dir):
        if filename.startswith('eco_motion_') and filename.endswith('.jpg'):
            filepath = os.path.join(frames_dir, filename)
            timestamp = os.path.getmtime(filepath)
            frames.append({
                "id": filename,
                "url": f"http://127.0.0.1:8000/camera/motion_frames/{filename}",
                "timestamp": datetime.fromtimestamp(timestamp).isoformat(),
                "type": "motion_frame"
            })
    
    frames.sort(key=lambda x: x['timestamp'], reverse=True)
    return {"frames": frames}

@app.get("/api/morse/state")
async def get_morse_state():
    """Devuelve el estado actual del decodificador Morse"""
    # Usamos la instancia global 'gesture_control' que ya está definida arriba
    if gesture_control.is_active and gesture_control.morse_mode:
        return gesture_control.morse_decoder.get_state()
    else:
        return {
            "sequence": "", 
            "current_word": "", 
            "full_text": "", 
            "active": False
        }

@app.websocket("/ws/camera/stream")
async def camera_stream_endpoint(websocket: WebSocket):
    await websocket.accept()
    import cv2
    import base64
    
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            _, buffer = cv2.imencode('.jpg', frame)
            frame_base64 = base64.b64encode(buffer).decode('utf-8')
            
            await websocket.send_json({
                "type": "frame",
                "data": frame_base64
            })
            
            await asyncio.sleep(0.033)
    except WebSocketDisconnect:
        print("[STREAM] Cliente desconectado del stream de cámara")
    except Exception as e:
        print(f"[STREAM] Error en stream: {e}")
    finally:
        cap.release()
        try:
            await websocket.close()
        except:
            pass
# ==========================================
# ENDPOINT PARA DIBUJO EN EL AIRE
# ==========================================

@app.websocket("/ws/drawing")
async def drawing_endpoint(websocket: WebSocket):
    await websocket.accept()
    air_drawing.add_client(websocket)
    print(f"[DRAWING] Cliente conectado. Total: {len(air_drawing.clients)}")
    
    if not air_drawing.is_active:
        air_drawing._loop = asyncio.get_event_loop()
        air_drawing.start()
    
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            if msg.get('type') == 'stop_drawing':
                print("[DRAWING] Cliente solicitó detener")
                break
    except WebSocketDisconnect:
        print("[DRAWING] Cliente desconectado del dibujo")
    except Exception as e:
        print(f"[DRAWING] Error o desconexión: {e}")
    finally:
        air_drawing.remove_client(websocket)
        try:
            await websocket.close()
        except:
            pass

# ==========================================
# WEBSOCKET PRINCIPAL
# ==========================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    print(f"[INFO] Cliente conectado. Total conexiones: {len(active_connections)}")
    
    initial_state = get_system_state()
    try:
        await websocket.send_text(json.dumps({"type": "state_update", **initial_state}))
    except:
        pass
    
    try:
        while True:
            data = await websocket.receive_text()
            data_json = json.loads(data)
            
            if data_json.get("type") == "chat_state":
                is_open = data_json.get("is_open", False)
                handle_chat_state(is_open)
                continue
            
            if data_json.get("type") == "camera_request":
                print("[INFO] Solicitud de cámara recibida desde el frontend")
                try: await websocket.send_text(json.dumps({"type": "state", "state": "thinking"}))
                except: pass
                
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, handle_camera_request)
                
                if result["success"]:
                    try:
                        await websocket.send_text(json.dumps({"type": "camera_result", "image_url": result["url"], "message": result["message"]}))
                        await websocket.send_text(json.dumps({"type": "state", "state": "speaking"}))
                        await asyncio.sleep(1)
                    except: pass
                else:
                    try: await websocket.send_text(json.dumps({"type": "camera_error", "message": result["message"]}))
                    except: pass
                
                try: await websocket.send_text(json.dumps({"type": "state", "state": "idle"}))
                except: pass
                continue
            
            if data_json.get("type") == "voice":
                text = data_json.get("text", "")
                print(f"[INFO] Comando del frontend: {text}")
                
                try: await websocket.send_text(json.dumps({"type": "state", "state": "thinking"}))
                except: pass
                
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(None, brain.process, text)
                
                try:
                    await websocket.send_text(json.dumps({"type": "conversation", "user": text, "eco": response}))
                    await websocket.send_text(json.dumps({"type": "state", "state": "speaking"}))
                    await asyncio.sleep(2)
                    await websocket.send_text(json.dumps({"type": "state", "state": "idle"}))
                except:
                    pass
                
    except WebSocketDisconnect:
        print("[INFO] Cliente desconectado del WebSocket principal")
    except Exception as e:
        print(f"[ERROR] WebSocket error: {e}")
    finally:
        if websocket in active_connections:
            active_connections.remove(websocket)
        print(f"[INFO] Conexiones activas restantes: {len(active_connections)}")


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)