from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple


class BasePlugin(ABC):
    """Clase base que todos los plugins de Eco deben implementar."""
    
    # Metadata del plugin (sobreescribir en cada plugin)
    name: str = "Plugin sin nombre"
    description: str = ""
    icon: str = "box"
    priority: int = 50  # 0-100, mayor = más prioridad en caso de conflicto
    enabled: bool = True
    
    @abstractmethod
    def get_intents(self) -> List[Dict]:
        """Devuelve la lista de intenciones que maneja este plugin.
        Cada intención es un dict con:
        {
            "tag": "nombre_unico",
            "patterns": ["frase 1", "frase 2"],
            "responses": ["respuesta por defecto"]
        }
        """
        pass
    
    @abstractmethod
    def get_forced_patterns(self) -> List[Tuple[List[str], str]]:
        """Devuelve patrones para forzado de intención.
        Lista de tuplas: (lista_de_keywords, intent_tag)
        Ejemplo: (["anota", "apunta"], "añadir_nota")
        """
        pass
    
    @abstractmethod
    def can_handle(self, text: str, intent: str, confidence: float) -> bool:
        """Indica si este plugin puede manejar la intención dada."""
        pass
    
    @abstractmethod
    def handle(self, text: str, intent: str, context: dict) -> str:
        """Ejecuta la acción y devuelve la respuesta de texto.
        
        Args:
            text: Texto original del usuario
            intent: Intención detectada
            context: Diccionario con información compartida (lower_text, brain, etc.)
        """
        pass
    
    def on_load(self):
        """Se llama cuando el plugin se carga. Útil para inicialización."""
        pass
    
    def on_unload(self):
        """Se llama cuando el plugin se desactiva. Útil para limpieza."""
        pass
    
    def get_metadata(self) -> Dict:
        """Devuelve metadata del plugin para la UI."""
        return {
            "name": self.name,
            "description": self.description,
            "icon": self.icon,
            "enabled": self.enabled,
            "intents_count": len(self.get_intents()),
            "forced_patterns_count": len(self.get_forced_patterns())
        }