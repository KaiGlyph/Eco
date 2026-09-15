import json
import os
from datetime import datetime

# Ruta del archivo de notas
NOTES_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'notes.json')

def _load_notes() -> list:
    """Carga las notas desde el archivo JSON"""
    if not os.path.exists(NOTES_FILE):
        return []
    try:
        with open(NOTES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []

def _save_notes(notes: list):
    """Guarda las notas en el archivo JSON"""
    os.makedirs(os.path.dirname(NOTES_FILE), exist_ok=True)
    with open(NOTES_FILE, 'w', encoding='utf-8') as f:
        json.dump(notes, f, ensure_ascii=False, indent=2)

def add_note(content: str) -> str:
    """Añade una nueva nota"""
    notes = _load_notes()
    
    # Generar ID único
    note_id = max([n['id'] for n in notes], default=0) + 1
    
    # Extraer tags automáticamente (palabras clave)
    tags = _extract_tags(content)
    
    note = {
        "id": note_id,
        "content": content,
        "created_at": datetime.now().isoformat(),
        "reminder_at": None,
        "calendar_link": False,
        "tags": tags
    }
    
    notes.append(note)
    _save_notes(notes)
    
    return f"Nota guardada: '{content}'"

def list_notes() -> str:
    """Lista todas las notas"""
    notes = _load_notes()
    
    if not notes:
        return "No tienes ninguna nota guardada."
    
    # Mostrar las 5 más recientes
    recent = notes[-5:]
    recent.reverse()  # Más reciente primero
    
    lines = [f"Tienes {len(notes)} notas. Las más recientes:"]
    for note in recent:
        date = datetime.fromisoformat(note['created_at']).strftime('%d/%m %H:%M')
        lines.append(f"  • {date}: {note['content']}")
    
    return "\n".join(lines)

def search_notes(query: str) -> str:
    """Busca notas por contenido o tags"""
    notes = _load_notes()
    query_lower = query.lower()
    
    results = [
        n for n in notes 
        if query_lower in n['content'].lower() or 
           any(query_lower in tag.lower() for tag in n.get('tags', []))
    ]
    
    if not results:
        return f"No encontré notas sobre '{query}'."
    
    lines = [f"Encontré {len(results)} nota(s):"]
    for note in results:
        date = datetime.fromisoformat(note['created_at']).strftime('%d/%m %H:%M')
        lines.append(f"  • {date}: {note['content']}")
    
    return "\n".join(lines)

def delete_note(query: str) -> str:
    """Elimina una nota por número o contenido"""
    notes = _load_notes()
    
    if not notes:
        return "No hay notas para eliminar."
    
    # Intentar buscar por número (ej: "elimina la nota 3")
    import re
    match = re.search(r'(\d+)', query)
    if match:
        note_num = int(match.group(1))
        if 1 <= note_num <= len(notes):
            deleted = notes.pop(note_num - 1)
            _save_notes(notes)
            return f"Nota eliminada: '{deleted['content']}'"
    
    # Buscar por contenido
    query_lower = query.lower()
    for i, note in enumerate(notes):
        if query_lower in note['content'].lower():
            deleted = notes.pop(i)
            _save_notes(notes)
            return f"Nota eliminada: '{deleted['content']}'"
    
    return "No encontré la nota para eliminar."

def edit_note(query: str, new_content: str = None) -> str:
    """Edita una nota existente."""
    notes = _load_notes()
    
    if not notes:
        return "No hay notas para editar."
    
    query_lower = query.lower().strip()
    
    # Si query está vacío o es "última", usar la última nota
    if not query_lower or query_lower in ["última", "la última", "ultima"]:
        if new_content:
            # Editar la última nota directamente
            note = notes[-1]
            old_content = note['content']
            note['content'] = new_content
            note['tags'] = _extract_tags(new_content)
            _save_notes(notes)
            return f"Nota actualizada. Antes: '{old_content}'. Ahora: '{new_content}'"
        else:
            note = notes[-1]
            return f"Última nota: '{note['content']}'. ¿Qué quieres poner en su lugar?"
    
    # Intentar buscar por número
    import re
    match = re.search(r'(\d+)', query_lower)
    if match:
        note_num = int(match.group(1))
        if 1 <= note_num <= len(notes):
            if new_content:
                old_content = notes[note_num - 1]['content']
                notes[note_num - 1]['content'] = new_content
                notes[note_num - 1]['tags'] = _extract_tags(new_content)
                _save_notes(notes)
                return f"Nota {note_num} actualizada. Antes: '{old_content}'. Ahora: '{new_content}'"
            else:
                note = notes[note_num - 1]
                return f"Nota {note_num}: '{note['content']}'. ¿Qué quieres poner en su lugar?"
    
    # Buscar por contenido (búsqueda parcial)
    for i, note in enumerate(notes):
        if query_lower in note['content'].lower():
            if new_content:
                old_content = note['content']
                note['content'] = new_content
                note['tags'] = _extract_tags(new_content)
                _save_notes(notes)
                return f"Nota actualizada. Antes: '{old_content}'. Ahora: '{new_content}'"
            else:
                return f"Encontré: '{note['content']}'. ¿Qué quieres poner?"
    
    return f"No encontré ninguna nota que diga '{query}'"


def get_notes_count() -> int:
    """Devuelve el número de notas (para el widget)"""
    return len(_load_notes())

def get_recent_notes(limit: int = 3) -> list:
    """Devuelve las notas más recientes (para el widget)"""
    notes = _load_notes()
    recent = notes[-limit:]
    recent.reverse()
    return recent

def _extract_tags(content: str) -> list:
    """Extrae tags automáticamente del contenido"""
    # Palabras clave comunes para categorizar
    tag_keywords = {
        'trabajo': ['reunión', 'jefe', 'oficina', 'proyecto', 'cliente', 'email', 'correo'],
        'personal': ['casa', 'familia', 'amigo', 'cumpleaños', 'cita'],
        'compras': ['comprar', 'tienda', 'supermercado', 'leche', 'pan'],
        'urgente': ['urgente', 'importante', 'ya', 'hoy', 'mañana'],
        'idea': ['idea', 'pensar', 'quizás', 'tal vez']
    }
    
    content_lower = content.lower()
    tags = []
    
    for tag, keywords in tag_keywords.items():
        if any(kw in content_lower for kw in keywords):
            tags.append(tag)
    
    return tags