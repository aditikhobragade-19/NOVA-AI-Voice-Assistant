NOVA – AI-Powered Voice Assistant

NOVA is an intelligent desktop-based AI Voice Assistant developed using Python and the Groq API. It provides an interactive interface that allows users to communicate with AI through text and voice commands.

Overview

NOVA is designed to simplify everyday tasks and provide AI-powered assistance through a user-friendly desktop application. It combines natural language processing, speech recognition, and text-to-speech functionality in one application.

Key Features

- AI-Powered Conversations: Generates intelligent responses using the Groq API.
- Voice Interaction: Supports voice input through speech recognition.
- Text-to-Speech: Converts responses into spoken output.
- Multilingual Support: Includes English and Hindi language options.
- Quick Access Shortcuts: Provides shortcuts to Google, YouTube, GitHub, Notepad, and Calculator.
- Desktop Interface: Built with a modern dark-themed graphical interface.

Technology Stack

Technology| Purpose
Python| Core programming language
CustomTkinter| Desktop GUI
Groq API| AI-powered responses
SpeechRecognition| Voice input
pyttsx3| Text-to-speech

Project Structure

NOVA/
├── main.py
├── requirements.txt
├── README.md
└── .gitignore

Installation & Setup

1. Clone the repository

git clone https://github.com/YOUR-USERNAME/NOVA-AI-Voice-Assistant.git

2. Navigate to the project directory

cd NOVA-AI-Voice-Assistant

3. Install dependencies

pip install -r requirements.txt

4. Configure your Groq API key

Set your API key as an environment variable in PowerShell:

$env:GROQ_API_KEY="YOUR_API_KEY"

5. Run the application

python main.py

Security

The Groq API key is accessed through an environment variable. Do not share or upload private API keys, passwords, or other sensitive credentials.

Future Enhancements

- Improved voice recognition
- Additional language support
- More desktop automation features
- Enhanced conversational capabilities

Author

Aditi Khobragade

Python | AI | Application Development

---

Developed as a Python-based AI Voice Assistant project.
