class WebSocketService {
  private ws: WebSocket | null = null;
  private url = "ws://127.0.0.1:8000/ws";

  connect(onMessage: (data: string) => void) {
    this.ws = new WebSocket(this.url);

    this.ws.onopen = () => {
      console.log("✅ Conectado con Eco");
    };

    this.ws.onmessage = (event) => {
      onMessage(event.data);
    };

    this.ws.onerror = (error) => {
      console.error("❌ Error WebSocket:", error);
    };

    this.ws.onclose = () => {
      console.log("🔌 Desconectado de Eco");
    };
  }

  send(message: string) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(message);
    }
  }

  disconnect() {
    this.ws?.close();
  }
}

export default new WebSocketService();