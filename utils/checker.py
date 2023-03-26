import re

# C3 
def get_functions(source_lines):
    functions = []
    found = False
    par = 0
    for i, l in enumerate(source_lines):
        if '{' in l:
            if not found:
                found = True
                functions.append([i + 1])
                par += 1
            else:
                par += 1

        if '}' in l:
            par -= 1
            if par == 0:
                found = False
                functions[-1].append(i + 1)
    return functions

def get_function_from_line(source_lines, line):
    functions = get_functions(source_lines)
    lineno = int(line)
    for f in functions:
        if lineno > f[0] and lineno <= f[1]:
            return f
    return None

def var_is_from_func(var, line, source_lines):
    func = get_function_from_line(source_lines, line)

    decl_line = None
    for i, l in enumerate(source_lines):
        if var in l:
            decl_line = i + 1
            break
    func_decl = get_function_from_line(source_lines, decl_line)

    return func == func_decl

def is_previous_first_decl(var, prev_line, source_lines):
    decl_line = None
    for i, l in enumerate(source_lines):
        if var in l:
            decl_line = i + 1
            break

    return decl_line > int(prev_line)

# C2
def parse_expression_variables(line, trace):
    expr = re.findall('(\w+)\s*=(.*)$', line.strip())[0][1]
    expr_vars = re.findall('[^\w]([l]_[0-9]{1,3})[^\w]', expr)
    expr_vars += re.findall('[^\w]([ijk])[^\w]', expr)

    return set(expr_vars), set(trace['available'])

# C1
def find_pointers(source_lines):
    ptrs = []
    for line in source_lines:
        if ('int' in line.split(' = ')[0] and ' = ' in line and not 'print' in line) or ('int' in line and ' = ' not in line and '[' in line):
            varname = line.split(' = ')[0].rsplit(' ', 1)[1]
            found = '*' in varname or '[' in varname
            varname = re.findall('l_[0-9]+', varname)

            if len(varname) == 0: continue
            varname = varname[0]
            
            if found:
                ptrs.append(varname)
    return ptrs