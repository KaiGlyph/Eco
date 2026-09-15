import os
import importlib
import sys
from typing import List, Optional, Dict

from .plugin_base import BasePlugin


class PluginManager:
    """Gestor de plugins de Eco. Descubre y carga plugins automáticamente."""
    
    def __init__(self, plugins_dir: str):
        self.plugins_dir = plugins_dir
        self.plugins: List[BasePlugin] = []
        self._plugin_registry: Dict[str, BasePlugin] = {}  # intent_tag -> plugin
        
        self._discover_plugins()
        self._build_registry()
    
    def _discover_plugins(self):
        """Descubre todos los plugins en la carpeta plugins/"""
        print(f"[PluginManager] Descubriendo plugins en: {self.plugins_dir}")
        
        if not os.path.exists(self.plugins_dir):
            print(f"[PluginManager] La carpeta de plugins no existe: {self.plugins_dir}")
            return
        
        # Añadir la carpeta backend al sys.path si no está
        backend_dir = os.path.dirname(self.plugins_dir)
        if backend_dir not in sys.path:
            sys.path.insert(0, backend_dir)
        
        # Recorrer cada subcarpeta de plugins
        for item in os.listdir(self.plugins_dir):
            plugin_path = os.path.join(self.plugins_dir, item)
            
            # Solo carpetas (no archivos, no __pycache__)
            if not os.path.isdir(plugin_path):
                continue
            if item.startswith('_') or item == '__pycache__':
                continue
            
            # Buscar archivo plugin.py
            plugin_file = os.path.join(plugin_path, 'plugin.py')
            if not os.path.exists(plugin_file):
                print(f"[PluginManager] ⚠ {item}: No tiene plugin.py, saltando")
                continue
            
            try:
                # Importar el módulo dinámicamente
                module_name = f"plugins.{item}.plugin"
                
                # Si ya está cargado, recargar (útil para desarrollo)
                if module_name in sys.modules:
                    module = importlib.reload(sys.modules[module_name])
                else:
                    module = importlib.import_module(module_name)
                
                # Buscar la clase que hereda de BasePlugin
                plugin_class = None
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and 
                        issubclass(attr, BasePlugin) and 
                        attr is not BasePlugin):
                        plugin_class = attr
                        break
                
                if plugin_class is None:
                    print(f"[PluginManager] ⚠ {item}: No se encontró clase BasePlugin")
                    continue
                
                # Instanciar el plugin
                plugin = plugin_class()
                plugin.on_load()
                self.plugins.append(plugin)
                print(f"[PluginManager] ✓ Plugin cargado: {plugin.name}")
                
            except Exception as e:
                print(f"[PluginManager] ✗ Error cargando {item}: {e}")
                import traceback
                traceback.print_exc()
        
        print(f"[PluginManager] Total plugins cargados: {len(self.plugins)}")
    
    def _build_registry(self):
        """Construye el registro de intenciones -> plugins"""
        self._plugin_registry = {}
        
        # Ordenar plugins por prioridad (mayor primero)
        sorted_plugins = sorted(self.plugins, key=lambda p: p.priority, reverse=True)
        
        for plugin in sorted_plugins:
            if not plugin.enabled:
                continue
            
            # Registrar intenciones
            for intent_def in plugin.get_intents():
                tag = intent_def['tag']
                if tag in self._plugin_registry:
                    print(f"[PluginManager] ⚠ Intención duplicada: {tag}")
                self._plugin_registry[tag] = plugin
        
        print(f"[PluginManager] Intenciones registradas: {len(self._plugin_registry)}")
    
    def get_plugin_for_intent(self, intent: str) -> Optional[BasePlugin]:
        """Devuelve el plugin responsable de una intención."""
        return self._plugin_registry.get(intent)
    
    def get_all_intents(self) -> List[Dict]:
        """Devuelve todas las intenciones de todos los plugins (para dataset)."""
        all_intents = []
        for plugin in self.plugins:
            if plugin.enabled:
                all_intents.extend(plugin.get_intents())
        return all_intents
    
    def get_all_forced_patterns(self) -> List[tuple]:
        """Devuelve todos los patrones forzados de todos los plugins, ordenados por prioridad."""
        all_patterns = []
        
        # Ordenar plugins por prioridad (mayor primero)
        sorted_plugins = sorted(self.plugins, key=lambda p: p.priority, reverse=True)
        
        for plugin in sorted_plugins:
            if plugin.enabled:
                for keywords, intent_tag in plugin.get_forced_patterns():
                    all_patterns.append((keywords, intent_tag, plugin))
        
        return all_patterns
    
    def get_all_plugins_metadata(self) -> List[Dict]:
        """Devuelve metadata de todos los plugins (para UI)."""
        return [p.get_metadata() for p in self.plugins]
    
    def enable_plugin(self, plugin_name: str) -> bool:
        """Activa un plugin."""
        for plugin in self.plugins:
            if plugin.name == plugin_name:
                plugin.enabled = True
                self._build_registry()
                return True
        return False
    
    def disable_plugin(self, plugin_name: str) -> bool:
        """Desactiva un plugin."""
        for plugin in self.plugins:
            if plugin.name == plugin_name:
                plugin.enabled = False
                self._build_registry()
                return True
        return False
    
    def reload_plugins(self):
        """Recarga todos los plugins (útil durante desarrollo)."""
        for plugin in self.plugins:
            plugin.on_unload()
        self.plugins = []
        self._plugin_registry = {}
        self._discover_plugins()
        self._build_registry()