# coding: UTF-8
import os
from dotenv import load_dotenv
load_dotenv()

LOG_LEVEL = os.getenv("LOG_LEVEL")
DEBUG_MODE = int(os.getenv("DEBUG_MODE")) != 0

SAMPLING_RATE = int(os.getenv("SAMPLING_RATE"))

STT_STREAMING_CHUNK_DURATION_MS = int(
    os.getenv("STT_STREAMING_CHUNK_DURATION_MS"))

# 16-bit sample
STT_STREAMING_CHUNK_SIZE_BYTE = int(2 * SAMPLING_RATE *
                                    (STT_STREAMING_CHUNK_DURATION_MS / 1000))
STT_LANGUAGE_CODE = os.getenv("STT_LANGUAGE_CODE")
STT_MAX_ALTERNATIVES = int(os.getenv("STT_MAX_ALTERNATIVES"))
STT_INTERIM_RESULTS = int(os.getenv("STT_INTERIM_RESULTS")) != 0
STT_ENABLE_WORD_TIME_OFFSETS = int(
    os.getenv("STT_ENABLE_WORD_TIME_OFFSETS")) != 0

VAD_MODE = int(os.getenv("VAD_MODE"))
VAD_FRAME_DURATION_MS = int(os.getenv("VAD_FRAME_DURATION_MS"))

# 16-bit sample
VAD_FRAME_SIZE_BYTE = int(2 * SAMPLING_RATE *
                          (VAD_FRAME_DURATION_MS / 1000))
VAD_PADDING_DURATION_MS = int(os.getenv("VAD_PADDING_DURATION_MS"))
VAD_VOICED_TRIGGER_RATE = float(os.getenv("VAD_VOICED_TRIGGER_RATE"))
VAD_UNVOICED_TRIGGER_RATE = float(os.getenv("VAD_UNVOICED_TRIGGER_RATE"))
