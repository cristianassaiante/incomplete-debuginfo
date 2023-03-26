#!/bin/bash

echo "-> Conjecture 1 Checking on gcc"
python conjecture-checking/c1_checker.py --path $(pwd) --gcc
echo "-> Conjecture 2 Checking on gcc"
python conjecture-checking/c2_checker.py --path $(pwd) --gcc
echo "-> Conjecture 3 Checking on gcc"
python conjecture-checking/c3_checker.py --path $(pwd) --gcc

echo "-> Conjecture 1 Checking on clang"
python conjecture-checking/c1_checker.py --path $(pwd) --clang
echo "-> Conjecture 2 Checking on clang"
python conjecture-checking/c2_checker.py --path $(pwd) --clang
echo "-> Conjecture 3 Checking on clang"
python conjecture-checking/c3_checker.py --path $(pwd) --clang