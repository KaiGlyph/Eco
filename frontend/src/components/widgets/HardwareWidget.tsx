interface HardwareWidgetProps {
  hardware: {
    cpu: number
    ram: number
    disk: number
    battery: number | null
  }
}

export function HardwareWidget({ hardware }: HardwareWidgetProps) {
  const metrics = [
    { label: 'CPU', value: hardware.cpu, color: 'from-eco-gold to-yellow-300' },
    { label: 'RAM', value: hardware.ram, color: 'from-eco-purple to-purple-400' },
    { label: 'Disco', value: hardware.disk, color: 'from-purple-500 to-purple-300' },
  ]

  if (hardware.battery !== null) {
    metrics.push({ label: 'Batería', value: hardware.battery, color: 'from-green-500 to-green-300' })
  }

  return (
    <div className="relative bg-eco-deep/40 backdrop-blur-xl border border-eco-purple/20 rounded-3xl p-6 flex flex-col hover:border-eco-purple/40 transition-all duration-300">
      <h3 className="text-white/80 font-light text-sm uppercase tracking-wider mb-5">Hardware</h3>
      
      <div className="space-y-4 flex-1 flex flex-col justify-center">
        {metrics.map(m => (
          <div key={m.label}>
            <div className="flex justify-between text-white/70 text-xs mb-1.5">
              <span className="font-light">{m.label}</span>
              <span className="font-mono text-eco-gold/80">{Math.round(m.value)}%</span>
            </div>
            <div className="w-full bg-white/5 rounded-full h-1 overflow-hidden">
              <div 
                className={`h-full bg-gradient-to-r ${m.color} transition-all duration-500`} 
                style={{ width: `${m.value}%` }}
              ></div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}