import customtkinter as ctk
import threading, datetime, webbrowser, time, math
import pyttsx3, speech_recognition as sr, sounddevice as sd, scipy.io.wavfile as wav
import openai, spotipy, wikipedia, requests, os
from spotipy.oauth2 import SpotifyOAuth
from playsound import playsound
from PIL import Image, ImageTk, ImageGrab
from dotenv import load_dotenv
import subprocess

# Load API keys from .env file
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
SPOTIPY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

# Spotify setup
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET,
    redirect_uri="http://127.0.0.1:8888/callback",
    scope="user-read-playback-state,user-modify-playback-state,streaming"
))

# GUI Setup
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")
app = ctk.CTk()
app.title("JARVIS HUD")
app.geometry("1200x700")

# Background animation
bg_frames = []
for file in sorted(os.listdir("bg")):
    if file.endswith(".png"):
        bg_frames.append(ImageTk.PhotoImage(Image.open(f"bg/{file}")))
bg_label = ctk.CTkLabel(app)
bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)
def animate_bg(idx=0):
    bg_label.configure(image=bg_frames[idx % len(bg_frames)])
    app.after(100, animate_bg, idx + 1)
animate_bg()

# Voice engine
engine = pyttsx3.init()
def speak(text):
    response_box.insert("end", f"JARVIS: {text}\n")
    response_box.see("end")
    engine.say(text)
    engine.runAndWait()

def record_audio(duration=4):
    fs = 44100
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
    sd.wait()
    wav.write("tmp.wav", fs, recording)

def listen(threshold=100):
    record_audio()
    r = sr.Recognizer()
    with sr.AudioFile("tmp.wav") as src:
        audio = r.record(src)
    try:
        cmd = r.recognize_google(audio).lower()
        if len(cmd.strip()) == 0:
            return ""
        response_box.insert("end", f"You: {cmd}\n")
        return cmd
    except:
        return ""

def chat_gpt(prompt):
    try:
        res = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": prompt}], max_tokens=150)
        speak(res.choices[0].message.content.strip())
    except:
        speak("Error connecting to GPT.")

def get_weather(city):
    try:
        data = requests.get(f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric").json()
        speak(f"{city}: {data['main']['temp']}°C, {data['weather'][0]['description']}")
    except:
        speak("Unable to fetch weather info.")

def play_spotify(song):
    try:
        res = sp.search(q=song, type='track', limit=1)
        if res['tracks']['items']:
            sp.start_playback(uris=[res['tracks']['items'][0]['uri']])
            speak(f"Playing {song} on Spotify.")
        else:
            speak("Song not found on Spotify.")
    except:
        speak("Spotify error. Make sure the app is open and a device is active.")

def take_screenshot():
    now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_path = f"screenshot_{now}.png"
    screenshot = ImageGrab.grab()
    screenshot.save(file_path)
    speak(f"Screenshot saved as {file_path}.")

def jarvis_brain():
    speak("Yes sir.")
    cmd = listen()
    if not cmd:
        speak("Sorry, I didn't catch that.")
        return
    if "time" in cmd:
        speak(datetime.datetime.now().strftime("%I:%M %p"))
    elif "weather" in cmd:
        city = cmd.replace("weather", "").strip()
        get_weather(city)
    elif "play" in cmd or "spotify" in cmd:
        song = cmd.replace("play", "").replace("spotify", "").strip()
        play_spotify(song)
    elif "wikipedia" in cmd or "wiki" in cmd:
        try:
            speak(wikipedia.summary(cmd.replace("wikipedia", "").replace("wiki", "").strip(), sentences=2))
        except:
            speak("No results found.")
    elif "chat" in cmd or "gpt" in cmd:
        speak("What do you want to ask?")
        chat_gpt(listen())
    elif "open google" in cmd:
        speak("Opening Google")
        webbrowser.open("https://www.google.com")
    elif "open youtube" in cmd:
        speak("Opening YouTube")
        webbrowser.open("https://www.youtube.com")
    elif "shutdown" in cmd:
        speak("Shutting down the system.")
        os.system("shutdown /s /t 1")
    elif "restart" in cmd:
        speak("Restarting the system.")
        os.system("shutdown /r /t 1")
    elif "screenshot" in cmd:
        take_screenshot()
    elif "exit" in cmd or "close" in cmd:
        speak("Goodbye.")
        return
    else:
        speak("Command not recognized.")

def wait_for_wake_word():
    while True:
        cmd = listen()
        if "jarvis" in cmd:
            jarvis_brain()

# GUI Elements
title = ctk.CTkLabel(app, text="🧠 J.A.R.V.I.S.", font=("Orbitron", 40))
title.place(relx=0.05, rely=0.05)
clock = ctk.CTkLabel(app, font=("Consolas", 18))
clock.place(relx=0.85, rely=0.05)
def update_clock():
    clock.configure(text=datetime.datetime.now().strftime("%I:%M:%S %p"))
    app.after(1000, update_clock)
update_clock()

response_box = ctk.CTkTextbox(app, width=900, height=300, font=("Consolas", 14))
response_box.place(relx=0.05, rely=0.15)

mic_btn = ctk.CTkButton(app, text="🎤 Wake JARVIS", font=("Orbitron", 20), command=lambda: threading.Thread(target=wait_for_wake_word, daemon=True).start())
mic_btn.place(relx=0.4, rely=0.8)

# Play intro and activate JARVIS after
try:
    playsound("jarvis_theme.mp3")
except:
    pass
speak("JARVIS activated, sir.")
threading.Thread(target=wait_for_wake_word, daemon=True).start()

app.mainloop()
