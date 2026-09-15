import { useState, useEffect } from 'react';
import Orb from './components/Orb';
import Chat from './components/Chat';
import MediaGallery from './components/MediaGallery';
import CameraView from './components/CameraView';
import { useEcoWebSocket } from './hooks/useEcoWebSocket';
import { useAudioAnalyzer } from './hooks/useAudioAnalyzer';

function App() {
  const { state, audioUrl, messages, sendMessage, isChatOpen, setIsChatOpen } = useEcoWebSocket();
  const { audioData, needsInteraction } = useAudioAnalyzer(audioUrl);
  
  const [isGalleryOpen, setIsGalleryOpen] = useState(false);
  const [cameraPermission, setCameraPermission] = useState<'granted' | 'denied' | 'prompt'>('prompt');
  const [autoPresence, setAutoPresence] = useState(true); // Por defecto activado

  const [isCameraOpen, setIsCameraOpen] = useState(false);

  // Cargar preferencias al iniciar
  useEffect(() => {
    const savedPrefs = localStorage.getItem('eco_preferences');
    if (savedPrefs) {
      const prefs = JSON.parse(savedPrefs);
      setAutoPresence(prefs.autoPresence ?? true);
      setCameraPermission(prefs.cameraPermission ?? 'prompt');
    }
    
    // Verificar permisos actuales del navegador
    navigator.permissions.query({ name: 'camera' }).then((result) => {
      setCameraPermission(result.state as 'granted' | 'denied' | 'prompt');
      
      // Si ya tiene permisos y autoPresence está activado, iniciar detector
      if (result.state === 'granted' && autoPresence) {
        requestCameraAndStartPresence();
      }
    });
  }, []);

  // Guardar preferencias cuando cambien
  useEffect(() => {
    const prefs = {
      autoPresence,
      cameraPermission,
    };
    localStorage.setItem('eco_preferences', JSON.stringify(prefs));
  }, [autoPresence, cameraPermission]);

  const requestCameraAndStartPresence = async () => {
    try {
      // Pedir permiso de cámara
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      setCameraPermission('granted');
      
      // Enviar comando al backend para activar detector de presencia
      const ws = new WebSocket('ws://localhost:8000/ws');
      ws.onopen = () => {
        ws.send(JSON.stringify({
          type: 'voice',
          text: 'activa el detector de presencia'
        }));
        ws.close();
      };
      
      // Detener el stream local (el backend ya tiene su propia cámara)
      stream.getTracks().forEach(track => track.stop());
    } catch (error) {
      console.error('Error al pedir permisos de cámara:', error);
      setCameraPermission('denied');
    }
  };

  return (
    <div className="w-screen h-screen bg-black flex items-center justify-center overflow-hidden relative">
      {/* Logo de Eco en la esquina superior izquierda */}
      <div className="absolute top-6 left-6 flex items-center gap-3 z-10">
        <img 
          src="/Eco.png" 
          alt="Eco Logo" 
          className="h-16 w-auto drop-shadow-[0_0_8px_rgba(255,215,0,0.5)]" 
        />
        <span className="text-[#FFD700] text-xl font-light tracking-[0.2em] uppercase drop-shadow-md">
          Eco
        </span>
      </div>
      {/* Orbe principal centrado */}
      <Orb 
        isSpeaking={state === 'speaking'} 
        audioData={audioData ?? undefined} 
      />

      {/* Dock inferior centralizado */}
      {!isChatOpen && (
        <div className="fixed bottom-8 left-1/2 transform -translate-x-1/2 z-50">
          <div className="flex items-center gap-2 bg-[#1A0033]/60 backdrop-blur-md border border-[#FFD700]/30 rounded-2xl px-4 py-3 shadow-2xl">
            
            {/* Botón Galería */}
            <button
              onClick={() => setIsGalleryOpen(true)}
              className="group relative flex flex-col items-center px-4 py-2 rounded-xl transition-all duration-300"
              title="Galería Multimedia"
            >
              <div className="w-10 h-10 bg-[#6A0DAD] hover:bg-[#9D4EDD] rounded-full flex items-center justify-center transition-all duration-300 group-hover:-translate-y-3 group-hover:shadow-[0_0_12px_rgba(106,13,173,0.6)]">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-white">
                  <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                  <circle cx="8.5" cy="8.5" r="1.5"></circle>
                  <polyline points="21 15 16 10 5 21"></polyline>
                </svg>
              </div>
              <span className="absolute -bottom-1 left-1/2 transform -translate-x-1/2 text-[#FFD700]/60 text-[10px] font-medium tracking-wider uppercase opacity-0 group-hover:opacity-100 transition-all duration-300 whitespace-nowrap">
                Galería
              </span>
            </button>

            {/* Separador */}
            <div className="w-px h-8 bg-[#FFD700]/20"></div>

            {/* Botón Chat */}
            <button
              onClick={() => setIsChatOpen(true)}
              className="group relative flex flex-col items-center px-4 py-2 rounded-xl transition-all duration-300"
              title="Abrir Chat"
            >
              <div className="w-10 h-10 bg-[#6A0DAD] hover:bg-[#9D4EDD] rounded-full flex items-center justify-center transition-all duration-300 group-hover:-translate-y-3 group-hover:shadow-[0_0_12px_rgba(106,13,173,0.6)]">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-white">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                </svg>
              </div>
              <span className="absolute -bottom-1 left-1/2 transform -translate-x-1/2 text-[#FFD700]/60 text-[10px] font-medium tracking-wider uppercase opacity-0 group-hover:opacity-100 transition-all duration-300 whitespace-nowrap">
                Chat
              </span>
            </button>

            {/* Separador */}
            <div className="w-px h-8 bg-[#FFD700]/20"></div>

            {/* Botón Cámara */}
            <button
              onClick={() => setIsCameraOpen(true)}
              className="group relative flex flex-col items-center px-4 py-2 rounded-xl transition-all duration-300"
              title="Cámara en Vivo"
            >
              <div className="w-10 h-10 bg-[#6A0DAD] hover:bg-[#9D4EDD] rounded-full flex items-center justify-center transition-all duration-300 group-hover:-translate-y-3 group-hover:shadow-[0_0_12px_rgba(106,13,173,0.6)]">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-white">
                  <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path>
                  <circle cx="12" cy="13" r="4"></circle>
                </svg>
              </div>
              <span className="absolute -bottom-1 left-1/2 transform -translate-x-1/2 text-[#FFD700]/60 text-[10px] font-medium tracking-wider uppercase opacity-0 group-hover:opacity-100 transition-all duration-300 whitespace-nowrap">
                Cámara
              </span>
            </button>
          </div>
        </div>
      )}

      {/* Añade el modal de Cámara después del modal del Chat */}
      {isCameraOpen && (
        <CameraView 
          isOpen={isCameraOpen}
          onClose={() => setIsCameraOpen(false)}
        />
      )}


      {/* Galería Multimedia */}
      <MediaGallery 
        isOpen={isGalleryOpen}
        onClose={() => setIsGalleryOpen(false)}
      />

      {/* Modal del Chat */}
      {isChatOpen && (
        <>
          <div className="absolute inset-0 z-40 bg-black/60 backdrop-blur-sm" />
          <div className="absolute inset-0 z-50 flex items-center justify-center p-4">
            <div className="relative w-full max-w-4xl h-[95vh]">
              <button
                onClick={() => setIsChatOpen(false)}
                className="absolute z-50 w-12 h-12 bg-[#1A0033] hover:bg-[#6A0DAD] border border-[#FFD700]/30 rounded-full flex items-center justify-center text-white shadow-[0_0_20px_rgba(106,13,173,0.5)] hover:shadow-[0_0_30px_rgba(255,215,0,0.4)] transition-all duration-300 lg:-left-16 lg:top-5 top-4 right-4"
                title="Cerrar chat"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
              </button>

              <Chat 
                messages={messages} 
                isSpeaking={state === 'speaking'} 
                audioData={audioData ?? undefined}
                onSendMessage={sendMessage}
              />
            </div>
          </div>
        </>
      )}

      {/* Aviso de interacción */}
      {needsInteraction && (
        <div className="absolute inset-0 bg-black/60 flex items-center justify-center z-50 backdrop-blur-sm">
          <div className="bg-[#1A0033] border border-[#FFD700]/50 p-8 rounded-2xl text-center shadow-[0_0_30px_rgba(255,215,0,0.3)]">
            <p className="text-[#FFD700] text-lg font-light mb-2">
              Eco necesita permiso para hablar
            </p>
            <p className="text-white/70 text-sm">
              Haz clic en cualquier parte de la pantalla para activar el sonido.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;