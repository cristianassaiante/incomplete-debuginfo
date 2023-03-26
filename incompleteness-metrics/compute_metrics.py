#!/usr/bin/env python3

import os
import sys
import json
from argparse import ArgumentParser

from pathlib import Path
sys.path.append(os.path.join(Path(__file__).resolve().parent, '..'))
from utils.log import *

def get_lines_filter(sourcefile):

    source_lines = [(i, line) for i, line in enumerate(open(sourcefile))]
    functions = {}
    found = False
    fname = None
    par = 0
    for i, line in enumerate(source_lines):
        if '{' in line[1]:
            if not found:
                found = True
                
                prototype = source_lines[i - 1][1]
                if 'main' in prototype or ' func' in prototype:
                    fname = prototype.strip().split('(')[0].split()[-1] 
                else:
                    fname = '%d' % i
                functions[fname] = []

                functions[fname].append(line[0])
                par += 1
            else:
                par += 1

        if '}' in line[1]:
            par -= 1
            if par == 0:
                found = False
                functions[fname].append(line[0] + 1)

    out = set()
    for func in functions:
        if 'main' in func or 'func' in func:
            out |= set(range(functions[func][0], functions[func][1] + 1))

    return out

def get_vars_diff_per_line(live_variables, opt_level, compiler, lines_filter):

    result = {}

    lines_unopt = 0
    for line in live_variables['0']:
        if not line.isnumeric():
            continue

        if int(line) in lines_filter:
            lines_unopt += 1

    lines_opt = 0
    
    for line in live_variables[opt_level]:

        if not line.isnumeric():
            continue
        if int(line) not in lines_filter:
            continue

        if line in live_variables['0']:

            unopt_vars = live_variables['0'][line]
            opt_vars = live_variables[opt_level][line]

            total = set(unopt_vars['available'])
            optimized_out = total & set(opt_vars['optimized_out'])
            available = total & set(opt_vars['available'])
            not_available = total & set(opt_vars['not_available'])

            total = set(filter(lambda x: x.startswith('l') or x in ['i', 'j', 'k', 'print_hash_value'], total))
            optimized_out = set(filter(lambda x: x.startswith('l') or x in ['i', 'j', 'k', 'print_hash_value'], optimized_out))
            available = set(filter(lambda x: x.startswith('l') or x in ['i', 'j', 'k', 'print_hash_value'], available))
            not_available = set(filter(lambda x: x.startswith('l') or x in ['i', 'j', 'k', 'print_hash_value'], not_available))

            missing = total - (optimized_out | available | not_available)

            assert(total == optimized_out | available | not_available | missing)

            if len(total) == 0:
                continue

            optimized_out = float(len(optimized_out)) / len(total)
            available = float(len(available)) / len(total)
            not_available = float(len(not_available)) / len(total)
            missing = float(len(missing)) / len(total)

            total = optimized_out + available + not_available + missing

            result[line] = list(map(lambda x: x / total, [available, missing, optimized_out, not_available]))

            lines_opt += 1

    if len(result) == 0:
        return {}

    lines_ratio = float(lines_opt) / lines_unopt

    # sum all the values
    out = {'available': 0, 'missing': 0, 'optimized_out': 0, 'not_available': 0}
    for line in result:
        out['available'] += result[line][0]
        out['missing'] += result[line][1]
        out['optimized_out'] += result[line][2]
        out['not_available'] += result[line][3]

    # calculate avg and multiply by ratio
    out['available'] /= len(result)
    out['missing'] /= len(result)
    out['optimized_out'] /= len(result)
    out['not_available'] /= len(result)

    total = out['available'] + out['missing'] + out['optimized_out'] + out['not_available']

    # normalize to 1
    out['available'] /= total
    out['missing'] /= total
    out['optimized_out'] /= total
    out['not_available'] /= total

    out['lines_ratio'] = lines_ratio
    return out


