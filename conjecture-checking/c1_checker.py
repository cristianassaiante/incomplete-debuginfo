#!/usr/bin/env python3

import os
import sys
import json
import re
import random
import shutil
from multiprocessing import Pool
from subprocess import *
from argparse import ArgumentParser


from pathlib import Path
sys.path.append(os.path.join(Path(__file__).resolve().parent, '..'))

from utils.log import *
from utils.run import *
from utils.tracer import *
from utils.checker import *
from utils.injection import *


# ARGS: path to framework - compiler - output - source_file - lib_file
CC = '%s/conjecture-checking/utils/c1_compile.sh %s %s %s %s'
# ARGS: ccomp_ready_file
CCOMP = 'ccomp -interp -quiet %s'


def check_C1(testcaseid, args):
    testcase_dir = os.path.join(args.indir, str(testcaseid))
    cc = 'gcc' if args.gcc else 'clang'
    sourcefile = os.path.join(testcase_dir, f'src/{cc}/a.c')

    with open(sourcefile) as f:
        source_lines_init = f.readlines()

    testcase_json = os.path.join(testcase_dir, 'testcase.json')
    with open(testcase_json) as f:
        testcase_info = json.load(f)

    if args.gcc:
        cc_version = 'gcc' if not args.gcc_version else 'gcc%s' % args.gcc_version
    else:
        cc_version = 'clang' if not args.clang_version else 'clang%s' % args.clang_version

    # insert call if not yet inserted
    if 'call_injection' not in testcase_info:
        trace = testcase_info['trace'][cc_version]['live_variables']
        trace_unopt = trace['0']

        keys = list(trace_unopt.keys())

        while not 'call_injection' in testcase_info:

            source_lines = source_lines_init[::]
            
            found = False
            while not found:
                line = random.choice(keys)

                line_code = source_lines[int(line) - 1]
                if 'return' in line_code or 'if' in line_code or 'for' in line_code:
                    log_debug(f'[{testcaseid}] Cannot inject in construct instruction')
                    keys.remove(line)
                    continue

                count = 0
                for var in trace_unopt[line]['available']:
                    if var.startswith('l_') or var in ['i', 'j', 'k']:
                        count += 1
                if count > 0 and count < 10:
                    found = line
                else:
                    keys.remove(line)
            
            func, call, _, call_vars = generate_module(line, trace_unopt, source_lines)

            if len(call_vars) == 0:
                log_debug(f'[{testcaseid}] No variables available at call site')
                keys.remove(line)
                continue

            log_debug(f'[{testcaseid}] Found call site to inject call')

            line = int(line)
            source_lines = source_lines[:line] + [call] + source_lines[line:]

            tobecreated = os.path.join(os.path.join(testcase_dir, 'src/gcc/call'))
            if not os.path.exists(tobecreated):            
                os.makedirs(tobecreated)
                os.makedirs(os.path.join(testcase_dir, 'src/clang/call'))

            ccdir = 'gcc' if 'gcc' in cc_version else 'clang'
            srcfile_path = os.path.join(os.path.join(testcase_dir, f'src/{ccdir}/call', 'a.c'))
            libfile_path = os.path.join(os.path.join(testcase_dir, f'src/{ccdir}/call', 'lib.c'))
            ccofile_path = os.path.join(os.path.join(testcase_dir, f'src/{ccdir}/call', 'a.ccomp.c'))

            with open(srcfile_path, 'w') as f:
                f.write(''.join(source_lines))
            with open(libfile_path, 'w') as f:
                f.write('#include <stdio.h>\n\n' + func)
            with open(ccofile_path, 'w') as f:
                f.write(''.join([func] + source_lines))
            
            # check ccomp
            ret = run_cmd(CCOMP % (ccofile_path))
            if ret:
                log_debug(f'[{testcaseid}] CompCert check failed, restarting code generation')
                keys.remove(str(line))
                continue
            
            log_debug(f'[{testcaseid}] CompCert check succedeed')
            
            # propagate call
            other_ccdir = 'clang' if 'gcc' in ccdir else 'gcc'
            other_file = os.path.join(testcase_dir, f'src/{other_ccdir}/a.c')
            with open(other_file) as f:
                source_lines_other = f.readlines()

            call_site_other = propagate_call(source_lines, source_lines_other)
            source_lines_other = source_lines_other[:call_site_other] + [call] + source_lines_other[call_site_other:]

            # write to source file and copy to libfile and generate a.ccomp.c for the other
            srcfile_path_other = os.path.join(os.path.join(testcase_dir, f'src/{other_ccdir}/call', 'a.c'))
            libfile_path_other = os.path.join(os.path.join(testcase_dir, f'src/{other_ccdir}/call', 'lib.c'))
            ccofile_path_other = os.path.join(os.path.join(testcase_dir, f'src/{other_ccdir}/call', 'a.ccomp.c'))
            
            with open(srcfile_path_other, 'w') as f:
                f.write(''.join(source_lines_other))
            shutil.copyfile(libfile_path, libfile_path_other)
            with open(ccofile_path_other, 'w') as f:
                f.write(''.join([func] + source_lines_other))

            testcase_info['call_injection'] = {ccdir: line, other_ccdir: call_site_other, 'vars': call_vars}
            with open(testcase_json, 'w') as f:
                json.dump(testcase_info, f)
    else:
        log_debug(f'[{testcaseid}] Call already injected')

    # compile
    tobecreated = os.path.join(testcase_dir, f'bin/{cc_version}/call')
    if not os.path.exists(tobecreated):
        os.makedirs(tobecreated)
        out_file = os.path.join(os.path.join(testcase_dir, f'bin/{cc_version}/call/', 'opt'))

        ccdir = 'gcc' if 'gcc' in cc_version else 'clang'
        source_file = os.path.join(os.path.join(testcase_dir, f'src/{ccdir}/call', 'a.c'))
        lib_file = os.path.join(os.path.join(testcase_dir, f'src/{ccdir}/call', 'lib.c'))

        ret = run_cmd(CC % (args.path, cc_version, out_file, source_file, lib_file))
        if ret:
            log_debug(f'[{testcaseid}] Error while compiling C1 binaries')
            return
    
    for opt_level in ['1', '2', '3', 'g', 's']:

        binary = os.path.join(os.path.join(testcase_dir, f'bin/{cc_version}/call/', f'opt-{opt_level}'))

        cc = ['gcc', 'clang'][not args.gcc]
        dbg = ['gdb', 'lldb'][not args.gcc]

        variables = get_traced_variables(binary, dbg)[str(testcase_info['call_injection'][cc] + 1)]
        
        call_vars = set(testcase_info['call_injection']['vars'])
        available = set(variables['available']) & call_vars
        not_and_opt = (set(variables['not_available']) | set(variables['optimized_out'])) & call_vars
        missing = call_vars - (available | not_and_opt)

        violations = list(not_and_opt | missing)

        for var in violations:
            violation = {'line': testcase_info['call_injection']['gcc' if args.gcc else 'clang'] + 1, 'var': var}

            log_info(f'[{testcaseid}] C1 violation found: {violation}')
            
            testcase_info['violations'][cc_version] = testcase_info['violations'].get(cc_version, {}) 
            testcase_info['violations'][cc_version]['C1'] = testcase_info['violations'][cc_version].get('C1', {}) 
            testcase_info['violations'][cc_version]['C1'][var] = testcase_info['violations'][cc_version]['C1'].get(var, {}) 

            testcase_info['violations'][cc_version]['C1'][var]['opt_level'] = testcase_info['violations'][cc_version]['C1'][var].get('opt_level', '')
            testcase_info['violations'][cc_version]['C1'][var]['opt_level'] += opt_level 
            testcase_info['violations'][cc_version]['C1'][var]['violation'] = testcase_info['violations'][cc_version]['C1'][var].get('violation', violation)

    with open(testcase_json, 'w') as f:
        json.dump(testcase_info, f)

def main(args):
    log_info(f'Conjecture 1 checking: STARTING')

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
            pool.apply_async(func = check_C1, args = (i, args))
        else:
            check_C1(i, args)
    pool.close()
    pool.join()

    log_info(f'Conjecture 1 checking: COMPLETED')

if __name__ == '__main__':

    parser = ArgumentParser(description = 'Check for C1 violations (offline - after traces extraction)')

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
