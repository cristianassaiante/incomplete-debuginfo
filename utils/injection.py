import os
import sys
import random

from pathlib import Path
sys.path.append(os.path.join(Path(__file__).resolve().parent, '..'))

from utils.run import *
from utils.log import *
from utils.checker import *


PROTO_FMT = """void c1_func(%s);
"""

FUNCT_FMT = """ 
void c1_func(%s) {
    %s
}"""

PRINTF_FMT = "printf(\"%s\\n\", %s);"

def generate_module(location, trace, source_lines):
    tmpnames = trace[location]['available']

    bl = find_pointers(source_lines)
    names = [var for var in tmpnames if var not in bl]

    types = ['int' for _ in names]

    decls = [a + ' ' + b for (a, b) in zip(types, names)]

    types_fmt = ['%p' for t in types]

    # prototype
    proto = PROTO_FMT % ', '.join(decls)

    # source
    func = FUNCT_FMT % (
            ', '.join(decls),
            PRINTF_FMT % (
                    ' '.join(types_fmt),
                    ', '.join(names)
                )
        )

    call = PROTO_FMT[5:] % ', '.join(names)

    return func, call, proto, names

def propagate_call(source_lines, out_lines): 
    
    idx = None
    for i, line in enumerate(source_lines):
        if 'c1_func' in line and not 'void' in line:
            for j, linej in enumerate(out_lines):
                if source_lines[i - 1].lstrip() == linej.lstrip() and source_lines[i + 1].lstrip() == out_lines[j + 1].lstrip():
                    idx = j + 1
                    break
            if idx:
                break
    return idx