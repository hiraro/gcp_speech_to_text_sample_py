#!/bin/bash
SCRIPT_PATH=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
source ${SCRIPT_PATH}/venv/bin/activate
source ${SCRIPT_PATH}/.env

OUTPUT_DIR=${SCRIPT_PATH}/output
[[ ! -d ${OUTPUT_DIR} ]] && mkdir -p ${OUTPUT_DIR}

export OUTPUT_WAVE_FILE=${OUTPUT_DIR}/$(date "+%Y%m%d%H%M").wav
export GOOGLE_APPLICATION_CREDENTIALS=${SCRIPT_PATH}/google_cloud_speech_service_account.json

${REC_CMD_PATH} -q -r ${SAMPLING_RATE} -b ${SAMPLE_SIZE_BIT} -c 1 -t wav -e 'signed-integer' - \
    | tee ${OUTPUT_WAVE_FILE} \
    | python recognizer.py ${OUTPUT_WAVE_FILE}
