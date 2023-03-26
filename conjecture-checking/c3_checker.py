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


def check_C3(testcaseid, args):
    
    def check_var(var, line, source_lines):
        functions = get_functions(source_lines)

        lineno = int(line)
        for f in functions:
            if lineno > f[0] and lineno <= f[1]:
                found = False
                ignore = []
                for idx in range(f[0] + 1, f[1]):
                    line = source_lines[idx].strip()

                    if len(line) == 0:
                        continue

                    if not (('char' in line or 'int' in line or 'double' in line) and 'safe' not in line):
                        found = True

                    if not found:
                        if ('char' in line or 'int' in line or 'double' in line) and 'safe' not in line and '=' not in line or ('=' in line and ';' not in line):
                            var_name = None
                            for a in line.strip().split(' '):
                                if 'l_' in a:
                                    var_name = a
                                    break
                            if not var_name:
                                continue
                            while var_name.startswith('*'):
                                var_name = var_name[1:]
                            if var_name[-1] == ';':
                                var_name = var_name[:-1]
                            if '[' in var_name:
                                var_name = var_name[:var_name.index('[')]
                            ignore.append(var_name);

                    if found:
                        if ('char' in line or 'int' in line or 'double' in line) and 'safe' not in line and '=' in line:
                            var_name = None
                            for a in line.strip().split(' '):
                                if 'l_' in a:
                                    var_name = a
                                    break
                            if not var_name:
                                continue
                            while var_name.startswith('*'):
                                var_name = var_name[1:]
                            if '[' in var_name:
                                var_name = var_name[:var_name.index('[')]
                            ignore.append(var_name);

                if var in ignore:
                    return False

        return True

    def verify(var, line, prev_line, source_lines):
        if check_var(var, line, source_lines):
            return {'line': line, 'prev_line': prev_line}
        return None
    

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

        for i in range(1, len(trace_opt.keys())):
            line = list(trace_opt.keys())[i]
            prev_line = list(trace_opt.keys())[i - 1]

            source_line = source_lines[int(line) - 1].strip()

            if ('int' in source_line or 'char' in source_line or 'double' in source_line) and 'safe' not in source_line:
                continue

            if '{' in source_line or '}' in source_line:
                continue

            for var in trace_opt[line]['available']:

                if var in ['i', 'j', 'k', 'print_hash_value']: continue

                if var not in trace_opt[prev_line]['available']:

                    fline = get_function_from_line(source_lines, line)
                    fprev_line = get_function_from_line(source_lines, prev_line)

                    if fline != fprev_line:
                        continue

                    if not var_is_from_func(var, line, source_lines):
                        continue

                    if is_previous_first_decl(var, prev_line, source_lines):
                        continue

                    violation = verify(var, line, prev_line, source_lines)
                    if violation:
                        log_info(f'[{testcaseid}] C3 violation found: {violation}')
                        
                        testcase_info['violations'][cc_version] = testcase_info['violations'].get(cc_version, {}) 
                        testcase_info['violations'][cc_version]['C3'] = testcase_info['violations'][cc_version].get('C3', {}) 
                        testcase_info['violations'][cc_version]['C3'][var] = testcase_info['violations'][cc_version]['C3'].get(var, {}) 

                        testcase_info['violations'][cc_version]['C3'][var]['opt_level'] = testcase_info['violations'][cc_version]['C3'][var].get('opt_level', '')
                        testcase_info['violations'][cc_version]['C3'][var]['opt_level'] += opt_level 
                        testcase_info['violations'][cc_version]['C3'][var]['violation'] = testcase_info['violations'][cc_version]['C3'][var].get('violation', violation)

    with open(testcase_json, 'w') as f:
        json.dump(testcase_info, f)

def main(args):
    log_info(f'Conjecture 3 checking: STARTING')

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
            pool.apply_async(func = check_C3, args = (i, args))
        else:
            check_C3(i, args)
    pool.close()
    pool.join()

    log_info(f'Conjecture 3 checking: COMPLETED')

if __name__ == '__main__':

    parser = ArgumentParser(description = 'Check for C3 violations (offline - after traces extraction)')

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
