import os
import shutil
from pathlib import Path

def build_backend():
    """Copia el backend a la carpeta de recursos de Tauri"""
    
    # Carpeta de destino (recursos de Tauri)
    tauri_resources = Path("../frontend/src-tauri/resources/backend")
    tauri_resources.mkdir(parents=True, exist_ok=True)
    
    # Carpetas y archivos a copiar
    items_to_copy = [
        "main.py",
        "core",
        "plugins",
        "data",
        "requirements.txt",
        "audio_files",
    ]
    
    for item in items_to_copy:
        src = Path(item)
        dst = tauri_resources / item
        
        if src.exists():
            if src.is_dir():
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
                print(f"✓ Copiado: {item}/")
            else:
                shutil.copy2(src, dst)
                print(f"✓ Copiado: {item}")
    
    print("\n✅ Backend preparado para Tauri")

if __name__ == "__main__":
    build_backend()