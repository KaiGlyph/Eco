import { useEffect, useRef, useState } from 'react';

interface EcoMessage {
  type: 'state' | 'audio' | 'text';
  state?: 'idle' | 'listening' | 'thinking' | 'speaking';
  audioUrl?: string;
  text?: string;
}

export function useEcoWebSocket() {
  const [state, setState] = useState<'idle' | 'listening' | 'thinking' | 'speaking'>('idle');
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    // Conectar al WebSocket del backend
    const ws = new WebSocket('ws://localhost:8000/ws');
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('[WebSocket] Conectado al backend');
    };

    ws.onmessage = (event) => {
      const data: EcoMessage = JSON.parse(event.data);
      
      if (data.type === 'state' && data.state) {
        setState(data.state);
      }
      
      if (data.type === 'audio' && data.audioUrl) {
        setAudioUrl(data.audioUrl);
      }
    };

    ws.onclose = () => {
      console.log('[WebSocket] Desconectado');
    };

    ws.onerror = (error) => {
      console.error('[WebSocket] Error:', error);
    };

    return () => {
      ws.close();
    };
  }, []);

  return { state, audioUrl };
}