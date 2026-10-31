import os
import ast
import operator
import threading
import datetime
import webbrowser
import subprocess
import customtkinter as ctk

try:
    from groq import Groq
except ImportError:
    Groq = None

try:
    import speech_recognition as sr
except ImportError:
    sr = None

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None


MODEL_NAME = "openai/gpt-oss-120b"

BG = "#050B19"
PANEL = "#08152B"
PANEL_LIGHT = "#0D2040"
BORDER = "#1C3766"
TEXT = "#F2F5FF"
MUTED = "#A9BCEB"
PURPLE = "#7657FF"
BLUE = "#168BFF"
CYAN = "#39D7FF"
GREEN = "#13D6A0"

OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def safe_calculate(expression):
    tree = ast.parse(expression, mode="eval")

    def evaluate(node):
        if isinstance(node, ast.Expression):
            return evaluate(node.body)

        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return node.value

        if isinstance(node, ast.BinOp) and type(node.op) in OPS:
            left = evaluate(node.left)
            right = evaluate(node.right)

            if isinstance(node.op, ast.Pow) and abs(right) > 10:
                raise ValueError("Power too large")

            return OPS[type(node.op)](left, right)

        if isinstance(node, ast.UnaryOp) and type(node.op) in OPS:
            return OPS[type(node.op)](evaluate(node.operand))

        raise ValueError("Unsupported calculation")

    return evaluate(tree)


