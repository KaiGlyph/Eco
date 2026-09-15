import re
from core.plugin_base import BasePlugin

class MemoryPlugin(BasePlugin):
    name = "Memoria"
    description = "Gestión de la memoria a largo plazo de Eco"
    icon = "brain"
    priority = 85
    
    def get_intents(self):
        return [
            {"tag": "memoria_guardar", "patterns": ["recuerda que", "ten en cuenta que", "no olvides que", "guarda en tu memoria"], "responses": ["Guardando en mi memoria..."]},
            {"tag": "memoria_consultar", "patterns": ["que sabes de mi", "que recuerdas", "que sabes sobre", "muestrame tu memoria"], "responses": ["Consultando mi memoria..."]},
            {"tag": "memoria_borrar", "patterns": ["olvida que", "borra de tu memoria", "quita de tu memoria"], "responses": ["Borrando de mi memoria..."]},
            {"tag": "memoria_listar", "patterns": ["lista tus recuerdos", "que cosas sabes", "muestrame lo que sabes"], "responses": ["Listando mis recuerdos..."]}
        ]
    
    def get_forced_patterns(self):
        return [
            (["recuerda que", "ten en cuenta que", "no olvides que", "guarda en tu memoria"], "memoria_guardar"),
            (["que sabes de mi", "que recuerdas", "que sabes sobre", "muestrame tu memoria", "que cosas sabes"], "memoria_consultar"),
            (["olvida que", "borra de tu memoria", "quita de tu memoria"], "memoria_borrar"),
            (["lista tus recuerdos", "muestrame lo que sabes"], "memoria_listar"),
        ]
    
    def can_handle(self, text: str, intent: str, confidence: float) -> bool:
        return intent in ["memoria_guardar", "memoria_consultar", "memoria_borrar", "memoria_listar"]
    
    def _extract_structured_fact(self, text: str, brain) -> tuple:
        """Usa el LLM para extraer información estructurada del texto"""
        try:
            prompt = f"""Analiza esta frase y extrae la información importante sobre el usuario.
Responde en formato JSON estricto con estas claves:
- "category": una de estas [personal, preferencias, trabajo, salud, ubicacion, hobbies, general]
- "fact": el hecho concreto y conciso (sin "me llamo", "prefiero", etc., solo el dato)
- "confidence": número del 0.0 al 1.0

Ejemplos:
- "me llamo Jordi" → {{"category": "personal", "fact": "Nombre: Jordi", "confidence": 0.95}}
- "soy alérgico al gluten" → {{"category": "salud", "fact": "Alérgico al gluten", "confidence": 0.95}}
- "me gusta el café negro" → {{"category": "preferencias", "fact": "Le gusta el café negro", "confidence": 0.9}}

Frase a analizar: "{text}"

Responde SOLO con el JSON, nada más:"""
            
            response = brain.llm.chat(prompt, "fast")
            
            # Extraer JSON de la respuesta
            json_match = re.search(r'\{[^}]+\}', response)
            if json_match:
                import json
                data = json.loads(json_match.group())
                return data.get('category', 'general'), data.get('fact', text), data.get('confidence', 0.8)
            
            return 'general', text, 0.7
        except Exception as e:
            print(f"[Memory] Error extrayendo hecho estructurado: {e}")
            return 'general', text, 0.7
    
    def handle(self, text: str, intent: str, context: dict) -> str:
        from core.memory import memory
        
        lower_text = text.lower()
        brain = context.get('brain')
        
        if intent == "memoria_guardar":
            # Extraer el hecho a recordar
            fact_raw = lower_text
            for prefix in ["recuerda que", "ten en cuenta que", "no olvides que", "guarda en tu memoria que", "guarda en tu memoria"]:
                if fact_raw.startswith(prefix):
                    fact_raw = fact_raw[len(prefix):].strip()
                    break
            
            if not fact_raw:
                return "¿Qué quieres que recuerde?"
            
            # Usar LLM para extraer información estructurada
            if brain:
                category, fact, confidence = self._extract_structured_fact(fact_raw, brain)
            else:
                category = self._categorize(fact_raw)
                fact = fact_raw
                confidence = 0.8
            
            # Intentar guardar (puede ser duplicado)
            result = memory.add(fact, category=category, confidence=confidence)
            
            if result:
                return f"Lo he guardado: {fact} (categoría: {category})."
            else:
                return f"Ya tenía ese dato en mi memoria: {fact}"
        
        elif intent == "memoria_consultar":
            if any(p in lower_text for p in ["de mi", "sobre mi", "acerca de mi", "que recuerdas", "que sabes"]):
                results = memory.get_all()
            else:
                query = lower_text
                for prefix in ["que sabes sobre", "que sabes de", "que recuerdas de", "que sabes acerca de"]:
                    if query.startswith(prefix):
                        query = query[len(prefix):].strip()
                        break
                results = memory.search(query) if query else memory.get_all()
            
            if not results:
                return "Aún no me has contado nada sobre ti. ¿Quieres contarme algo?"
            
            lines = [f"Tengo {len(results)} dato(s) sobre ti:"]
            for mem in results[:10]:
                lines.append(f"  • {mem['fact']}")
            
            return "\n".join(lines)
        
        elif intent == "memoria_borrar":
            query = lower_text
            for prefix in ["olvida que", "borra de tu memoria", "quita de tu memoria"]:
                if query.startswith(prefix):
                    query = query[len(prefix):].strip()
                    break
            
            results = memory.search(query)
            if not results:
                return "No encontré nada sobre eso en mi memoria."
            
            removed = memory.remove(results[0]['id'])
            if removed:
                return f"He olvidado: {results[0]['fact']}"
            
            return "No pude borrar ese dato."
        
        elif intent == "memoria_listar":
            all_memories = memory.get_all()
            if not all_memories:
                return "Mi memoria está vacía. ¿Quieres contarme algo sobre ti?"
            
            lines = [f"Tengo {len(all_memories)} datos guardados:"]
            for mem in all_memories[-10:]:
                lines.append(f"  • [{mem['category']}] {mem['fact']}")
            
            return "\n".join(lines)
        
        return "No entendí qué hacer con mi memoria."
    
    def _categorize(self, fact: str) -> str:
        fact_lower = fact.lower()
        categories = {
            'salud': ['alérgico', 'alergia', 'enfermo', 'medicina', 'dieta', 'vegetariano', 'vegano'],
            'preferencias': ['prefiero', 'me gusta', 'odio', 'detesto', 'favorito', 'colores', 'comida', 'café'],
            'trabajo': ['trabajo', 'oficina', 'jefe', 'empresa', 'proyecto', 'reunión', 'desarrollador'],
            'personal': ['familia', 'amigo', 'pareja', 'hijo', 'padre', 'madre', 'casa', 'llamo', 'nombre'],
            'ubicacion': ['vivo en', 'ciudad', 'país', 'calle', 'dirección'],
            'hobbies': ['juego', 'deporte', 'leer', 'música', 'cine', 'series', 'cocinar']
        }
        
        for category, keywords in categories.items():
            if any(kw in fact_lower for kw in keywords):
                return category
        
        return 'general'