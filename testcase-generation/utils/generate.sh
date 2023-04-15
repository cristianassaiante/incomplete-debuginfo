#!/bin/bash

OUT_DIR=$1/src
CSMITH_SCRIPT=$2
SEED=$3

# 'gcc' and 'clang' always refer to the trunk version
GCC_BIN=$(which gcc)
CLANG_BIN=$(which clang)
CSMITH_INCLUDE=$(find /usr/include -maxdepth 1 | grep csmith | head -n1) 
SOURCE_FILE=a.c

set -x

if [[ $# -eq 0 ]] ; then
    echo 'usage: $0 <source-file> <csmith-scripts> <csmith-seed> <cc-bin>'
    exit 1
fi

# generate random C file
${CSMITH_SCRIPT} ${SEED} > ${OUT_DIR}/${SOURCE_FILE}.orig.c
rm platform.info

# apply preprocessor
${GCC_BIN} -E -P ${OUT_DIR}/${SOURCE_FILE}.orig.c -I${CSMITH_INCLUDE} -o ${OUT_DIR}/gcc/${SOURCE_FILE}.tmp -w
${CLANG_BIN} -E ${OUT_DIR}/${SOURCE_FILE}.orig.c -I${CSMITH_INCLUDE} -o ${OUT_DIR}/clang/${SOURCE_FILE}.tmp -Wno-everything

# cleanup for clang
mv ${OUT_DIR}/clang/${SOURCE_FILE}.tmp ${OUT_DIR}/clang/${SOURCE_FILE}
perl -pi -e 's/__asm__ \(.*?\)//' ${OUT_DIR}/clang/${SOURCE_FILE}
perl -pi -e 's/^#.*//' ${OUT_DIR}/clang/${SOURCE_FILE}
perl -pi -e 's/__PRETTY_FUNCTION__/__func__/g' ${OUT_DIR}/clang/${SOURCE_FILE}
sed '/^#/ d' ${OUT_DIR}/clang/${SOURCE_FILE} > ${OUT_DIR}/clang/${SOURCE_FILE}.clear
rm ${OUT_DIR}/clang/${SOURCE_FILE}
mv ${OUT_DIR}/clang/${SOURCE_FILE}.clear ${OUT_DIR}/clang/${SOURCE_FILE}

# cleanup for gcc
mv ${OUT_DIR}/gcc/${SOURCE_FILE}.tmp ${OUT_DIR}/gcc/${SOURCE_FILE}
perl -pi -e 's/__asm__ \(.*?\)//' ${OUT_DIR}/gcc/${SOURCE_FILE}
perl -pi -e 's/^#.*//' ${OUT_DIR}/gcc/${SOURCE_FILE}
perl -pi -e 's/__PRETTY_FUNCTION__/__func__/g' ${OUT_DIR}/gcc/${SOURCE_FILE}
perl -pi -e 's/.*__extension__ __func__.*//g' ${OUT_DIR}/gcc/${SOURCE_FILE}
sed -z 's/extern int __fpclassifyf128.*Float.*\n     __attribute__ ((__const__));\n//g' ${OUT_DIR}/gcc/${SOURCE_FILE} > ${OUT_DIR}/gcc/${SOURCE_FILE}.tmp
mv ${OUT_DIR}/gcc/${SOURCE_FILE}.tmp ${OUT_DIR}/gcc/${SOURCE_FILE}
sed '/^#/ d' ${OUT_DIR}/gcc/${SOURCE_FILE} > ${OUT_DIR}/gcc/${SOURCE_FILE}.clear
rm ${OUT_DIR}/gcc/${SOURCE_FILE}
mv ${OUT_DIR}/gcc/${SOURCE_FILE}.clear ${OUT_DIR}/gcc/${SOURCE_FILE}

exit 0
