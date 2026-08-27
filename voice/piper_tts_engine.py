"""
voice/piper_tts_engine.py

ASTRA-AI
Offline Piper Neural Text-To-Speech Engine

Features
--------
✓ Fully offline
✓ Female neural voice
✓ ONNX based Piper model
✓ WAV generation
✓ pygame playback
✓ Thread safe
✓ Stop current speech
✓ Explicit success/failure reporting
✓ Compatible with TextToSpeech fallback manager
✓ Uses the same Python interpreter as ASTRA-AI
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

import pygame


class PiperTTSEngine:
    """
    Offline Piper TTS engine.

    This engine uses the same Python interpreter that runs
    ASTRA-AI. This prevents Windows PATH from launching a
    different Python installation where the piper package is
    not installed.

    Default model:

        models/piper/
            en_US-hfc_female-medium.onnx
            en_US-hfc_female-medium.onnx.json
    """

    def __init__(self):

        # --------------------------------------------------
        # Paths
        # --------------------------------------------------

        self.project_root = (
            Path(__file__)
            .resolve()
            .parent
            .parent
        )

        self.model_path = (
            self.project_root
            / "models"
            / "piper"
            / "en_US-hfc_female-medium.onnx"
        )

        self.config_path = (
            self.project_root
            / "models"
            / "piper"
            / "en_US-hfc_female-medium.onnx.json"
        )

        # --------------------------------------------------
        # Piper command
        #
        # IMPORTANT:
        #
        # Do NOT use:
        #
        #     python -m piper
        #
        # because Windows may resolve "python" to a system
        # Python installation instead of ASTRA's virtual
        # environment.
        #
        # sys.executable always points to the Python
        # interpreter currently running ASTRA-AI.
        # --------------------------------------------------

        self.python_executable = sys.executable

        self.piper_command = [
            self.python_executable,
            "-m",
            "piper",
        ]

        # --------------------------------------------------
        # State
        # --------------------------------------------------

        self.lock = threading.RLock()

        self.stop_event = threading.Event()

        self.current_process = None

        self.current_thread = None

        self.is_speaking = False

        self._closed = False

        # --------------------------------------------------
        # Voice configuration
        # --------------------------------------------------

        self.voice = (
            "en_US-hfc_female-medium"
        )

        self.rate = 0

        self.volume = 1.0

        # --------------------------------------------------
        # Process timeout
        # --------------------------------------------------

        self.generation_timeout = 120

        # --------------------------------------------------
        # Validate model
        # --------------------------------------------------

        if not self.model_path.exists():

            print(
                "\nPiper TTS Warning : "
                "Piper ONNX model not found."
            )

            print(
                f"Expected Model : {self.model_path}"
            )

        if not self.config_path.exists():

            print(
                "\nPiper TTS Warning : "
                "Piper model config not found."
            )

            print(
                f"Expected Config : {self.config_path}"
            )

        # --------------------------------------------------
        # Validate Piper installation
        # --------------------------------------------------

        self.piper_available = (
            self._check_piper_available()
        )

        if not self.piper_available:

            print(
                "\nPiper TTS Warning : "
                "Piper Python module is not available."
            )

            print(
                "ASTRA Python Interpreter : "
                f"{self.python_executable}"
            )

            print(
                "Install Piper into the same Python "
                "environment used by ASTRA-AI."
            )

        else:

            print(
                "Piper TTS module detected."
            )

            print(
                "Piper Python Interpreter : "
                f"{self.python_executable}"
            )

        # --------------------------------------------------
        # Pygame mixer
        # --------------------------------------------------

        try:

            if not pygame.mixer.get_init():

                pygame.mixer.init()

        except Exception as error:

            print(
                f"Piper pygame initialization error : {error}"
            )

    # ======================================================
    # Piper Installation Validation
    # ======================================================

    def _check_piper_available(self):
        """
        Check whether the Piper module is installed in the
        same Python environment that is running ASTRA-AI.
        """

        try:

            return (
                importlib.util.find_spec(
                    "piper"
                )
                is not None
            )

        except Exception as error:

            print(
                f"Piper module check error : {error}"
            )

            return False

    # ======================================================
    # Model Validation
    # ======================================================

    def _model_available(self):
        """
        Check whether Piper model and config exist.
        """

        return (

            self.model_path.exists()

            and

            self.config_path.exists()

        )

    # ======================================================
    # Process Creation Flags
    # ======================================================

    @staticmethod
    def _creation_flags():
        """
        Return Windows-safe subprocess creation flags.
        """

        if hasattr(
            subprocess,
            "CREATE_NO_WINDOW"
        ):

            return subprocess.CREATE_NO_WINDOW

        return 0

    # ======================================================
    # Generate WAV
    # ======================================================

    def _generate_audio(
        self,
        text,
        output_file
    ):
        """
        Generate WAV audio using Piper CLI.

        Returns
        -------
        bool
            True when generation succeeds.
        """

        if self._closed:

            return False

        if not self._model_available():

            print(
                "Piper TTS Error : "
                "Model files are missing."
            )

            return False

        if not self.piper_available:

            print(
                "Piper TTS Error : "
                "Piper is not installed in the active "
                "ASTRA Python environment."
            )

            print(
                "Active Python : "
                f"{self.python_executable}"
            )

            return False

        if not text:

            return False

        if self.stop_event.is_set():

            return False

        process = None

        try:

            command = [

                *self.piper_command,

                "--model",
                str(self.model_path),

                "--config",
                str(self.config_path),

                "--output-file",
                str(output_file),

            ]

            print(
                "Generating Piper speech..."
            )

            # --------------------------------------------------
            # Piper reads text from stdin.
            # --------------------------------------------------

            process = subprocess.Popen(

                command,

                stdin=subprocess.PIPE,

                stdout=subprocess.PIPE,

                stderr=subprocess.PIPE,

                text=True,

                encoding="utf-8",

                errors="replace",

                creationflags=(
                    self._creation_flags()
                ),

            )

            self.current_process = process

            try:

                stdout, stderr = process.communicate(

                    input=str(text),

                    timeout=self.generation_timeout,

                )

            except subprocess.TimeoutExpired:

                print(
                    "Piper TTS Error : "
                    "Audio generation timed out."
                )

                try:

                    process.kill()

                except Exception:

                    pass

                try:

                    stdout, stderr = process.communicate(
                        timeout=5
                    )

                except Exception:

                    pass

                return False

            except Exception as error:

                print(
                    f"Piper process communication error : {error}"
                )

                try:

                    if process.poll() is None:

                        process.kill()

                except Exception:

                    pass

                return False

            finally:

                if self.current_process is process:

                    self.current_process = None

            # --------------------------------------------------
            # Stop requested
            # --------------------------------------------------

            if self.stop_event.is_set():

                return False

            # --------------------------------------------------
            # Piper process failure
            # --------------------------------------------------

            if process.returncode != 0:

                print(
                    "\nPiper TTS Generate Error"
                )

                print(
                    "Python Interpreter Used : "
                    f"{self.python_executable}"
                )

                if stderr:

                    print(
                        stderr.strip()
                    )

                return False

            # --------------------------------------------------
            # Validate WAV
            # --------------------------------------------------

            if not os.path.exists(
                output_file
            ):

                print(
                    "Piper TTS Error : "
                    "Output WAV was not created."
                )

                return False

            if os.path.getsize(
                output_file
            ) <= 44:

                print(
                    "Piper TTS Error : "
                    "Generated WAV is empty."
                )

                return False

            return True

        except FileNotFoundError as error:

            print(
                "Piper TTS Error : "
                "Python executable was not found."
            )

            print(
                f"Expected Python : {self.python_executable}"
            )

            print(
                f"Details : {error}"
            )

            return False

        except Exception as error:

            print(
                f"Piper TTS Generate Error : {error}"
            )

            return False

        finally:

            if self.current_process is process:

                self.current_process = None

    # ======================================================
    # Blocking Speak
    # ======================================================

    def speak_blocking(
        self,
        text
    ):
        """
        Generate and play Piper speech synchronously.

        Returns
        -------
        bool
            True  -> Piper speech completed.
            False -> Piper failed.
        """

        if self._closed:

            return False

        if not text:

            return False

        text = str(text).strip()

        if not text:

            return False

        output_file = None

        self.stop_event.clear()

        self.is_speaking = True

        try:

            # --------------------------------------------------
            # Temporary WAV file
            # --------------------------------------------------

            temp = tempfile.NamedTemporaryFile(

                delete=False,

                suffix=".wav",

            )

            output_file = temp.name

            temp.close()

            # --------------------------------------------------
            # Generate Piper audio
            # --------------------------------------------------

            generated = self._generate_audio(

                text,

                output_file,

            )

            if not generated:

                return False

            # --------------------------------------------------
            # Stop requested
            # --------------------------------------------------

            if self.stop_event.is_set():

                return False

            # --------------------------------------------------
            # Playback
            # --------------------------------------------------

            try:

                pygame.mixer.music.load(
                    output_file
                )

                pygame.mixer.music.set_volume(
                    self.volume
                )

                pygame.mixer.music.play()

            except Exception as error:

                print(
                    f"Piper TTS Playback Error : {error}"
                )

                return False

            # --------------------------------------------------
            # Wait for playback
            # --------------------------------------------------

            while (

                pygame.mixer.music.get_busy()

                and

                not self.stop_event.is_set()

            ):

                pygame.time.wait(10)

            if self.stop_event.is_set():

                return False

            return True

        except Exception as error:

            print(
                f"Piper TTS Error : {error}"
            )

            return False

        finally:

            # --------------------------------------------------
            # Stop playback
            # --------------------------------------------------

            try:

                pygame.mixer.music.stop()

            except Exception:

                pass

            try:

                pygame.mixer.music.unload()

            except Exception:

                pass

            # --------------------------------------------------
            # Remove temporary WAV
            # --------------------------------------------------

            if output_file:

                try:

                    if os.path.exists(
                        output_file
                    ):

                        os.remove(
                            output_file
                        )

                except Exception:

                    pass

            self.is_speaking = False

    # ======================================================
    # Non-Blocking Speak
    # ======================================================

    def speak(
        self,
        text
    ):
        """
        Non-blocking public speak method.
        """

        if self._closed:

            return None

        if not text:

            return None

        text = str(text).strip()

        if not text:

            return None

        with self.lock:

            self.stop()

            self.stop_event.clear()

            self.current_thread = threading.Thread(

                target=self.speak_blocking,

                args=(text,),

                daemon=True,

                name="ASTRA-Piper-TTS",

            )

            self.current_thread.start()

            return self.current_thread

    # ======================================================
    # Stop
    # ======================================================

    def stop(self):
        """
        Stop Piper generation/playback.
        """

        self.stop_event.set()

        # --------------------------------------------------
        # Stop Piper subprocess
        # --------------------------------------------------

        process = self.current_process

        if process is not None:

            try:

                if process.poll() is None:

                    process.terminate()

                    try:

                        process.wait(
                            timeout=2
                        )

                    except subprocess.TimeoutExpired:

                        process.kill()

            except Exception:

                try:

                    process.kill()

                except Exception:

                    pass

            finally:

                if self.current_process is process:

                    self.current_process = None

        # --------------------------------------------------
        # Stop pygame playback
        # --------------------------------------------------

        try:

            pygame.mixer.music.stop()

        except Exception:

            pass

        self.is_speaking = False

    # ======================================================
    # Voice
    # ======================================================

    def set_voice(
        self,
        voice
    ):
        """
        Set voice identifier.

        Piper model is fixed to the bundled
        female neural voice for ASTRA V1.
        """

        if voice:

            self.voice = str(
                voice
            )

    # ======================================================
    # Rate
    # ======================================================

    def set_rate(
        self,
        rate
    ):
        """
        Store rate for API compatibility.

        Piper CLI uses length-scale rather than
        a conventional speech rate.
        """

        try:

            self.rate = float(
                rate
            )

        except (
            TypeError,
            ValueError,
        ):

            self.rate = 0

    # ======================================================
    # Volume
    # ======================================================

    def set_volume(
        self,
        volume
    ):
        """
        Set Piper playback volume.
        """

        try:

            value = float(
                volume
            )

            self.volume = max(
                0.0,
                min(
                    value,
                    1.0
                )
            )

            try:

                if pygame.mixer.get_init():

                    pygame.mixer.music.set_volume(
                        self.volume
                    )

            except Exception:

                pass

        except (
            TypeError,
            ValueError,
        ):

            self.volume = 1.0

    # ======================================================
    # Speaking Status
    # ======================================================

    def speaking(self):

        return self.is_speaking

    # ======================================================
    # Cleanup
    # ======================================================

    def close(self):

        if self._closed:

            return

        self._closed = True

        self.stop()

        thread = self.current_thread

        if (

            thread

            and
            thread.is_alive()

            and
            thread is not threading.current_thread()

        ):

            try:

                thread.join(
                    timeout=2
                )

            except Exception:

                pass

        self.current_thread = None

        print(
            "Piper TTS Engine shutdown completed."
        )