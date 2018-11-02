#!/usr/bin/env python3
# coding: UTF-8
import io
import sys
import logging
import logzero
from logzero import logger

from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types

import Settings

logzero.loglevel(getattr(logging, Settings.LOG_LEVEL))


def execute(task_queue):
    logger.debug("start: gcp_speech_to_text.execute")

    while True:
        segment_info = task_queue.get()
        logger.debug("dequeued: {} {}".format(segment_info[0], segment_info[2]))

        transcribe_streaming(segment_info[2])

def transcribe_streaming(stream_file):
    """Streams transcription of the given audio file."""
    # pylint: disable=E1101

    logger.debug("start: gcp_speech_to_text.transcribe_streaming")

    client = speech.SpeechClient()

    chunks = []
    with io.open(stream_file, 'rb') as audio_file:
        for chunk in iter(lambda: audio_file.read(Settings.STT_STREAMING_CHUNK_SIZE_BYTE), b""):
            chunks.append(chunk)

    # In practice, stream should be a generator yielding chunks of audio data.
    requests = (types.StreamingRecognizeRequest(audio_content=chunk)
                for chunk in chunks)

    config = types.RecognitionConfig(
        encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=Settings.SAMPLING_RATE,
        language_code=Settings.STT_LANGUAGE_CODE)
    streaming_config = types.StreamingRecognitionConfig(
        config=config)

    # streaming_recognize returns a generator.
    responses = client.streaming_recognize(streaming_config, requests)

    for response in responses:
        # Once the transcription has settled, the first result will contain the
        # is_final result. The other results will be for subsequent portions of
        # the audio.
        for result in response.results:
            logger.info('Finished: {}'.format(result.is_final))
            logger.info('Stability: {}'.format(result.stability))

            alternatives = result.alternatives
            # The alternatives are ordered from most likely to least.
            for alternative in alternatives:
                logger.info('Confidence: {}'.format(alternative.confidence))
                logger.info(u'Transcript: {}'.format(alternative.transcript))


if __name__ == '__main__':
    if (len(sys.argv) != 2):
        print('Usage: python {} input_filename'.format(sys.argv[0]))
        quit()

    transcribe_streaming(sys.argv[1])
