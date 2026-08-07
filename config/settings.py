"""
Application settings for ASTRA-AI.
"""

import os

from dotenv import load_dotenv

# ==========================================================
# Load Environment Variables
# ==========================================================

load_dotenv()

# ==========================================================
# Application Information
# ==========================================================

APP_NAME = "ASTRA-AI"
APP_VERSION = "0.1.0"
APP_AUTHOR = "Naresh"

# ==========================================================
# Window Settings
# ==========================================================

WINDOW_WIDTH = 700
WINDOW_HEIGHT = 500
WINDOW_TITLE = APP_NAME

# ==========================================================
# UI Settings
# ==========================================================

DEFAULT_STATUS = "Ready"
WELCOME_MESSAGE = "Welcome to ASTRA-AI"

# ==========================================================
# File Indexing Settings
# ==========================================================

INDEX_USER_FOLDERS = [

    "Desktop",

    "Documents",

    "Downloads",

    "Pictures",

    "Videos",

    "Music"

]

# ==========================================================
# Custom folders outside user profile
# ==========================================================

# Example:
#
# r"E:\College"
# r"E:\Projects"
# r"E:\TANCET"

INDEX_CUSTOM_FOLDERS = [

]

# ==========================================================
# Microphone
# ==========================================================

MIC_BUTTON_TEXT = "🎤"

# ==========================================================
# Gemini API
# ==========================================================

GEMINI_API_KEY_1 = os.getenv(
    "GEMINI_API_KEY_1",
    ""
).strip()

GEMINI_API_KEY_2 = os.getenv(
    "GEMINI_API_KEY_2",
    ""
).strip()

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "models/gemini-3.5-flash"
).strip()

# ==========================================================
# Debug
# ==========================================================

DEBUG = os.getenv(
    "DEBUG",
    "False"
).lower() == "true"