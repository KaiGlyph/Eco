interface PowerWidgetProps {
  onCommand: (text: string) => void
}

export function PowerWidget({ onCommand }: PowerWidgetProps) {
  const handlePowerAction = (action: 'shutdown' | 'restart' | 'suspend' | 'lock') => {
    // Añadimos "ahora" para indicar ejecución inmediata sin confirmación
    const commands = {
      shutdown: 'apaga el ordenador ahora',
      restart: 'reinicia el ordenador ahora',
      suspend: 'suspende el ordenador ahora',
      lock: 'bloquea el equipo' // El bloqueo no suele necesitar confirmación extra
    }
    onCommand(commands[action])
  }

  const buttons = [
    { 
      label: 'Apagar', 
      action: 'shutdown' as const, 
      icon: <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M18.36 6.64a9 9 0 1 1-12.73 0"></path><line x1="12" y1="2" x2="12" y2="12"></line></svg>
    },
    { 
      label: 'Reiniciar', 
      action: 'restart' as const, 
      icon: <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path></svg>
    },
    { 
      label: 'Suspender', 
      action: 'suspend' as const, 
      icon: <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>
    },
    { 
      label: 'Bloquear', 
      action: 'lock' as const, 
      icon: <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
    },
  ]

  return (
    <div className="relative bg-eco-deep/40 backdrop-blur-xl border border-eco-purple/20 rounded-3xl p-6 flex flex-col hover:border-eco-purple/40 transition-all duration-300">
      <h3 className="text-white/80 font-light text-sm uppercase tracking-wider mb-4">Sistema</h3>
      
      <div className="grid grid-cols-2 gap-3 flex-1">
        {buttons.map(btn => (
          <button
            key={btn.action}
            onClick={() => handlePowerAction(btn.action)}
            className="bg-white/5 hover:bg-eco-purple/30 text-white/70 hover:text-white rounded-xl flex flex-col items-center justify-center gap-2 transition-all duration-300 border border-transparent hover:border-eco-purple/30"
          >
            {btn.icon}
            <span className="text-xs font-light">{btn.label}</span>
          </button>
        ))}
      </div>
    </div>
  )
}