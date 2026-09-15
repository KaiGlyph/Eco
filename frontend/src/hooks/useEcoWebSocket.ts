import { useEffect, useRef, useState } from 'react';

export interface ChatMessage {
  id: string;
  user: string;
  eco: string;
  cameraImage?: string;
  motionVideo?: string;
  timestamp: Date;
}

export function useEcoWebSocket() {
  const [state, setState] = useState<'idle' | 'listening' | 'thinking' | 'speaking'>('idle');
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isChatOpen, setIsChatOpen] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);

  const sendMessage = (text: string) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      console.log('[SendMessage] Enviando:', text);
      
      const userMessage: ChatMessage = {
        id: `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`,
        user: text,
        eco: '',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, userMessage]);

      const message = JSON.stringify({
        type: 'voice',
        text: text
      });
      
      console.log('[SendMessage] Mensaje enviado:', message);
      wsRef.current.send(message);
    } else {
      console.error('[SendMessage] WebSocket NO está abierto. Estado:', wsRef.current?.readyState);
    }
  };

  const updateChatState = (isOpen: boolean) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      console.log('[ChatState] Notificando al backend: chat', isOpen ? 'abierto' : 'cerrado');
      wsRef.current.send(JSON.stringify({
        type: 'chat_state',
        is_open: isOpen
      }));
    }
  };

  useEffect(() => {
    updateChatState(isChatOpen);
  }, [isChatOpen]);

  useEffect(() => {
    const connect = () => {
      const ws = new WebSocket('ws://localhost:8000/ws');
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('[WebSocket] Conectado al backend');
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === 'state' && data.state) {
            setState(data.state);
          }
          if (data.type === 'audio_play' && data.url) {
            setAudioUrl(data.url);
          }
          // Manejar alertas de movimiento
          if (data.type === 'motion_alert') {
            const alertMessage: ChatMessage = {
              id: `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`,
              user: "Sistema",
              eco: data.message || "He detectado movimiento.",
              cameraImage: data.camera_image || undefined,
              motionVideo: data.motion_video || undefined,
              timestamp: new Date(),
            };
            
            setMessages(prev => [...prev, alertMessage]);
          }
          // Manejar alertas de presencia
          if (data.type === 'presence_alert') {
            const presenceMessage: ChatMessage = {
              id: `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`,
              user: "Sistema",
              eco: data.message || "",
              timestamp: new Date(),
            };
            
            setMessages(prev => [...prev, presenceMessage]);
          }
          if (data.type === 'conversation' && data.user && data.eco) {
            const newMessage: ChatMessage = {
              id: `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`,
              user: data.user,
              eco: data.eco,
              cameraImage: data.camera_image || undefined, // Capturar imagen de cámara
              timestamp: new Date(),
            };
            
            setMessages(prev => {
              const isDuplicate = prev.some(
                msg => msg.user === newMessage.user && msg.eco === newMessage.eco
              );
              if (isDuplicate) return prev;
              return [...prev, newMessage];
            });
          }
        } catch (e) {
          console.error('[WebSocket] Error parsing message:', e);
        }
      };

      ws.onclose = () => {
        console.log('[WebSocket] Desconectado');
        reconnectTimeoutRef.current = window.setTimeout(connect, 2000);
      };

      ws.onerror = (error) => {
        console.error('[WebSocket] Error:', error);
      };
    };

    connect();

    return () => {
      if (reconnectTimeoutRef.current !== null) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  return { state, audioUrl, messages, sendMessage, isChatOpen, setIsChatOpen };
}