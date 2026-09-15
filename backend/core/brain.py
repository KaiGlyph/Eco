import json
import os
import random
import re
import threading
from core.speaker import speaker
from core.memory import memory
from core.camera import get_available_cameras, capture_snapshot
from .intent_classifier import IntentClassifier
from .llm_engine import LLMEngine
from .plugin_manager import PluginManager

class Brain:
    def __init__(self):
        print("Iniciando el Router de Eco...")
        self.classifier = IntentClassifier()
        self.classifier.load()
        self.llm = LLMEngine()
        self.pending_action = None
        self.pending_note_edit = None
        
        import sys
        if getattr(sys, 'frozen', False):
            # Modo empaquetado
            base_dir = sys._MEIPASS
        else:
            # Modo desarrollo
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        dataset_path = os.path.join(base_dir, 'data', 'dataset.json')
        with open(dataset_path, 'r', encoding='utf-8') as f:
            self.dataset = json.load(f)
        
        plugins_dir = os.path.join(base_dir, 'plugins')
        self.plugin_manager = PluginManager(plugins_dir)

    def _decide_model(self, intent: str, confidence: float, text: str) -> str:
        if intent == "conversacion": return "smart"
        if confidence < 60: return "smart"
        return "fast"

    def _speak_response(self, response: str):
        if response:
            threading.Thread(target=speaker.speak, args=(response,), daemon=True).start()

    def _split_commands(self, text: str) -> list:
        """Separa comandos múltiples pero respeta conectores temporales y de hora"""
        # Conectores que SÍ separan comandos (acciones secuenciales)
        split_connectors = [
            ' y después ', ' y luego ', ' después ', ' luego ', 
            ' también ', ' además ',
        ]
        
        # Conectores que NO deben separar (proteger temporalmente)
        protected_connectors = [
            ' y a las ', ' y para las ', ' y sobre las ',
            ' y del ', ' y al ', ' y de las ',
            ' y el ', ' y la ', ' y los ', ' y las ',
        ]
        
        text_lower = text.lower()
        
        # 1. Proteger conectores que no deben separar
        protected_text = text_lower
        for i, connector in enumerate(protected_connectors):
            protected_text = protected_text.replace(connector, f"__PROTECT{i}__")
        
        # 2. Separar por conectores válidos
        for connector in split_connectors:
            if connector in protected_text:
                parts = protected_text.split(connector)
                commands = [p.strip() for p in parts if p.strip()]
                if len(commands) >= 2:
                    # 3. Restaurar conectores protegidos
                    final_commands = []
                    for cmd in commands:
                        for i, connector in enumerate(protected_connectors):
                            cmd = cmd.replace(f"__PROTECT{i}__", connector)
                        final_commands.append(cmd)
                    return final_commands
        
        # Si no hay separación, devolver el texto original
        return [text]

    # ==========================================
    # 1. GENERADOR DE RESPUESTAS (Genérico)
    # ==========================================
    def _generate_natural_response(self, action_context: str, success: bool = True) -> str:
        import random
        if not action_context: 
            return "Entendido, lo he hecho."
        
        # 1. Intentar con LLM, pero con un prompt más específico
        try:
            estado = "se realizó correctamente" if success else "falló"
            prompt = f"""Eres Eco. Acción realizada: {action_context}. Estado: {estado}.
            
            Responde de forma natural y breve, pero SIEMPRE debes mencionar el valor numérico o dato clave si existe en el contexto (porcentajes, tiempos, nombres, etc.).
            
            Ejemplos CORRECTOS:
            - "Listo, volumen al 50%"
            - "Hecho, brillo ajustado al 20%"
            - "Perfecto, temporizador de 30 minutos iniciado"
            - "Entendido, nota guardada: comprar leche"
            
            Ejemplos INCORRECTOS (demasiado vagos):
            - "Listo"
            - "Hecho"
            - "Perfecto"
            
            Tu respuesta:"""
            response = self.llm.chat(prompt, "fast")
            clean = response.strip().strip('"').strip("'").strip()
            
            # Filtrar respuestas demasiado vagas o con errores
            if clean and len(clean) > 5 and len(clean) < 150 and "error" not in clean.lower():
                # Verificar que si hay un número en el contexto, esté en la respuesta
                import re
                numbers_in_context = re.findall(r'\d+', action_context)
                if numbers_in_context:
                    # Si hay números en el contexto, verificar que al menos uno esté en la respuesta
                    has_number = any(num in clean for num in numbers_in_context)
                    if has_number:
                        return clean
                    else:
                        # Si el LLM no incluyó el número, forzar una respuesta con el dato
                        pass
                else:
                    return clean
        except Exception:
            pass
        
        # 2. FALLBACK INTELIGENTE (si el LLM falla o es muy vago)
        if success:
            lower_ctx = action_context.lower()
            
            # Extraer cualquier dato numérico/temporal del contexto
            data_match = re.search(r'(\d+\s*(?:minuto|hora|segundo|%|a las \d+:\d+)|\d{1,2}:\d{2}|\d+)', lower_ctx)
            
            if data_match:
                data_str = data_match.group(0)
                # Detectar el tipo de acción
                if "volumen" in lower_ctx or "audio" in lower_ctx:
                    templates = [
                        f"Listo, volumen al {data_str}.",
                        f"Hecho, audio ajustado al {data_str}.",
                        f"Perfecto, volumen establecido al {data_str}."
                    ]
                elif "brillo" in lower_ctx or "pantalla" in lower_ctx:
                    templates = [
                        f"Listo, brillo al {data_str}.",
                        f"Hecho, brillo ajustado al {data_str}.",
                        f"Perfecto, pantalla al {data_str}."
                    ]
                elif "temporizador" in lower_ctx or "alarma" in lower_ctx:
                    templates = [
                        f"Listo, {data_str} configurado.",
                        f"Hecho, temporizador de {data_str} iniciado.",
                        f"Perfecto, te aviso en {data_str}."
                    ]
                elif "nota" in lower_ctx:
                    templates = [
                        f"Anotado.",
                        f"Hecho, ya lo tengo apuntado.",
                        f"Perfecto, guardado en tus notas."
                    ]
                else:
                    templates = [
                        f"Listo, configurado al {data_str}.",
                        f"Hecho, ajustado al {data_str}.",
                        f"Perfecto, ya está al {data_str}."
                    ]
            else:
                templates = [
                    "Listo, ya lo tienes.",
                    "Hecho, está configurado.",
                    "Perfecto, lo tienes.",
                    "Entendido, ya está."
                ]
            return random.choice(templates)
        
        return random.choice([
            "Vaya, no he podido hacerlo.",
            "Lo siento, algo ha fallado.",
            "No he logrado completar esa acción."
        ])
    
    # ==========================================
    # 2. FLUJO PRINCIPAL (Enrutador)
    # ==========================================
    def process(self, text: str):
        if self.pending_action:
            response = self._handle_confirmation(text)
            self._speak_response(response)
            return response
        
        if self.pending_note_edit:
            response = self._handle_note_edit(text)
            self._speak_response(response)
            return response
        
        commands = self._split_commands(text)
        if len(commands) > 1:
            print(f"[DEBUG] Múltiples comandos detectados: {commands}")
            responses = []
            for cmd in commands:
                response = self._process_single_command(cmd)
                if response:
                    # Si es dict, extraemos el contexto, si es string, lo usamos tal cual
                    resp_text = response.get('context', '') if isinstance(response, dict) else str(response)
                    responses.append(resp_text)
            
            if responses:
                if len(responses) == 2:
                    final_response = f"{responses[0]} y {responses[1].lower()}"
                elif len(responses) > 2:
                    final_response = ", ".join(responses[:-1]) + f" y {responses[-1].lower()}"
                else:
                    final_response = ". ".join(responses)
            else:
                final_response = "No he podido procesar las órdenes."
            
            self._speak_response(final_response)
            return final_response
        else:
            response = self._process_single_command(text)
            
            # === CORRECCIÓN AQUÍ ===
            # Si la respuesta es un diccionario (ej. cámara), extraemos el texto para hablar
            if isinstance(response, dict):
                text_to_speak = response.get('context', 'Hecho.')
                self._speak_response(text_to_speak)
            else:
                self._speak_response(response)
            
            return response

    def _handle_confirmation(self, text: str) -> str:
        lower_text = text.lower()
        if any(w in lower_text for w in ["sí", "si", "vale", "confirma", "adelante", "ok"]):
            action = self.pending_action
            self.pending_action = None
            from plugins.system import shutdown_pc, restart_pc, suspend_pc
            if action == "shutdown": return shutdown_pc(1)["context"]
            elif action == "restart": return restart_pc(1)["context"]
            elif action == "suspend": return suspend_pc()["context"]
        self.pending_action = None
        return "Acción cancelada."

    def _handle_note_edit(self, text: str) -> str:
        from plugins.notes import edit_note
        self.pending_note_edit = None
        return edit_note("última", text)

    def _process_single_command(self, text: str) -> str:
        intent, confidence = self.classifier.predict(text)
        print(f"Eco pensó: '{intent}' (Confianza: {confidence:.0f}%)")
        lower_text = text.lower()

        # ==========================================
        # DETECCIÓN DE CÁMARA (Antes que nada)
        # ==========================================
        camera_keywords = ["activame la cámara", "activa la cámara", "enciende la cámara", 
                          "abre la cámara", "mira", "hazme una foto", "toma una foto", 
                          "saca una foto", "muéstrame", "qué ves"]
        
        if any(kw in lower_text for kw in camera_keywords):
            print("[CAMERA] Detectada solicitud de cámara en el brain")
            try:
                from core.camera import get_available_cameras, capture_snapshot
                
                cameras = get_available_cameras()
                if not cameras:
                    return "No detecto ninguna cámara conectada en este momento."
                
                print(f"[CAMERA] Cámaras disponibles: {cameras}")
                image_url = capture_snapshot(camera_index=cameras[0])
                
                if image_url:
                    print(f"[CAMERA] Imagen capturada: {image_url}")
                    # Devolver un diccionario especial con la URL de la imagen
                    return {
                        'context': 'He capturado una imagen con la cámara',
                        'success': True,
                        'camera_image': image_url,
                        'raw_response': True
                    }
                else:
                    return "Tuve un error al intentar capturar la imagen."
                    
            except Exception as e:
                print(f"[CAMERA] Error: {e}")
                return "Lo siento, no pude acceder a la cámara."
            
        # ==========================================
        # DETECTOR DE MOVIMIENTO (MODO VIGILIA)
        # ==========================================
        motion_keywords = ["vigila", "vigilar", "detecta movimiento", "modo seguridad", 
                           "avísame si se mueve", "observa la sala", "vigilancia"]
        
        # Palabras que indican DESACTIVAR
        desactivar_keywords = ["deja", "detén", "para", "apaga", "desactiva", "cierra", "basta"]
        
        if any(kw in lower_text for kw in motion_keywords):
            print("[MOTION] Solicitud de modo vigilia detectada")
            from main import motion_detector
            
            # Primero comprobar si es desactivación
            if any(kw in lower_text for kw in desactivar_keywords):
                response = motion_detector.stop()
            else:
                response = motion_detector.start()
            
            return {'context': response, 'success': True, 'raw_response': True}

        # ==========================================
        # CONTROL MANUAL DEL DETECTOR DE PRESENCIA
        # ==========================================
        presence_keywords = ["presencia", "detectame", "detecta si estoy"]
        
        if any(kw in lower_text for kw in presence_keywords):
            print("[PRESENCE] Control manual del detector")
            from main import presence_detector
            
            if "desactiva" in lower_text or "apaga" in lower_text or "para" in lower_text:
                response = presence_detector.stop()
            else:
                response = presence_detector.start()
            
            return {'context': response, 'success': True, 'raw_response': True}

        # ==========================================
        # CONTROL POR GESTOS
        # ==========================================
        gesture_keywords = ["control por gestos", "gestos", "mueve el ratón con la mano", 
                           "controla el ratón", "modo gesto"]
        
        if any(kw in lower_text for kw in gesture_keywords):
            print("[GESTURE] Solicitud de control por gestos")
            from main import gesture_control
            
            if "desactiva" in lower_text or "apaga" in lower_text or "para" in lower_text:
                response = gesture_control.stop()
            else:
                response = gesture_control.start()
            
            return {'context': response, 'success': True, 'raw_response': True}

        # ==========================================
        # VENTANA OVERLAY DE CÁMARA
        # ==========================================
        overlay_keywords = ["ventana", "overlay", "muestra la cámara", 
                           "abre la ventana", "cámara en vivo", "ver cámara"]
        
        if any(kw in lower_text for kw in overlay_keywords):
            print("[OVERLAY] Solicitud de ventana overlay")
            from main import overlay_window
            
            if "cierra" in lower_text or "apaga" in lower_text or "para" in lower_text:
                response = overlay_window.stop()
            else:
                response = overlay_window.start()
            
            return {'context': response, 'success': True, 'raw_response': True}
        
        # Primero, verificar forced_patterns de TODOS los plugins
        for keywords, intent_tag, plugin in self.plugin_manager.get_all_forced_patterns():
            if any(kw in lower_text for kw in keywords):
                intent = intent_tag
                confidence = 100
                print(f"-> Plugin '{plugin.name}' forzó intención a '{intent_tag}'")
                break

        print(f"[DEBUG] Intent final: {intent}, Confidence: {confidence}")
        response = None

        # ==========================================
        # MODO MORSE
        # ==========================================
        morse_keywords = ["modo morse", "código morse", "morse", "transmitir en morse"]
        
        if any(kw in lower_text for kw in morse_keywords):
            print("[MORSE] Solicitud de modo morse")
            from main import gesture_control
            
            if "desactiva" in lower_text or "apaga" in lower_text or "para" in lower_text:
                response = gesture_control.stop()
            else:
                response = gesture_control.start(morse_mode=True)
            
            return {'context': response, 'success': True, 'raw_response': True}

        
        # 1. Ejecutar con Plugin (El plugin decide cómo interpretar y actuar)
        plugin = self.plugin_manager.get_plugin_for_intent(intent)
        if plugin and plugin.can_handle(text, intent, confidence):
            context = {'brain': self, 'lower_text': lower_text, 'speaker': speaker}
            plugin_response = plugin.handle(text, intent, context)
            
            if plugin_response:
                if isinstance(plugin_response, dict):
                    action_context = plugin_response.get('context', '')
                    success = plugin_response.get('success', True)
                    raw_response = plugin_response.get('raw_response', False)
                    
                    # Si el plugin indica que es respuesta completa, usarla tal cual
                    if raw_response:
                        response = action_context
                    else:
                        response = self._generate_natural_response(action_context, success)
                else:
                    response = self._generate_natural_response(str(plugin_response), True)
                return response

        # 2. Fallback a dataset
        if confidence >= 50 and intent != "conversacion":
            for item in self.dataset['intents']:
                if item['tag'] == intent:
                    response = random.choice(item['responses'])
                    break
        
        # 3. Delegar al Oráculo (LLM)
        if not response:
            model_type = self._decide_model(intent, confidence, text)
            print(f"Delegando al LLM (modelo: {model_type})...")
            
            memory_context = memory.get_context_for_llm(text, max_memories=5)
            enhanced_text = f"CONTEXTO:\n{memory_context}\n\nUSUARIO: {text}" if memory_context else text
            
            response = self.llm.chat(enhanced_text, model_type)
            
            if intent == "conversacion" and response and not response.startswith("No puedo responder"):
                self._extract_facts_automatically(text, response)
        
        return response
    
    def _extract_facts_automatically(self, user_text: str, eco_response: str):
        def extract_task():
            try:
                prompt = f"""Analiza esta conversación y extrae HECHOS importantes sobre el usuario.
Si no hay hechos, responde "NONE".
Usuario: {user_text}
Eco: {eco_response}
Responde SOLO con JSON: [{"category": "personal|preferencias|trabajo|salud|general", "fact": "hecho conciso", "confidence": 0.9}]"""
                extraction = self.llm.chat(prompt, "fast")
                if extraction and "NONE" not in extraction.upper():
                    json_match = re.search(r'\[[^\]]+\]', extraction)
                    if json_match:
                        facts = json.loads(json_match.group())
                        for fact_data in facts:
                            category = fact_data.get('category', 'general')
                            fact = fact_data.get('fact', '')
                            if fact:
                                result = memory.add(fact, category=category, confidence=fact_data.get('confidence', 0.8), source="inferred")
                                if result: print(f"[Memory] Hecho inferido: [{category}] {fact}")
            except Exception as e:
                print(f"[Memory] Error extrayendo hechos: {e}")
        threading.Thread(target=extract_task, daemon=True).start()