import speech_recognition as sr

recognizer = sr.Recognizer()

with sr.Microphone() as source:
    print("NOVA: Speak now...")
    recognizer.adjust_for_ambient_noise(source, duration=1)
    audio = recognizer.listen(source, timeout=5, phrase_time_limit=8)

try:
    text = recognizer.recognize_google(audio)
    print("You said:", text)
except sr.UnknownValueError:
    print("Sorry, I could not understand.")
except sr.RequestError as e:
    print("Internet or speech service error:", e)