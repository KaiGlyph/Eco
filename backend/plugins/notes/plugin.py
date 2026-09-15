import json
import os
import sys
import re
from datetime import datetime
from core.plugin_base import BasePlugin

# ==========================================
# RUTA PERSISTENTE PARA LAS NOTAS
# ==========================================
if getattr(sys, 'frozen', False):
    # En modo empaquetado, guardar en AppData
    app_data = os.path.join(
        os.environ.get('LOCALAPPDATA', os.path.expanduser('~')),
        'Eco',
        'data'
    )
    os.makedirs(app_data, exist_ok=True)
    NOTES_FILE = os.path.join(app_data, 'notes.json')
else:
    # En modo desarrollo, usar la ruta relativa original
    NOTES_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'notes.json')

# ==========================================
# GESTIÓN DE ESTADO
# ==========================================
def _load_notes() -> list:
    if not os.path.exists(NOTES_FILE):
        return []
    try:
        with open(NOTES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []

def _save_notes(notes: list):
    os.makedirs(os.path.dirname(NOTES_FILE), exist_ok=True)
    with open(NOTES_FILE, 'w', encoding='utf-8') as f:
        json.dump(notes, f, ensure_ascii=False, indent=2)

def _extract_tags(content: str) -> list:
    tag_keywords = {
        'trabajo': ['reunión', 'jefe', 'oficina', 'proyecto', 'cliente', 'email', 'correo'],
        'personal': ['casa', 'familia', 'amigo', 'cumpleaños', 'cita'],
        'compras': ['comprar', 'tienda', 'supermercado', 'leche', 'pan'],
        'urgente': ['urgente', 'importante', 'ya', 'hoy', 'mañana'],
        'idea': ['idea', 'pensar', 'quizás', 'tal vez']
    }
    content_lower = content.lower()
    return [tag for tag, keywords in tag_keywords.items() if any(kw in content_lower for kw in keywords)]

def _find_note_index(query: str, notes: list) -> int:
    query_lower = query.lower().strip()
    match = re.search(r'(\d+)', query_lower)
    if match:
        note_num = int(match.group(1))
        if 1 <= note_num <= len(notes):
            return note_num - 1
    if query_lower in ["última", "la última", "ultima"]:
        return len(notes) - 1
    for i, note in enumerate(notes):
        if query_lower in note['content'].lower():
            return i
    return -1

# ==========================================
# FUNCIONES DE EJECUCIÓN
# ==========================================
def add_note(content: str) -> dict:
    # Evitar guardar frases vacías o demasiado cortas (ruido)
    if not content or len(content.strip()) < 3:
        return {"action": "note_added", "success": False, "context": "El contenido de la nota es demasiado corto.", "raw_response": True}
    
    notes = _load_notes()
    note_id = max([n['id'] for n in notes], default=0) + 1
    tags = _extract_tags(content)
    note = {
        "id": note_id, "content": content, "created_at": datetime.now().isoformat(),
        "reminder_at": None, "calendar_link": False, "tags": tags
    }
    notes.append(note)
    _save_notes(notes)
    return {
        "action": "note_added",
        "success": True,
        "context": f"Nota guardada: '{content}'"
    }

def list_notes() -> dict:
    notes = _load_notes()
    if not notes:
        return {"action": "notes_listed", "success": True, "context": "No tienes ninguna nota guardada.", "raw_response": True}
    
    recent = notes[-5:][::-1]
    lines = [f"Tienes {len(notes)} notas. Las más recientes:"]
    for note in recent:
        date = datetime.fromisoformat(note['created_at']).strftime('%d/%m %H:%M')
        lines.append(f"  • {date}: {note['content']}")
    
    return {"action": "notes_listed", "success": True, "context": "\n".join(lines), "raw_response": True}

def search_notes(query: str) -> dict:
    notes = _load_notes()
    query_lower = query.lower()
    results = [n for n in notes if query_lower in n['content'].lower() or any(query_lower in tag.lower() for tag in n.get('tags', []))]
    
    if not results:
        return {"action": "notes_searched", "success": True, "context": f"No encontré notas sobre '{query}'.", "raw_response": True}
    
    lines = [f"Encontré {len(results)} nota(s):"]
    for note in results:
        date = datetime.fromisoformat(note['created_at']).strftime('%d/%m %H:%M')
        lines.append(f"  • {date}: {note['content']}")
    
    return {"action": "notes_searched", "success": True, "context": "\n".join(lines), "raw_response": True}

def delete_note(query: str) -> dict:
    notes = _load_notes()
    if not notes:
        return {"action": "note_deleted", "success": False, "context": "No hay notas para eliminar.", "raw_response": True}
    
    idx = _find_note_index(query, notes)
    if idx != -1:
        deleted = notes.pop(idx)
        _save_notes(notes)
        return {"action": "note_deleted", "success": True, "context": f"Nota eliminada: '{deleted['content']}'"}
    
    return {"action": "note_deleted", "success": False, "context": f"No encontré la nota '{query}' para eliminar.", "raw_response": True}

def clear_notes() -> dict:
    """Elimina TODAS las notas"""
    notes = _load_notes()
    if not notes:
        return {"action": "notes_cleared", "success": True, "context": "No había notas que eliminar.", "raw_response": True}
    
    count = len(notes)
    _save_notes([])
    return {"action": "notes_cleared", "success": True, "context": f"Se han eliminado {count} notas. La lista está vacía.", "raw_response": True}

def edit_note(query: str, new_content: str = None) -> dict:
    notes = _load_notes()
    if not notes:
        return {"action": "note_edited", "success": False, "context": "No hay notas para editar.", "raw_response": True}
    
    idx = _find_note_index(query, notes)
    if idx == -1:
        return {"action": "note_edited", "success": False, "context": f"No encontré la nota '{query}'.", "raw_response": True}
    
    note = notes[idx]
    
    if new_content:
        old_content = note['content']
        note['content'] = new_content
        note['tags'] = _extract_tags(new_content)
        _save_notes(notes)
        return {
            "action": "note_edited",
            "success": True,
            "context": f"Nota actualizada. Antes: '{old_content}'. Ahora: '{new_content}'"
        }
    
    return {
        "action": "edit_prompt",
        "success": True,
        "context": f"Encontré esta nota: '{note['content']}'. ¿Qué quieres poner en su lugar?",
        "pending_query": query
    }


# ==========================================
# PLUGIN NOTES
# ==========================================
class NotesPlugin(BasePlugin):
    name = "Notas"
    description = "Gestión de notas personales con lenguaje natural"
    icon = "sticky-note"
    priority = 60
    
    def get_intents(self):
        return [
            {"tag": "añadir_nota", "patterns": ["anota", "apunta", "toma nota", "recuerda", "guárdame"], "responses": ["..."]},
            {"tag": "listar_notas", "patterns": ["qué notas", "que notas", "mis notas", "lista las notas", "ver notas"], "responses": ["..."]},
            {"tag": "buscar_nota", "patterns": ["busca en las notas", "busca la nota", "encuentra la nota"], "responses": ["..."]},
            {"tag": "eliminar_nota", "patterns": ["elimina", "borra", "quita la nota"], "responses": ["..."]},
            {"tag": "editar_nota", "patterns": ["edita", "modifica", "cambia", "corrige"], "responses": ["..."]},
            {"tag": "note_detectado", "patterns": ["nota", "notas"], "responses": ["..."]}
        ]

    def get_forced_patterns(self):
        return [
            (["anota", "apunta", "toma nota", "guárdame", "tengo que", "debo"], "añadir_nota"),
            (["qué notas", "que notas", "mis notas", "lista las notas", "ver notas", "consultar notas"], "listar_notas"),
            (["busca en las notas", "busca la nota", "encuentra la nota", "dónde apunté"], "buscar_nota"),
            (["elimina", "borra", "quita la nota"], "eliminar_nota"),
            (["edita", "modifica", "cambia", "corrige", "actualiza"], "editar_nota"),
            (["nota", "notas"], "note_detectado")
        ]

    def can_handle(self, text: str, intent: str, confidence: float) -> bool:
        # Para intents de notas, verificar que el texto realmente parezca sobre notas
        if intent in ["añadir_nota", "listar_notas", "buscar_nota", "eliminar_nota", "editar_nota", "note_detectado"]:
            lower_text = text.lower()
            
            # Palabras clave que indican que es sobre notas
            note_keywords = ["nota", "notas", "apunta", "anota", "guárdame", 
                           "borra", "elimina", "edita", "modifica", 
                           "cambia", "busca", "lista", "mis notas", "qué notas", "que notas"]
            
            # Si contiene palabras específicas de notas, lo manejamos
            if any(kw in lower_text for kw in note_keywords):
                return True
            
            # Si dice "recuerda" o "no olvides", verificar si hay componente temporal
            # Si hay tiempo, NO es una nota, es un recordatorio/temporizador
            if "recuerda" in lower_text or "no olvides" in lower_text or "tengo que" in lower_text or "debo" in lower_text:
                # Buscar patrones de tiempo
                time_patterns = [
                    r'\d+\s*(minuto|hora|segundo)',  # "30 minutos", "1 hora"
                    r'en\s+\d+',  # "en 30"
                    r'dentro de',  # "dentro de"
                    r'mañana|tarde|noche',  # "mañana", "esta tarde"
                    r'a las \d+',  # "a las 10"
                ]
                
                # Si encuentra algún patrón temporal, NO es una nota
                for pattern in time_patterns:
                    if re.search(pattern, lower_text):
                        return False
                
                # Si no hay tiempo, es una nota
                return True
            
            # Si no contiene nada relevante, no lo manejamos
            return False
        return False

    def _parse_with_llm(self, text: str, schema: str, examples: str, llm_engine) -> dict:
        if not llm_engine:
            return {}
        prompt = f"""Analiza esta frase sobre notas y extrae la información en JSON estricto.
Frase: "{text}"
Esquema requerido: {schema}
Ejemplos: {examples}
Responde SOLO con el JSON:"""
        try:
            response = llm_engine.chat(prompt, "fast")
            json_match = re.search(r'\{[^}]+\}', response)
            if json_match:
                return json.loads(json_match.group())
            return {}
        except Exception as e:
            print(f"[NotesPlugin] Error parseando con LLM: {e}")
            return {}

    def handle(self, text: str, intent: str, context: dict) -> dict:
        lower_text = text.lower()
        brain = context.get('brain')
        llm = brain.llm if brain else None
        
        # Si hay una edición pendiente, verificar si el usuario está continuándola
        if brain and getattr(brain, 'pending_note_edit', None):
            no_continuation_words = ["anota", "apunta", "recuerda", "borra", "elimina", "edita", "modifica", "cambia", "busca", "lista", "qué notas", "que notas", "mis notas"]
            if not any(lower_text.startswith(w) for w in no_continuation_words):
                query = brain.pending_note_edit
                brain.pending_note_edit = None
                return edit_note(query, text)
            else:
                brain.pending_note_edit = None
        
        # Esquema AMPLIADO con acción "clear"
        schema = '{"action": "add"|"list"|"search"|"delete"|"edit"|"clear", "content": "string|null", "query": "string|null", "new_content": "string|null"}'
        examples = '''
        - "Anota que tengo que comprar leche" -> {"action": "add", "content": "tengo que comprar leche", "query": null, "new_content": null}
        - "Qué notas tengo" -> {"action": "list", "content": null, "query": null, "new_content": null}
        - "Busca la nota del trabajo" -> {"action": "search", "content": null, "query": "trabajo", "new_content": null}
        - "Borra la última nota" -> {"action": "delete", "content": null, "query": "última", "new_content": null}
        - "Elimina la nota de la leche" -> {"action": "delete", "content": null, "query": "leche", "new_content": null}
        - "Elimina todas las notas" -> {"action": "clear", "content": null, "query": null, "new_content": null}
        - "Borra todo" -> {"action": "clear", "content": null, "query": null, "new_content": null}
        - "Limpia las notas" -> {"action": "clear", "content": null, "query": null, "new_content": null}
        - "Cambia la nota de la leche por pan" -> {"action": "edit", "content": null, "query": "leche", "new_content": "pan"}
        - "Edita la última nota y pon que llega a las 5" -> {"action": "edit", "content": null, "query": "última", "new_content": "llega a las 5"}
        '''
        
        command = self._parse_with_llm(lower_text, schema, examples, llm)
        action = command.get("action", "list")
        
        if action == "add":
            content = command.get("content") or text
            return add_note(content)
        elif action == "list":
            return list_notes()
        elif action == "search":
            query = command.get("query") or text
            return search_notes(query)
        elif action == "delete":
            query = command.get("query") or "última"
            return delete_note(query)
        elif action == "clear":
            return clear_notes()
        elif action == "edit":
            query = command.get("query") or "última"
            new_content = command.get("new_content")
            result = edit_note(query, new_content)
            if result.get("action") == "edit_prompt" and brain:
                brain.pending_note_edit = result.get("pending_query", "última")
            return result
        
        return {"action": "unknown", "success": False, "context": "No entendí el comando de notas.", "raw_response": True}