#!/usr/bin/env python3
# coding: UTF-8
from multiprocessing import Process, Queue
import sys
import logging
import logzero
from logzero import logger
import vad
import gcp_speech_to_text
import Settings

logzero.loglevel(getattr(logging, Settings.LOG_LEVEL))

def __enqueue_chunk_info_closure(task_queue):
    def enqueue_chunk_info(i, segment, chunk_wave_file, input_wave_file):
        logger.debug("enqueue_chunk_info: {}".format(i))
        task_queue.put((i, segment, chunk_wave_file, input_wave_file))
    return enqueue_chunk_info

if __name__ == '__main__':
    if (len(sys.argv) != 2):
        print('Usage: python {} input_wave_file'.format(sys.argv[0]))
        quit()

    input_wave_file = sys.argv[1]

    task_queue = Queue()

    p = Process(target=gcp_speech_to_text.execute, args=(task_queue,))
    p.start()

    callback = __enqueue_chunk_info_closure(task_queue)
    vad.execute(input_wave_file=input_wave_file, callback=callback)

    p.join()
