"""
MicrophonePTTModule
==================

This module provides push-to-talk capabilities to the classic retico MicrophoneModule
which captures audio signal from the microphone and chunks the audio signal into AudioIUs.
"""

import queue
import sys
import keyboard as keyb
import librosa
from pynput import keyboard
import pyaudio
import os

import retico_core
from retico_core.audio import MicrophoneModule


class PTTMicrophoneModule(MicrophoneModule):
    """A modules overrides the MicrophoneModule which captures audio signal from the microphone and chunks the audio signal into AudioIUs.
    The addition of this module is the introduction of the push-to-talk capacity : the microphone's audio signal is captured only while the M key is pressed.
    """

    @staticmethod
    def name():
        return "PttMicrophone Module"

    @staticmethod
    def description():
        return "A producing module that produce audio from wave file when M key is pressed."

    def __init__(
        self,
        key: str = "m",
        hotkey_library: str = "pynput",
        **kwargs,
    ):
        """
        Initialize the Push-To-Talk Microphone Module.

        Args:
            key (string): Key used for Push-To-Talk.
            hotkey_library (str): The hotkey library to use (keyboard or pynput)
        """
        super().__init__(**kwargs)

        # Check OS to set rate
        computer_os = sys.platform
        self.terminal_logger.debug(f"OS : {computer_os}", cl="trace")
        if sys.platform.startswith("linux"):
            self.terminal_logger.debug(f"OS is LINUX, forcing to use 48k audio rate", cl="trace")
            self.rate = 48000

        self._run_thread_active = False
        self.args = None
        self.list_ius = []
        self.silence_ius = []
        self.cpt = 0
        self.play_audio = False
        self.hotkey_library = hotkey_library
        self.key = key

    def setup(self, **kwargs):
        super().setup(**kwargs)
        # init "m" key listener
        if self.hotkey_library == "pynput":
            self.m_listener = keyboard.Listener(on_press=self.on_press)
            self.m_listener.start()

    def on_press(self, key):
        try:
            if key.char == self.key:
                self.play_audio = True
        except AttributeError:
            pass

    def callback(self, in_data, frame_count, time_info, status):
        """The callback function that gets called by pyaudio.

        Args:
            in_data (bytes[]): The raw audio that is coming in from the
                microphone
            frame_count (int): The number of frames that are stored in in_data
        """
        if self.hotkey_library == "keyboard" and keyb.is_pressed(self.key):
            self.play_audio = True
        if self.play_audio is True:
            self.audio_buffer.put(in_data)
            self.play_audio = False
        else:
            self.audio_buffer.put(b"\x00" * self.sample_width * self.chunk_size)
        return (in_data, pyaudio.paContinue)

    def process_update(self, _):
        """
        Returns:
            UpdateMessage: list of AudioIUs produced from the microphone's audio signal.
        """
        if not self.audio_buffer:
            return None
        try:
            sample = self.audio_buffer.get(timeout=1.0)
        except queue.Empty:
            return None
        output_iu = self.create_iu(
            raw_audio=sample,
            nframes=self.chunk_size,
            rate=self.rate,
            sample_width=self.sample_width,
        )
        return retico_core.UpdateMessage.from_iu(output_iu, retico_core.UpdateType.ADD)
