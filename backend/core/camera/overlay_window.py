import tkinter as tk
from PIL import Image, ImageTk
import cv2
import mss
import threading
import time
import numpy as np

class OverlayWindow:
    """Ventana Picture-in-Picture: Cámara de fondo + Pantalla arrastrable"""
    
    def __init__(self):
        self.is_active = False
        self.cap = None
        self.root = None
        
        # Configuración de tamaños
        self.cam_width = 800
        self.cam_height = 600
        self.screen_width = 320  # Tamaño del rectángulo de pantalla
        self.screen_height = 180
        
        # Estado
        self.is_dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0

    def start(self):
        if self.is_active:
            return "La ventana ya está activa."
        
        self.is_active = True
        
        # Crear ventana Tkinter sin bordes (estilo overlay)
        self.root = tk.Tk()
        self.root.title("Eco - Cámara + Pantalla")
        self.root.attributes('-topmost', True)
        self.root.overrideredirect(True)  # Quitar barra de título
        self.root.geometry(f"{self.cam_width}x{self.cam_height}+100+100")
        
        # Fondo negro por si acaso
        self.root.configure(bg='black')
        
        # 1. Label para la cámara (FONDO)
        self.cam_label = tk.Label(self.root, bg='black')
        self.cam_label.place(x=0, y=0, width=self.cam_width, height=self.cam_height)
        
        # Hacer que toda la ventana sea arrastrable (por si quieres mover el conjunto)
        self.cam_label.bind("<Button-1>", self.start_drag_window)
        self.cam_label.bind("<B1-Motion>", self.drag_window)
        
        # 2. Frame para el rectángulo de pantalla (PRIMER PLANO)
        self.screen_frame = tk.Frame(self.root, bg='#6A0DAD', bd=2, relief='solid')
        self.screen_frame.place(x=20, y=20, width=self.screen_width, height=self.screen_height)
        
        # Label dentro del frame para la imagen de pantalla
        self.screen_label = tk.Label(self.screen_frame, bg='black')
        self.screen_label.pack(fill=tk.BOTH, expand=True)
        
        # Hacer el rectángulo arrastrable
        self.screen_frame.bind("<Button-1>", self.start_drag_rect)
        self.screen_frame.bind("<B1-Motion>", self.drag_rect)
        self.screen_label.bind("<Button-1>", self.start_drag_rect)
        self.screen_label.bind("<B1-Motion>", self.drag_rect)
        
        # 3. Botón de cerrar (pequeña X en la esquina)
        close_btn = tk.Button(
            self.root, text="✕", command=self.stop,
            bg='red', fg='white', relief='flat', font=('Arial', 10, 'bold'),
            bd=0, width=2, height=1
        )
        close_btn.place(x=self.cam_width-30, y=5)
        
        # Iniciar threads de captura
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            self.is_active = False
            self.root.destroy()
            return "No se pudo acceder a la cámara."
        
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 800)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 600)
        
        # Thread para la cámara
        threading.Thread(target=self._camera_loop, daemon=True).start()
        # Thread para la pantalla
        threading.Thread(target=self._screen_loop, daemon=True).start()
        
        # Iniciar loop de Tkinter
        self.root.mainloop()
        return "Ventana PiP activada."

    # --- Lógica de Arrastre del Rectángulo de Pantalla ---
    def start_drag_rect(self, event):
        self.is_dragging = True
        self.drag_start_x = event.x
        self.drag_start_y = event.y

    def drag_rect(self, event):
        if not self.is_dragging:
            return
        
        # Calcular nueva posición relativa al frame principal
        x = self.screen_frame.winfo_x() + (event.x - self.drag_start_x)
        y = self.screen_frame.winfo_y() + (event.y - self.drag_start_y)
        
        # Limitar para que no se salga de la ventana principal
        x = max(0, min(x, self.cam_width - self.screen_width))
        y = max(0, min(y, self.cam_height - self.screen_height))
        
        self.screen_frame.place(x=x, y=y)

    # --- Lógica de Arrastre de la Ventana Completa ---
    def start_drag_window(self, event):
        self.window_drag_start_x = event.x
        self.window_drag_start_y = event.y

    def drag_window(self, event):
        x = self.root.winfo_pointerx() - self.window_drag_start_x
        y = self.root.winfo_pointery() - self.window_drag_start_y
        self.root.geometry(f"+{x}+{y}")

    # --- Bucle de Captura de Cámara ---
    def _camera_loop(self):
        while self.is_active:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            frame = cv2.flip(frame, 1)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Redimensionar si es necesario
            frame = cv2.resize(frame, (self.cam_width, self.cam_height))
            
            img = Image.fromarray(frame)
            img_tk = ImageTk.PhotoImage(image=img)
            
            # Actualizar label (thread-safe)
            if self.root:
                self.root.after(0, lambda img=img_tk: self.cam_label.config(image=img))
            
            time.sleep(0.03)  # ~30 FPS

    # --- Bucle de Captura de Pantalla ---
    def _screen_loop(self):
        with mss.mss() as sct:
            # Capturar el monitor principal (índice 1)
            monitor = sct.monitors[1]
            
            while self.is_active:
                # Capturar pantalla
                screenshot = sct.grab(monitor)
                
                # Convertir a formato PIL
                img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
                
                # Redimensionar al tamaño del rectángulo
                img = img.resize((self.screen_width, self.screen_height), Image.Resampling.LANCZOS)
                img_tk = ImageTk.PhotoImage(image=img)
                
                # Actualizar label (thread-safe)
                if self.root:
                    self.root.after(0, lambda img=img_tk: self.screen_label.config(image=img))
                
                time.sleep(0.05)  # ~20 FPS para la pantalla (suficiente y menos carga)

    def stop(self):
        if not self.is_active:
            return "La ventana ya estaba cerrada."
        
        self.is_active = False
        
        if self.cap:
            self.cap.release()
        
        if self.root:
            self.root.destroy()
        
        print("[OVERLAY] Ventana PiP cerrada")
        return "Ventana overlay cerrada."