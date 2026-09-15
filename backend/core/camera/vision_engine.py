"""Motor central de visión - Pendiente de implementar"""

class VisionEngine:
    def __init__(self):
        self.is_active = False
    
    def start(self):
        return "Vision Engine: pendiente de implementar"
    
    def stop(self):
        return "Vision Engine detenida"
    
    def register_callback(self, name, callback):
        pass
    
    def unregister_callback(self, name):
        pass

# Instancia global
vision_engine = VisionEngine()