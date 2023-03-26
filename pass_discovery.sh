#!/bin/bash


for i in 1 2 3; do
    echo "-> Pass Discovery for conjecture ${i} on gcc"
    python pass-discovery/gcc_pass_discovery.py --path $(pwd) --conj C$i
done

for i in 1 2 3; do
    echo "-> Pass Discovery for conjecture ${i} on clang"
    python pass-discovery/clang_pass_discovery.py --path $(pwd) --conj C$i
done