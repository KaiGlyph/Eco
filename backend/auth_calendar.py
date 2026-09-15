import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from plugins.calendar.plugin import get_google_service

print("Iniciando autenticación de Google Calendar...")
print("Se abrirá el navegador. Inicia sesión con tu cuenta de Google y acepta los permisos.")
print("(Si te sale 'Aplicación no verificada', haz clic en 'Configuración avanzada' y luego 'Ir a Eco (inseguro)').")

service = get_google_service()

if service:
    print("✅ Autenticación completada! Se creó el archivo token.json")
else:
    print("❌ Error en la autenticación")