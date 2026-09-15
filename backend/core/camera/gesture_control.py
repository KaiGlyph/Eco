import cv2
import mediapipe as mp
import pyautogui
import threading
import time
import numpy as np
import ctypes
from .morse_decoder import MorseDecoder

# Constantes de Windows
SM_XVIRTUALSCREEN = 76
SM_YVIRTUALSCREEN = 77
SM_CXVIRTUALSCREEN = 78
SM_CYVIRTUALSCREEN = 79

VK_VOLUME_UP = 0xAF
VK_VOLUME_DOWN = 0xAE
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002

def _send_key(vk_code):
    try:
        ctypes.windll.user32.keybd_event(vk_code, 0, KEYEVENTF_EXTENDEDKEY, 0)
        time.sleep(0.05)
        ctypes.windll.user32.keybd_event(vk_code, 0, KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP, 0)
    except Exception:
        pass

class GestureControl:
    def __init__(self):
        self.is_active = False
        self.thread = None
        self.cap = None
        
        self.mp_hands = mp.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        
        # Estado del ratón
        self.last_x, self.last_y = 0, 0
        self.is_clicking = False
        self.click_threshold_close = 0.06
        self.click_threshold_open = 0.09
        
        # Estado de gestos
        self.last_gesture_y = 0
        self.last_gesture_x = 0
        self.gesture_cooldown = 0
        self.last_finger_count = -1
        
        # Modo Morse
        self.morse_mode = False
        self.morse_decoder = MorseDecoder()
        self.fist_start_time = 0
        self.is_fist_closed = False
        
        # Dimensiones pantalla
        self._update_screen_bounds()
        self.margin_x = 0.02
        self.margin_y = 0.02

    def _update_screen_bounds(self):
        try:
            user32 = ctypes.windll.user32
            self.virtual_x = user32.GetSystemMetrics(SM_XVIRTUALSCREEN)
            self.virtual_y = user32.GetSystemMetrics(SM_YVIRTUALSCREEN)
            self.virtual_width = user32.GetSystemMetrics(SM_CXVIRTUALSCREEN)
            self.virtual_height = user32.GetSystemMetrics(SM_CYVIRTUALSCREEN)
        except Exception:
            self.virtual_x = 0
            self.virtual_y = 0
            self.virtual_width, self.virtual_height = pyautogui.size()

    def _count_fingers(self, landmarks):
        """Cuenta dedos extendidos con umbral estricto"""
        tips = [8, 12, 16, 20]  # Índice, Corazón, Anular, Meñique
        pips = [6, 10, 14, 18]
        count = 0
        
        # 4 dedos: usar umbral de 0.05 para evitar falsos positivos
        for tip, pip in zip(tips, pips):
            if landmarks[tip].y < landmarks[pip].y - 0.05:
                count += 1
                
        # Pulgar: comparar distancia a la muñeca
        wrist = landmarks[0]
        thumb_tip = landmarks[4]
        thumb_ip = landmarks[3]
        thumb_dist = np.linalg.norm([thumb_tip.x - wrist.x, thumb_tip.y - wrist.y])
        thumb_ip_dist = np.linalg.norm([thumb_ip.x - wrist.x, thumb_ip.y - wrist.y])
        if thumb_dist > thumb_ip_dist * 1.2:
            count += 1
            
        return count

    def _is_pinch(self, index_tip, thumb_tip):
        """Detecta gesto de pinza (click izquierdo)"""
        distance = np.sqrt((index_tip.x - thumb_tip.x)**2 + (index_tip.y - thumb_tip.y)**2)
        return distance < self.click_threshold_close, distance

    def _is_ok_gesture(self, landmarks, finger_count):
        """
        Detecta gesto de OK (click derecho): 
        Requiere que índice y pulgar estén juntos Y que los otros 3 dedos 
        (corazón, anular, meñique) estén CLARAMENTE extendidos.
        """
        index_tip = landmarks[8]
        middle_tip = landmarks[12]
        middle_pip = landmarks[10]
        ring_tip = landmarks[16]
        ring_pip = landmarks[14]
        pinky_tip = landmarks[20]
        pinky_pip = landmarks[18]
        
        middle_extended = middle_tip.y < middle_pip.y - 0.05
        ring_extended = ring_tip.y < ring_pip.y - 0.05
        pinky_extended = pinky_tip.y < pinky_pip.y - 0.05
        
        three_fingers_extended = middle_extended and ring_extended and pinky_extended
        
        thumb_tip = landmarks[4]
        distance = np.sqrt((index_tip.x - thumb_tip.x)**2 + (index_tip.y - thumb_tip.y)**2)
        pinch_close = distance < 0.08
        
        return three_fingers_extended and pinch_close

    def start(self, morse_mode=False):
        if self.is_active:
            return "El control por gestos ya está activo."
        
        self.is_active = True
        self.morse_mode = morse_mode
        self.is_clicking = False
        self.last_finger_count = -1
        self._update_screen_bounds()
        
        # Resetear estado Morse si se activa en ese modo
        if morse_mode:
            self.morse_decoder.reset()
            self.is_fist_closed = False
            self.fist_start_time = 0
            print("[GESTURE] Iniciando en modo MORSE")
        
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            self.is_active = False
            return "No se pudo acceder a la cámara."
        
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        self.thread = threading.Thread(target=self._run_gesture_loop, daemon=True)
        self.thread.start()
        
        if morse_mode:
            return "Modo Morse activado. Puño corto = Punto (.) | Puño largo = Raya (-) | Abre la mano para separar letras."
        else:
            return "Control activado. Ratón siempre activo. Pinza=Click Izq, OK=Click Der, 5 dedos=Scroll/Volumen, Puño=Alt+Tab"

    def stop(self):
        if not self.is_active:
            return "El control por gestos ya estaba desactivado."
        
        self.is_active = False
        self.morse_mode = False
        self.is_fist_closed = False
        
        if self.is_clicking:
            pyautogui.mouseUp()
            self.is_clicking = False
        
        if self.thread:
            self.thread.join(timeout=2.0)
            self.thread = None
        if self.cap:
            self.cap.release()
            self.cap = None
        
        self.mp_hands.close()
        print("[GESTURE] Control por gestos detenido")
        return "Control por gestos desactivado."

    def _run_gesture_loop(self):
        print("[GESTURE] Iniciando bucle de control por gestos...")
        
        while self.is_active:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            # Saltar frames para evitar overflow de MediaPipe
            self.frame_skip_counter = getattr(self, 'frame_skip_counter', 0) + 1
            if self.frame_skip_counter < 2:
                time.sleep(0.01)
                continue
            self.frame_skip_counter = 0
            
            try:
                frame = cv2.flip(frame, 1)
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self.mp_hands.process(frame_rgb)
                
                current_time = time.time()
                
                if results.multi_hand_landmarks:
                    hand_landmarks = results.multi_hand_landmarks[0].landmark
                    finger_count = self._count_fingers(hand_landmarks)
                    
                    index_tip = hand_landmarks[8]
                    thumb_tip = hand_landmarks[4]
                    wrist = hand_landmarks[0]
                    
                    # ==========================================
                    # MODO MORSE (Prioridad absoluta sobre el ratón)
                    # ==========================================
                    if self.morse_mode:
                        # 0 dedos = Puño cerrado
                        if finger_count == 0:
                            if not self.is_fist_closed:
                                self.is_fist_closed = True
                                self.fist_start_time = current_time
                        else:
                            # Acaba de abrir la mano
                            if self.is_fist_closed:
                                self.is_fist_closed = False
                                duration = current_time - self.fist_start_time
                                if duration > 0.1:  # Ignorar ruidos muy cortos
                                    self.morse_decoder.process_signal(duration)
                        
                        # Verificar pausas entre letras/palabras
                        self.morse_decoder.check_gaps()
                        
                        # En modo morse, NO mover el ratón ni hacer nada más
                        self.last_finger_count = finger_count
                        time.sleep(0.03)
                        continue
                    
                    # ==========================================
                    # MODO NORMAL: RATÓN SIEMPRE ACTIVO
                    # ==========================================
                    normalized_x = max(self.margin_x, min(1.0 - self.margin_x, index_tip.x))
                    normalized_y = max(self.margin_y, min(1.0 - self.margin_y, index_tip.y))
                    
                    target_x = int(self.virtual_x + (normalized_x - self.margin_x) / (1.0 - 2 * self.margin_x) * self.virtual_width)
                    target_y = int(self.virtual_y + (normalized_y - self.margin_y) / (1.0 - 2 * self.margin_y) * self.virtual_height)
                    
                    self.last_x = self.last_x + (target_x - self.last_x) * 0.25
                    self.last_y = self.last_y + (target_y - self.last_y) * 0.25
                    pyautogui.moveTo(int(self.last_x), int(self.last_y), duration=0.02)
                    
                    # ==========================================
                    # CLICK IZQUIERDO: PINZA (índice + pulgar)
                    # PRIORIDAD ABSOLUTA - siempre se evalúa primero
                    # ==========================================
                    is_pinch, pinch_distance = self._is_pinch(index_tip, thumb_tip)
                    
                    if is_pinch:
                        if not self.is_clicking:
                            self.is_clicking = True
                            pyautogui.mouseDown()
                    else:
                        if self.is_clicking:
                            self.is_clicking = False
                            pyautogui.mouseUp()
                    
                    # ==========================================
                    # GESTOS ESPECIALES (según número de dedos)
                    # ==========================================
                    
                    # 5 DEDOS: SCROLL (usando teclas de flecha)
                    if finger_count == 5:
                        if self.is_clicking:
                            pyautogui.mouseUp()
                            self.is_clicking = False
                        
                        delta_y = self.last_gesture_y - wrist.y
                        
                        if abs(delta_y) > 0.003:
                            press_count = int(abs(delta_y) * 200)
                            press_count = max(1, min(10, press_count))
                            
                            if delta_y > 0:
                                for _ in range(press_count):
                                    pyautogui.press('up')
                            else:
                                for _ in range(press_count):
                                    pyautogui.press('down')
                        
                        self.last_gesture_y = wrist.y
                    
                    # 0 DEDOS (PUÑO): VOLUMEN o ALT+TAB
                    elif finger_count == 0:
                        if self.is_clicking:
                            pyautogui.mouseUp()
                            self.is_clicking = False
                        
                        delta_y = self.last_gesture_y - wrist.y
                        delta_x = wrist.x - self.last_gesture_x
                        
                        if abs(delta_y) > 0.08 and current_time > self.gesture_cooldown:
                            if delta_y > 0:
                                _send_key(VK_VOLUME_UP)
                                print("[GESTURE] Volumen +")
                            else:
                                _send_key(VK_VOLUME_DOWN)
                                print("[GESTURE] Volumen -")
                            self.gesture_cooldown = current_time + 0.2
                        
                        elif abs(delta_x) > 0.15 and current_time > self.gesture_cooldown:
                            pyautogui.hotkey('alt', 'tab')
                            print("[GESTURE] Alt + Tab")
                            self.gesture_cooldown = current_time + 1.0
                        
                        self.last_gesture_y = wrist.y
                        self.last_gesture_x = wrist.x
                    
                    # CLICK DERECHO: Gesto OK (3 dedos extendidos + pinza)
                    elif not is_pinch and self._is_ok_gesture(hand_landmarks, finger_count):
                        if self.is_clicking:
                            pyautogui.mouseUp()
                            self.is_clicking = False
                        
                        if self.last_finger_count != 4 and current_time > self.gesture_cooldown:
                            pyautogui.rightClick()
                            print("[GESTURE] Click derecho (gesto OK)")
                            self.gesture_cooldown = current_time + 0.5
                    
                    self.last_finger_count = finger_count
                else:
                    if self.is_clicking:
                        pyautogui.mouseUp()
                        self.is_clicking = False
                    self.last_finger_count = -1
                    
            except Exception as e:
                print(f"[GESTURE] Error en procesamiento: {e}")
                if "overflow" in str(e).lower():
                    print("[GESTURE] Overflow detectado, aumentando tiempo de espera")
                    time.sleep(0.1)
                else:
                    time.sleep(0.05)
                continue
            
            time.sleep(0.03)
        
        print("[GESTURE] Bucle finalizado.")