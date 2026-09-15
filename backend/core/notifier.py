import threading
from plyer import notification

def send_notification(title: str, message: str, timeout: int = 10):
    """
    Envía una notificación nativa de Windows en un hilo separado.
    """
    def _notify():
        try:
            notification.notify(
                title=title,
                message=message,
                app_name="Eco",
                timeout=timeout
            )
            print(f"[Notifier] Notificación enviada: {title} - {message}")
        except Exception as e:
            print(f"[Notifier] Error enviando notificación: {e}")

    # Ejecutar en segundo plano para no congelar la respuesta de voz
    threading.Thread(target=_notify, daemon=True).start()