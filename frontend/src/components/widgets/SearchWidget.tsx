import { useState } from 'react'

interface SearchWidgetProps {
  onCommand: (text: string) => void
}

export function SearchWidget({ onCommand }: SearchWidgetProps) {
  const [query, setQuery] = useState('')

  const handleSearch = () => {
    if (query.trim()) {
      onCommand(`busca en google ${query}`)
      setQuery('')
    }
  }

  return (
    <div className="relative bg-eco-deep/40 backdrop-blur-xl border border-eco-purple/20 rounded-3xl p-6 flex flex-col hover:border-eco-purple/40 transition-all duration-300">
      <h3 className="text-white/80 font-light text-sm uppercase tracking-wider mb-4">Búsqueda</h3>
      
      <div className="flex-1 flex flex-col justify-center">
        <div className="flex gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="Buscar en Google..."
            className="flex-1 bg-white/5 text-white/90 px-4 py-3 rounded-xl border border-white/10 focus:outline-none focus:border-eco-purple/50 text-sm font-light placeholder:text-white/30 transition-all"
          />
          <button
            onClick={handleSearch}
            className="w-12 h-12 rounded-xl bg-eco-purple/30 hover:bg-eco-purple/50 text-eco-gold flex items-center justify-center transition-all duration-300"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
          </button>
        </div>
      </div>
    </div>
  )
}