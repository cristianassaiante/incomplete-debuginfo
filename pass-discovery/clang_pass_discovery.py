import os
import sys
import json
import tempfile
import shutil
from multiprocessing import Pool
from subprocess import *
from argparse import ArgumentParser

from checkers import c1_checker, c2_checker, c3_checker

from pathlib import Path
sys.path.append(os.path.join(Path(__file__).resolve().parent, '..'))

from utils.log import *
from utils.run import *

# ARGS: path to framework - compiler - output - source_file - lib_file - opt_level - extra
CC_C1 = '%s/pass-discovery/utils/c1_compile.sh %s %s %s %s %s %s'
# ARGS: path to framework - compiler - output - source_file - opt_level - extra
CC = '%s/pass-discovery/utils/compile.sh %s %s %s %s %s'

def pass_discovery(testcaseid, args):
    
    testcase_dir = os.path.join(args.indir, str(testcaseid))

    testcase_json = os.path.join(testcase_dir, 'testcase.json')
    with open(testcase_json) as f:
        testcase_info = json.load(f)

    if 'clang' not in testcase_info['violations'] or args.conj not in testcase_info['violations']['clang']:
        return

    checkers = {'C1': c1_checker, 'C2': c2_checker, 'C3': c3_checker}
    conjecture_checker = checkers[args.conj]

    tdir = tempfile.TemporaryDirectory()
    tmpdir = tdir.name
    tmpsrcpath = os.path.join(tmpdir, 'a.c')
    if args.conj == 'C1':
        tmplibpath = os.path.join(tmpdir, 'lib.c')
        srcpath = os.path.join(testcase_dir, 'src/clang/call/a.c')
        libpath = os.path.join(testcase_dir, 'src/clang/call/lib.c')
        shutil.copyfile(srcpath, tmpsrcpath)
        shutil.copyfile(libpath, tmplibpath)
    else:
        srcpath = os.path.join(testcase_dir, 'src/clang/a.c')
        shutil.copyfile(srcpath, tmpsrcpath)

    for violation in testcase_info['violations']['clang'][args.conj]:

        if 'pass' in testcase_info['violations']['clang'][args.conj][violation] and 'pass_name' in testcase_info['violations']['clang'][args.conj][violation]:
            continue

        opt_level = testcase_info['violations']['clang'][args.conj][violation]['opt_level'][0]

        # find max_limit
        out_file = os.path.join(tmpdir, 'opt')
        source_file = os.path.join(tmpdir, 'a.c')
        if args.conj == 'C1':
            lib_file = os.path.join(tmpdir, 'lib.c')
            bisect_out = run_cmd(CC_C1 % (args.path, 'clang', out_file, source_file, lib_file, opt_level, '0'), get_err = True)
        else:
            bisect_out = run_cmd(CC % (args.path, 'clang', out_file, source_file, opt_level, '0'), get_err = True)
        bisect_out = list(filter(lambda x: 'BISECT' in x, bisect_out.split('\n')))

        min_limit = 0
        max_limit = len(bisect_out)

        mid_limit = (max_limit + min_limit) // 2

        # pass discovery via binary search
        while min_limit != max_limit - 1:
            
            log_debug(f'[{testcaseid}] Testing violation with bisect-limit = {mid_limit}')

            if args.conj == 'C1':
                new_violations = conjecture_checker(args, tmpdir, 'clang', opt_level, str(testcase_info['call_injection']['clang'] + 1), testcase_info['call_injection']['vars'], limit = str(mid_limit))
            else:
                new_violations = conjecture_checker(args, tmpdir, 'clang', opt_level, limit = str(mid_limit))

            if not violation in new_violations:
                min_limit = mid_limit
            else:
                max_limit = mid_limit

            mid_limit = (max_limit + min_limit) // 2

        # find pass name
        out_file = os.path.join(tmpdir, 'opt')
        source_file = os.path.join(tmpdir, 'a.c')
        if args.conj == 'C1':
            lib_file = os.path.join(tmpdir, 'lib.c')
            bisect_out = run_cmd(CC_C1 % (args.path, 'clang', out_file, source_file, lib_file, opt_level, '0'), get_err = True)
        else:
            bisect_out = run_cmd(CC % (args.path, 'clang', out_file, source_file, opt_level, '0'), get_err = True)
        bisect_out = list(filter(lambda x: 'BISECT' in x, bisect_out.split('\n')))
        pass_name = bisect_out[min_limit].split(')', 1)[1].split('(')[0].strip()

        testcase_info['violations']['clang'][args.conj][violation]['pass'] = min_limit
        testcase_info['violations']['clang'][args.conj][violation]['pass_name'] = pass_name

        log_info(f'[{testcaseid}] Found culprit pass: {min_limit} -> {pass_name}')

    tdir.cleanup()

def main(args):
    log_info(f'CLANG Pass Discovery: STARTING')

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
            pool.apply_async(func = pass_discovery, args = (i, args))
        else:
            pass_discovery(i, args)
    pool.close()
    pool.join()

    log_info(f'CLANG Pass Discovery: COMPLETED')

if __name__ == '__main__':

    parser = ArgumentParser(description = 'CLANG Pass Discovery')

    parser.add_argument('--indir', dest = 'indir', type = str, help = 'Input directory (default = `./testcases`)', default = 'testcases')
    parser.add_argument('--path', dest = 'path', type = str, help = 'Path to framework', required = True)
    parser.add_argument('--proc', dest = 'proc', type = int, help = 'Number of processes to use', default = 1)
    parser.add_argument('--conj', dest = 'conj', type = str, help = 'Conjecture to be tested', required = True)
    parser.add_argument('--debug', dest = 'debug', action='store_true', help='Enable debug prints (only when `nproc` is set to `1`)', default = False)

    args = parser.parse_args()

    log_init(args)

    main(args)