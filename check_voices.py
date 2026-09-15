import pyttsx3

engine = pyttsx3.init()
voices = engine.getProperty('voices')

print("Voces disponibles en Windows:")
for i, voice in enumerate(voices):
    print(f"{i}: {voice.name} - {voice.id}")