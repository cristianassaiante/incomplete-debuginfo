#!/usr/bin/env python3
  
import os
import sys
import json
import random
from glob import glob
from multiprocessing import Pool
from argparse import ArgumentParser

from pathlib import Path
sys.path.append(os.path.join(Path(__file__).resolve().parent, '..'))

from utils.log import *
from utils.run import *

# ARGS: path to framework - testcase_dir - csmith seed   
CSMITH = '%s/testcase-generation/utils/generate.sh %s %s/testcase-generation/utils/csmith.pl %s'
# ARGS: path to framework - compiler - output - source_file
CC = '%s/testcase-generation/utils/compile.sh %s %s %s'

def create_directories(testcase_dir, testcaseid, gcc, clang):
    if not os.path.exists(testcase_dir):
        os.makedirs(testcase_dir)

        os.makedirs(os.path.join(testcase_dir, 'src'))
        os.makedirs(os.path.join(testcase_dir, 'src/gcc'))
        os.makedirs(os.path.join(testcase_dir, 'src/clang'))

        os.makedirs(os.path.join(testcase_dir, 'bin'))
        os.makedirs(os.path.join(testcase_dir, 'bin/gcc'))
        os.makedirs(os.path.join(testcase_dir, 'bin/clang'))

    for version in gcc.split(':'):
        cc_bin_path = os.path.join(testcase_dir, 'bin/gcc%s' % version)
        if not os.path.exists(cc_bin_path):
            os.makedirs(cc_bin_path)
    for version in clang.split(':'):
        cc_bin_path = os.path.join(testcase_dir, 'bin/clang%s' % version)
        if not os.path.exists(cc_bin_path):
            os.makedirs(cc_bin_path)

def generate(testcaseid, args):
    testcase_dir = os.path.join(args.outdir, str(testcaseid))
    create_directories(testcase_dir, testcaseid, args.gcc, args.clang)
    log_debug(f'[{testcaseid}] Testcase directory structure generated')

    testcase_json = os.path.join(testcase_dir, 'testcase.json')
    testcase_info = {}
    if os.path.exists(testcase_json):
        with open(testcase_json) as f:
            testcase_info = json.load(f)

    # generate source
    done = False
    if not testcase_info:
        while not done:
            seed = (args.seed * (testcaseid + 1) % 2**32)
            ret = run_cmd(CSMITH % (args.path, testcase_dir, args.path, seed))
            if ret:
                log_debug(f'[{testcaseid}] Error while generating source code')
            else:
                done = True

        log_debug(f'[{testcaseid}] Testcase source code generated')

    # compile trunk if none
    if not testcase_info:
        gcc_out_file = os.path.join(testcase_dir, 'bin/gcc/opt')
        clang_out_file = os.path.join(testcase_dir, 'bin/clang/opt')

        gcc_source_file = os.path.join(testcase_dir, 'src/gcc/a.c')
        clang_source_file = os.path.join(testcase_dir, 'src/clang/a.c')

        ret = run_cmd(CC % (args.path, 'gcc', gcc_out_file, gcc_source_file))
        if ret:
            log_debug(f'[{testcaseid}] Error while compiling with GCC')

        ret = run_cmd(CC % (args.path, 'clang', clang_out_file, clang_source_file))
        if ret:
            log_debug(f'[{testcaseid}] Error while compiling with CLANG')

        log_debug(f'[{testcaseid}] Testcase GCC/CLANG trunk version compilation completed')

    if not 'gcc_versions' in testcase_info:
        testcase_info['gcc_versions'] = ['gcc']
    if not 'clang_versions' in testcase_info:
        testcase_info['clang_versions'] = ['clang']

    # compile required gcc versions
    if args.gcc:
        for version in args.gcc.split(':'):
            if version in testcase_info['gcc_versions']:
                continue

            gcc_out_file = os.path.join(testcase_dir, 'bin/gcc%s/opt' % version)
            gcc_source_file = os.path.join(testcase_dir, 'src/gcc/a.c')
            gcc_version = 'gcc-%s' % version

            ret = run_cmd(CC % (args.path, gcc_version, gcc_out_file, gcc_source_file))
            if ret:
                cc_bin_path = os.path.join(testcase_dir, 'bin/gcc%s' % version)
                os.rmdir(cc_bin_path)
                log_debug(f'[{testcaseid}] Error while compiling with GCC-{version}')
            else:
                testcase_info['gcc_versions'].append('gcc%s' % version)

        log_debug(f'[{testcaseid}] Testcase GCC extra-version compilation completed')

    # compile required clang versions 
    if args.clang:
        for version in args.clang.split(':'):
            if version in testcase_info['clang_versions']:
                continue

            clang_out_file = os.path.join(testcase_dir, 'bin/clang%s/opt' % version)
            clang_source_file = os.path.join(testcase_dir, 'src/clang/a.c')
            clang_version = 'clang-%s' % version

            ret = run_cmd(CC % (args.path, clang_version, clang_out_file, clang_source_file))
            if ret:
                cc_bin_path = os.path.join(testcase_dir, 'bin/clang%s' % version)
                os.rmdir(cc_bin_path)
                log_debug(f'[{testcaseid}] Error while compiling with CLANG-{version}')
            else:
                testcase_info['clang_versions'].append('clang%s' % version)

        log_debug(f'[{testcaseid}] Testcase CLANG extra-version compilation completed')

    if not 'violations' in testcase_info:
        testcase_info['violations'] = {}
    if not 'trace' in testcase_info:
        testcase_info['trace'] = {}
    with open(testcase_json, 'w') as f:
        json.dump(testcase_info, f)

    log_debug(f'[{testcaseid}] Testcase generation completed')

