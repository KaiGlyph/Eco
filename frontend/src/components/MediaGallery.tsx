import { useState, useEffect } from 'react';

interface MediaItem {
  id: string;
  url: string;
  timestamp: string;
  type: 'photo' | 'video';
}

interface FolderCard {
  id: string;
  title: string;
  subtitle: string;
  count: number;
  lastModified?: string;
  gradient: string;
  icon: React.ReactNode;
}

interface MediaGalleryProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function MediaGallery({ isOpen, onClose }: MediaGalleryProps) {
  const [selectedFolder, setSelectedFolder] = useState<'photos' | 'videos' | null>(null);
  const [photos, setPhotos] = useState<MediaItem[]>([]);
  const [videos, setVideos] = useState<MediaItem[]>([]);

  useEffect(() => {
    if (isOpen) {
      fetchGallery();
    } else {
      setSelectedFolder(null);
    }
  }, [isOpen]);

  const fetchGallery = async () => {
    try {
      const [photosRes, videosRes] = await Promise.all([
        fetch('http://localhost:8000/api/gallery/photos'),
        fetch('http://localhost:8000/api/gallery/videos')
      ]);
      setPhotos((await photosRes.json()).photos || []);
      setVideos((await videosRes.json()).videos || []);
    } catch (error) {
      console.error('Error cargando galería:', error);
    }
  };

  const folders: FolderCard[] = [
    { 
      id: 'photos', 
      title: 'Capturas de Pantalla', 
      subtitle: 'Imágenes guardadas automáticamente',
      count: photos.length,
      lastModified: photos[0]?.timestamp,
      gradient: 'from-[#6A0DAD]/20 to-[#FFD700]/10',
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-[#FFD700]">
          <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
          <circle cx="8.5" cy="8.5" r="1.5"></circle>
          <polyline points="21 15 16 10 5 21"></polyline>
        </svg>
      )
    },
    { 
      id: 'videos', 
      title: 'Videos de Detección de Movimiento', 
      subtitle: 'Detección de actividad',
      count: videos.length,
      lastModified: videos[0]?.timestamp,
      gradient: 'from-[#FFD700]/10 to-[#6A0DAD]/20',
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-[#FFD700]">
          <polygon points="23 7 16 12 23 17 23 7"></polygon>
          <rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect>
        </svg>
      )
    }
  ];

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
            title="Cerrar galería"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="group-hover:rotate-90 transition-transform duration-500">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>

          {/* Modal principal */}
          <div className="bg-gradient-to-br from-[#1A0033] via-[#0D001A] to-[#1A0033] border border-[#FFD700]/20 rounded-3xl w-full max-h-[90vh] shadow-[0_0_60px_rgba(106,13,173,0.3)] overflow-hidden flex flex-col">
            
            {/* Header elegante */}
            <div className="relative px-8 lg:px-12 py-8 border-b border-[#FFD700]/10">
              {/* Logo Eco */}
              <div className="flex items-center gap-4 mb-4">
                <div className="w-12 h-12 rounded-full bg-gradient-to-br from-[#6A0DAD] to-[#FFD700] p-[2px] shadow-[0_0_20px_rgba(255,215,0,0.3)]">
                  <div className="w-full h-full rounded-full bg-[#1A0033] flex items-center justify-center">
                    <img src="/Eco.png" alt="Eco" className="w-7 h-7" />
                  </div>
                </div>
                <div>
                  <h1 className="text-[#FFD700] text-2xl font-extralight tracking-[0.2em] uppercase">
                    Galería
                  </h1>
                  <p className="text-white/40 text-xs tracking-widest uppercase mt-0.5">
                    Archivos y contenido
                  </p>
                </div>
              </div>
              
