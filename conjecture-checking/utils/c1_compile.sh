#!/bin/bash

COMPILER=$1
BIN_FILE=$2
SOURCE_FILE=$3
LIB_FILE=$4

CC_BIN=$(which ${COMPILER})


set -x

if [[ $# -eq 0 ]] ; then
    echo 'usage: $0 <compiler> <binary-file> <source-file> <lib-file>'
    exit 1
fi

for i in 0 1 2 3 g s; do
if [[ "${CC_BIN}" == *gcc* ]]; then
	${CC_BIN} -O$i -g -o ${BIN_FILE}-$i ${SOURCE_FILE} ${LIB_FILE} -w
else
	${CC_BIN} -O$i -g -o ${BIN_FILE}-$i ${SOURCE_FILE} ${LIB_FILE} -Wno-everything
fi
done

exit 0
