"""Reconocimiento de lenguaje de señas - Pendiente de implementar"""

class SignLanguageDetector:
    def __init__(self, vision_engine):
        self.vision = vision_engine
        self.is_active = False
    
    def start(self):
        return "Detector de señas: pendiente de implementar"
    
    def stop(self):
        return "Detector de señas desactivado"
    
    def get_detected_signs(self):
        return []