def percentage_per_testcase(testcases, args, compiler):

    jsons = []
    for i in range(testcases['computed_testcases']):
        testcase_dir = os.path.join(args.indir, str(i))
        testcase_file = os.path.join(testcase_dir, 'testcase.json')
        with open(testcase_file) as f:
            jsons.append(json.load(f))
        break

    total = []
    for i, testcase in enumerate(jsons):
        results = {}

        cc = ['clang', 'gcc']['gcc' in compiler]
        lines_filter = get_lines_filter(os.path.join(args.indir, f'{i}/src/{cc}/a.c'))

        err = False
        for opt_level in ['1', '2', '3', 'g', 's']:
            if compiler not in testcase['trace']:
                break

            live_variables = testcase['trace'][compiler]['live_variables'] 
            if not opt_level in live_variables or live_variables[opt_level] == 'ERROR' or live_variables['0'] == 'ERROR':
                err = True
                break

            results[opt_level] = get_vars_diff_per_line(live_variables, opt_level, compiler, lines_filter)
            if len(results[opt_level]) == 0:
                err = True
                break

        if err or len(results) == 0:
            err = False
            continue

        total.append(results)
    
    return total

def percentage_per_optlevel(testcases, args, compiler):

    total = percentage_per_testcase(testcases, args, compiler)

    hist = {}
    for opt_level in ['1', '2', '3', 'g', 's']:
        hist[opt_level] = {'lines_ratio': 0, 'available': 0, 'missing': 0, 'optimized_out': 0, 'not_available': 0}
        for key in hist[opt_level]:
            hist[opt_level][key] += sum(map(lambda x: x[opt_level][key], total))
            hist[opt_level][key] /= len(total)
    
    for opt_level in ['1', '2', '3', 'g', 's']:
        if hist[opt_level]:
            log_info(f'At -O{opt_level}: ')
            log_info(f'\tAvailable variables:     \t{hist[opt_level]["available"]:.4f}')
            log_info(f'\tMissing variables:       \t{hist[opt_level]["missing"]:.4f}')
            log_info(f'\tOptmized out variables:  \t{hist[opt_level]["optimized_out"]:.4f}')
            log_info(f'\tNot Available variables: \t{hist[opt_level]["not_available"]:.4f}')
            log_info(f'\tLines Ratio:             \t{hist[opt_level]["lines_ratio"]:.4f}')

    return hist

def main(args):
    log_info(f'Metrics computation: STARTING')

    if not os.path.exists(args.indir):
        log_info(f'[-] Directory `{args.indir}` does not exists')
        exit(1)

    testcases_json = os.path.join(args.indir, 'testcases.json')
    testcases = {}
    if os.path.exists(args.indir):
        with open(testcases_json) as f:
            testcases = json.load(f)
    else:
        log_info(f'[-] Could not find `testcases.json` file inside `{args.indir}`')
        exit(1)

    log_debug(f'[+] Found {testcases["computed_testcases"]} to be computed')

    if args.gcc:
        gcc_version = 'gcc' if not args.gcc_version else 'gcc%s' % args.gcc_version
        stats = percentage_per_optlevel(testcases, args, gcc_version)
        testcases['statistics'][gcc_version] = stats
    elif args.clang:
        clang_version = 'clang' if not args.clang_version else 'clang%s' % args.clang_version
        stats = percentage_per_optlevel(testcases, args, clang_version)
        testcases['statistics'][clang_version] = stats

    with open(testcases_json, 'w') as f:
        json.dump(testcases, f)

    log_info(f'Metrics computation: COMPLETED')


if __name__ == '__main__':

    parser = ArgumentParser(description = 'Get statistics about live variables per line')

    parser.add_argument('--indir', dest = 'indir', type = str, help = 'Input directory (default = `./testcases`)', default = 'testcases')
    parser.add_argument('--debug', dest = 'debug', action='store_true', help='Enable debug prints', default = False)
    parser.add_argument('--gcc', dest = 'gcc', action='store_const', help = 'Get statistics about GCC binaries using GDB (default = `enabled`)', default = 0, const = 1)
    parser.add_argument('--gcc-version', dest = 'gcc_version', type = str, help = 'GCC versions to be tested (default = `trunk`)', default = '')
    parser.add_argument('--clang', dest = 'clang', action='store_const', help = 'Get statistics about CLANG binaries using LLDB (default = `disabled`)', default = 0, const = 1)
    parser.add_argument('--clang-version', dest = 'clang_version', type = str, help = 'CLANG versions to be tested (default = `trunk`)', default = '')

    args = parser.parse_args()

    log_init(args)
    
    main(args)
