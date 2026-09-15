import cv2
import mediapipe as mp
import threading
import time
import json
import asyncio

class AirDrawing:
    """Stream de landmarks de manos para dibujo en el aire"""
    
    def __init__(self):
        self.is_active = False
        self.thread = None
        self.cap = None
        self.clients = []
        self._loop = None
        
        # MediaPipe Hands
        self.mp_hands = mp.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )

    def start(self):
        if self.is_active:
            return
        
        self.is_active = True
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        
        if not self.cap.isOpened():
            self.is_active = False
            return
        
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        self.thread = threading.Thread(target=self._stream_loop, daemon=True)
        self.thread.start()
        print("[DRAWING] Stream de dibujo iniciado")

    def stop(self):
        self.is_active = False
        if self.thread:
            self.thread.join(timeout=2.0)
        if self.cap:
            self.cap.release()
        self.mp_hands.close()
        print("[DRAWING] Stream de dibujo detenido")

    def add_client(self, websocket):
        self.clients.append(websocket)

    def remove_client(self, websocket):
        if websocket in self.clients:
            self.clients.remove(websocket)

    async def broadcast(self, data: dict):
        """Envía datos a todos los clientes conectados"""
        if not self.clients:
            return
        
        message = json.dumps(data)
        disconnected = []
        
        for client in self.clients:
            try:
                await client.send_text(message)
            except Exception:
                disconnected.append(client)
        
        for client in disconnected:
            self.clients.remove(client)

    def _stream_loop(self):
        """Bucle principal: detecta manos y envía landmarks"""
        while self.is_active:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            # Voltear horizontalmente (efecto espejo)
            frame = cv2.flip(frame, 1)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            results = self.mp_hands.process(frame_rgb)
            
            if results.multi_hand_landmarks:
                hand_landmarks = results.multi_hand_landmarks[0].landmark
                
                # Detectar si el índice está extendido (para dibujar)
                index_tip = hand_landmarks[8]
                index_pip = hand_landmarks[6]
                middle_tip = hand_landmarks[12]
                middle_pip = hand_landmarks[10]
                
                # Índice extendido si la punta está más arriba que el PIP
                index_extended = index_tip.y < index_pip.y
                # Medio recogido (para evitar dibujar accidentalmente con la mano abierta)
                middle_curled = middle_tip.y > middle_pip.y
                
                is_drawing = index_extended and middle_curled
                
                data = {
                    'type': 'hand_landmarks',
                    'is_drawing': is_drawing,
                    'index_tip': {'x': index_tip.x, 'y': index_tip.y}
                }
                
                # Enviar a todos los clientes de forma segura desde el thread
                if self._loop:
                    asyncio.run_coroutine_threadsafe(
                        self.broadcast(data),
                        self._loop
                    )
            
            time.sleep(0.033)  # ~30 FPS