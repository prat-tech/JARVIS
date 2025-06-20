import customtkinter as ctk
from tkinter import Label
import threading, datetime, webbrowser, time, os, psutil, platform, random
import pyttsx3, speech_recognition as sr, sounddevice as sd, scipy.io.wavfile as wav
import requests, wikipedia, cv2, pyautogui
from playsound import playsound
from PIL import ImageGrab, ImageTk, Image
from llama_cpp import Llama

# ——— CONFIGURATION ————————
WEATHER_API_KEY = "your_openweathermap_key"
MODEL_PATH = "models/mistral-7b-instruct-v0.1.Q4_K_M.gguf"

# ——— Load Local GPT ——————
llm = Llama(model_path=MODEL_PATH, n_ctx=2048)
memory = [{"role": "system", "content": "You are JARVIS, a helpful AI assistant."}]

# ——— GUI Setup ————————
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")
app = ctk.CTk()
app.title("JARVIS HUD")
app.state("zoomed")
SCREEN_WIDTH, SCREEN_HEIGHT = app.winfo_screenwidth(), app.winfo_screenheight()
app.geometry(f"{SCREEN_WIDTH}x{SCREEN_HEIGHT}+0+0")

# ——— Background Video ——————
video_label = Label(app)
video_label.place(x=0, y=0, relwidth=1, relheight=1)
cap = cv2.VideoCapture("jarvis_loop.mp4")

def update_video():
    ret, frame = cap.read()
    if ret:
        frame = cv2.resize(frame, (SCREEN_WIDTH, SCREEN_HEIGHT))
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame)
        tkimg = ImageTk.PhotoImage(img)
        video_label.configure(image=tkimg)
        video_label.image = tkimg
    else:
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    app.after(30, update_video)
update_video()

# ——— GUI Labels ——————
title = ctk.CTkLabel(app, text="🤖 [ J.A.R.V.I.S ]", font=("Orbitron", 36, "bold"), text_color="#00FFFF")
title.place(relx=0.05, rely=0.05)

you_lbl = ctk.CTkLabel(app, font=("Consolas", 20), text="", text_color="#00BFFF")
you_lbl.place(relx=0.05, rely=0.75)
jarvis_lbl = ctk.CTkLabel(app, font=("Consolas", 20), text="", text_color="#00FF00")
jarvis_lbl.place(relx=0.05, rely=0.80)
mic = ctk.CTkLabel(app, text="🎙️", font=("Consolas", 24), text_color="#00FFFF")
mic.place(relx=0.95, rely=0.92)
mic.lower()

# ——— Clock ——————
clock_lbl = ctk.CTkLabel(app, font=("Consolas", 18), text_color="#00FF00")
clock_lbl.place(relx=0.85, rely=0.05)
def update_clock():
    clock_lbl.configure(text=datetime.datetime.now().strftime("%I:%M:%S %p"))
    app.after(1000, update_clock)
update_clock()

# ——— System Info ——————
sys_lbl = ctk.CTkLabel(app, font=("Consolas", 18), text_color="#FF0000")
sys_lbl.place(relx=0.80, rely=0.90)
def update_sys():
    sys_lbl.configure(text=f"CPU: {psutil.cpu_percent()}% | RAM: {int(psutil.virtual_memory().percent)}%")
    app.after(1000, update_sys)
update_sys()

# ——— Arc Reactor (Rotating) ——————
arc_raw = Image.open("arc_reactor.png").resize((200, 112))
arc_label = Label(app, bg="black")
arc_label.place(relx=0.90, rely=0.85)
angle = 0
def rotate_arc():
    global angle
    rotated = arc_raw.rotate(angle)
    img = ImageTk.PhotoImage(rotated)
    arc_label.configure(image=img)
    arc_label.image = img
    angle = (angle + 5) % 360
    app.after(100, rotate_arc)
rotate_arc()

# ——— TTS & Typing ——————
engine = pyttsx3.init()
def type_text(lbl, text):
    def animate():
        lbl.configure(text="")
        for i in range(len(text) + 1):
            lbl.configure(text=text[:i])
            time.sleep(0.02)
        time.sleep(4)
        lbl.configure(text="")
    threading.Thread(target=animate, daemon=True).start()

def speak(txt):
    type_text(jarvis_lbl, f"JARVIS: {txt}")
    engine.say(txt)
    engine.runAndWait()

