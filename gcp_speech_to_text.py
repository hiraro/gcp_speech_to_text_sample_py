#!/usr/bin/env python3
# coding: UTF-8
import io
import os
import sys
import time
import itertools
from logzero import logger

from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types

import Settings


def execute(task_queue, callback=None):
    while True:
        try:
            logger.debug("waiting for queuing speech segment info...")

            segment_info = task_queue.get()

            logger.debug("dequeued segment: {} {}".format(
                segment_info[0], segment_info[2]))

            transcribe_streaming(segment_info[2], callback)
        except:
            import traceback
            logger.error(traceback.format_exc())

        time.sleep(1)


def __log_recognition_response_result_alternatives(alternatives):
    for alternative in alternatives:
        logger.debug('Confidence: {}'.format(alternative.confidence))
        logger.info(u'Transcript: {}'.format(alternative.transcript))
        for word_info in alternative.words:
            word = word_info.word
            start_time = word_info.start_time
            end_time = word_info.end_time
            logger.debug('Word: {}, start_time: {}, end_time: {}'.format(
                word,
                start_time.seconds + start_time.nanos * 1e-9,
                end_time.seconds + end_time.nanos * 1e-9))


def transcribe_streaming(stream_file=None, callback=None):
    """Streams transcription of the given audio file."""
    # pylint: disable=E1101

    logger.debug("start: gcp_speech_to_text.transcribe_streaming")

    # Create chunk list from audio file
    chunks = []
    with io.open(stream_file, 'rb') as audio_file:
        for chunk in iter(lambda: audio_file.read(Settings.STT_STREAMING_CHUNK_SIZE_BYTE), b""):
            chunks.append(chunk)

    # Create Recognize API Requests from the chunks
    requests = (types.StreamingRecognizeRequest(audio_content=chunk)
                for chunk in chunks)

    config = types.RecognitionConfig(
        encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
        profanity_filter=True,
        sample_rate_hertz=Settings.SAMPLING_RATE,
        max_alternatives=Settings.STT_MAX_ALTERNATIVES,
        enable_word_time_offsets=Settings.STT_ENABLE_WORD_TIME_OFFSETS,
        language_code=Settings.STT_LANGUAGE_CODE)
    streaming_config = types.StreamingRecognitionConfig(
        interim_results=Settings.STT_INTERIM_RESULTS,
        config=config)

    # streaming_recognize returns a generator.
    logger.debug("start: streaming_recognize()")

    client = speech.SpeechClient()
    responses = client.streaming_recognize(
        streaming_config, requests, timeout=150)

    logger.debug("end: streaming_recognize()")

    for response in responses:
        for result in response.results:
            logger.debug('Finished: {}'.format(result.is_final))
            logger.debug('Stability: {}'.format(result.stability))

            alternatives = list(result.alternatives)

            if callable(callable):
                callback(alternatives)

            __log_recognition_response_result_alternatives(alternatives)

    logger.debug("end: gcp_speech_to_text.transcribe_streaming")


if __name__ == '__main__':
    if (len(sys.argv) != 2):
        print('Usage: python {} recording_wave_file'.format(sys.argv[0]))
        quit()

    transcribe_streaming(sys.argv[1])
