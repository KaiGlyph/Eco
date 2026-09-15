import './Orb.css';
import SoundWave from './SoundWave';

interface OrbProps {
  isSpeaking: boolean;
  audioData?: Uint8Array;
}

export default function Orb({ isSpeaking, audioData }: OrbProps) {
  return (
    <div className="orb-container">
      <div className="orb-eclipse-outer" />
      <div className="orb-eclipse-inner" />
      <div className="orb-glow" />
      <div className="orb">
        <SoundWave isActive={isSpeaking} audioData={audioData} />
      </div>
    </div>
  );
}