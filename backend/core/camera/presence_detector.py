import cv2
import mediapipe as mp
import threading
import time


class PresenceDetector:
    def __init__(self, on_presence_change_callback=None):
        self.on_presence_change_callback = on_presence_change_callback
        self.is_active = False
        self.thread = None
        self.cap = None
        
        # Estado de presencia
        self.presence_detected = False
        self.last_presence_time = 0
        self.absence_timeout = 6.0  # 6 segundos sin detectar cara = ausencia
        self.presence_cooldown = 0
        
        # Inicializar MediaPipe Face Detection (usando el import explícito)
        self.mp_face_detection = mp.solutions.face_detection.FaceDetection(
            model_selection=0,
            min_detection_confidence=0.5
        )
        
    def start(self):
        if self.is_active:
            return "El detector de presencia ya está activo."
        
        self.is_active = True
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        
        if not self.cap.isOpened():
            self.is_active = False
            return "No se pudo acceder a la cámara del portátil."
        
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        self.thread = threading.Thread(target=self._run_detection_loop, daemon=True)
        self.thread.start()
        return "Detector de presencia activado."

    def stop(self):
        if not self.is_active:
            return "El detector de presencia ya estaba desactivado."
        
        self.is_active = False
        
        if self.thread:
            self.thread.join(timeout=2.0)
            self.thread = None
        if self.cap:
            self.cap.release()
            self.cap = None
        
        self.mp_face_detection.close()
        print("[PRESENCE] Detector detenido")
        return "Detector de presencia desactivado."

    def _run_detection_loop(self):
        print("[PRESENCE] Iniciando detección automática de presencia...")
        
        # Esperar 3 segundos para que la cámara se estabilice
        time.sleep(3)
        
        while self.is_active:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            frame = cv2.flip(frame, 1)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            results = self.mp_face_detection.process(frame_rgb)
            
            current_time = time.time()
            faces_detected = bool(results.detections)
            
            if faces_detected:
                self.last_presence_time = current_time
                
                if not self.presence_detected and current_time > self.presence_cooldown:
                    self.presence_detected = True
                    print("[PRESENCE] ✓ Persona detectada")
                    
                    if self.on_presence_change_callback:
                        try:
                            self.on_presence_change_callback(present=True)
                        except Exception as e:
                            print(f"[PRESENCE] Error en callback: {e}")
                    
                    self.presence_cooldown = current_time + 5.0
            else:
                time_since_last_presence = current_time - self.last_presence_time
                
                if self.presence_detected and time_since_last_presence > self.absence_timeout:
                    self.presence_detected = False
                    print("[PRESENCE] ✗ Persona ausente (6 segundos)")
                    
                    if self.on_presence_change_callback:
                        try:
                            self.on_presence_change_callback(present=False)
                        except Exception as e:
                            print(f"[PRESENCE] Error en callback: {e}")
                    
                    self.presence_cooldown = current_time + 5.0
            
            time.sleep(0.1)
        
        print("[PRESENCE] Bucle finalizado.")
    
    def is_present(self):
        return self.presence_detected