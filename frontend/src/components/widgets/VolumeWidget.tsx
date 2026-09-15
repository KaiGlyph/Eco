import { useState } from 'react'

interface VolumeWidgetProps {
  onCommand: (text: string) => void
  volume: number
}

export function VolumeWidget({ onCommand, volume }: VolumeWidgetProps) {
  const [isMuted, setIsMuted] = useState(false)

  const handleVolumeChange = (action: 'up' | 'down' | 'mute') => {
    const commands = {
      up: 'sube el volumen',
      down: 'baja el volumen',
      mute: 'silencia'
    }
    onCommand(commands[action])
  }

  return (
    <div className="relative bg-eco-deep/40 backdrop-blur-xl border border-eco-purple/20 rounded-3xl p-6 flex flex-col justify-between hover:border-eco-purple/40 transition-all duration-300 group">
      <div className="flex items-center justify-between">
        <h3 className="text-white/80 font-light text-sm uppercase tracking-wider">Volumen</h3>
        <button
          onClick={() => {
            setIsMuted(!isMuted)
            handleVolumeChange('mute')
          }}
          className="text-eco-gold/80 hover:text-eco-gold transition-colors p-1"
        >
          {isMuted ? (
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><line x1="23" y1="9" x2="17" y2="15"></line><line x1="17" y1="9" x2="23" y2="15"></line></svg>
          ) : (
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path></svg>
          )}
        </button>
      </div>
      
      <div className="my-4">
        <div className="text-6xl font-thin text-white">
          {Math.round(volume)}<span className="text-2xl text-eco-gold">%</span>
        </div>
      </div>
      
      <div className="w-full bg-white/5 rounded-full h-1 mb-4 overflow-hidden">
        <div 
          className="h-full bg-gradient-to-r from-eco-purple to-eco-gold transition-all duration-300" 
          style={{ width: `${volume}%` }}
        ></div>
      </div>
      
      <div className="flex gap-4 justify-center">
        <button
          onClick={() => handleVolumeChange('down')}
          className="w-12 h-12 rounded-full bg-white/5 hover:bg-eco-purple/30 text-white/70 hover:text-white flex items-center justify-center transition-all duration-300"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><line x1="5" y1="12" x2="19" y2="12"></line></svg>
        </button>
        <button
          onClick={() => handleVolumeChange('up')}
          className="w-12 h-12 rounded-full bg-white/5 hover:bg-eco-purple/30 text-white/70 hover:text-white flex items-center justify-center transition-all duration-300"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
        </button>
      </div>
    </div>
  )
}