#!/usr/bin/env python3

import os
import sys
import json
from multiprocessing import Pool
from argparse import ArgumentParser

from pathlib import Path
sys.path.append(os.path.join(Path(__file__).resolve().parent, '..'))

from utils.log import *
from utils.checker import *


def check_CX(testcaseid, args):

    def verify():
        # TODO
        # here you should implement your conjecture verifier that returns 
        # info about the violation when it occurs
        return
    

    testcase_dir = os.path.join(args.indir, str(testcaseid))
    cc = 'gcc' if args.gcc else 'clang'
    sourcefile = os.path.join(testcase_dir, f'src/{cc}/a.c')

    with open(sourcefile) as f:
        source_lines = f.readlines()

    testcase_json = os.path.join(testcase_dir, 'testcase.json')
    with open(testcase_json) as f:
        testcase_info = json.load(f)

    if args.gcc:
        cc_version = 'gcc' if not args.gcc_version else 'gcc%s' % args.gcc_version
    else:
        cc_version = 'clang' if not args.clang_version else 'clang%s' % args.clang_version

    trace = testcase_info['trace'][cc_version]['live_variables']

    for opt_level in ['1', '2', '3', 'g', 's']:
        trace_opt = trace[opt_level]
        for line in trace_opt:

            # TODO
            # here you should be filter out the lines that are not useful for your conjecture

            violation = verify()
            if violation:

                log_info(f'[{testcaseid}] CX violation found: {violation}')
                
                testcase_info['violations'][cc_version] = testcase_info['violations'].get(cc_version, {}) 
                testcase_info['violations'][cc_version]['CX'] = testcase_info['violations'][cc_version].get('CX', {}) 
                testcase_info['violations'][cc_version]['CX'][line] = testcase_info['violations'][cc_version]['CX'].get(line, {}) 

                testcase_info['violations'][cc_version]['CX'][line]['opt_level'] = testcase_info['violations'][cc_version]['CX'][line].get('opt_level', '')
                testcase_info['violations'][cc_version]['CX'][line]['opt_level'] += opt_level 
                testcase_info['violations'][cc_version]['CX'][line]['violation'] = testcase_info['violations'][cc_version]['CX'][line].get('violation', violation)

    with open(testcase_json, 'w') as f:
        json.dump(testcase_info, f)


def main(args):
    log_info(f'Conjecture X checking: STARTING')

    if not os.path.exists(args.indir):
        log_info(f'Directory `{args.indir}` does not exists')
        exit(1)

    testcases_json = os.path.join(args.indir, 'testcases.json')
    testcases = {}
    if os.path.exists(args.indir):
        with open(testcases_json) as f:
            testcases = json.load(f)
    else:
        log_info(f'Could not find `testcases.json` file inside `{args.indir}`')
        exit(1)

    log_debug(f'Found {testcases["computed_testcases"]} to be computed')

    pool = Pool(args.proc)
    for i in range(testcases['computed_testcases']):
        if args.proc > 1:
            pool.apply_async(func = check_CX, args = (i, args))
        else:
            check_CX(i, args)
    pool.close()
    pool.join()

    log_info(f'Conjecture X checking: COMPLETED')

if __name__ == '__main__':

    parser = ArgumentParser(description = 'Check for CX violations (offline - after traces extraction)')

    parser.add_argument('--indir', dest = 'indir', type = str, help = 'Input directory (default = `./testcases`)', default = 'testcases')
    parser.add_argument('--path', dest = 'path', type = str, help = 'Path to framework', required = True)
    parser.add_argument('--proc', dest = 'proc', type = int, help = 'Number of processes to use', default = 1)
    parser.add_argument('--gcc', dest = 'gcc', action='store_const', help = 'Check for violations GCC traces (default = `disabled`)', default = 0, const = 1)
    parser.add_argument('--gcc-version', dest = 'gcc_version', type = str, help = 'GCC versions to be chceked (default = `trunk`)', default = '')
    parser.add_argument('--clang', dest = 'clang', action='store_const', help = 'Check for violations CLANG traces (default = `disabled`)', default = 0, const = 1)
    parser.add_argument('--clang-version', dest = 'clang_version', type = str, help = 'CLANG versions to be tested (default = `trunk`)', default = '')
    parser.add_argument('--debug', dest = 'debug', action='store_true', help='Enable debug prints (only when `nproc` is set to `1`)', default = False)

    args = parser.parse_args()

    log_init(args)

    main(args)
