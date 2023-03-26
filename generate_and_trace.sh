#!/bin/bash

if [ -z "$1" ]; then
    echo "Usage: $0 [number of testcases] <--metrics>"
    exit 1
fi

echo "-> Generation"
python testcase-generation/generate.py --path $(pwd) --testcases $1

echo "-> Debug Tracer for gcc"
python conjecture-checking/debug_trace.py --path $(pwd) --gcc
echo "-> Debug Tracer for clang"
python conjecture-checking/debug_trace.py --path $(pwd) --clang

if [ "$2" == "--metrics" ]; then
    echo "-> Incompleteness Metrics Computation for gcc"
    python incompleteness-metrics/compute_metrics.py --gcc
    echo "-> Incompleteness Metrics Computation for clang"
    python incompleteness-metrics/compute_metrics.py --clang
else
    echo "Usage: $0 [number of testcases] <--metrics>"
    rm -rf testcases
    exit 1
fi