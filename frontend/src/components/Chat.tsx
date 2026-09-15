import { useState, useEffect, useRef } from 'react';
import type { ChatMessage } from '../hooks/useEcoWebSocket';

interface ChatProps {
  messages: ChatMessage[];
  isSpeaking: boolean;
  audioData?: Uint8Array;
  onSendMessage: (text: string) => void;
}

export default function Chat({ messages, isSpeaking, onSendMessage }: ChatProps) {
  const [inputText, setInputText] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputText.trim()) {
      onSendMessage(inputText.trim());
      setInputText('');
    }
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('es-ES', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  return (
    <div className="w-full h-full bg-gradient-to-br from-[#1A0033] via-[#0D001A] to-[#1A0033] border border-[#FFD700]/20 rounded-3xl overflow-hidden flex flex-col shadow-[0_0_60px_rgba(106,13,173,0.3)]">
      
      {/* Header elegante */}
      <div className="relative px-6 lg:px-8 py-6 border-b border-[#FFD700]/10 shrink-0">
        <div className="flex items-center gap-4">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#6A0DAD] to-[#FFD700] p-[2px] shadow-[0_0_15px_rgba(255,215,0,0.3)]">
            <div className="w-full h-full rounded-full bg-[#1A0033] flex items-center justify-center">
              <img src="/Eco.png" alt="Eco" className="w-6 h-6" />
            </div>
          </div>
          <div>
            <h1 className="text-[#FFD700] text-xl font-extralight tracking-[0.15em] uppercase">
              Eco
            </h1>
            <div className="flex items-center gap-2 mt-0.5">
              <div className={`w-1.5 h-1.5 rounded-full ${isSpeaking ? 'bg-[#FFD700] animate-pulse' : 'bg-white/30'}`}></div>
              <p className="text-white/40 text-[10px] tracking-widest uppercase">
                {isSpeaking ? 'Hablando' : 'Esperando'}
              </p>
            </div>
          </div>
        </div>
        
        {/* Línea decorativa dorada */}
        <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-[#FFD700]/40 to-transparent"></div>
      </div>

      {/* Área de mensajes */}
      <div className="flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-[#6A0DAD]/40 scrollbar-track-transparent p-6 lg:p-8">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-white/30 animate-fade-in">
            <div className="w-16 h-16 rounded-full bg-[#6A0DAD]/10 border border-[#FFD700]/10 flex items-center justify-center mb-4">
              <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-[#FFD700]/40">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
              </svg>
            </div>
            <p className="text-sm font-light tracking-wide">Inicia una conversación con Eco...</p>
          </div>
        ) : (
          <div className="w-full space-y-6">
            {messages.map((msg) => (
              <div key={msg.id} className="space-y-4 animate-fade-in">
                {/* Mensaje del usuario */}
                <div className="flex justify-end">
                  <div className="max-w-[85%] lg:max-w-[70%] bg-[#6A0DAD]/30 border border-[#FFD700]/20 rounded-2xl rounded-tr-sm px-5 py-3.5 shadow-[0_4px_20px_rgba(106,13,173,0.2)] backdrop-blur-sm">
                    <p className="text-white text-sm leading-relaxed font-light">{msg.user}</p>
                    <p className="text-white/40 text-[10px] mt-2 text-right tracking-wide">
                      {formatTime(msg.timestamp)}
                    </p>
                  </div>
                </div>

                {/* Respuesta de Eco */}
                <div className="flex justify-start">
                  <div className="max-w-[85%] lg:max-w-[70%] bg-[#000000]/40 border border-[#FFD700]/30 rounded-2xl rounded-tl-sm px-5 py-3.5 shadow-[0_4px_20px_rgba(0,0,0,0.3)] backdrop-blur-sm">
                    <div className="flex items-center gap-2 mb-2">
                      <img src="/Eco.png" alt="Eco" className="w-4 h-4" />
                      <p className="text-[#FFD700] text-[10px] font-light uppercase tracking-widest">
                        Eco
                      </p>
                    </div>
                    <p className="text-white text-sm leading-relaxed font-light">{msg.eco}</p>
                    
                    {/* Imagen de cámara si existe */}
                    {msg.cameraImage && (
                      <div className="mt-4 rounded-xl overflow-hidden border border-[#FFD700]/20 bg-black/60 shadow-lg">
                        <img 
                          src={msg.cameraImage} 
                          alt="Captura de cámara" 
                          className="w-full max-w-sm h-auto object-cover"
                        />
                      </div>
                    )}

                    {/* Reproductor de video si existe */}
                    {msg.motionVideo && (
                      <div className="mt-4 rounded-xl overflow-hidden border border-[#FFD700]/20 bg-black/60 shadow-lg">
                        <video 
                          src={msg.motionVideo} 
                          controls 
                          preload="metadata"
                          className="w-full max-w-sm h-auto"
                        />
                        <div className="px-3 py-2 bg-[#1A0033]/80 border-t border-[#FFD700]/10">
                          <p className="text-white/40 text-[10px] tracking-wide flex items-center gap-1.5">
                            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                            Video de seguridad (30s)
                          </p>
                        </div>
                      </div>
                    )}
                    
                    <p className="text-white/40 text-[10px] mt-3 text-right tracking-wide">
                      {formatTime(msg.timestamp)}
                    </p>
                  </div>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Barra inferior unificada */}
      <div className="border-t border-[#FFD700]/10 bg-[#0D001A]/80 backdrop-blur-md p-4 lg:p-6 shrink-0">
        {/* Input de texto */}
        <form onSubmit={handleSubmit} className="flex gap-2 lg:gap-3">
          <input
            ref={inputRef}
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Escribe un mensaje a Eco..."
            className="flex-1 bg-[#000000]/40 border border-[#FFD700]/20 rounded-xl px-4 py-2.5 lg:px-5 lg:py-3 text-white text-sm font-light placeholder-white/30 focus:outline-none focus:border-[#FFD700]/50 focus:bg-[#000000]/60 transition-all duration-300"
          />
          <button
            type="submit"
            disabled={!inputText.trim()}
            className="w-10 h-10 lg:w-auto lg:h-auto lg:px-5 lg:py-3 bg-[#6A0DAD] hover:bg-[#9D4EDD] disabled:bg-[#6A0DAD]/30 disabled:cursor-not-allowed text-white rounded-xl transition-all duration-300 border border-[#FFD700]/30 hover:border-[#FFD700]/50 hover:shadow-[0_0_20px_rgba(106,13,173,0.4)] flex items-center justify-center shrink-0 group"
          >
            <svg 
              xmlns="http://www.w3.org/2000/svg" 
              width="16" 
              height="16" 
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              strokeWidth="2" 
              strokeLinecap="round" 
              strokeLinejoin="round"
              className="group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform duration-300"
            >
              <line x1="22" y1="2" x2="11" y2="13"></line>
              <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
            </svg>
          </button>
        </form>
      </div>
    </div>
  );
}