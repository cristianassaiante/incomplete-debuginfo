import os
import sys
import random
import tempfile


from pathlib import Path
sys.path.append(os.path.join(Path(__file__).resolve().parent, '..'))

from utils.run import *
from utils.log import *


# ARGS: binary
DWARF = 'llvm-dwarfdump --debug-line %s'
# ARGS: dbg_script_path - binary
GDB = 'gdb -q -x %s %s'
LLDB = 'lldb -s %s %s'


GDB_SCRIPT_TEMPLATE = """python gdb.events.exited.connect(lambda x : gdb.execute("quit"))
set pagination off
set style enabled off

%s

run
quit
"""

GDB_BP_TEMPLATE = """tbreak %d
commands
    info locals    
    continue
end
"""

LLDB_SCRIPT_TEMPLATE = """%s

run
quit
"""

LLDB_BP_TEMPLATE = """tbreak %d
break command add %d
    frame info
    frame var
    continue
DONE
"""


def get_lines(binary):
    lines = set()
    output = run_cmd(DWARF % (binary), get_output = True)
    for line in output.split('\n'):
        if len(line.strip().split()) < 2:
            continue
        if 'is_stmt' not in line.strip().split()[-1].strip():
            continue
        line = line.strip().split()[1].strip()
        if line.isnumeric():
            lines.add(int(line))
    if 0 in lines:
        lines.remove(0)
    return list(lines)

def run_dbg(binary, dbg_script, dbg):

    output = ''

    cmd = [GDB, LLDB][dbg == 'lldb']

    with tempfile.TemporaryDirectory() as tmpdir:    

        tmpfile = str(random.randint(0, 2**32)) + '.dbg'
        with open(os.path.join(tmpdir, tmpfile), 'w') as f:
            f.write(dbg_script)

        output = run_cmd(cmd % (os.path.join(tmpdir, tmpfile), binary), get_output = True)

    return output

def get_variables_from_trace(trace, dbg):

    output = {}

    current_line = None
    for line in trace.split('\n'):
        line = line.strip()
        
        if dbg == 'gdb':

            if 'No locals' in line or 'Inferior' in line or 'Temporary' in line or 'Reading' in line or len(line.split()) == 0:
                continue

            line_no = line.split()[0]
            if line_no.isnumeric():
                current_line = line_no
                output[current_line] = {'available': [], 'optimized_out': [], 'not_available': []}
                continue

            if current_line and ' = ' in line:
                var_name = line.split(' = ')[0]
                value = line.split(' = ')[-1]
                if '<optimized out>' in value:
                    output[current_line]['optimized_out'].append(var_name)
                else:
                    output[current_line]['available'].append(var_name)

        else:

            if 'lldb' in line or 'Current' in line or 'Breakpoint' in line or 'Process' in line or 'Command' in line or len(line.split()) == 0:
                continue
            if line.startswith('[') or line.startswith('*'):
                continue

            line_no = line.split()[-1]
            if ':' in line_no:
                line_no = line_no.split(':')[-2]
                current_line = line_no
                output[current_line] = {'available': [], 'optimized_out': [], 'not_available': []}
                continue

            if current_line and ' = ' in line:
                var_name = line.split(' = ')[0]
                if var_name.startswith('('):
                    var_name = var_name.split(')')[1].rstrip().lstrip()
                value = line.split(' = ')[-1].rstrip().lstrip()
                if 'optimized out' in value:
                    output[current_line]['optimized_out'].append(var_name)
                elif 'not available' in value:
                    output[current_line]['not_available'].append(var_name)
                else:
                    output[current_line]['available'].append(var_name)

    for line in output:
        output[line]['optimized_out'] = list(set(output[line]['optimized_out']))
        output[line]['available'] = list(set(output[line]['available']))

        for var in output[line]['available']:
            if var in output[line]['optimized_out']:
                output[line]['optimized_out'].remove(var)
            if var in output[line]['not_available']:
                output[line]['not_available'].remove(var)

    return output

def get_traced_variables(binary, dbg):
    lines = get_lines(binary)

    script_template = [GDB_SCRIPT_TEMPLATE, LLDB_SCRIPT_TEMPLATE][dbg == 'lldb']

    if dbg == 'lldb':
        bps = [LLDB_BP_TEMPLATE % (line, i + 1) for i, line in enumerate(lines)]
    else:
        bps = [GDB_BP_TEMPLATE % line for line in lines]
    dbg_script = script_template % ''.join(bps)

    trace = run_dbg(binary, dbg_script, dbg)

    return get_variables_from_trace(trace, dbg)
    