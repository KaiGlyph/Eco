import { useState, useEffect, useRef } from 'react';

interface CameraViewProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function CameraView({ isOpen, onClose }: CameraViewProps) {
  const [cameraStream, setCameraStream] = useState<string | null>(null);
  const [screenStream, setScreenStream] = useState<MediaStream | null>(null);
  
  const [isDrawingMode, setIsDrawingMode] = useState(false);
  const [drawColor, setDrawColor] = useState('#FFD700');
  const [drawSize, setDrawSize] = useState(5);
  const [isEraserMode, setIsEraserMode] = useState(false);
  
  const [morseState, setMorseState] = useState({ 
    sequence: '', current_word: '', full_text: '', active: false 
  });
  
  const [, setIsDragging] = useState(false);
  const [isResizing, setIsResizing] = useState(false);
  const [isGrabbed, setIsGrabbed] = useState(false);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const [screenPosition, setScreenPosition] = useState({ x: 20, y: 20 });
  const [screenSize, setScreenSize] = useState({ width: 320, height: 180 });
  const [resizeStart, setResizeStart] = useState({ x: 0, y: 0, width: 0, height: 0 });
  
  const wsRef = useRef<WebSocket | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const drawingCanvasRef = useRef<HTMLCanvasElement>(null);
  const drawingWsRef = useRef<WebSocket | null>(null);
  const lastDrawPoint = useRef<{ x: number; y: number } | null>(null);
  const lastMousePoint = useRef<{ x: number; y: number } | null>(null);
  const [isDrawingWithMouse, setIsDrawingWithMouse] = useState(false);
  const canvasInitialized = useRef(false);

  const MIN_WIDTH = 160;
  const MIN_HEIGHT = 90;
  const MAX_WIDTH = 800;
  const MAX_HEIGHT = 450;

  useEffect(() => {
    if (!isOpen) {
      stopAllStreams();
    }
  }, [isOpen]);

  useEffect(() => {
    if (screenStream && videoRef.current) {
      videoRef.current.srcObject = screenStream;
      videoRef.current.play().catch(e => console.error('Error al reproducir:', e));
    } else if (!screenStream && videoRef.current) {
      videoRef.current.srcObject = null;
    }
  }, [screenStream]);

  useEffect(() => {
    if (isDrawingMode && cameraStream && !canvasInitialized.current) {
      const canvas = drawingCanvasRef.current;
      if (canvas && canvas.parentElement) {
        canvas.width = canvas.parentElement.offsetWidth;
        canvas.height = canvas.parentElement.offsetHeight;
        const ctx = canvas.getContext('2d');
        if (ctx) { ctx.lineCap = 'round'; ctx.lineJoin = 'round'; }
        canvasInitialized.current = true;
      }
      connectDrawingStream();
    } else if (!isDrawingMode) {
      disconnectDrawingStream();
      canvasInitialized.current = false;
    }
  }, [isDrawingMode, cameraStream]);

  useEffect(() => {
    if (!isOpen) return;
    const interval = setInterval(async () => {
      try {
        const res = await fetch('http://localhost:8000/api/morse/state');
        const data = await res.json();
        setMorseState(data);
      } catch (error) { /* Ignorar */ }
    }, 1000);
    return () => clearInterval(interval);
  }, [isOpen]);

