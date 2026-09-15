import time

class MorseDecoder:
    def __init__(self):
        # Diccionario Morse (Español/Inglés básico)
        self.morse_dict = {
            '.-': 'A', '-...': 'B', '-.-.': 'C', '-..': 'D', '.': 'E',
            '..-.': 'F', '--.': 'G', '....': 'H', '..': 'I', '.---': 'J',
            '-.-': 'K', '.-..': 'L', '--': 'M', '-.': 'N', '---': 'O',
            '.--.': 'P', '--.-': 'Q', '.-.': 'R', '...': 'S', '-': 'T',
            '..-': 'U', '...-': 'V', '.--': 'W', '-..-': 'X', '-.--': 'Y',
            '--..': 'Z',
            '-----': '0', '.----': '1', '..---': '2', '...--': '3', '....-': '4',
            '.....': '5', '-....': '6', '--...': '7', '---..': '8', '----.': '9',
            '.-.-.-': '.', '--..--': ',', '..--..': '?', '.----.': "'",
            '-.-.--': '!', '-..-.': '/', '-.--.': '(', '-.--.-': ')',
            '.-...': '&', '---...': ':', '-.-.-.': ';', '-...-': '=',
            '.-.-.': '+', '-....-': '-', '..--.-': '_', '.-..-.': '"',
            '...-..-': '$', '.--.-.': '@'
        }
        
        # Estado actual
        self.current_sequence = ""  # Secuencia de puntos/rayas actual (ej: ".-")
        self.current_word = ""      # Palabra en construcción
        self.full_text = ""         # Texto completo decodificado
        
        # Tiempos (en segundos)
        self.dot_threshold = 0.35   # < 350ms = Punto
        self.letter_gap = 0.8       # Pausa > 800ms = Nueva letra
        self.word_gap = 1.5         # Pausa > 1.5s = Nueva palabra
        
        self.last_signal_time = 0
        self.is_waiting_gap = False

    def process_signal(self, duration: float):
        """Procesa la duración de un puño cerrado"""
        self.last_signal_time = time.time()
        self.is_waiting_gap = True
        
        if duration < self.dot_threshold:
            self.current_sequence += "."
        else:
            self.current_sequence += "-"
        
        print(f"[MORSE] Señal: {'Punto' if duration < self.dot_threshold else 'Raya'} ({duration:.2f}s) -> Secuencia: {self.current_sequence}")

    def check_gaps(self):
        """Verifica si ha pasado tiempo suficiente para separar letra o palabra"""
        if not self.is_waiting_gap:
            return
        
        elapsed = time.time() - self.last_signal_time
        
        if elapsed > self.word_gap:
            # Nueva palabra
            if self.current_sequence:
                self._decode_current_letter()
            if self.current_word:
                self.full_text += self.current_word + " "
                self.current_word = ""
            self.is_waiting_gap = False
            print(f"[MORSE] Palabra completada: '{self.full_text}'")
            
        elif elapsed > self.letter_gap:
            # Nueva letra
            if self.current_sequence:
                self._decode_current_letter()
            self.is_waiting_gap = False

    def _decode_current_letter(self):
        """Decodifica la secuencia actual a una letra"""
        letter = self.morse_dict.get(self.current_sequence, '?')
        self.current_word += letter
        print(f"[MORSE] Letra decodificada: {self.current_sequence} -> {letter}")
        self.current_sequence = ""

    def get_state(self) -> dict:
        """Devuelve el estado actual para el frontend"""
        return {
            "sequence": self.current_sequence,
            "current_word": self.current_word,
            "full_text": self.full_text
        }

    def reset(self):
        """Reinicia el decodificador"""
        self.current_sequence = ""
        self.current_word = ""
        self.full_text = ""
        self.last_signal_time = 0
        self.is_waiting_gap = False