interface TimerWidgetProps {
  onCommand: (text: string) => void
  timers: Array<{
    id: number
    label: string
    type: string
    remaining_seconds: number
  }>
}

export function TimerWidget({ onCommand, timers }: TimerWidgetProps) {
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  return (
    <div className="relative bg-eco-deep/40 backdrop-blur-xl border border-eco-purple/20 rounded-3xl p-6 flex flex-col hover:border-eco-purple/40 transition-all duration-300">
      <h3 className="text-white/80 font-light text-sm uppercase tracking-wider mb-4">Temporizadores</h3>
      
      {timers.length === 0 ? (
        <div className="flex-1 flex items-center justify-center flex-col gap-3">
          <p className="text-white/30 text-sm font-light">Sin temporizadores activos</p>
          <button
            onClick={() => onCommand('pon un temporizador de 5 minutos')}
            className="text-xs text-eco-gold/60 hover:text-eco-gold transition-colors"
          >
            Crear temporizador
          </button>
        </div>
      ) : (
        <div className="space-y-2 flex-1 overflow-y-auto">
          {timers.map(timer => (
            <div key={timer.id} className="bg-white/5 rounded-xl p-3 flex justify-between items-center border border-eco-purple/10">
              <div className="flex flex-col">
                <span className="text-white/80 text-sm font-light">
                  {timer.type === 'alarm' ? 'Alarma' : 'Timer'}: {timer.label}
                </span>
              </div>
              <span className="text-eco-gold font-mono text-sm">
                {formatTime(timer.remaining_seconds)}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}