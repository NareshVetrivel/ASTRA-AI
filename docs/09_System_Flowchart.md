Main Flowchart
+----------------------+
|     Start System     |
+----------------------+
           |
           v
+----------------------+
| Initialize Modules   |
+----------------------+
           |
           v
+----------------------+
| Wait for Voice Input |
+----------------------+
           |
           v
+----------------------+
| Capture Voice        |
+----------------------+
           |
           v
+----------------------+
| Speech to Text       |
+----------------------+
           |
           v
+----------------------+
| Detect Intent        |
+----------------------+
           |
           v
+----------------------+
| Extract Entities     |
+----------------------+
           |
           v
+----------------------+
| Check Context        |
+----------------------+
           |
           v
+----------------------+
| Plan Task            |
+----------------------+
           |
           v
+----------------------+
| Execute Task         |
+----------------------+
           |
           v
+----------------------+
| Generate Response    |
+----------------------+
           |
           v
+----------------------+
| Text to Speech       |
+----------------------+
           |
           v
+----------------------+
| Wait Next Command    |
+----------------------+

Decision Flow
Add one decision block.

User Command
↓
Intent Detected?
↓
Yes ----------------→ Execute
↓
No
↓
Show Error Message
↓
Wait Again


Error Flow
Voice Received
↓
Speech Failed?
↓
Yes
↓
Ask User To Repeat
↓
Listen Again


Application Flow
Example:
Open Chrome
↓
Intent
↓
Launch Application
↓
Entity
↓
Chrome
↓
Planner
↓
Executor
↓
PyWinAuto
↓
Chrome Opens
↓
Voice Response
↓
Completed


Multi-Step Flow
This is one of the research highlights.

Example:
Open my NOVA project
↓
Intent
↓
Planner
↓
Step 1
Open VS Code
↓
Step 2
Open Project Folder
↓
Step 3
Open Terminal
↓
Step 4
Activate Environment
↓
Completed

Mention that Task Planner converts a single natural language command into multiple executable steps.

Context Flow
Example:
User
↓
Open Chrome
↓
Chrome Opened
↓
Context Updated
↓
User
↓
Close It
↓
Context Manager
↓
"It"
↓
Chrome
↓
Executor
↓
Chrome Closed

This demonstrates context awareness, which is one of the key research contributions.

Software Engineering Notes
At the end of the document, mention:

The system follows a modular execution pipeline where each module performs a dedicated responsibility. This approach improves maintainability, scalability, debugging, and independent testing of each component.