def main(args):
    log_info(f'Testcases generation: STARTING')
    
    if not os.path.exists(args.outdir):
        os.makedirs(args.outdir)
    else:
        log_info(f'Output directory already existing: EXITING')
        exit(1)
    
    pool = Pool(processes = args.proc)
    for i in range(args.testcases):
        if args.proc > 1:
            pool.apply_async(func = generate, args = (i, args))
        else:
            generate(i, args)
    pool.close()
    pool.join()
    
    testcases_json = os.path.join(args.outdir, 'testcases.json')
    testcases = {}

    count = 0
    for _ in glob(args.outdir + '/[0-9]*'):
        count += 1

    testcases['computed_testcases'] = count
    if 'seed' not in testcases:
        testcases['seed'] = args.seed
    if 'statistics' not in testcases:
        testcases['statistics'] = {}

    with open(testcases_json, 'w') as f:
        json.dump(testcases, f)

    log_info(f'Testcases generation: COMPLETED')

if __name__ == '__main__':

    parser = ArgumentParser(description = 'Testcase generation')

    parser.add_argument('--outdir', dest = 'outdir', type = str, help = 'Output directory (default = `./testcases`)', default = 'testcases')
    parser.add_argument('--seed', dest = 'seed', type = int, help = 'Starting seed for random generation (default = `random`)', default = random.randint(0, 2**32))
    parser.add_argument('--path', dest = 'path', type = str, help = 'Path to framework', required = True)
    parser.add_argument('--testcases', dest = 'testcases', type = int, help = 'Number of testcases to be generated', required = True)
    parser.add_argument('--proc', dest = 'proc', type = int, help = 'Number of processes to use', default = 1)
    parser.add_argument('--gcc', dest = 'gcc', type = str, help = 'GCC versions to be compiled beside `trunk` (:-separated list)', default = '')
    parser.add_argument('--clang', dest = 'clang', type = str, help = 'CLANG versions to be compiled beside `trunk` (:-separated list)', default = '')
    parser.add_argument("--debug", dest = 'debug', action="store_true", help="Enable debug prints (only when `nproc` is set to `1`)", default = False)

    args = parser.parse_args()

    log_init(args)
    
    main(args)