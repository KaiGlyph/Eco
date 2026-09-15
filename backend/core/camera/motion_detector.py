import cv2
import threading
import time
import os
from datetime import datetime

class MotionDetector:
    def __init__(self, on_motion_detected_callback=None):
        self.on_motion_detected_callback = on_motion_detected_callback
        self.is_active = False
        self.thread = None
        self.cap = None
        self.cooldown = False
        self.last_motion_time = 0
        self.cooldown_seconds = 10
        self.motion_count = 0
        
        # Para grabación de video
        self.recording = False
        self.record_thread = None
        self.video_writer = None
        self.record_duration = 30
        
    def start(self):
        if self.is_active:
            return "La detección de movimiento ya está activa."
        
        self.is_active = True
        self.motion_count = 0
        
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        
        if not self.cap.isOpened():
            self.is_active = False
            return "No se pudo acceder a la cámara del portátil."
        
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        self.thread = threading.Thread(target=self._run_detection_loop, daemon=True)
        self.thread.start()
        return "Modo vigilia activado. Estoy observando la habitación."

    def stop(self):
        if not self.is_active:
            return "La detección de movimiento ya estaba desactivada."
        
        self.is_active = False
        
        if self.recording:
            self.recording = False
            if self.video_writer:
                self.video_writer.release()
                self.video_writer = None
        
        if self.thread:
            self.thread.join(timeout=2.0)
            self.thread = None
        if self.cap:
            self.cap.release()
            self.cap = None
        
        print(f"[MOTION] Total de movimientos detectados: {self.motion_count}")
        return "Modo vigilia desactivado."

    def _run_detection_loop(self):
        print("[MOTION] Iniciando bucle de detección...")
        
        ret, frame1 = self.cap.read()
        if not ret:
            print("[MOTION] Error al leer el frame inicial")
            self.is_active = False
            return

        prev_gray = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
        prev_gray = cv2.GaussianBlur(prev_gray, (21, 21), 0)
        
        frame_count = 0

        while self.is_active:
            ret, frame2 = self.cap.read()
            if not ret:
                break
            
            frame_count += 1
            
            if frame_count < 5:
                prev_gray = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
                prev_gray = cv2.GaussianBlur(prev_gray, (21, 21), 0)
                continue
            
            gray = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)
            
            frame_diff = cv2.absdiff(prev_gray, gray)
            thresh = cv2.threshold(frame_diff, 30, 255, cv2.THRESH_BINARY)[1]
            thresh = cv2.dilate(thresh, None, iterations=2)
            
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            motion_detected = False
            max_area = 0
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > max_area:
                    max_area = area
                if area > 2000:
                    motion_detected = True
                    break
            
            current_time = time.time()
            if motion_detected and (current_time - self.last_motion_time) > self.cooldown_seconds:
                self.motion_count += 1
                self.last_motion_time = current_time
                print(f"[MOTION] ¡Movimiento detectado! (#{self.motion_count}, área: {max_area}px)")
                
                # 1. Guardar el frame de movimiento en su carpeta dedicada
                motion_frames_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'camera_files', 'videos', 'motion_frames')  # CAMBIO: dentro de videos
                os.makedirs(motion_frames_dir, exist_ok=True)
                frame_filename = f"eco_motion_{int(time.time() * 1000)}.jpg"
                frame_filepath = os.path.join(motion_frames_dir, frame_filename)
                cv2.imwrite(frame_filepath, frame2, [cv2.IMWRITE_JPEG_QUALITY, 85])
                print(f"[MOTION] Frame guardado: {frame_filename}")
                
                # 2. Iniciar grabación de video y obtener la URL
                video_url = self._start_recording()
                
                # 3. Llamar al callback pasando el frame y la URL del video
                if self.on_motion_detected_callback:
                    try:
                        self.on_motion_detected_callback(frame2, video_url)
                    except Exception as e:
                        print(f"[MOTION] Error en callback: {e}")
            
            prev_gray = gray
            time.sleep(0.1)
        
        print("[MOTION] Bucle de detección finalizado.")
    
    def _start_recording(self):
        """Inicia la grabación de video cuando se detecta movimiento"""
        if self.recording:
            return None
        
        self.recording = True
        
        video_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'camera_files', 'videos')
        os.makedirs(video_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"eco_motion_{timestamp}.webm"
        filepath = os.path.join(video_dir, filename)
        
        # Codec VP80 - nativo en WebM, soportado por todos los navegadores
        fourcc = cv2.VideoWriter_fourcc(*'vp80')
        self.video_writer = cv2.VideoWriter(filepath, fourcc, 10.0, (640, 480))
        
        print(f"[MOTION] Iniciando grabación: {filename} (codec: VP80/WebM)")
        
        self.record_thread = threading.Thread(
            target=self._record_video, 
            args=(filepath,), 
            daemon=True
        )
        self.record_thread.start()
        
        return f"http://127.0.0.1:8000/camera/videos/{filename}"
    
    def _record_video(self, filepath):
        """Graba video durante record_duration segundos"""
        start_time = time.time()
        frame_count = 0
        
        while self.recording and self.is_active:
            elapsed = time.time() - start_time
            
            if elapsed >= self.record_duration:
                print(f"[MOTION] Grabación finalizada: {frame_count} frames en {elapsed:.1f}s")
                break
            
            if self.cap and self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret and self.video_writer:
                    self.video_writer.write(frame)
                    frame_count += 1
            
            time.sleep(0.1)
        
        self.recording = False
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
            print(f"[MOTION] Video guardado: {filepath}")