class NovaAssistant(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("NOVA AI Assistant")
        self.geometry("1250x800")
        self.minsize(900, 620)
        self.configure(fg_color=BG)

        self.notes = []
        self.language = "English"
        self.busy = False
        self.tts_lock = threading.Lock()
        self.chat_history = []
        self.client = None

        api_key = os.getenv("GROQ_API_KEY")

        if Groq and api_key:
            try:
                self.client = Groq(
                    api_key=api_key,
                    timeout=45.0,
                    max_retries=1
                )
            except Exception as exc:
                print("Groq setup error:", repr(exc))

        self.voice_engine = None

        if pyttsx3:
            try:
                self.voice_engine = pyttsx3.init()
                self.voice_engine.setProperty("rate", 175)
            except Exception as exc:
                print("Voice setup error:", repr(exc))

        self.grid_columnconfigure(0, weight=0, minsize=205)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0, minsize=235)
        self.grid_rowconfigure(0, weight=1)

        self.build_sidebar()
        self.build_main_area()
        self.build_right_panel()

        self.add_message(
            "NOVA",
            "Hello! I'm NOVA, your AI assistant.\n"
            "Ask me anything, or press Speak to talk to me."
        )

        if not api_key:
            self.add_message(
                "NOVA",
                "GROQ_API_KEY is not set. Set it in your terminal, "
                "then close and reopen NOVA."
            )
        elif not Groq:
            self.add_message(
                "NOVA",
                "Groq package is missing. Install it using: "
                "python -m pip install groq"
            )

        self.protocol("WM_DELETE_WINDOW", self.close_app)

    def build_sidebar(self):
        self.sidebar = ctk.CTkFrame(
            self,
            fg_color="#061020",
            corner_radius=0,
            border_width=1,
            border_color=BORDER
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_columnconfigure(0, weight=1)

        logo = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo.grid(row=0, column=0, padx=18, pady=(25, 25), sticky="ew")

        ctk.CTkLabel(
            logo,
            text="✦ NOVA",
            font=ctk.CTkFont(size=29, weight="bold"),
            text_color="#9B8BFF"
        ).pack(anchor="w")

        ctk.CTkLabel(
            logo,
            text="PERSONAL AI ASSISTANT",
            font=ctk.CTkFont(size=10),
            text_color=MUTED
        ).pack(anchor="w", pady=(4, 0))

        ctk.CTkButton(
            self.sidebar,
            text="＋  New Chat",
            height=42,
            corner_radius=10,
            fg_color=PURPLE,
            hover_color="#6042E0",
            command=self.clear_chat
        ).grid(row=1, column=0, padx=15, pady=5, sticky="ew")

        ctk.CTkLabel(
            self.sidebar,
            text="QUICK ACTIONS",
            text_color=MUTED,
            font=ctk.CTkFont(size=11, weight="bold")
        ).grid(row=2, column=0, padx=20, pady=(28, 10), sticky="w")

        actions = [
            ("🌐  Open Google", "google"),
            ("▶  Open YouTube", "youtube"),
            ("⌘  Open GitHub", "github"),
            ("📝  Open Notepad", "notepad"),
            ("🧮  Calculator", "calculator")
        ]

        for row, (label, action) in enumerate(actions, start=3):
            ctk.CTkButton(
                self.sidebar,
                text=label,
                anchor="w",
                height=38,
                fg_color="transparent",
                hover_color=PANEL_LIGHT,
                text_color=TEXT,
                command=lambda a=action: self.quick_action(a)
            ).grid(row=row, column=0, padx=10, pady=3, sticky="ew")

        ctk.CTkLabel(
            self.sidebar,
            text="●  Assistant Ready",
            text_color=GREEN,
            font=ctk.CTkFont(size=12)
        ).grid(row=10, column=0, padx=15, pady=20, sticky="s")

    def build_main_area(self):
        self.main = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        self.main.grid(row=0, column=1, padx=18, pady=18, sticky="nsew")
        self.main.grid_columnconfigure(0, weight=1)
        self.main.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self.main, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 15))

        ctk.CTkLabel(
            header,
            text="NOVA AI",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=TEXT
        ).pack(side="left")

        ctk.CTkLabel(
            header,
            text="  •  Your intelligent companion",
            font=ctk.CTkFont(size=12),
            text_color=MUTED
        ).pack(side="left", pady=(6, 0))

        self.chat_box = ctk.CTkTextbox(
            self.main,
            fg_color=PANEL,
            text_color=TEXT,
            corner_radius=14,
            border_width=1,
            border_color=BORDER,
            font=ctk.CTkFont(size=14),
            wrap="word"
        )
        self.chat_box.grid(row=1, column=0, sticky="nsew")
        self.chat_box.configure(state="disabled")
        self.chat_box.tag_config("nova", foreground="#A99AFF")
        self.chat_box.tag_config("you", foreground=CYAN)

        composer = ctk.CTkFrame(
            self.main,
            fg_color=PANEL,
            corner_radius=14,
            border_width=1,
            border_color=BORDER
        )
        composer.grid(row=2, column=0, sticky="ew", pady=(15, 0))
        composer.grid_columnconfigure(0, weight=1)

        self.input_box = ctk.CTkEntry(
            composer,
            placeholder_text="Message NOVA...",
            height=46,
            corner_radius=10,
            fg_color=PANEL_LIGHT,
            border_color=BORDER,
            text_color=TEXT,
            font=ctk.CTkFont(size=14)
        )
        self.input_box.grid(
            row=0, column=0, padx=(10, 5), pady=10, sticky="ew"
        )
        self.input_box.bind("<Return>", self.on_enter)

        ctk.CTkButton(
            composer,
            text="🎙 Speak",
            width=85,
            height=44,
            fg_color=BLUE,
            hover_color="#0871D4",
            command=self.listen
        ).grid(row=0, column=1, padx=5, pady=10)

        ctk.CTkButton(
            composer,
            text="Send ➤",
            width=95,
            height=44,
            fg_color=PURPLE,
            hover_color="#6042E0",
            command=self.send_message
        ).grid(row=0, column=2, padx=(5, 10), pady=10)

        ctk.CTkButton(
            self.main,
            text="■ Stop Voice",
            height=32,
            width=110,
            fg_color="#452538",
            hover_color="#63334B",
            command=self.stop_voice
        ).grid(row=3, column=0, pady=(8, 0), sticky="e")

    def build_right_panel(self):
        self.right = ctk.CTkFrame(
            self,
            fg_color="#061020",
            corner_radius=0,
            border_width=1,
            border_color=BORDER
        )
        self.right.grid(row=0, column=2, sticky="nsew")
        self.right.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self.right,
            text="QUICK ACCESS",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color=TEXT
        ).grid(row=0, column=0, padx=16, pady=(28, 5), sticky="w")

        ctk.CTkLabel(
            self.right,
            text="Tools at your fingertips",
            font=ctk.CTkFont(size=11),
            text_color=MUTED
        ).grid(row=1, column=0, padx=16, pady=(0, 20), sticky="w")

        cards = [
            ("✦  AI Assistant", "Ask questions and get AI answers."),
            ("🎙  Voice Input", "Talk to NOVA using your microphone."),
            ("🔊  Voice Output", "Listen to NOVA's responses."),
            ("⚡  Quick Commands", "Open websites and use tools.")
        ]

        for row, (title, description) in enumerate(cards, start=2):
            card = ctk.CTkFrame(
                self.right,
                fg_color=PANEL,
                corner_radius=12,
                border_width=1,
                border_color=BORDER
            )
            card.grid(row=row, column=0, padx=12, pady=6, sticky="ew")

            ctk.CTkLabel(
                card,
                text=title,
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color="#A99AFF"
            ).pack(anchor="w", padx=12, pady=(12, 5))

            ctk.CTkLabel(
                card,
                text=description,
                font=ctk.CTkFont(size=11),
                text_color=MUTED,
                wraplength=185,
                justify="left"
            ).pack(anchor="w", padx=12, pady=(0, 12))

        ctk.CTkLabel(
            self.right,
            text="Language",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=TEXT
        ).grid(row=7, column=0, padx=15, pady=(25, 8), sticky="w")

        self.language_menu = ctk.CTkOptionMenu(
            self.right,
            values=["English", "Hindi"],
            fg_color=PANEL_LIGHT,
            button_color=PURPLE,
            button_hover_color="#6042E0",
            command=self.change_language
        )
        self.language_menu.set("English")
        self.language_menu.grid(row=8, column=0, padx=15, sticky="ew")

    def add_message(self, sender, message):
        self.chat_box.configure(state="normal")
        tag = "you" if sender == "You" else "nova"
        self.chat_box.insert("end", f"{sender}\n", tag)
        self.chat_box.insert("end", f"{message}\n\n")
        self.chat_box.configure(state="disabled")
        self.chat_box.see("end")

    def safe_add_message(self, sender, message):
        self.after(0, lambda: self.add_message(sender, message))

    def clear_chat(self):
        if self.busy:
            self.add_message(
                "NOVA",
                "Please wait for the current answer to finish."
            )
            return

        self.chat_box.configure(state="normal")
        self.chat_box.delete("1.0", "end")
        self.chat_box.configure(state="disabled")
        self.chat_history = []
        self.add_message("NOVA", "New chat started. How can I help you?")

    def on_enter(self, event):
        self.send_message()
        return "break"

    def send_message(self):
        message = self.input_box.get().strip()

        if not message or self.busy:
            return

        self.input_box.delete(0, "end")
        self.add_message("You", message)

        local_answer = self.handle_command(message)

        if local_answer is not None:
            self.add_message("NOVA", local_answer)
            return

        if not self.client:
            self.add_message(
                "NOVA",
                "Groq AI is not configured. Set GROQ_API_KEY in this "
                "terminal, then close and reopen NOVA."
            )
            return

        self.busy = True
        self.add_message("NOVA", "Thinking...")

        threading.Thread(
            target=self.ask_ai,
            args=(message,),
            daemon=True
        ).start()

    def ask_ai(self, message):
        try:
            messages = [
                {
                    "role": "system",
                    "content": (
                        f"You are NOVA, a helpful desktop AI assistant. "
                        f"Reply in {self.language}. Be clear and friendly."
                    )
                }
            ]

            messages.extend(self.chat_history[-10:])
            messages.append({"role": "user", "content": message})

            # Keep this request simple while diagnosing API errors.
            response = self.client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                max_completion_tokens=1200
            )

            answer = (
                response.choices[0].message.content
                or "I couldn't generate a response."
            )

            self.chat_history.extend([
                {"role": "user", "content": message},
                {"role": "assistant", "content": answer}
            ])

            self.after(
                0,
                lambda result=answer: self.finish_answer(result)
            )

        except Exception as exc:
            error_text = f"{type(exc).__name__}: {exc}"

            print("\n========== NOVA AI ERROR ==========")
            print("FULL ERROR:", repr(exc))
            print("ERROR BODY:", repr(getattr(exc, "body", None)))

            response_obj = getattr(exc, "response", None)
            if response_obj is not None:
                try:
                    print("SERVER RESPONSE:", response_obj.text)
                except Exception:
                    pass

            print("===================================\n")

            self.after(
                0,
                lambda error=error_text: self.finish_answer(
                    "AI request failed: " + error
                )
            )

    def finish_answer(self, answer):
        self.busy = False

        self.chat_box.configure(state="normal")
        content = self.chat_box.get("1.0", "end")
        marker = "NOVA\nThinking...\n\n"
        start = content.rfind(marker)

        if start >= 0:
            self.chat_box.delete(
                f"1.0+{start}c",
                f"1.0+{start + len(marker)}c"
            )

        self.chat_box.configure(state="disabled")
        self.add_message("NOVA", answer)

        if not answer.startswith("AI request failed") and self.voice_engine:
            self.speak_answer(answer)

    def handle_command(self, message):
        text = message.lower().strip()

        if text in ("time", "what time is it", "current time"):
            return "Current time: " + datetime.datetime.now().strftime(
                "%I:%M %p"
            )

        if text in (
            "date",
            "today's date",
            "what is the date",
            "today date"
        ):
            return "Today's date: " + datetime.datetime.now().strftime(
                "%d %B %Y"
            )

        if text.startswith("open google"):
            webbrowser.open("https://www.google.com")
            return "Opening Google."

        if text.startswith("open youtube"):
            webbrowser.open("https://www.youtube.com")
            return "Opening YouTube."

        if text.startswith("open github"):
            webbrowser.open("https://github.com")
            return "Opening GitHub."

        if text.startswith("calculate "):
            try:
                expression = message[9:].strip()
                return f"Result: {safe_calculate(expression)}"
            except Exception:
                return (
                    "I couldn't calculate that expression. "
                    "Try: calculate 12 * (5 + 2)"
                )

        if text.startswith("save note "):
            note = message[10:].strip()

            if note:
                self.notes.append(note)
                return "Your note has been saved in this session."

            return "Please write the note after 'save note'."

        if text in ("show notes", "my notes"):
            if not self.notes:
                return "You haven't saved any notes in this session."

            return "Your notes:\n" + "\n".join(
                f"{i + 1}. {note}"
                for i, note in enumerate(self.notes)
            )

        return None

    def quick_action(self, action):
        urls = {
            "google": "https://www.google.com",
            "youtube": "https://www.youtube.com",
            "github": "https://github.com"
        }

        if action in urls:
            webbrowser.open(urls[action])
            self.add_message("NOVA", f"Opening {action.title()}.")

        elif action == "notepad":
            try:
                subprocess.Popen(["notepad.exe"])
            except Exception as exc:
                self.add_message(
                    "NOVA",
                    "Could not open Notepad: " + str(exc)
                )

        elif action == "calculator":
            try:
                subprocess.Popen(["calc.exe"])
            except Exception as exc:
                self.add_message(
                    "NOVA",
                    "Could not open Calculator: " + str(exc)
                )

    def listen(self):
        if not sr:
            self.add_message(
                "NOVA",
                "SpeechRecognition is missing. Run: "
                "python -m pip install SpeechRecognition"
            )
            return

        if self.busy:
            self.add_message(
                "NOVA",
                "Please wait for the current answer."
            )
            return

        self.add_message("NOVA", "Listening... Please speak now.")

        threading.Thread(
            target=self.listen_worker,
            daemon=True
        ).start()

    def listen_worker(self):
        try:
            recognizer = sr.Recognizer()

            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(
                    source,
                    duration=0.5
                )
                audio = recognizer.listen(
                    source,
                    timeout=5,
                    phrase_time_limit=12
                )

            try:
                language_code = (
                    "hi-IN" if self.language == "Hindi" else "en-IN"
                )
                recognized_text = recognizer.recognize_google(
                    audio,
                    language=language_code
                )

            except sr.UnknownValueError:
                self.safe_add_message(
                    "NOVA",
                    "Sorry, I couldn't understand that."
                )
                return

            except sr.RequestError:
                self.safe_add_message(
                    "NOVA",
                    "Speech recognition needs an internet connection."
                )
                return

            self.after(
                0,
                lambda text=recognized_text: self.put_voice_text(text)
            )

        except Exception as exc:
            self.safe_add_message(
                "NOVA",
                "Microphone error: " + str(exc)
            )

    def put_voice_text(self, text):
        self.input_box.delete(0, "end")
        self.input_box.insert(0, text)
        self.send_message()

    def speak_answer(self, text):
        if self.voice_engine:
            threading.Thread(
                target=self.speak_worker,
                args=(text,),
                daemon=True
            ).start()

    def speak_worker(self, text):
        with self.tts_lock:
            try:
                self.voice_engine.say(text)
                self.voice_engine.runAndWait()
            except Exception as exc:
                print("Voice output error:", repr(exc))

    def stop_voice(self):
        try:
            if self.voice_engine:
                self.voice_engine.stop()
        except Exception:
            pass

    def change_language(self, choice):
        self.language = choice
        self.add_message("NOVA", f"Language changed to {choice}.")

    def close_app(self):
        self.stop_voice()
        self.destroy()


if __name__ == "__main__":
    app = NovaAssistant()
    app.mainloop()