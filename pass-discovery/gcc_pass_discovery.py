import os
import sys
import json
import tempfile
import shutil
from multiprocessing import Pool
from subprocess import *
from argparse import ArgumentParser

from checkers import c1_checker, c2_checker, c3_checker
from gcc_enabled_opts import enabled_opts

from pathlib import Path
sys.path.append(os.path.join(Path(__file__).resolve().parent, '..'))

from utils.log import *
from utils.run import *

def pass_discovery(testcaseid, args):
    
    testcase_dir = os.path.join(args.indir, str(testcaseid))

    testcase_json = os.path.join(testcase_dir, 'testcase.json')
    with open(testcase_json) as f:
        testcase_info = json.load(f)

    if 'gcc' not in testcase_info['violations'] or args.conj not in testcase_info['violations']['gcc']:
        return

    checkers = {'C1': c1_checker, 'C2': c2_checker, 'C3': c3_checker}
    conjecture_checker = checkers[args.conj]

    tdir = tempfile.TemporaryDirectory()
    tmpdir = tdir.name
    tmpsrcpath = os.path.join(tmpdir, 'a.c')
    if args.conj == 'C1':
        tmplibpath = os.path.join(tmpdir, 'lib.c')
        srcpath = os.path.join(testcase_dir, 'src/gcc/call/a.c')
        libpath = os.path.join(testcase_dir, 'src/gcc/call/lib.c')
        shutil.copyfile(srcpath, tmpsrcpath)
        shutil.copyfile(libpath, tmplibpath)
    else:
        srcpath = os.path.join(testcase_dir, 'src/gcc/a.c')
        shutil.copyfile(srcpath, tmpsrcpath)

    for violation in testcase_info['violations']['gcc'][args.conj]:
        optset = set()
        opt_level = testcase_info['violations']['gcc'][args.conj][violation]['opt_level'][0]
        for opt in enabled_opts[opt_level]:

            log_debug(f'[{testcaseid}] Testing violation with {opt}')

            if args.conj == 'C1':
                new_violations = conjecture_checker(args, tmpdir, 'gcc', opt_level, str(testcase_info['call_injection']['gcc'] + 1), testcase_info['call_injection']['vars'], flags = opt)
            else:
                new_violations = conjecture_checker(args, tmpdir, 'gcc', opt_level, flags = opt)

            if not violation in new_violations:
                log_debug(f'[{testcaseid}] Found culprit flag: {opt}')
                optset.add(opt)
        
        testcase_info['violations']['gcc'][args.conj][violation]['pass'] = optset
        log_info(f"[{testcaseid}] Found culprit flag(s): {testcase_info['violations']['gcc'][args.conj][violation]['pass']}")

    tdir.cleanup()

    with open(testcase_json, 'w') as f:
        json.dump(testcase_info, f)


def main(args):
    log_info(f'GCC Pass Discovery: STARTING')

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

    log_info(f'GCC Pass Discovery: COMPLETED')

if __name__ == '__main__':

    parser = ArgumentParser(description = 'GCC Pass Discovery')

    parser.add_argument('--indir', dest = 'indir', type = str, help = 'Input directory (default = `./testcases`)', default = 'testcases')
    parser.add_argument('--path', dest = 'path', type = str, help = 'Path to framework', required = True)
    parser.add_argument('--proc', dest = 'proc', type = int, help = 'Number of processes to use', default = 1)
    parser.add_argument('--conj', dest = 'conj', type = str, help = 'Conjecture to be tested', required = True)
    parser.add_argument('--debug', dest = 'debug', action='store_true', help='Enable debug prints (use only when `proc=1`)', default = False)

    args = parser.parse_args()

    log_init(args)

    main(args)