#!/usr/bin/env python3
# coding: UTF-8
from multiprocessing import Process, Queue
import multiprocessing
import os
import sys
import signal
import logging
import logzero
from logzero import logger
import vad
import gcp_speech_to_text
import Settings

logzero.loglevel(getattr(logging, Settings.LOG_LEVEL))
logzero.logfile("{}/recognizer.log".format(Settings.SCRIPT_PATH),
                maxBytes=1e8,
                backupCount=3)


def __enqueue_chunk_info_closure(task_queue):
    def enqueue_chunk_info(i, vad_segment, chunk_wave_file, recording_wave_file):
        logger.debug("enqueuing chunk info...")

        task_queue.put(
            (i, vad_segment, chunk_wave_file, recording_wave_file), block=False)

        logger.debug("enqueued chunk info: {} {}".format(
            i, chunk_wave_file))
    return enqueue_chunk_info


def __prepare_result_file(result_file_path):
    f = open(result_file_path, 'a')
    return f


def __on_recognition_response_result_alternatives_closure(result_file_path):
    def on_recognition_response_result_alternatives(alternatives):
        with __prepare_result_file(result_file_path) as result_file_handler:
            result_file_handler.write(
                alternatives[0].transcript + "\n")

    return on_recognition_response_result_alternatives


def execute(input_stream=None,
            recording_wave_file=None,
            result_file_path="{}/{}.txt".format(Settings.OUTPUT_DIR, Settings.START_DATETIME),):

    task_queue = Queue()

    on_recognition_responses = \
        __on_recognition_response_result_alternatives_closure(result_file_path)

    logger.info("output text file: {}".format(result_file_path))

    recognition_process = Process(
        target=gcp_speech_to_text.execute,
        args=(task_queue, on_recognition_responses)
    )
    recognition_process.start()

    callback = __enqueue_chunk_info_closure(task_queue)

    if input_stream is None:
        new_stdin = os.fdopen(os.dup(sys.stdin.fileno()))
        input_stream = new_stdin.buffer

    logger.info("recording wave file: {}".format(recording_wave_file))

    vad_process = Process(
        target=vad.execute,
        args=(input_stream, recording_wave_file, callback)
    )
    vad_process.start()

    def __signalHandler(signal, handler):
        recognition_process.terminate()
        vad_process.terminate()

    signal.signal(signal.SIGINT,  __signalHandler)
    signal.signal(signal.SIGTERM, __signalHandler)


if __name__ == '__main__':
    if (len(sys.argv) != 2):
        print('Usage: python {} recording_wave_file'.format(sys.argv[0]))
        quit()

    execute(recording_wave_file=sys.argv[1])
