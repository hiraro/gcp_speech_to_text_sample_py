#!/usr/bin/env python3
# coding: UTF-8

"""
Based on py-webrtcvad/example.py
https://github.com/wiseman/py-webrtcvad/blob/master/example.py
"""

import sys
import webrtcvad
import collections
import contextlib
import wave

import logging
import logzero
from logzero import logger

import Settings
from Frame import Frame

logzero.loglevel(getattr(logging, Settings.LOG_LEVEL))


def __frame_generator():
    current_timestamp = 0.0

    while not sys.stdin.buffer.closed:
        byte_data = sys.stdin.buffer.read(Settings.VAD_FRAME_SIZE_BYTE)

        frame = Frame(byte_data, current_timestamp,
                      Settings.VAD_FRAME_DURATION_MS)
        yield frame

        current_timestamp += Settings.VAD_FRAME_DURATION_MS


def __vad_collector(frames,
                    sampling_rate=Settings.SAMPLING_RATE,
                    frame_duration_ms=Settings.VAD_FRAME_DURATION_MS,
                    padding_duration_ms=Settings.VAD_PADDING_DURATION_MS):
    """Filters out non-voiced audio frames.

    Given a source of audio frames, yields only
    the voiced audio.

    Uses a padded, sliding window algorithm over the audio frames.
    When more than 90% of the frames in the window are voiced (as
    reported by the VAD), the collector triggers and begins yielding
    audio frames. Then the collector waits until 90% of the frames in
    the window are unvoiced to detrigger.

    The window is padded at the front and back to provide a small
    amount of silence or the beginnings/endings of speech around the
    voiced frames.

    Arguments:

    frames - a source of audio frames (sequence or generator).
    sampling_rate - The audio sample rate, in Hz.
    frame_duration_ms - The frame duration in milliseconds.
    padding_duration_ms - The amount to pad the window, in milliseconds.

    Returns: A generator that yields PCM audio data.
    """

    def voiced_frame_bytes():
        return b''.join([f.bytes for f in voiced_frames])

    def voiced_frame_range():
        start_timestamp = voiced_frames[0].timestamp
        end_timestamp = voiced_frames[-1].timestamp
        return (start_timestamp, end_timestamp + Settings.VAD_FRAME_DURATION_MS)

    vad = webrtcvad.Vad()
    vad.set_mode(Settings.VAD_MODE)

    num_padding_frames = int(padding_duration_ms / frame_duration_ms)

    # We use a deque for our sliding window/ring buffer.
    ring_buffer = collections.deque(maxlen=num_padding_frames)

    # We have two states: TRIGGERED and NOTTRIGGERED. We start in the
    # NOTTRIGGERED state.
    triggered = False

    voiced_frames = []
    for frame in frames:
        is_speech = vad.is_speech(frame.bytes, sampling_rate)

        if not triggered:
            ring_buffer.append((frame, is_speech))
            num_voiced = len([f for f, speech in ring_buffer if speech])

            # If we're NOTTRIGGERED and more than 90% of the frames in
            # the ring buffer are voiced frames, then enter the
            # TRIGGERED state.
            if num_voiced > 0.9 * ring_buffer.maxlen:
                triggered = True
                logger.info('+(%s)' % (ring_buffer[0][0].timestamp,))

                # We want to yield all the audio we see from now until
                # we are NOTTRIGGERED, but we have to start with the
                # audio that's already in the ring buffer.
                for f, _ in ring_buffer:
                    voiced_frames.append(f)

                ring_buffer.clear()
        else:
            # We're in the TRIGGERED state, so collect the audio data
            # and add it to the ring buffer.
            voiced_frames.append(frame)
            ring_buffer.append((frame, is_speech))
            num_unvoiced = len([f for f, speech in ring_buffer if not speech])

            # If more than 90% of the frames in the ring buffer are
            # unvoiced, then enter NOTTRIGGERED and yield whatever
            # audio we've collected.
            if num_unvoiced > 0.9 * ring_buffer.maxlen:
                logger.info('-(%s)' % (frame.timestamp + frame.duration))
                triggered = False

                yield (voiced_frame_bytes(), voiced_frame_range())

                ring_buffer.clear()
                voiced_frames = []

    if triggered:
        logger.info('-(%s)' % (frame.timestamp + frame.duration))

    # If we have any leftover voiced audio when we run out of input,
    # yield it.
    if voiced_frames:
        yield (voiced_frame_bytes(), voiced_frame_range())


def __write_wave(input_wave_file, audio, serial_num, sampling_rate=Settings.SAMPLING_RATE):
    """Writes a .wav file.
    Takes path, PCM audio data, and sample rate.
    """

    # if not Settings.DEBUG_MODE:
    #     return

    save_path = "{}-{}.wav".format(input_wave_file, serial_num)
    with contextlib.closing(wave.open(save_path, 'wb')) as wave_file:
        # pylint: disable=E1101
        wave_file.setnchannels(1)
        wave_file.setsampwidth(2)
        wave_file.setframerate(sampling_rate)
        wave_file.writeframes(audio)

    logger.debug("wrote {}".format(save_path))
    return save_path


def execute(input_wave_file=None, callback=lambda *x: None):
    frames = __frame_generator()
    segment_collector = __vad_collector(frames)
    for i, segment in enumerate(segment_collector):
        chunk_wave_file = __write_wave(input_wave_file, segment[0], i)
        logger.debug("chunk {} start: {}".format(i, segment[1][0]/1000))
        logger.debug("chunk {} end: {}".format(i, segment[1][1]/1000))
        callback(i, segment, chunk_wave_file, input_wave_file)


if __name__ == '__main__':
    if (len(sys.argv) != 2):
        print('Usage: python {} input_wave_file'.format(sys.argv[0]))
        quit()

    input_wave_file = sys.argv[1]

    execute(input_wave_file=input_wave_file)
