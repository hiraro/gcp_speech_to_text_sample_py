#!/usr/bin/env python3
# coding: UTF-8

"""
Based on py-webrtcvad/example.py
https://github.com/wiseman/py-webrtcvad/blob/master/example.py
"""

import os
import sys
import webrtcvad
import collections
import contextlib
import wave

from logzero import logger

import Settings
from Frame import Frame


def __frame_generator(input_stream):
    current_timestamp = 0.0

    while not input_stream.closed:
        try:
            byte_data = input_stream.read(Settings.VAD_FRAME_SIZE_BYTE)
            current_timestamp += Settings.VAD_FRAME_DURATION_MS
        except:
            import traceback
            logger.error(traceback.format_exc())

        if byte_data is None:
            continue

        frame = Frame(byte_data, current_timestamp,
                      Settings.VAD_FRAME_DURATION_MS)
        yield frame



def __voiced_frame_bytes(voiced_frames):
    return b''.join([f.bytes for f in voiced_frames])


def __voiced_frame_range(voiced_frames):
    start_timestamp = voiced_frames[0].timestamp
    end_timestamp = voiced_frames[-1].timestamp
    return (start_timestamp, end_timestamp + Settings.VAD_FRAME_DURATION_MS)


def __vad_segment_collector(frames):
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

    Returns: A generator that yields PCM audio data.
    """

    vad = webrtcvad.Vad()
    vad.set_mode(Settings.VAD_MODE)

    num_padding_frames = int(Settings.VAD_PADDING_DURATION_MS /
                             Settings.VAD_FRAME_DURATION_MS)

    # We use a deque for our sliding window/ring buffer.
    ring_buffer = collections.deque(maxlen=num_padding_frames)

    # We have two states: TRIGGERED and NOTTRIGGERED. We start in the
    # NOTTRIGGERED state.
    triggered = False

    voiced_frames = []
    for frame in frames:
        is_speech = vad.is_speech(frame.bytes, Settings.SAMPLING_RATE)

        if not triggered:
            ring_buffer.append((frame, is_speech))
            num_voiced = len([f for f, speech in ring_buffer if speech])

            # If we're NOTTRIGGERED and more than Settings.VAD_VOICED_TRIGGER_RATE of the frames in
            # the ring buffer are voiced frames, then enter the
            # TRIGGERED state.
            if num_voiced > Settings.VAD_VOICED_TRIGGER_RATE * ring_buffer.maxlen:
                triggered = True
                logger.info('voiced: (%s)' % (ring_buffer[0][0].timestamp,))

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

            # If more than Settings.VAD_UNVOICED_TRIGGER_RATE of the frames in the ring buffer are
            # unvoiced, then enter NOTTRIGGERED and yield whatever
            # audio we've collected.
            if num_unvoiced > Settings.VAD_UNVOICED_TRIGGER_RATE * ring_buffer.maxlen:
                logger.info('unvoiced: (%s)' % (frame.timestamp + frame.duration))
                triggered = False

                yield (__voiced_frame_bytes(voiced_frames), __voiced_frame_range(voiced_frames))

                ring_buffer.clear()
                voiced_frames = []

    if triggered:
        logger.info('unvoiced: (%s)' % (frame.timestamp + frame.duration))

    # If we have any leftover voiced audio when we run out of input,
    # yield it.
    if voiced_frames:
        yield (__voiced_frame_bytes(voiced_frames), __voiced_frame_range(voiced_frames))


def __write_wave(audio, recording_wave_file, serial_num, sampling_rate=Settings.SAMPLING_RATE):
    """Writes a .wav file.
    Takes path, PCM audio data, and sample rate.
    """

    save_path = "{}-{}.wav".format(recording_wave_file, serial_num)
    with contextlib.closing(wave.open(save_path, 'wb')) as wave_file:
        # pylint: disable=E1101
        wave_file.setnchannels(1)
        wave_file.setsampwidth(2)
        wave_file.setframerate(sampling_rate)
        wave_file.writeframes(audio)
    logger.info(
        "wrote chunk of recording wave file: {}".format(save_path))
    return save_path


def execute(input_stream=sys.stdin.buffer,
            recording_wave_file="{}/{}.wav".format(Settings.OUTPUT_DIR, Settings.START_DATETIME),
            callback=None):
    frames = __frame_generator(input_stream)
    # TODO: エセストリーミングじゃなく真面目にストリーミング変換するなら、サブプロセス作って適当なファイルディスクリプタに音声ストリーム垂れ流すようにする
    vad_segment_collector = __vad_segment_collector(frames)
    for i, vad_segment in enumerate(vad_segment_collector):
        try:
            chunk_wave_file = __write_wave(vad_segment[0], recording_wave_file, i)
            logger.debug("chunk {} start: {}".format(i, vad_segment[1][0]/1000))
            logger.debug("chunk {} end: {}".format(i, vad_segment[1][1]/1000))
            if callable(callback):
                callback(i, vad_segment, chunk_wave_file, recording_wave_file)
        except:
            import traceback
            logger.error(traceback.format_exc())


if __name__ == '__main__':
    if (len(sys.argv) != 2):
        print('Usage: python {} recording_wave_file'.format(sys.argv[0]))
        quit()

    execute(recording_wave_file=sys.argv[1])
