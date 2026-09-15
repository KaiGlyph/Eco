import { useEffect, useRef, useState } from 'react';

// Contexto de audio GLOBAL para evitar que el navegador lo bloquee repetidamente
let globalAudioContext: AudioContext | null = null;

export function useAudioAnalyzer(audioUrl: string | null) {
  const [audioData, setAudioData] = useState<Uint8Array | null>(null);
  const [needsInteraction, setNeedsInteraction] = useState(false);
  const audioElementRef = useRef<HTMLAudioElement | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animationFrameRef = useRef<number>(0);

  useEffect(() => {
    if (!audioUrl) {
      setAudioData(null);
      if (audioElementRef.current) {
        audioElementRef.current.pause();
        audioElementRef.current = null;
      }
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      return;
    }

    const audio = new Audio(audioUrl);
    audio.crossOrigin = "anonymous";
    audioElementRef.current = audio;

    const setupAudio = async () => {
      try {
        // 1. Crear o reutilizar el contexto global
        if (!globalAudioContext) {
          globalAudioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
        }
        const ctx = globalAudioContext;

        // 2. Función que se ejecuta al hacer clic en cualquier parte de la pantalla
        const handleInteraction = async () => {
          if (ctx.state === 'suspended') {
            await ctx.resume();
            setNeedsInteraction(false);
            console.log("[AudioAnalyzer] Audio desbloqueado por el usuario.");
            
            // Reintentar la reproducción una vez desbloqueado
            try {
              await audio.play();
            } catch (e) {
              console.error("Aún falló al reproducir:", e);
            }
          }
        };

        // Escuchar el primer clic o tecla en toda la ventana
        window.addEventListener('click', handleInteraction);
        window.addEventListener('keydown', handleInteraction);

        // 3. Verificar estado inicial
        if (ctx.state === 'suspended') {
          setNeedsInteraction(true);
          console.log("[AudioAnalyzer] Esperando clic del usuario para activar el sonido...");
        }

        // 4. Configurar el analizador (solo la primera vez)
        if (!analyserRef.current) {
          const analyser = ctx.createAnalyser();
          analyser.fftSize = 256;
          analyser.smoothingTimeConstant = 0.8;
          analyserRef.current = analyser;

          const source = ctx.createMediaElementSource(audio);
          source.connect(analyser);
          analyser.connect(ctx.destination);
        }

        const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);

        const updateData = () => {
          analyserRef.current!.getByteFrequencyData(dataArray);
          setAudioData(new Uint8Array(dataArray));
          animationFrameRef.current = requestAnimationFrame(updateData);
        };

        updateData();

        // 5. Intentar reproducir
        const playPromise = audio.play();
        if (playPromise !== undefined) {
          playPromise.catch((err) => {
            if (err.name === 'NotAllowedError') {
              console.log("[AudioAnalyzer] Reproducción bloqueada. Haz clic en la pantalla.");
              setNeedsInteraction(true);
            } else {
              console.error("[AudioAnalyzer] Error al reproducir:", err);
            }
          });
        }

        audio.onended = () => {
          setAudioData(null);
          if (animationFrameRef.current) {
            cancelAnimationFrame(animationFrameRef.current);
          }
        };

      } catch (err: any) {
        console.error('[AudioAnalyzer] Error en setup:', err);
      }
    };

    setupAudio();

    // Limpieza al desmontar o cambiar URL
    return () => {
      if (audioElementRef.current) {
        audioElementRef.current.pause();
        audioElementRef.current = null;
      }
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [audioUrl]);

  return { audioData, needsInteraction };
}