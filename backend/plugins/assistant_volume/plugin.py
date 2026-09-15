from core.plugin_base import BasePlugin

class AssistantVolumePlugin(BasePlugin):
    name = "Volumen del Asistente"
    description = "Control del volumen de voz de Eco"
    icon = "volume-2"
    priority = 65
    
    def get_intents(self):
        return [
            {"tag": "eco_volumen_subir", "patterns": ["habla más fuerte", "sube tu voz", "eco más alto", "habla más alto"], "responses": ["Subiendo mi voz..."]},
            {"tag": "eco_volumen_bajar", "patterns": ["habla más bajo", "baja tu voz", "eco más bajo", "habla más suave"], "responses": ["Bajando mi voz..."]},
            {"tag": "eco_volumen_fijo", "patterns": ["habla al", "pon tu voz al", "tu volumen al"], "responses": ["Ajustando mi voz..."]},
            {"tag": "app_volumen", "patterns": ["baja el volumen de", "sube el volumen de", "silencia", "volumen de"], "responses": ["Ajustando volumen de la aplicación..."]}
        ]

    def get_forced_patterns(self):
        return [
            (["habla más fuerte", "sube tu voz", "eco más alto", "habla más alto"], "eco_volumen_subir"),
            (["habla más bajo", "baja tu voz", "eco más bajo", "habla más suave"], "eco_volumen_bajar"),
            (["habla al", "pon tu voz al", "tu volumen al"], "eco_volumen_fijo"),
        ]

    def can_handle(self, text: str, intent: str, confidence: float) -> bool:
        return intent in ["eco_volumen_subir", "eco_volumen_bajar", "eco_volumen_fijo", "app_volumen"]

    def handle(self, text: str, intent: str, context: dict) -> str:
        from core.speaker import speaker
        lower_text = text.lower()
        
        if intent == "eco_volumen_subir":
            new_vol = speaker.change_assistant_volume("up", 15.0)
            return f"Mi voz ahora está al {new_vol:.0f}%."
        
        elif intent == "eco_volumen_bajar":
            new_vol = speaker.change_assistant_volume("down", 15.0)
            return f"Mi voz ahora está al {new_vol:.0f}%."
        
        elif intent == "eco_volumen_fijo":
            import re
            match = re.search(r'al\s+(\d+)', lower_text)
            if match:
                percentage = float(match.group(1))
                new_vol = speaker.set_assistant_volume(percentage)
                return f"Mi voz ajustada al {new_vol:.0f}%."
            return "No entendí a qué volumen quieres que hable."
        
        return "No entendí el comando de volumen."