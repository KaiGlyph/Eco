import json
import os
import sys
from datetime import datetime
from typing import List, Dict, Optional
import re

# ==========================================
# RUTA PERSISTENTE PARA LA MEMORIA (Se modifica y guarda)
# ==========================================
if getattr(sys, 'frozen', False):
    # En modo empaquetado, guardar en AppData para que sea persistente y tenga permisos de escritura
    app_data = os.path.join(
        os.environ.get('LOCALAPPDATA', os.path.expanduser('~')),
        'Eco',
        'data'
    )
    os.makedirs(app_data, exist_ok=True)
    MEMORY_FILE = os.path.join(app_data, 'memory.json')
else:
    # En modo desarrollo, usar la carpeta local del proyecto
    MEMORY_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'memory.json')

class Memory:
    def __init__(self):
        self.memories: List[Dict] = self._load()
    
    def _load(self) -> List[Dict]:
        if not os.path.exists(MEMORY_FILE):
            return []
        try:
            with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []
    
    def _save(self):
        os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)
        with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.memories, f, ensure_ascii=False, indent=2)
    
    def _normalize_text(self, text: str) -> str:
        """Normaliza texto para comparar duplicados"""
        text = text.lower().strip()
        text = re.sub(r'[^\w\s]', '', text)  # Quitar puntuación
        text = re.sub(r'\s+', ' ', text)  # Normalizar espacios
        return text
    
    def _is_duplicate(self, fact: str, category: str, threshold: float = 0.8) -> bool:
        """Verifica si ya existe un hecho similar"""
        normalized_new = self._normalize_text(fact)
        
        for mem in self.memories:
            if mem['category'] != category:
                continue
            
            normalized_existing = self._normalize_text(mem['fact'])
            
            # Si es exactamente igual
            if normalized_new == normalized_existing:
                return True
            
            # Si uno contiene al otro (ej: "jordi" está en "me llamo jordi")
            if normalized_new in normalized_existing or normalized_existing in normalized_new:
                return True
            
            # Similaridad simple por palabras compartidas
            words_new = set(normalized_new.split())
            words_existing = set(normalized_existing.split())
            
            if len(words_new) > 0 and len(words_existing) > 0:
                similarity = len(words_new & words_existing) / max(len(words_new), len(words_existing))
                if similarity >= threshold:
                    return True
        
        return False
    
    def add(self, fact: str, category: str = "general", confidence: float = 1.0, source: str = "conversation") -> Optional[Dict]:
        """Añade un hecho solo si no es duplicado"""
        # Verificar duplicados
        if self._is_duplicate(fact, category):
            print(f"[Memory] Duplicado detectado, no se guarda: '{fact}'")
            return None
        
        memory = {
            "id": len(self.memories) + 1,
            "fact": fact,
            "category": category,
            "created_at": datetime.now().isoformat(),
            "confidence": confidence,
            "source": source
        }
        self.memories.append(memory)
        self._save()
        return memory
    
    def update(self, memory_id: int, new_fact: str) -> bool:
        """Actualiza un hecho existente"""
        for mem in self.memories:
            if mem['id'] == memory_id:
                mem['fact'] = new_fact
                self._save()
                return True
        return False
    
    def remove(self, memory_id: int) -> bool:
        for i, mem in enumerate(self.memories):
            if mem['id'] == memory_id:
                removed = self.memories.pop(i)
                self._save()
                return True
        return False
    
    def get_all(self) -> List[Dict]:
        return self.memories
    
    def get_by_category(self, category: str) -> List[Dict]:
        return [m for m in self.memories if m['category'] == category]
    
    def search(self, query: str) -> List[Dict]:
        query_lower = query.lower()
        results = []
        for mem in self.memories:
            if query_lower in mem['fact'].lower() or query_lower in mem['category'].lower():
                results.append(mem)
        return results
    
    def get_context_for_llm(self, user_query: str, max_memories: int = 5) -> str:
        relevant = self.search(user_query)
        
        if not relevant:
            relevant = self.memories[-max_memories:] if self.memories else []
        
        if not relevant:
            return ""
        
        lines = ["Información relevante sobre el usuario:"]
        for mem in relevant[:max_memories]:
            lines.append(f"- {mem['fact']} (categoría: {mem['category']})")
        
        return "\n".join(lines)
    
    def get_count(self) -> int:
        return len(self.memories)
    
    def clear(self):
        """Limpia toda la memoria (útil para pruebas)"""
        self.memories = []
        self._save()


# Instancia global
memory = Memory()