# ——— Voice Input ——————
def record_audio(duration=4):
    fs = 44100
    rec = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
    sd.wait()
    wav.write("tmp.wav", fs, rec)

def listen():
    mic.lift()
    record_audio()
    mic.lower()
    r = sr.Recognizer()
    with sr.AudioFile("tmp.wav") as src:
        aud = r.record(src)
    try:
        cmd = r.recognize_google(aud).lower()
        type_text(you_lbl, f"YOU: {cmd}")
        return cmd
    except:
        return ""

# ——— Local AI Memory Chat ——————
def chat_memory(prompt):
    memory.append({"role": "user", "content": prompt})
    try:
        res = llm(f"[INST] {prompt} [/INST]", max_tokens=200, stop=["</s>"])
        reply = res['choices'][0]['text'].strip()
        memory.append({"role": "assistant", "content": reply})
        speak(reply)
    except:
        speak("Local GPT error.")

# ——— Utilities ——————
def get_weather(city):
    try:
        d = requests.get(f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric").json()
        speak(f"{city}: {d['main']['temp']}°C, {d['weather'][0]['description']}.")
    except:
        speak("Couldn't fetch weather.")

def play_on_youtube(q):
    speak(f"Playing {q}")
    webbrowser.open(f"https://www.youtube.com/results?search_query={q}")
    time.sleep(3)
    pyautogui.press('tab', presses=3, interval=0.3)
    pyautogui.press('enter')

def take_ss():
    name = f"screenshot_{datetime.datetime.now().strftime('%H%M%S')}.png"
    ImageGrab.grab().save(name)
    speak(f"Screenshot saved as {name}")

def tell_joke():
    jokes = ["Why don’t scientists trust atoms? They make up everything!",
             "Why did the computer join the gym? To get fit-bit!",
             "I told my computer a joke—it laughed in binary."]
    speak(random.choice(jokes))

# ——— Brain ——————
def jarvis_brain():
    speak("Yes sir.")
    cmd = listen()
    if not cmd:
        speak("I didn't catch that.")
        return
    match cmd:
        case _ if "time" in cmd: speak(datetime.datetime.now().strftime("%I:%M %p"))
        case _ if "weather" in cmd: get_weather(cmd.replace("weather", "").strip())
        case _ if cmd.startswith("play"): play_on_youtube(cmd.replace("play", "").strip())
        case _ if "wiki" in cmd: speak(wikipedia.summary(cmd, sentences=2))
        case _ if "chat" in cmd or "ask" in cmd: speak("What would you like to ask?"); chat_memory(listen())
        case _ if "google" in cmd: webbrowser.open("https://google.com"); speak("Opening Google.")
        case _ if "youtube" in cmd: webbrowser.open("https://youtube.com"); speak("Opening YouTube.")
        case _ if "joke" in cmd: tell_joke()
        case _ if "cpu" in cmd: speak(f"CPU usage is {psutil.cpu_percent()} percent.")
        case _ if "battery" in cmd:
            bat = psutil.sensors_battery()
            speak(f"Battery at {bat.percent}%") if bat else speak("No battery info.")
        case _ if "screenshot" in cmd: take_ss()
        case _ if "shutdown" in cmd: os.system("shutdown /s /t 1")
        case _ if "restart" in cmd: os.system("shutdown /r /t 1")
        case _ if cmd.startswith("pause"): pyautogui.press("k"); speak("Paused.")
        case _ if cmd.startswith("resume") or cmd.startswith("play again"): pyautogui.press("k"); speak("Resumed.")
        case _ if "mute" in cmd: pyautogui.press("m"); speak("Muted.")
        case _ if "volume up" in cmd: pyautogui.press("up"); speak("Volume increased.")
        case _ if "volume down" in cmd: pyautogui.press("down"); speak("Volume decreased.")
        case _ if cmd.startswith("exit") or cmd.startswith("close"): speak("Goodbye."); app.destroy()
        case _: speak("Command not recognized.")

# ——— Wake Word Loop ——————
def wait_wake():
    while True:
        if "jarvis" in listen():
            jarvis_brain()

def launch_jarvis():
    try: playsound("jarvis_theme.mp3")
    except: pass
    speak("JARVIS activated.")
    threading.Thread(target=wait_wake, daemon=True).start()

# ——— Start System ——————
threading.Thread(target=launch_jarvis, daemon=True).start()
app.bind("<Escape>", lambda e: app.destroy())
app.mainloop()
