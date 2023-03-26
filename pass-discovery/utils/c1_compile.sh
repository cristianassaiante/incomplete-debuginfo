#!/bin/bash

COMPILER=$1
BIN_FILE=$2
SOURCE_FILE=$3
LIB_FILE=$4
OPT_LEVEL=$5
EXTRA=$6

CC_BIN=$(which ${COMPILER})


set -x

if [[ $# -eq 0 ]] ; then
    echo 'usage: $0 <compiler> <binary-file> <source-file> <lib-file> <opt-level>'
    exit 1
fi

if [[ "${CC_BIN}" == *gcc* ]]; then
	${CC_BIN} -O${OPT_LEVEL} -g -o ${BIN_FILE}-${OPT_LEVEL} ${SOURCE_FILE} ${LIB_FILE} -w ${EXTRA}
else
	${CC_BIN} -O${OPT_LEVEL} -g -o ${BIN_FILE}-${OPT_LEVEL} ${SOURCE_FILE} ${LIB_FILE} -Wno-everything -mllvm -opt-bisect-limit=${EXTRA}
fi

exit 0
