from subprocess import *

def run_cmd(cmd, debug = False, get_output = False, get_err = False):
    r = None
    try:
        if debug:
            r = run(cmd.split(), timeout = 100)
            r.check_returncode()
        elif get_output:
            r = run(cmd.split(), stdout = PIPE, stderr = PIPE, timeout = 100)
            return r.stdout.decode()
        elif get_err:
            r = run(cmd.split(), stdout = PIPE, stderr = PIPE, timeout = 100)
            return r.stderr.decode()
        else:
            r = run(cmd.split(), stdout = DEVNULL, stderr = DEVNULL, timeout = 100)
            r.check_returncode()
    except (CalledProcessError, TimeoutExpired):
        if r == None:
            return 1
        if r.returncode == 254:
            return 2
        return 1
    return 0