1️⃣ app Module
Purpose
Project entry point.

Responsibilities
Start application
Initialize modules
Load configuration
Launch GUI

Files
main.py

2️⃣ voice Module
Purpose
Handle all voice-related operations.

Responsibilities
Capture voice
Speech Recognition
Text-To-Speech

Files
speech_recognition.py
text_to_speech.py

3️⃣ planner Module ⭐
This is the Heart of NOVA-AI

Responsibilities
Intent Detection
Entity Extraction
Context Management
Task Planning

Files
intent_detector.py
entity_extractor.py
context_manager.py
task_planner.py

Example
User says: Open Chrome

Planner decides:
Intent
↓
Launch App
↓
Entity
↓
Chrome
↓
Plan
↓
Launch Chrome

4️⃣ executor Module
Responsibilities
Actually execute tasks.

Files
app_executor.py
file_executor.py
system_executor.py

Example
Planner says : Launch Chrome

Executor
↓
Launches Chrome.

5️⃣ automation Module
Responsibilities
Communicate with Windows.

Libraries:

yAutoGUI
PyWinAuto
keyboard
mouse
psutil

Files:
pyautogui_controller.py
pywinauto_controller.py

Example:
Mouse Click
Keyboard
Window Control

6️⃣ database Module
Responsibilities:
Store:
Settings, Preferences, History, Recent Commands

Files: sqlite_manager.py

7️⃣ ui Module
Responsibilities
Graphical Interface.

Files:
main_window.py
widgets.py
settings_dialog.py

Later:
Microphone Button
Chat Area
Status
History

Everything here.

8️⃣ tests Module
Responsibilities
Testing every module.

Example:
test_voice.py
test_planner.py
test_executor.py

Later use:
pytest

Module Interaction
This is important.

User
↓
UI
↓
Voice Module
↓
Planner Module
↓
Executor Module
↓
Automation Module
↓
Windows
↓
Response
↓
UI

This shows how modules communicate.

Design Principles
Mention these in the document:

✅ Single Responsibility Principle (SRP)
Each module should perform only one major responsibility.

✅ Loose Coupling
Modules should depend on interfaces rather than implementation.

✅ High Cohesion
Related functionality should remain within the same module.

✅ Modular Architecture
Each module should be independently testable and maintainable.

📁 Final Folder Mapping
NOVA-AI/

app/
│── main.py
voice/
│── speech_recognition.py
│── text_to_speech.py
planner/
│── intent_detector.py
│── entity_extractor.py
│── context_manager.py
│── task_planner.py
executor/
│── app_executor.py
│── file_executor.py
│── system_executor.py
automation/
│── pyautogui_controller.py
│── pywinauto_controller.py
database/
│── sqlite_manager.py
ui/
│── main_window.py
│── widgets.py
│── settings_dialog.py
tests/
│── test_voice.py
│── test_planner.py
│── test_executor.py
config/
│── settings.py
│── constants.py
utils/
│── logger.py
│── helpers.py
│── validators.py