              {/* Línea decorativa dorada */}
              <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-[#FFD700]/40 to-transparent"></div>
            </div>

            {/* Contenido */}
            <div className="flex-1 overflow-y-auto p-8 lg:p-12 scrollbar-thin scrollbar-thumb-[#6A0DAD]/30 scrollbar-track-transparent">
              
              {/* Vista de Carpetas */}
              {!selectedFolder && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {folders.map((folder) => (
                    <button
                      key={folder.id}
                      onClick={() => setSelectedFolder(folder.id as 'photos' | 'videos')}
                      className="group relative p-8 bg-[#000000]/40 border-2 border-[#FFD700]/20 hover:border-[#FFD700]/50 rounded-2xl overflow-hidden transition-all duration-700 text-left hover:scale-[1.02] hover:shadow-[0_0_40px_rgba(106,13,173,0.2)]"
                    >
                      {/* Fondo gradiente animado */}
                      <div className={`absolute inset-0 bg-gradient-to-br ${folder.gradient} opacity-0 group-hover:opacity-100 transition-opacity duration-700`}></div>
                      
                      {/* Glow dorado en hover */}
                      <div className="absolute inset-0 bg-gradient-to-br from-[#FFD700]/0 via-transparent to-[#FFD700]/0 group-hover:from-[#FFD700]/5 group-hover:to-transparent transition-all duration-700"></div>
                      
                      <div className="relative z-10">
                        {/* Icono con glow */}
                        <div className="flex items-start justify-between mb-6">
                          <div className="w-20 h-20 rounded-2xl bg-[#6A0DAD]/20 border border-[#FFD700]/20 flex items-center justify-center group-hover:scale-110 group-hover:bg-[#6A0DAD]/30 group-hover:border-[#FFD700]/40 group-hover:shadow-[0_0_30px_rgba(255,215,0,0.2)] transition-all duration-700">
                            {folder.icon}
                          </div>
                          
                          {/* Flecha animada */}
                          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-white/20 group-hover:text-[#FFD700]/60 group-hover:translate-x-1 transition-all duration-500">
                            <polyline points="9 18 15 12 9 6"></polyline>
                          </svg>
                        </div>
                        
                        {/* Título */}
                        <h3 className="text-white text-xl font-light tracking-wide mb-1 group-hover:text-[#FFD700] transition-colors duration-500">
                          {folder.title}
                        </h3>
                        
                        {/* Subtítulo */}
                        <p className="text-white/40 text-sm font-light mb-4">
                          {folder.subtitle}
                        </p>
                        
                        {/* Estadísticas */}
                        <div className="flex items-center gap-4 text-white/50 text-sm">
                          <div className="flex items-center gap-2">
                            <div className="w-2 h-2 rounded-full bg-[#FFD700]/60"></div>
                            <span>{folder.count} {folder.count === 1 ? 'archivo' : 'archivos'}</span>
                          </div>
                          {folder.lastModified && (
                            <>
                              <div className="w-1 h-1 rounded-full bg-white/30"></div>
                              <span className="text-white/40">{new Date(folder.lastModified).toLocaleDateString('es-ES', { day: '2-digit', month: 'short', year: 'numeric' })}</span>
                            </>
                          )}
                        </div>
                      </div>
                      
                      {/* Borde inferior dorado animado */}
                      <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-[#FFD700]/0 to-transparent group-hover:via-[#FFD700]/60 transition-all duration-700"></div>
                    </button>
                  ))}
                </div>
              )}

              {/* Vista de Fotos */}
              {selectedFolder === 'photos' && (
                <div className="animate-fade-in">
                  <button 
                    onClick={() => setSelectedFolder(null)} 
                    className="mb-8 flex items-center gap-3 text-[#FFD700]/60 hover:text-[#FFD700] transition-all duration-300 group font-light tracking-wide"
                  >
                    <div className="w-10 h-10 rounded-full border border-[#FFD700]/30 flex items-center justify-center group-hover:border-[#FFD700]/60 group-hover:bg-[#FFD700]/10 transition-all duration-300">
                      <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="group-hover:-translate-x-0.5 transition-transform duration-300">
                        <polyline points="15 18 9 12 15 6"></polyline>
                      </svg>
                    </div>
                    <span>Volver a carpetas</span>
                  </button>
                  
                  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
                    {photos.map((photo) => (
                      <div key={photo.id} className="group relative aspect-square rounded-2xl overflow-hidden border border-[#FFD700]/10 hover:border-[#FFD700]/40 transition-all duration-500 hover:shadow-[0_0_30px_rgba(255,215,0,0.15)] bg-[#000000]/40">
                        <img 
                          src={photo.url} 
                          alt={photo.id} 
                          className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700" 
                        />
                        <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-all duration-500">
                          <div className="absolute bottom-0 left-0 right-0 p-5">
                            <p className="text-[#FFD700] text-xs font-light tracking-wide mb-1">
                              {new Date(photo.timestamp).toLocaleDateString('es-ES', { day: '2-digit', month: 'short', year: 'numeric' })}
                            </p>
                            <p className="text-white/60 text-[10px]">
                              {new Date(photo.timestamp).toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })}
                            </p>
                          </div>
                        </div>
                        {/* Overlay dorado sutil */}
                        <div className="absolute inset-0 bg-[#FFD700]/0 group-hover:bg-[#FFD700]/5 transition-colors duration-500 pointer-events-none"></div>
                      </div>
                    ))}
                    {photos.length === 0 && (
                      <div className="col-span-full flex flex-col items-center justify-center py-24 text-white/30">
                        <div className="w-24 h-24 rounded-full bg-[#6A0DAD]/10 border border-[#FFD700]/10 flex items-center justify-center mb-6">
                          <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" className="text-[#FFD700]/40">
                            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                            <circle cx="8.5" cy="8.5" r="1.5"></circle>
                            <polyline points="21 15 16 10 5 21"></polyline>
                          </svg>
                        </div>
                        <p className="text-lg font-light tracking-wide mb-2">No hay fotos capturadas</p>
                        <p className="text-sm text-white/40">Las capturas aparecerán aquí automáticamente</p>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Vista de Videos */}
              {selectedFolder === 'videos' && (
                <div className="animate-fade-in">
                  <button 
                    onClick={() => setSelectedFolder(null)} 
                    className="mb-8 flex items-center gap-3 text-[#FFD700]/60 hover:text-[#FFD700] transition-all duration-300 group font-light tracking-wide"
                  >
                    <div className="w-10 h-10 rounded-full border border-[#FFD700]/30 flex items-center justify-center group-hover:border-[#FFD700]/60 group-hover:bg-[#FFD700]/10 transition-all duration-300">
                      <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="group-hover:-translate-x-0.5 transition-transform duration-300">
                        <polyline points="15 18 9 12 15 6"></polyline>
                      </svg>
                    </div>
                    <span>Volver a carpetas</span>
                  </button>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {videos.map((video) => (
                      <div key={video.id} className="group relative rounded-2xl overflow-hidden border border-[#FFD700]/10 hover:border-[#FFD700]/40 transition-all duration-500 bg-[#000000]/40 hover:shadow-[0_0_30px_rgba(106,13,173,0.2)]">
                        <div className="aspect-video bg-[#000000]/60 relative overflow-hidden">
                          <video 
                            src={video.url} 
                            controls 
                            className="w-full h-full"
                            preload="metadata"
                          />
                        </div>
                        <div className="p-6">
                          <p className="text-white/40 text-xs font-light mb-3">
                            {new Date(video.timestamp).toLocaleString('es-ES', { 
                              day: '2-digit', 
                              month: 'short', 
                              year: 'numeric',
                              hour: '2-digit',
                              minute: '2-digit'
                            })}
                          </p>
                          <a 
                            href={video.url} 
                            download 
                            className="inline-flex items-center gap-2 px-5 py-2.5 bg-[#6A0DAD]/40 hover:bg-[#6A0DAD]/60 border border-[#FFD700]/20 hover:border-[#FFD700]/40 rounded-xl text-[#FFD700] text-xs font-light tracking-wide transition-all duration-300 hover:shadow-[0_0_20px_rgba(255,215,0,0.2)]"
                          >
                            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                              <polyline points="7 10 12 15 17 10"></polyline>
                              <line x1="12" y1="15" x2="12" y2="3"></line>
                            </svg>
                            Descargar video
                          </a>
                        </div>
                      </div>
                    ))}
                    {videos.length === 0 && (
                      <div className="col-span-full flex flex-col items-center justify-center py-24 text-white/30">
                        <div className="w-24 h-24 rounded-full bg-[#6A0DAD]/10 border border-[#FFD700]/10 flex items-center justify-center mb-6">
                          <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" className="text-[#FFD700]/40">
                            <polygon points="23 7 16 12 23 17 23 7"></polygon>
                            <rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect>
                          </svg>
                        </div>
                        <p className="text-lg font-light tracking-wide mb-2">No hay videos de detección</p>
                        <p className="text-sm text-white/40">Los videos se generarán al detectar actividad</p>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}