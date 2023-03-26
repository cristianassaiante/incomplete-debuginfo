#!/bin/bash

COMPILER=$1
BIN_FILE=$2
SOURCE_FILE=$3
OPT_LEVEL=$4
EXTRA=$5

CC_BIN=$(which ${COMPILER})


set -x

if [[ $# -eq 0 ]] ; then
    echo 'usage: $0 <compiler> <binary-file> <source-file> <opt-level>'
    exit 1
fi

if [[ "${CC_BIN}" == *gcc* ]]; then
	${CC_BIN} -O${OPT_LEVEL} -g -o ${BIN_FILE}-${OPT_LEVEL} ${SOURCE_FILE} -w ${EXTRA}
else
	${CC_BIN} -O${OPT_LEVEL} -g -o ${BIN_FILE}-${OPT_LEVEL} ${SOURCE_FILE} -Wno-everything -mllvm -opt-bisect-limit=${EXTRA}
fi

exit 0
