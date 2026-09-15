import { useEffect, useRef, useState } from 'react';

interface SoundWaveProps {
  isActive: boolean;
  audioData?: Uint8Array;
}

export default function SoundWave({ isActive, audioData }: SoundWaveProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const animationRef = useRef<number>(0);
  const currentPhase = useRef(0);
  const currentAmplitude = useRef(0);
  
  // Estado para las dimensiones del contenedor
  const [dimensions, setDimensions] = useState({ width: 300, height: 100 });

  // Observar cambios de tamaño del contenedor
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        if (width > 0 && height > 0) {
          setDimensions({ width, height });
        }
      }
    });

    observer.observe(container);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const { width, height } = dimensions;
    canvas.width = width;
    canvas.height = height;

    const draw = () => {
      ctx.clearRect(0, 0, width, height);

      // Calcular amplitud del audio (0-1)
      let targetAmplitude = 0;
      if (isActive && audioData && audioData.length > 0) {
        const sum = audioData.reduce((acc, val) => acc + val, 0);
        targetAmplitude = (sum / audioData.length) / 255;
      }

      // Suavizado
      currentAmplitude.current += (targetAmplitude - currentAmplitude.current) * 0.2;

      // Velocidad
      const speed = isActive ? 0.035 : 0.015;
      currentPhase.current += speed;

      // === ONDA PRINCIPAL ===
      ctx.beginPath();
      ctx.strokeStyle = isActive ? 'rgba(255, 255, 255, 0.95)' : 'rgba(255, 215, 0, 0.6)';
      ctx.lineWidth = 3;

      const mainBaseAmplitude = isActive ? 18 : 6;
      const mainAudioBoost = currentAmplitude.current * 20;
      const mainTotalAmplitude = mainBaseAmplitude + mainAudioBoost;

      const mainFrequency = 0.02;
      const mainPhase = currentPhase.current;

      for (let x = 0; x < width; x++) {
        const edgeFade = Math.sin((x / width) * Math.PI);
        
        const y = height / 2 + 
                  Math.sin(x * mainFrequency + mainPhase) * mainTotalAmplitude * edgeFade +
                  Math.sin(x * mainFrequency * 1.5 + mainPhase * 0.7) * (mainTotalAmplitude * 0.25) * edgeFade;
        
        if (x === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.stroke();

      // === ONDAS SECUNDARIAS ===
      const waveCount = 3;
      for (let wave = 1; wave <= waveCount; wave++) {
        ctx.beginPath();
        
        const alpha = isActive ? (0.6 - wave * 0.12) : 0.15;
        ctx.strokeStyle = `rgba(255, 215, 0, ${alpha})`;
        ctx.lineWidth = wave === 1 ? 2 : 1.5;

        const baseAmplitude = isActive ? 12 + (wave * 5) : 5 + (wave * 2);
        const audioBoost = currentAmplitude.current * 25 * (1 + wave * 0.4);
        const totalAmplitude = baseAmplitude + audioBoost;

        const frequency = 0.015 + wave * 0.005;
        const phase = currentPhase.current * (1 + wave * 0.15);

        for (let x = 0; x < width; x++) {
          const edgeFade = Math.pow(Math.sin((x / width) * Math.PI), 0.8);
          
          const y = height / 2 + 
                    Math.sin(x * frequency + phase) * totalAmplitude * edgeFade +
                    Math.sin(x * frequency * 1.7 + phase * 0.8) * (totalAmplitude * 0.15) * edgeFade;
          
          if (x === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        }

        ctx.stroke();
      }

      animationRef.current = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      cancelAnimationFrame(animationRef.current);
    };
  }, [isActive, audioData, dimensions]);

  return (
    <div 
      ref={containerRef}
      className="absolute inset-0 flex items-center justify-center pointer-events-none"
    >
      <canvas 
        ref={canvasRef} 
        className="w-full h-full"
        style={{ 
          maskImage: 'linear-gradient(to right, transparent 0%, black 10%, black 90%, transparent 100%)',
          WebkitMaskImage: 'linear-gradient(to right, transparent 0%, black 10%, black 90%, transparent 100%)'
        }}
      />
    </div>
  );
}