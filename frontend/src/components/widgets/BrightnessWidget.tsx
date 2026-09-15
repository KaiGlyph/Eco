interface BrightnessWidgetProps {
  onCommand: (text: string) => void
  brightness: number
}

export function BrightnessWidget({ onCommand, brightness }: BrightnessWidgetProps) {
  const handleBrightnessChange = (action: 'up' | 'down') => {
    const commands = {
      up: 'sube el brillo',
      down: 'baja el brillo'
    }
    onCommand(commands[action])
  }

  return (
    <div className="relative bg-eco-deep/40 backdrop-blur-xl border border-eco-purple/20 rounded-3xl p-6 flex flex-col justify-between hover:border-eco-purple/40 transition-all duration-300">
      <div className="flex items-center justify-between">
        <h3 className="text-white/80 font-light text-sm uppercase tracking-wider">Brillo</h3>
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-eco-gold/80"><circle cx="12" cy="12" r="4"></circle><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"></path></svg>
      </div>
      
      <div className="my-4">
        <div className="text-6xl font-thin text-white">
          {Math.round(brightness)}<span className="text-2xl text-eco-gold">%</span>
        </div>
      </div>
      
      <div className="w-full bg-white/5 rounded-full h-1 mb-4 overflow-hidden">
        <div 
          className="h-full bg-gradient-to-r from-eco-purple to-eco-gold transition-all duration-300" 
          style={{ width: `${brightness}%` }}
        ></div>
      </div>
      
      <div className="flex gap-4 justify-center">
        <button
          onClick={() => handleBrightnessChange('down')}
          className="w-12 h-12 rounded-full bg-white/5 hover:bg-eco-purple/30 text-white/70 hover:text-white flex items-center justify-center transition-all duration-300"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><line x1="5" y1="12" x2="19" y2="12"></line></svg>
        </button>
        <button
          onClick={() => handleBrightnessChange('up')}
          className="w-12 h-12 rounded-full bg-white/5 hover:bg-eco-purple/30 text-white/70 hover:text-white flex items-center justify-center transition-all duration-300"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
        </button>
      </div>
    </div>
  )
}