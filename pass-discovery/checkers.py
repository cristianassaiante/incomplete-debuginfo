import os
import sys
import re
from subprocess import *

from pathlib import Path
sys.path.append(os.path.join(Path(__file__).resolve().parent, '..'))

from utils.run import *
from utils.tracer import *
from utils.checker import *


# ARGS: path to framework - compiler - output - source_file - lib_file - opt_level - extra
CC_C1 = '%s/pass-discovery/utils/c1_compile.sh %s %s %s %s %s %s'
# ARGS: path to framework - compiler - output - source_file - opt_level - extra
CC = '%s/pass-discovery/utils/compile.sh %s %s %s %s %s'


def c1_checker(args, testcase_dir, cc, opt_level, call_site, call_vars, flags = None, limit = None):

    out_file = os.path.join(testcase_dir, 'opt')
    source_file = os.path.join(testcase_dir, 'a.c')
    lib_file = os.path.join(testcase_dir, 'lib.c')
    extra = flags if not limit else limit
    run_cmd(CC_C1 % (args.path, cc, out_file, source_file, lib_file, opt_level, extra))

    out_file = out_file + ('-%s' % opt_level)

    dbg = ['lldb', 'gdb'][cc == 'gcc']
    variables = get_traced_variables(out_file, dbg)[call_site]
    
    call_vars = set(call_vars)
    available = set(variables['available']) & call_vars
    not_and_opt = (set(variables['not_available']) | set(variables['optimized_out'])) & call_vars
    missing = call_vars - (available | not_and_opt)

    tmp_violations = list(not_and_opt | missing)

    violations = {}
    for var in tmp_violations:
        violation = {'line': call_site}
        violations[var] = violation

    return violations

def c2_checker(args, testcase_dir, cc, opt_level, flags = None, limit = None):

    def verify(expr, live):
        violation = {}
        if not live.issuperset(expr):
            violation = {
                        "expr": list(expr),
                        "live": list(live),
                        "mism": list(expr - live)
                }

        return violation

    out_file = os.path.join(testcase_dir, 'opt')
    source_file = os.path.join(testcase_dir, 'a.c')
    extra = flags if not limit else limit
    run_cmd(CC % (args.path, cc, out_file, source_file, opt_level, extra))

    with open(source_file) as f:
        source_lines = f.readlines()

    out_file = out_file + ('-%s' % opt_level)

    dbg = ['lldb', 'gdb'][cc == 'gcc']
    trace_opt = get_traced_variables(out_file, dbg)

    violations = {}
    for line in trace_opt:
            source_line = source_lines[int(line) - 1].strip()

            if '{' in source_line or '}' in source_line:
                continue

            if not re.match('(\w+)\s*=.*$', source_line.strip()):
                continue

            if source_line.count('=') > 1:
                continue

            expr, live = parse_expression_variables(source_line, trace_opt[line])

            violation = verify(expr, live)
            if violation:
                var = source_line.split(' = ')[0].split()
                if 'int' in var[0]:
                    var = var[1].replace('*', '')
                else:
                    var = var[0].replace('*', '')

                # check if lhs is global memory
                if not (var.startswith('g') or 'sink' in var):
                    continue

                violations[line] = violation
  
    return violations

def c3_checker(args, testcase_dir, cc, opt_level, flags = None, limit = None):
    
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

    out_file = os.path.join(testcase_dir, 'opt')
    source_file = os.path.join(testcase_dir, 'a.c')
    extra = flags if not limit else limit
    run_cmd(CC % (args.path, cc, out_file, source_file, opt_level, extra))

    with open(source_file) as f:
        source_lines = f.readlines()

    out_file = out_file + ('-%s' % opt_level)
    
    dbg = ['lldb', 'gdb'][cc == 'gcc']
    trace_opt = get_traced_variables(out_file, dbg)

    violations = {}
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

                    # var is a violation
                    violation = verify(var, line, prev_line, source_lines)
                    if violation:
                        violations[var] = violation
    
    return violations

def cX_checker(args, testcase_dir, cc, opt_level, flags = None, limit = None):

    out_file = os.path.join(testcase_dir, 'opt')
    source_file = os.path.join(testcase_dir, 'a.c')
    extra = flags if not limit else limit
    run_cmd(CC % (args.path, cc, out_file, source_file, opt_level, extra))

    with open(source_file) as f:
        source_lines = f.readlines()

    out_file = out_file + ('-%s' % opt_level)
    
    dbg = ['lldb', 'gdb'][cc == 'gcc']
    variables = get_traced_variables(out_file, dbg)

    violations = {}

    # TODO
    # add here your checker, it should have the same logic as its offline version)

    return violations