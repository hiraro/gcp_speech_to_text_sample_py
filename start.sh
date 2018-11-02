#!/bin/bash
SCRIPT_PATH=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
source ${SCRIPT_PATH}/venv/bin/activate

OUTPUT_DIR=${SCRIPT_PATH}/output
[[ ! -d ${OUTPUT_DIR} ]] && mkdir -p ${OUTPUT_DIR}

export OUTPUT_WAVE_FILE=${SCRIPT_PATH}/output/$(date "+%Y%m%d%H%M").wav
export GOOGLE_APPLICATION_CREDENTIALS=${SCRIPT_PATH}/google_cloud_speech_service_account.json

rec -q -r 16000 -b 16 -c 1 -t wav -e 'signed-integer' - \
    | tee ${OUTPUT_WAVE_FILE} \
    | python recognizer.py ${OUTPUT_WAVE_FILE}
