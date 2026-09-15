import subprocess
import os
import shutil
from pathlib import Path
import re

def clean_app_name(text: str) -> str:
    """Limpia el texto para extraer solo el nombre de la aplicación"""
    text = text.lower()
    
    # Palabras y frases a eliminar (incluyendo 'puedes', 'podrías', etc.)
    trigger_patterns = [
        r'\bábreme\b', r'\bábre\b', r'\babre\b', r'\babrir\b',
        r'\blanza\b', r'\blanzar\b', r'\binicia\b', r'\biniciar\b',
        r'\bejecuta\b', r'\bejecutar\b', r'\babre la\b', r'\babre el\b',
        r'\babre los\b', r'\babre las\b', r'\beco\b', r'\bporfa\b',
        r'\bpor favor\b', r'\bquiero\b', r'\bjuego\b', r'\bque me\b',
        r'\bme\b', r'\bla aplicación\b', r'\bel juego\b',
        r'\bcierra\b', r'\bciérrame\b', r'\bcerrar\b', r'\btermina\b',
        r'\bterminar\b', r'\bcierre\b', r'\bciérralo\b',
        r'\bmata\b', r'\bmatar\b', r'\bfinaliza\b', r'\bfinalizar\b',
        r'\bapaga\b', r'\bapagar\b',
        r'\bpuedes\b', r'\bpodrias\b', r'\bpodrías\b', r'\bpodria\b', r'\bpodría\b',
        r'\bpor favor\b', r'\bporfa\b'
    ]
    
    for pattern in trigger_patterns:
        text = re.sub(pattern, '', text).strip()
    
    # Eliminar palabras sueltas comunes
    text = re.sub(r'\b(que|el|la|los|las|un|una|me|mi|de|del)\b', '', text).strip()
    
    return text

def find_application(app_name: str) -> str:
    """Busca la aplicación con scoring para priorizar coincidencias exactas"""
    app_name_lower = app_name.lower().strip()
    if not app_name_lower:
        return None
    
    # Alias comunes
    aliases = {
        'chrome': ['chrome', 'google chrome', 'navegador'],
        'firefox': ['firefox', 'mozilla'],
        'spotify': ['spotify'],
        'discord': ['discord'],
        'steam': ['steam'],
        'valorant': ['valorant', 'riot'],
        'minecraft': ['minecraft'],
        'calculadora': ['calculadora', 'calc'],
        'notepad': ['notepad', 'bloc de notas', 'notas'],
        'explorer': ['explorer', 'explorador', 'archivos'],
        'vscode': ['code', 'vscode', 'visual studio code'],
        'excel': ['excel', 'microsoft excel'],
        'word': ['word', 'microsoft word'],
    }
    
    search_terms = [app_name_lower]
    for key, variations in aliases.items():
        if any(var in app_name_lower for var in variations):
            search_terms.append(key)
            search_terms.extend(variations)
    
    candidates = []
    
    # 1. Buscar en el Menú Inicio
    start_menu_paths = [
        Path(os.environ.get('PROGRAMDATA', 'C:\\ProgramData')) / 'Microsoft' / 'Windows' / 'Start Menu' / 'Programs',
        Path(os.environ.get('APPDATA', '')) / 'Microsoft' / 'Windows' / 'Start Menu' / 'Programs',
    ]
    
    for start_path in start_menu_paths:
        if start_path.exists():
            for search_term in search_terms:
                for shortcut in start_path.rglob("*.lnk"):
                    name = shortcut.stem.lower()
                    if name == search_term:
                        candidates.append((100, str(shortcut)))
                    elif search_term in name:
                        candidates.append((50, str(shortcut)))
    
    # 2. Buscar en Program Files
    program_files = [
        Path(os.environ.get('PROGRAMFILES', 'C:\\Program Files')),
        Path(os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)')),
    ]
    
    for pf in program_files:
        if pf.exists():
            for search_term in search_terms:
                for folder in pf.rglob(f"*{search_term}*"):
                    if folder.is_dir():
                        for exe in folder.glob("*.exe"):
                            name_lower = exe.name.lower()
                            if ('uninstall' not in name_lower and 
                                'setup' not in name_lower and 
                                'crash' not in name_lower):
                                if name_lower == f"{search_term}.exe":
                                    candidates.append((100, str(exe)))
                                else:
                                    candidates.append((50, str(exe)))
    
    # 3. Buscar en PATH
    for search_term in search_terms:
        exe_path = shutil.which(search_term)
        if exe_path:
            candidates.append((100, exe_path))
    
    if candidates:
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]
    
    return None

def open_application(text: str) -> str:
    """Abre la aplicación"""
    app_name = clean_app_name(text)
    if not app_name:
        return "No me has dicho qué aplicación abrir."
    
    print(f"Buscando aplicación: '{app_name}'")
    exe_path = find_application(app_name)
    
    if exe_path:
        try:
            print(f"Encontrado: {exe_path}")
            if exe_path.endswith('.lnk'):
                subprocess.Popen(f'start "" "{exe_path}"', shell=True)
            else:
                subprocess.Popen([exe_path], shell=True)
            return f"Abriendo {app_name}."
        except Exception as e:
            return f"Encontré {app_name} pero no pude ejecutarlo: {str(e)}"
    else:
        return f"No encontré '{app_name}' en tu sistema."

def close_application(text: str) -> str:
    """Cierra la aplicación por nombre de proceso"""
    app_name = clean_app_name(text)
    if not app_name:
        return "No me has dicho qué aplicación cerrar."
    
    print(f"Cerrando aplicación: '{app_name}'")
    
    # Mapeo de nombres a procesos de Windows
    process_names = {
        'chrome': 'chrome',
        'google chrome': 'chrome',
        'firefox': 'firefox',
        'mozilla': 'firefox',
        'spotify': 'spotify',
        'discord': 'discord',
        'steam': 'steam',
        'valorant': 'valorant',
        'riot': 'valorant',
        'minecraft': 'minecraft',
        'calculadora': 'calc',
        'calc': 'calc',
        'notepad': 'notepad',
        'bloc de notas': 'notepad',
        'explorer': 'explorer',
        'explorador': 'explorer',
        'vscode': 'code',
        'visual studio code': 'code',
        'excel': 'excel',
        'microsoft excel': 'excel',
        'word': 'winword',
        'microsoft word': 'winword',
    }
    
    process_name = process_names.get(app_name, app_name)
    
    # Lista de procesos a intentar matar
    # (Algunas apps modernas de Windows usan ApplicationFrameHost)
    processes_to_kill = [f'{process_name}.exe']
    if process_name == 'calc':
        processes_to_kill.append('ApplicationFrameHost.exe')
    
    success = False
    for proc in processes_to_kill:
        try:
            # IMPORTANTE: shell=False con lista es mucho más fiable en Windows
            result = subprocess.run(
                ['taskkill', '/F', '/IM', proc],
                capture_output=True,
                text=True,
                shell=False
            )
            
            # Imprimir el resultado para depurar si falla
            print(f"Taskkill {proc}: {result.stdout.strip()} {result.stderr.strip()}")
            
            if result.returncode == 0:
                success = True
        except Exception as e:
            print(f"Error matando {proc}: {e}")
            
    if success:
        return f"Cerrando {app_name}."
    else:
        return f"No pude cerrar {app_name}. Asegúrate de que esté abierta."