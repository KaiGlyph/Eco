interface ManualProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function Manual({ isOpen, onClose }: ManualProps) {
  if (!isOpen) return null;

  return (
    <>
      {/* Fondo oscuro */}
      <div 
        className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm"
        onClick={onClose}
      />
      
      {/* Modal del manual */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div className="bg-[#1A0033] border border-[#FFD700]/30 rounded-2xl max-w-2xl w-full max-h-[80vh] overflow-y-auto shadow-2xl">
          {/* Header */}
          <div className="px-6 py-4 border-b border-[#FFD700]/20 flex items-center justify-between sticky top-0 bg-[#1A0033] z-10">
            <h2 className="text-[#FFD700] text-xl font-light tracking-wide">Manual de Eco 1.1</h2>
            <button
              onClick={onClose}
              className="w-10 h-10 bg-[#000000]/40 hover:bg-[#6A0DAD] rounded-full flex items-center justify-center text-white transition-colors"
            >
              <svg 
                xmlns="http://www.w3.org/2000/svg" 
                width="20" 
                height="20" 
                viewBox="0 0 24 24" 
                fill="none" 
                stroke="currentColor" 
                strokeWidth="2"
              >
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          </div>

          {/* Contenido */}
          <div className="p-6 space-y-6">
            {/* Introducción */}
            <section>
              <h3 className="text-[#FFD700] text-lg mb-3">¿Qué es Eco?</h3>
              <p className="text-white/80 text-sm leading-relaxed">
                Eco es tu asistente personal inteligente que puede controlar tu sistema, 
                reproducir música, crear temporizadores, tomar notas y mucho más. 
                Puedes interactuar con ella por voz o por texto.
              </p>
            </section>

            {/* Comandos de voz */}
            <section>
              <h3 className="text-[#FFD700] text-lg mb-3">Comandos de voz</h3>
              <div className="space-y-3">
                <div className="bg-[#000000]/40 p-3 rounded-lg">
                  <p className="text-white text-sm font-medium">"Hola Eco" / "Buenos días"</p>
                  <p className="text-white/60 text-xs mt-1">Saluda a Eco para iniciar una conversación</p>
                </div>
                <div className="bg-[#000000]/40 p-3 rounded-lg">
                  <p className="text-white text-sm font-medium">"¿Qué hora es?"</p>
                  <p className="text-white/60 text-xs mt-1">Consulta la hora actual</p>
                </div>
                <div className="bg-[#000000]/40 p-3 rounded-lg">
                  <p className="text-white text-sm font-medium">"Sube el volumen" / "Baja el brillo"</p>
                  <p className="text-white/60 text-xs mt-1">Controla el volumen y brillo de tu sistema</p>
                </div>
                <div className="bg-[#000000]/40 p-3 rounded-lg">
                  <p className="text-white text-sm font-medium">"Pon música de..." / "Reproduce..."</p>
                  <p className="text-white/60 text-xs mt-1">Controla Spotify y reproduce música</p>
                </div>
                <div className="bg-[#000000]/40 p-3 rounded-lg">
                  <p className="text-white text-sm font-medium">"Crea un temporizador de 5 minutos"</p>
                  <p className="text-white/60 text-xs mt-1">Crea temporizadores y alarmas</p>
                </div>
                <div className="bg-[#000000]/40 p-3 rounded-lg">
                  <p className="text-white text-sm font-medium">"Toma nota:..."</p>
                  <p className="text-white/60 text-xs mt-1">Guarda notas y recordatorios</p>
                </div>
                <div className="bg-[#000000]/40 p-3 rounded-lg">
                  <p className="text-white text-sm font-medium">"Abre [aplicación]"</p>
                  <p className="text-white/60 text-xs mt-1">Abre aplicaciones como Chrome, Spotify, etc.</p>
                </div>
              </div>
            </section>

            {/* Capacidades */}
            <section>
              <h3 className="text-[#FFD700] text-lg mb-3">Capacidades</h3>
              <ul className="space-y-2 text-white/80 text-sm">
                <li className="flex items-start gap-2">
                  <span className="text-[#FFD700] mt-1">•</span>
                  <span>Control del sistema: volumen, brillo, velocidad del ratón</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-[#FFD700] mt-1">•</span>
                  <span>Reproducción de música con Spotify</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-[#FFD700] mt-1">•</span>
                  <span>Temporizadores y alarmas</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-[#FFD700] mt-1">•</span>
                  <span>Gestión de notas y recordatorios</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-[#FFD700] mt-1">•</span>
                  <span>Apertura de aplicaciones</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-[#FFD700] mt-1">•</span>
                  <span>Información del sistema: CPU, RAM, batería</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-[#FFD700] mt-1">•</span>
                  <span>Conversación natural con IA</span>
                </li>
              </ul>
            </section>

            {/* Atajos de teclado */}
            <section>
              <h3 className="text-[#FFD700] text-lg mb-3">Atajos de teclado</h3>
              <div className="space-y-2 text-white/80 text-sm">
                <p><span className="text-[#FFD700]">Ctrl + M</span> - Abrir/cerrar chat</p>
                <p><span className="text-[#FFD700]">Ctrl + S</span> - Abrir ajustes</p>
                <p><span className="text-[#FFD700]">Ctrl + H</span> - Abrir manual</p>
              </div>
            </section>
          </div>
        </div>
      </div>
    </>
  );
}