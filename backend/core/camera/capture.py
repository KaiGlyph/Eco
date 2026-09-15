import cv2
import os
import time

def get_available_cameras():
    """
    Detecta TODAS las cámaras disponibles probando múltiples backends de OpenCV.
    """
    print("[CAMERA] === INICIANDO BÚSQUEDA DE CÁMARAS ===")
    available = []
    usb_cameras = []
    integrated_cameras = []
    
    # Backends a probar en orden de preferencia para Windows
    backends_to_try = [
        cv2.CAP_ANY,       # Backend por defecto (el más compatible)
        cv2.CAP_MSMF,      # Media Foundation (mejor para USB modernas en Windows)
        cv2.CAP_DSHOW,     # DirectShow (el que usábamos, a veces falla con USB)
    ]
    
    # Probamos los primeros 5 índices (suficiente para 99% de los casos)
    for i in range(5):
        camera_found = False
        
        for backend in backends_to_try:
            if camera_found:
                break
                
            print(f"[CAMERA] Probando índice {i} con backend {backend}...")
            cap = cv2.VideoCapture(i, backend)
            
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    print(f"[CAMERA] ✓ ÉXITO: Índice {i} funciona con backend {backend}")
                    camera_found = True
                    cap.release()
                    
                    # Clasificación simple: índice 0 suele ser la integrada
                    if i == 0:
                        integrated_cameras.append(i)
                    else:
                        usb_cameras.append(i)
                    break
                else:
                    cap.release()
            else:
                if backend == cv2.CAP_ANY:
                    print(f"[CAMERA]   -> Índice {i} no disponible en backend por defecto")
    
    # Priorizar USB sobre integradas
    available = usb_cameras + integrated_cameras
    
    print(f"[CAMERA] === RESULTADO ===")
    print(f"[CAMERA] USB/Externas detectadas: {usb_cameras}")
    print(f"[CAMERA] Integradas detectadas: {integrated_cameras}")
    print(f"[CAMERA] Prioridad de uso: {available}")
    print(f"[CAMERA] =================")
    
    return available

def capture_snapshot(camera_index=0):
    """Toma una foto con la cámara indicada y la guarda"""
    print(f"[CAMERA] Intentando capturar con índice {camera_index}...")
    
    # Intentar primero con el backend por defecto, luego MSMF
    backends_to_try = [cv2.CAP_ANY, cv2.CAP_MSMF, cv2.CAP_DSHOW]
    cap = None
    
    for backend in backends_to_try:
        cap = cv2.VideoCapture(camera_index, backend)
        if cap.isOpened():
            print(f"[CAMERA] ✓ Cámara {camera_index} abierta con backend {backend}")
            break
        else:
            print(f"[CAMERA]   -> Falló con backend {backend}")
            cap = None
    
    if cap is None or not cap.isOpened():
        print(f"[CAMERA] ERROR: No se pudo abrir la cámara {camera_index} con ningún backend")
        return None
    
    # Configurar resolución
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    # Esperar a que la cámara se ajuste a la luz
    time.sleep(1.0)
    
    # Capturar varios frames para asegurar calidad
    best_frame = None
    for i in range(5):
        ret, frame = cap.read()
        if ret:
            best_frame = frame
            print(f"[CAMERA] Frame {i+1}/5 capturado")
            if i == 4:
                break
            time.sleep(0.1)
    
    cap.release()
    
    if best_frame is not None:
        camera_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'camera_files', 'fotos')  # CAMBIO: fotos en lugar de capturas
        os.makedirs(camera_dir, exist_ok=True)
        
        filename = f"eco_cam_{int(time.time() * 1000)}.jpg"
        filepath = os.path.join(camera_dir, filename)
        
        success = cv2.imwrite(filepath, best_frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
        
        if success:
            print(f"[CAMERA] ✓ Foto guardada exitosamente: {filename}")
            return f"http://127.0.0.1:8000/camera/{filename}"
        else:
            print(f"[CAMERA] ERROR: Fallo al escribir el archivo en disco")
            return None
    
    print("[CAMERA] ERROR: No se pudo capturar ningún frame válido")
    return None