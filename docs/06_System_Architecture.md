                        USER
                          │
                          ▼
                  🎤 Voice Input
                          │
                          ▼
              Speech Recognition
                          │
                          ▼
         Natural Language Understanding
                          │
          ┌───────────────┴───────────────┐
          ▼                               ▼
   Intent Detection              Entity Extraction
          │                               │
          └───────────────┬───────────────┘
                          ▼
                  Context Manager
                          │
                          ▼
                    Task Planner
                          │
                          ▼
                   Task Executor
          ┌─────────┼──────────┬─────────┐
          ▼         ▼          ▼         ▼
    App Control  File Ops  System Ctrl  Automation
          │         │          │         │
          └─────────┴──────────┴─────────┘
                          │
                          ▼
                      Windows OS
                          │
                          ▼
                 Text-To-Speech Response

Idhu namma Level-1 Architecture.

Module Explanation
1️⃣ Voice Input

Responsibility
Receive user voice.

Library: SpeechRecognition

2️⃣ Speech Recognition
Convert

Voice
↓
Text

3️⃣ Natural Language Understanding (NLU)
Example
User: Open Chrome
System understands: Meaning

4️⃣ Intent Detection
Find: User wants what?
Example: Launch Application

5️⃣ Entity Extraction
Extract

Chrome
Notepad
Documents
Downloads
File Name


6️⃣ Context Manager
Remember previous conversation.

Example
Open Chrome
↓
Close it
↓
"It"
↓
Chrome

7️⃣ Task Planner

This is our research heart ❤️
Example

User: Open my NOVA project

Planner

Step 1
Open VS Code
↓
Step 2
Open Project
↓
Step 3
Open Terminal
↓
Done

Planner decides sequence.

8️⃣ Task Executor
Planner decides.
Executor executes.

9️⃣ Desktop Automation

Libraries:
1. PyAutoGUI
2. PyWinAuto
3. keyboard
4. mouse
5. psutil

Actual mouse click.
Keyboard typing.
Application opening.
Everything here.

🔟 Database
SQLite

Stores:
Settings
History
Preferences
Recent Commands

1️⃣1️⃣ GUI
PySide6

Shows:
Main Window
Microphone
History
Settings


Folder Mapping
This is very important.

app/
│
├── main.py
voice/
│
├── speech_recognition.py
├── text_to_speech.py
planner/
│
├── intent_detector.py
├── entity_extractor.py
├── context_manager.py
├── task_planner.py
executor/
│
├── app_executor.py
├── file_executor.py
├── system_executor.py
automation/
│
├── pyautogui_controller.py
├── pywinauto_controller.py
database/
│
├── sqlite_manager.py
ui/
│
├── main_window.py


See?
Every folder has ONE responsibility.
This follows the Single Responsibility Principle (SRP).