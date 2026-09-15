import os
from llama_cpp import Llama

class LLMEngine:
    def __init__(self):
        import sys
        if getattr(sys, 'frozen', False):
            # Modo empaquetado: los recursos están en la carpeta _MEIPASS
            base_dir = sys._MEIPASS
        else:
            # Modo desarrollo
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        model_path = os.path.join(base_dir, 'models', 'qwen2.5-1.5b-instruct-q4_k_m.gguf')
        
        print(f"[LLM] Cargando modelo local: {model_path}")
        
        if not os.path.exists(model_path):
            print(f"[LLM] ERROR: No se encontró el modelo en {model_path}")
            self.model = None
            return

        try:
            self.model = Llama(
                model_path=model_path,
                n_gpu_layers=0,          # 0 para CPU
                n_ctx=4096,              # AUMENTADO: de 2048 a 4096 para evitar desbordamientos
                n_batch=512,             # NUEVO: Mejora la estabilidad en CPU
                n_threads=4,             # Hilos de CPU
                verbose=False
            )
            print("[LLM] Modelo cargado correctamente en memoria.")
        except Exception as e:
            print(f"[LLM] Error crítico al cargar el modelo: {e}")
            self.model = None

    def chat(self, prompt: str, model_type: str = "fast") -> str:
        if self.model is None:
            return "El modelo de lenguaje no está disponible."

        messages = [
            {"role": "system", "content": """Eres Eco, un asistente personal útil y conciso.
            
        REGLAS IMPORTANTES:
        - Si no tienes información específica sobre lo que el usuario pregunta, di "No tengo información sobre eso" o "No puedo ayudarte con eso".
        - NO inventes respuestas ni asumas información que no tienes.
        - Responde de forma breve y directa.
        - Si el usuario te saluda, responde de forma natural y breve.
        - Si el usuario te pregunta algo que no está en tu contexto, di que no lo sabes.

        Ejemplos de respuestas correctas:
        - Usuario: "Hola" → Eco: "Hola, ¿en qué puedo ayudarte?"
        - Usuario: "¿Qué tiempo hace?" → Eco: "No tengo acceso a información del clima en este momento."
        - Usuario: "¿Qué sabes de mí?" → Eco: "Aún no me has contado mucho sobre ti."

        NUNCA inventes información. Si no sabes algo, dilo claramente."""},
            {"role": "user", "content": prompt}
        ]

        try:
            output = self.model.create_chat_completion(
                messages=messages,
                max_tokens=150,
                temperature=0.7,
                stop=["<|im_end|>", "Usuario:", "Eco:"],
                # Parámetros de seguridad para evitar el error GGML_ASSERT
                top_k=40,
                top_p=0.95,
                repeat_penalty=1.1
            )
            
            response_text = output['choices'][0]['message']['content'].strip()
            return response_text
            
        except Exception as e:
            # Capturamos el error de C++ para que la app no se rompa
            error_msg = str(e)
            if "GGML_ASSERT" in error_msg or "llama_decode" in error_msg:
                print(f"[LLM] ⚠️ El motor C++ tuvo un error de contexto. Reiniciando instancia...")
                # Intento de recuperación: recargar el modelo en memoria
                try:
                    del self.model
                    self.__init__() # Recarga el modelo
                except Exception:
                    pass
            else:
                print(f"[LLM] Error durante la generación: {e}")
                
            return "Tuve un pequeño tropiezo procesando eso. ¿Podrías repetirlo?"