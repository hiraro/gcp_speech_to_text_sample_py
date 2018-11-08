#!/bin/bash
SCRIPT_PATH=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
source ${SCRIPT_PATH}/venv/bin/activate
source ${SCRIPT_PATH}/.env

OUTPUT_DIR=${SCRIPT_PATH}/output
[[ ! -d ${OUTPUT_DIR} ]] && mkdir -p ${OUTPUT_DIR}

export RECORDING_WAVE_FILE=${OUTPUT_DIR}/$(date "+%Y%m%d%H%M").wav
export GOOGLE_APPLICATION_CREDENTIALS=${SCRIPT_PATH}/google_cloud_speech_service_account.json

rec -q -r ${SAMPLING_RATE} -b ${SAMPLE_SIZE_BIT} -c 1 -t wav -e 'signed-integer' - \
    | tee ${RECORDING_WAVE_FILE} \
    | python recognizer.py ${RECORDING_WAVE_FILE}
