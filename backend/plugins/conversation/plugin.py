from core.plugin_base import BasePlugin

class ConversationPlugin(BasePlugin):
    name = "Conversación"
    description = "Cambiar voz de Eco y conversación general"
    icon = "message-circle"
    priority = 30  # Baja prioridad, fallback
    
    def get_intents(self):
        return [
            {
                "tag": "cambiar_voz",
                "patterns": ["cambia tu voz", "usa tu voz", "usa edge", "usa la voz neural", "cambia de voz", "voz online", "voz offline"],
                "responses": ["Cambiando voz..."]
            },
            {
                "tag": "saludo",
                "patterns": ["hola", "buenos días", "buenas tardes", "buenas noches", "hey", "eh"],
                "responses": ["¡Hola! ¿En qué puedo ayudarte?", "¡Buenas! ¿Qué tal?", "¡Hey! ¿Qué cuentas?"]
            },
            {
                "tag": "despedida",
                "patterns": ["adiós", "hasta luego", "hasta pronto", "nos vemos", "bye", "chao"],
                "responses": ["¡Hasta luego!", "¡Que tengas buen día!", "¡Nos vemos!"]
            }
        ]

    def get_forced_patterns(self):
        return [
            (["cambia tu voz", "usa tu voz", "usa edge", "cambia de voz", "voz online", "voz offline"], "cambiar_voz"),
            (["hola", "buenos días", "buenas tardes", "buenas noches", "hey"], "saludo"),
            (["adiós", "hasta luego", "hasta pronto", "nos vemos", "bye", "chao"], "despedida")
        ]

    def can_handle(self, text: str, intent: str, confidence: float) -> bool:
        return intent in ["cambiar_voz", "saludo", "despedida"]

    def handle(self, text: str, intent: str, context: dict) -> str:
        lower_text = text.lower()
        speaker = context.get('speaker')
        
        if intent == "cambiar_voz":
            if speaker:
                if any(word in lower_text for word in ["edge", "neural", "microsoft", "online"]):
                    speaker.set_voice("edge")
                    return "He cambiado a la voz neural de Microsoft."
                elif any(word in lower_text for word in ["offline", "local", "sistema", "pyttsx3"]):
                    speaker.set_voice("pyttsx3")
                    return "He cambiado a la voz local del sistema."
                else:
                    speaker.use_edge_tts = not speaker.use_edge_tts
                    if speaker.use_edge_tts:
                        return "He cambiado a la voz neural de Microsoft."
                    else:
                        return "He cambiado a la voz local del sistema."
            return "No puedo cambiar la voz en este momento."
        
        elif intent == "saludo":
            return "¡Hola! ¿En qué puedo ayudarte hoy?"
        
        elif intent == "despedida":
            return "¡Hasta luego! Que tengas un buen día."
        
        return "No entendí."