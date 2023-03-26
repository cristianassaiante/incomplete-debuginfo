#!/usr/bin/env python3

import os
import sys
import json
from multiprocessing import Pool
from subprocess import *
from argparse import ArgumentParser

from pathlib import Path
sys.path.append(os.path.join(Path(__file__).resolve().parent, '..'))

from utils.log import *
from utils.run import *
from utils.tracer import *


def get_trace(testcaseid, args):

    log_debug(f'[{testcaseid}] Testcase live variables computation: STARTED')

    testcase_dir = os.path.join(args.indir, str(testcaseid))
    testcase_json = os.path.join(testcase_dir, 'testcase.json')
    with open(testcase_json) as f:
        testcase_info = json.load(f)

    if args.gcc:
        cc_version = 'gcc' if not args.gcc_version else 'gcc%s' % args.gcc_version
        dbg = 'gdb'
    if args.clang:
        cc_version = 'clang' if not args.clang_version else 'clang%s' % args.clang_version
        dbg = 'lldb'

    if cc_version not in testcase_info['trace']:
        testcase_info['trace'][cc_version] = {}
    if 'live_variables' not in testcase_info['trace'][cc_version]:
        testcase_info['trace'][cc_version]['live_variables'] = {}
    else:
        log_debug(f'[{testcaseid}] Trace already computed')
        log_debug(f'[{testcaseid}] Testcase live variables computation: COMPLETED')
        return

    # compute live variables
    for opt_level in ['0', '1', '2', '3', 'g', 's']:
        bin_filename = os.path.join(testcase_dir, 'bin/%s/opt-%s' % (cc_version, opt_level)) 

        if not os.path.exists(bin_filename):
            log_debug(f'[{testcaseid}] {bin_filename} does not exist')
            continue

        variables = get_traced_variables(bin_filename, dbg)
        testcase_info['trace'][cc_version]['live_variables'][opt_level] = variables
        
    with open(testcase_json, 'w') as f:
        json.dump(testcase_info, f)

    log_debug(f'[{testcaseid}] Testcase live variables computation: COMPLETED')

def main(args):
    log_info(f'Debug trace computation: STARTING')

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

    pool = Pool(processes = args.proc)
    for i in range(testcases['computed_testcases']):
        if args.proc > 1:
            pool.apply_async(func = get_trace, args = (i, args))
        else:
            get_trace(i, args)
    pool.close()
    pool.join()

    log_info(f'Debug trace computation: COMPLETED')

if __name__ == '__main__':

    parser = ArgumentParser(description = 'Get trace about live variables per line')

    parser.add_argument('--indir', dest = 'indir', type = str, help = 'Input directory (default = `./testcases`)', default = 'testcases')
    parser.add_argument('--path', dest = 'path', type = str, help = 'Path to framework', required = True)
    parser.add_argument('--proc', dest = 'proc', type = int, help = 'Number of processes to use', default = 1)
    parser.add_argument('--gcc', dest = 'gcc', action='store_const', help = 'Get trace about GCC binaries using GDB (default = `disabled`)', default = 0, const = 1)
    parser.add_argument('--gcc-version', dest = 'gcc_version', type = str, help = 'GCC versions to be tested (default = `trunk`)', default = '')
    parser.add_argument('--clang', dest = 'clang', action='store_const', help = 'Get trace about CLANG binaries using LLDB (default = `disabled`)', default = 0, const = 1)
    parser.add_argument('--clang-version', dest = 'clang_version', type = str, help = 'CLANG versions to be tested (default = `trunk`)', default = '')
    parser.add_argument('--debug', dest = 'debug', action='store_true', help='Enable debug prints (only when `nproc` is set to `1`)', default = False)

    args = parser.parse_args()

    log_init(args)

    main(args)