  const startCameraStream = () => {
    if (wsRef.current) return;
    const ws = new WebSocket('ws://localhost:8000/ws/camera/stream');
    wsRef.current = ws;
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'frame') setCameraStream(`data:image/jpeg;base64,${data.data}`);
    };
    ws.onclose = () => setCameraStream(null);
  };

  const startScreenCapture = async () => {
    try {
      const stream = await navigator.mediaDevices.getDisplayMedia({ video: { frameRate: 30 }, audio: false });
      setScreenStream(stream);
      stream.getVideoTracks()[0].onended = () => setScreenStream(null);
    } catch (error) {
      console.error('Error al capturar pantalla:', error);
    }
  };

  const stopAllStreams = () => {
    if (wsRef.current) { wsRef.current.close(); wsRef.current = null; }
    setCameraStream(null);
    if (screenStream) { screenStream.getTracks().forEach(track => track.stop()); setScreenStream(null); }
    disconnectDrawingStream();
    setIsDrawingMode(false);
    canvasInitialized.current = false;
  };

  const stopScreenOnly = () => {
    if (screenStream) { screenStream.getTracks().forEach(track => track.stop()); setScreenStream(null); }
  };

  const connectDrawingStream = () => {
    if (drawingWsRef.current) return;
    const ws = new WebSocket('ws://localhost:8000/ws/drawing');
    drawingWsRef.current = ws;
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'hand_landmarks') {
        if (data.is_drawing) drawPointFromGesture(data.index_tip);
        else lastDrawPoint.current = null;
      }
    };
    ws.onclose = () => { drawingWsRef.current = null; };
  };

  const disconnectDrawingStream = () => {
    if (drawingWsRef.current) {
      drawingWsRef.current.send(JSON.stringify({ type: 'stop_drawing' }));
      drawingWsRef.current.close();
      drawingWsRef.current = null;
    }
  };

  const drawPointFromGesture = (point: { x: number; y: number }) => {
    const canvas = drawingCanvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    const x = point.x * canvas.width;
    const y = point.y * canvas.height;
    
    if (isEraserMode) {
      ctx.globalCompositeOperation = 'destination-out';
      ctx.strokeStyle = 'rgba(0,0,0,1)';
      ctx.lineWidth = drawSize * 3;
    } else {
      ctx.globalCompositeOperation = 'source-over';
      ctx.strokeStyle = drawColor;
      ctx.lineWidth = drawSize;
    }
    
    if (lastDrawPoint.current) {
      ctx.beginPath();
      ctx.moveTo(lastDrawPoint.current.x, lastDrawPoint.current.y);
      ctx.lineTo(x, y);
      ctx.stroke();
    }
    lastDrawPoint.current = { x, y };
  };

  const getCanvasCoordinates = (e: React.MouseEvent<HTMLCanvasElement> | React.TouchEvent<HTMLCanvasElement>) => {
    const canvas = drawingCanvasRef.current;
    if (!canvas) return { x: 0, y: 0 };
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    
    if ('touches' in e) {
      const touch = e.touches[0];
      return {
        x: (touch.clientX - rect.left) * scaleX,
        y: (touch.clientY - rect.top) * scaleY
      };
    } else {
      return {
        x: (e.clientX - rect.left) * scaleX,
        y: (e.clientY - rect.top) * scaleY
      };
    }
  };

  const handleCanvasMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    setIsDrawingWithMouse(true);
    const coords = getCanvasCoordinates(e);
    lastMousePoint.current = coords;
  };

  const handleCanvasMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDrawingWithMouse) return;
    const canvas = drawingCanvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const coords = getCanvasCoordinates(e);

    if (isEraserMode) {
      ctx.globalCompositeOperation = 'destination-out';
      ctx.strokeStyle = 'rgba(0,0,0,1)';
      ctx.lineWidth = drawSize * 3;
    } else {
      ctx.globalCompositeOperation = 'source-over';
      ctx.strokeStyle = drawColor;
      ctx.lineWidth = drawSize;
    }

    if (lastMousePoint.current) {
      ctx.beginPath();
      ctx.moveTo(lastMousePoint.current.x, lastMousePoint.current.y);
      ctx.lineTo(coords.x, coords.y);
      ctx.stroke();
    }
    lastMousePoint.current = coords;
  };

  const handleCanvasMouseUp = () => {
    setIsDrawingWithMouse(false);
    lastMousePoint.current = null;
    lastDrawPoint.current = null;
    const canvas = drawingCanvasRef.current;
    if (canvas) {
      const ctx = canvas.getContext('2d');
      if (ctx) ctx.globalCompositeOperation = 'source-over';
    }
  };

  // Touch handlers para dibujo
  const handleTouchStart = (e: React.TouchEvent<HTMLCanvasElement>) => {
    e.preventDefault();
    setIsDrawingWithMouse(true);
    const coords = getCanvasCoordinates(e);
    lastMousePoint.current = coords;
  };

  const handleTouchMove = (e: React.TouchEvent<HTMLCanvasElement>) => {
    e.preventDefault();
    if (!isDrawingWithMouse) return;
    const canvas = drawingCanvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const coords = getCanvasCoordinates(e);

    if (isEraserMode) {
      ctx.globalCompositeOperation = 'destination-out';
      ctx.strokeStyle = 'rgba(0,0,0,1)';
      ctx.lineWidth = drawSize * 3;
    } else {
      ctx.globalCompositeOperation = 'source-over';
      ctx.strokeStyle = drawColor;
      ctx.lineWidth = drawSize;
    }

    if (lastMousePoint.current) {
      ctx.beginPath();
      ctx.moveTo(lastMousePoint.current.x, lastMousePoint.current.y);
      ctx.lineTo(coords.x, coords.y);
      ctx.stroke();
    }
    lastMousePoint.current = coords;
  };

  const handleTouchEnd = () => {
    setIsDrawingWithMouse(false);
    lastMousePoint.current = null;
    lastDrawPoint.current = null;
    const canvas = drawingCanvasRef.current;
    if (canvas) {
      const ctx = canvas.getContext('2d');
      if (ctx) ctx.globalCompositeOperation = 'source-over';
    }
  };

  const clearDrawing = () => {
    const canvas = drawingCanvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (ctx) ctx.clearRect(0, 0, canvas.width, canvas.height);
    lastDrawPoint.current = null;
    lastMousePoint.current = null;
  };

  const saveDrawing = () => {
    const canvas = drawingCanvasRef.current;
    if (!canvas) return;
    const link = document.createElement('a');
    link.download = `eco_drawing_${Date.now()}.png`;
    link.href = canvas.toDataURL('image/png');
    link.click();
  };

  const handleRectMouseDown = (e: React.MouseEvent | React.TouchEvent) => {
    if ((e.target as HTMLElement).closest('.resize-handle') || (e.target as HTMLElement).closest('.close-btn')) return;
    
    const clientX = 'touches' in e ? e.touches[0].clientX : e.clientX;
    const clientY = 'touches' in e ? e.touches[0].clientY : e.clientY;
    
    const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
    setDragOffset({ x: clientX - rect.left, y: clientY - rect.top });
    setIsGrabbed(true);
    setIsDragging(true);
  };

  const handleResizeMouseDown = (e: React.MouseEvent | React.TouchEvent) => {
    e.stopPropagation();
    const clientX = 'touches' in e ? e.touches[0].clientX : e.clientX;
    const clientY = 'touches' in e ? e.touches[0].clientY : e.clientY;
    setResizeStart({ x: clientX, y: clientY, width: screenSize.width, height: screenSize.height });
    setIsResizing(true);
  };

  const handleMouseMove = (e: React.MouseEvent | React.TouchEvent) => {
    if (isResizing) {
      const clientX = 'touches' in e ? e.touches[0].clientX : e.clientX;
      const clientY = 'touches' in e ? e.touches[0].clientY : e.clientY;
      
      const container = e.currentTarget as HTMLElement;
      const containerRect = container.getBoundingClientRect();
      const deltaX = clientX - resizeStart.x;
      const deltaY = clientY - resizeStart.y;
      const newWidth = Math.max(MIN_WIDTH, Math.min(MAX_WIDTH, resizeStart.width + deltaX));
      const newHeight = Math.max(MIN_HEIGHT, Math.min(MAX_HEIGHT, resizeStart.height + deltaY));
      const aspectRatio = 16 / 9;
      const useWidth = Math.abs(newWidth - resizeStart.width) > Math.abs(newHeight - resizeStart.height);
      const finalWidth = useWidth ? newWidth : newHeight * aspectRatio;
      const finalHeight = useWidth ? newWidth / aspectRatio : newHeight;
      setScreenSize({ width: finalWidth, height: finalHeight });
      setScreenPosition(prev => ({
        x: Math.min(prev.x, containerRect.width - finalWidth),
        y: Math.min(prev.y, containerRect.height - finalHeight)
      }));
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
    setIsResizing(false);
  };

  useEffect(() => {
    if (!isGrabbed) return;
    const handleGlobalMouseMove = (e: MouseEvent | TouchEvent) => {
      const clientX = 'touches' in e ? e.touches[0].clientX : e.clientX;
      const clientY = 'touches' in e ? e.touches[0].clientY : e.clientY;
      
      if (!containerRef.current) return;
      const containerRect = containerRef.current.getBoundingClientRect();
      const newX = clientX - containerRect.left - dragOffset.x;
      const newY = clientY - containerRect.top - dragOffset.y;
      setScreenPosition({
        x: Math.max(0, Math.min(newX, containerRect.width - screenSize.width)),
        y: Math.max(0, Math.min(newY, containerRect.height - screenSize.height))
      });
    };
    const handleGlobalMouseUp = () => { setIsGrabbed(false); setIsDragging(false); };
    document.addEventListener('mousemove', handleGlobalMouseMove);
    document.addEventListener('mouseup', handleGlobalMouseUp);
    document.addEventListener('touchmove', handleGlobalMouseMove);
    document.addEventListener('touchend', handleGlobalMouseUp);
    return () => {
      document.removeEventListener('mousemove', handleGlobalMouseMove);
      document.removeEventListener('mouseup', handleGlobalMouseUp);
      document.removeEventListener('touchmove', handleGlobalMouseMove);
      document.removeEventListener('touchend', handleGlobalMouseUp);
    };
  }, [isGrabbed, dragOffset, screenSize]);

  if (!isOpen) return null;

  return (
    <>
      <div className="fixed inset-0 z-50 bg-black/90 backdrop-blur-xl" onClick={onClose} />
      
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 lg:p-8">
        <div className="relative w-full max-w-6xl max-h-[90vh] flex flex-col">
          
          {/* Botón de cerrar */}
          <button
            onClick={onClose}
            className="absolute z-50 w-12 h-12 bg-[#1A0033]/80 hover:bg-[#6A0DAD] border border-[#FFD700]/30 rounded-full flex items-center justify-center text-white/80 hover:text-white shadow-[0_0_20px_rgba(106,13,173,0.3)] hover:shadow-[0_0_30px_rgba(255,215,0,0.4)] transition-all duration-500 xl:-left-16 xl:top-5 top-4 right-4 group"
            title="Cerrar cámara"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="group-hover:rotate-90 transition-transform duration-500">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>

          {/* Modal principal con gradiente de lujo */}
          <div className="bg-gradient-to-br from-[#1A0033] via-[#0D001A] to-[#1A0033] border border-[#FFD700]/20 rounded-3xl w-full max-h-[90vh] shadow-[0_0_60px_rgba(106,13,173,0.3)] overflow-hidden flex flex-col">
            
            {/* Header elegante */}
            <div className="relative px-8 lg:px-12 py-8 border-b border-[#FFD700]/10 shrink-0">
              <div className="flex items-center gap-4 mb-4">
                <div className="w-12 h-12 rounded-full bg-gradient-to-br from-[#6A0DAD] to-[#FFD700] p-[2px] shadow-[0_0_20px_rgba(255,215,0,0.3)]">
                  <div className="w-full h-full rounded-full bg-[#1A0033] flex items-center justify-center">
                    <img src="/Eco.png" alt="Eco" className="w-7 h-7" />
                  </div>
                </div>
                <div>
                  <h1 className="text-[#FFD700] text-2xl font-extralight tracking-[0.2em] uppercase">
                    Cámara
                  </h1>
                  <p className="text-white/40 text-xs tracking-widest uppercase mt-0.5">
                    Transmisión y control
                  </p>
                </div>
              </div>
              
              {/* Línea decorativa dorada */}
              <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-[#FFD700]/40 to-transparent"></div>
            </div>

            {/* Contenido */}
            <div className="flex-1 overflow-y-auto p-4 lg:p-10 flex flex-col items-center scrollbar-thin scrollbar-thumb-[#6A0DAD]/30 scrollbar-track-transparent">
              
              {/* Contenedor de la cámara */}
              <div 
                ref={containerRef}
                className="relative w-full aspect-[3/4] lg:aspect-video rounded-xl lg:rounded-2xl overflow-hidden border border-[#FFD700]/20 bg-black shadow-[0_0_40px_rgba(0,0,0,0.5)]"
                onMouseMove={handleMouseMove}
                onMouseUp={handleMouseUp}
                onMouseLeave={handleMouseUp}
                onTouchMove={handleMouseMove}
              >
                {cameraStream ? (
                  <img 
                    src={cameraStream} 
                    alt="Cámara en vivo" 
                    className="w-full h-full object-contain lg:object-cover" 
                  />
                ) : (
                <div className="absolute inset-0 flex items-center justify-center bg-[#000000]/40">
                  <div className="text-center px-4">
                    <div className="w-16 h-16 lg:w-20 lg:h-20 rounded-full bg-[#6A0DAD]/10 border border-[#FFD700]/20 flex items-center justify-center mx-auto mb-4">
                      <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-[#FFD700]/60">
                        <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path>
                        <circle cx="12" cy="13" r="4"></circle>
                      </svg>
                    </div>
                    <p className="text-white/60 mb-6 font-light tracking-wide text-sm lg:text-base">La cámara está apagada</p>
                    <button 
                      onClick={startCameraStream} 
                      className="w-16 h-16 lg:w-20 lg:h-20 mx-auto rounded-full bg-gradient-to-br from-[#6A0DAD] to-[#9D4EDD] hover:from-[#9D4EDD] hover:to-[#6A0DAD] border border-[#FFD700]/30 hover:border-[#FFD700]/60 flex items-center justify-center transition-all duration-500 hover:shadow-[0_0_30px_rgba(106,13,173,0.6)] hover:scale-110 group"
                      title="Encender Cámara"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-white group-hover:text-[#FFD700] transition-colors duration-300">
                        <path d="M18.36 6.64a9 9 0 1 1-12.73 0"></path>
                        <line x1="12" y1="2" x2="12" y2="12"></line>
                      </svg>
                    </button>
                  </div>
                </div>
              )}

                <canvas
                  ref={drawingCanvasRef}
                  className={`absolute inset-0 w-full h-full ${isEraserMode ? 'cursor-cell' : 'cursor-crosshair'} touch-none`}
                  style={{ zIndex: isDrawingMode ? 10 : 1, display: isDrawingMode ? 'block' : 'none' }}
                  onMouseDown={handleCanvasMouseDown}
                  onMouseMove={handleCanvasMouseMove}
                  onMouseUp={handleCanvasMouseUp}
                  onMouseLeave={handleCanvasMouseUp}
                  onTouchStart={handleTouchStart}
                  onTouchMove={handleTouchMove}
                  onTouchEnd={handleTouchEnd}
                />

                {screenStream && (
                  <div
                    className={`absolute rounded-xl overflow-hidden shadow-2xl bg-black transition-all duration-150 ${isGrabbed ? 'border-2 border-[#FFD700] scale-[1.02]' : 'border-2 border-[#6A0DAD] cursor-move hover:border-[#9D4EDD] touch-none'}`}
                    style={{ left: `${screenPosition.x}px`, top: `${screenPosition.y}px`, width: `${screenSize.width}px`, height: `${screenSize.height}px`, zIndex: isDrawingMode ? 5 : 20 }}
                    onMouseDown={handleRectMouseDown}
                    onTouchStart={handleRectMouseDown}
                  >
                    <video ref={videoRef} autoPlay playsInline muted className="w-full h-full object-cover" />
                    <div className="absolute top-0 left-0 right-0 bg-[#6A0DAD]/90 px-2 py-1 flex items-center justify-between backdrop-blur-sm">
                      <div className="flex items-center gap-1.5">
                        <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-white"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect><line x1="8" y1="21" x2="16" y2="21"></line><line x1="12" y1="17" x2="12" y2="21"></line></svg>
                        <span className="text-white text-xs font-medium">Pantalla</span>
                      </div>
                      <button onClick={(e) => { e.stopPropagation(); stopScreenOnly(); }} className="close-btn text-white hover:text-red-300 transition-colors">
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                      </button>
                    </div>
                    {isGrabbed && (
                      <div className="absolute inset-0 pointer-events-none border-2 border-[#FFD700]/50 rounded-xl">
                        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 bg-[#FFD700]/90 rounded-full p-2">
                          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-black"><path d="M18 11V6a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v0"></path><path d="M14 10V4a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v2"></path><path d="M10 10.5V6a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v8"></path><path d="M18 8a2 2 0 1 1 4 0v6a8 8 0 0 1-8 8h-2c-2.8 0-4.5-.86-5.99-2.34l-3.6-3.6a2 2 0 0 1 2.83-2.82L7 15"></path></svg>
                        </div>
                      </div>
                    )}
                    <div className="resize-handle absolute bottom-0 right-0 w-5 h-5 cursor-nwse-resize flex items-center justify-center bg-[#6A0DAD]/80 rounded-tl touch-none" onMouseDown={handleResizeMouseDown} onTouchStart={handleResizeMouseDown}>
                      <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-white"><polyline points="15 3 21 3 21 9"></polyline><polyline points="9 21 3 21 3 15"></polyline><line x1="21" y1="3" x2="14" y2="10"></line><line x1="3" y1="21" x2="10" y2="14"></line></svg>
                    </div>
                  </div>
                )}

                {morseState.active && (
                  <div className="absolute bottom-4 left-4 right-4 bg-[#1A0033]/90 border border-[#FFD700]/30 rounded-xl p-4 z-30 backdrop-blur-md shadow-2xl">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-[#FFD700] rounded-full animate-pulse shadow-[0_0_8px_rgba(255,215,0,0.6)]"></div>
                        <span className="text-[#FFD700] text-xs font-bold tracking-widest uppercase">Modo Morse Activo</span>
                      </div>
                      <span className="text-white/50 text-[10px]">Puño corto = Punto | Puño largo = Raya</span>
                    </div>
                    <div className="grid grid-cols-3 gap-4">
                      <div className="bg-[#000000]/40 rounded-lg p-3 border border-[#FFD700]/20">
                        <div className="text-[#FFD700]/60 text-[10px] mb-1 uppercase tracking-wider">Señal</div>
                        <div className="text-xl font-mono text-[#FFD700] tracking-widest min-h-[1.75rem]">{morseState.sequence || <span className="text-white/20">...</span>}</div>
                      </div>
                      <div className="bg-[#000000]/40 rounded-lg p-3 border border-[#FFD700]/20">
                        <div className="text-[#FFD700]/60 text-[10px] mb-1 uppercase tracking-wider">Palabra</div>
                        <div className="text-lg font-mono text-white min-h-[1.75rem]">{morseState.current_word}<span className="animate-pulse text-[#FFD700]">|</span></div>
                      </div>
                      <div className="bg-[#000000]/40 rounded-lg p-3 border border-[#FFD700]/20">
                        <div className="text-[#FFD700]/60 text-[10px] mb-1 uppercase tracking-wider">Mensaje</div>
                        <div className="text-sm text-white/80 min-h-[1.75rem] break-all font-light">{morseState.full_text || <span className="text-white/20">Vacío</span>}</div>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Controles de dibujo */}
              {isDrawingMode && (
                <div className="mt-4 lg:mt-6 flex flex-col gap-3 items-center bg-[#1A0033]/80 backdrop-blur-md border border-[#FFD700]/20 rounded-2xl px-4 py-3 shadow-xl w-full max-w-2xl">
                  
                  {/* Fila 1: Colores y grosor */}
                  <div className="flex flex-wrap items-center justify-center gap-2 w-full">
                    {!isEraserMode && (
                      <>
                        <div className="flex gap-2">
                          {['#FFD700', '#FF0000', '#00FF00', '#00BFFF', '#FF00FF', '#FFFFFF'].map(color => (
                            <button 
                              key={color} 
                              onClick={() => setDrawColor(color)} 
                              className={`w-6 h-6 rounded-full border-2 transition-transform ${drawColor === color ? 'border-white scale-125 shadow-[0_0_10px_rgba(255,255,255,0.5)]' : 'border-transparent hover:scale-110'}`} 
                              style={{ backgroundColor: color }} 
                            />
                          ))}
                        </div>
                        <div className="w-px h-6 bg-[#FFD700]/20" />
                        <input 
                          type="range" 
                          min="2" 
                          max="20" 
                          value={drawSize} 
                          onChange={(e) => setDrawSize(parseInt(e.target.value))} 
                          className="w-20 accent-[#FFD700]" 
                        />
                      </>
                    )}
                  </div>

                  {/* Fila 2: Herramientas */}
                  <div className="flex items-center justify-center gap-2 w-full pt-2 border-t border-[#FFD700]/10">
                    <button 
                      onClick={() => setIsEraserMode(!isEraserMode)} 
                      className={`w-8 h-8 rounded-full flex items-center justify-center transition-all duration-300 ${isEraserMode ? 'bg-white text-black border border-[#FFD700] shadow-[0_0_10px_rgba(255,215,0,0.4)]' : 'bg-[#6A0DAD] hover:bg-[#9D4EDD] text-white'}`} 
                      title="Goma"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 20H7L3 16C2 15 2 13 3 12L13 2L22 11L20 20Z"></path><path d="M17 17L7 7"></path></svg>
                    </button>
                    <button 
                      onClick={clearDrawing} 
                      className="w-8 h-8 bg-red-600/80 hover:bg-red-600 rounded-full flex items-center justify-center text-white transition-all duration-300 hover:shadow-[0_0_10px_rgba(220,38,38,0.4)]" 
                      title="Borrar todo"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>
                    </button>
                    <button 
                      onClick={saveDrawing} 
                      className="w-8 h-8 bg-[#FFD700] hover:bg-[#FFED4E] rounded-full flex items-center justify-center text-black transition-all duration-300 hover:shadow-[0_0_10px_rgba(255,215,0,0.4)]" 
                      title="Guardar"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path><polyline points="17 21 17 13 7 13 7 21"></polyline><polyline points="7 3 7 8 15 8"></polyline></svg>
                    </button>
                    <button 
                      onClick={() => { setIsDrawingMode(false); setIsEraserMode(false); }} 
                      className="w-8 h-8 bg-red-600 hover:bg-red-700 rounded-full flex items-center justify-center text-white transition-all duration-300 hover:shadow-[0_0_10px_rgba(220,38,38,0.4)]" 
                      title="Salir"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                    </button>
                  </div>
                </div>
              )}

              {/* Botones de acción principales */}
              <div className="mt-4 lg:mt-8 flex gap-4 lg:gap-6 items-center">
                {cameraStream && !screenStream && !isDrawingMode && (
                  <button onClick={startScreenCapture} className="group w-12 h-12 bg-[#6A0DAD] hover:bg-[#9D4EDD] rounded-full flex items-center justify-center text-white transition-all duration-300 shadow-lg hover:shadow-[0_0_20px_rgba(106,13,173,0.5)] border border-[#FFD700]/20 hover:border-[#FFD700]/40" title="Compartir pantalla">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="group-hover:scale-110 transition-transform duration-300"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect><line x1="8" y1="21" x2="16" y2="21"></line><line x1="12" y1="17" x2="12" y2="21"></line></svg>
                  </button>
                )}
                {cameraStream && !isDrawingMode && (
                  <button onClick={() => setIsDrawingMode(true)} className="group w-12 h-12 bg-[#FFD700] hover:bg-[#FFED4E] rounded-full flex items-center justify-center text-black transition-all duration-300 shadow-lg hover:shadow-[0_0_20px_rgba(255,215,0,0.5)] border border-white/20 hover:border-white/40" title="Modo dibujo">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="group-hover:scale-110 transition-transform duration-300"><path d="M12 19l7-7 3 3-7 7-3-3z"></path><path d="M18 13l-1.5-7.5L2 2l3.5 14.5L13 18l5-5z"></path><path d="M2 2l7.586 7.586"></path><circle cx="11" cy="11" r="2"></circle></svg>
                  </button>
                )}
                {cameraStream && (
                  <button onClick={stopAllStreams} className="group w-12 h-12 bg-red-600 hover:bg-red-700 rounded-full flex items-center justify-center text-white transition-all duration-300 shadow-lg hover:shadow-[0_0_20px_rgba(220,38,38,0.5)] border border-white/10 hover:border-white/30" title="Detener todo">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="group-hover:scale-110 transition-transform duration-300"><path d="M18.36 6.64a9 9 0 1 1-12.73 0"></path><line x1="12" y1="2" x2="12" y2="12"></line></svg>
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}