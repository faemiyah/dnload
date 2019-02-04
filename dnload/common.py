import os
import re
import subprocess

########################################
# Globals ##############################
########################################

g_temporary_directory = None
g_verbose = False

IGNORE_PATHS = ("/lib/modules",)

########################################
# Functions ############################
########################################

def executable_check(op):
    """Check for existence of a single binary."""
    try:
        proc = subprocess.Popen([op], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError:
        return False
    try:
        if not proc.poll():
            proc.kill()
            proc.wait()
    except OSError:
        print("WARNING: subprocess '%s' did not terminate properly" % (op))
        return True
    return True

def executable_find(proposition, default_list, name):
    """Try to find given executable from proposition and default list."""
    if proposition:
        if not executable_check(proposition):
            raise RuntimeError("could not use supplied '%s' executable '%s'" % (name, proposition))
        return proposition
    ret = executable_search(default_list, name)
    if not ret:
        raise RuntimeError("suitable '%s' executable not found" % (name))
    return ret

def executable_search(op, description=None):
    """Check for existence of binary, everything within the list will be tried."""
    checked = []
    ret = None
    if is_listing(op):
        for ii in op:
            if ii not in checked:
                if executable_check(ii):
                    ret = ii
                    break
                else:
                    checked += [ii]
    elif isinstance(op, str):
        if op not in checked:
            if executable_check(op):
                ret = op
            checked += [op]
    else:
        raise RuntimeError("weird argument given to executable search: %s" % (str(op)))
    if description and is_verbose():
        output_message = "Looking for '%s' executable... " % (description)
        if ret:
            print("%s'%s'" % (output_message, ret))
        else:
            print("%snot found" % (output_message))
    return ret


def file_is_ascii_text(op):
    """Check if given file contains nothing but ASCII7 text."""
    if not os.path.isfile(op):
        return False
    fd = open(op, "rb")
    while True:
        line = fd.readline()
        if 0 >= len(line):
            fd.close()
            return True
        try:
            line.decode("ascii")
        except UnicodeDecodeError:
            fd.close()
            return False

def get_indent(op):
    """Get indentation for given level."""
    ret = ""
    for ii in range(op):
        # Would tab be better?
        ret += "  "
    return ret

def is_listing(op):
    """Tell if given parameter is a listing."""
    return isinstance(op, (list, tuple))

def is_verbose():
    """Tell if verbose mode is on."""
    return g_verbose

def labelify(op):
    """Take string as input. Convert into string that passes as label."""
    return re.sub(r'[\/\.]', '_', op)

def listify(lhs, rhs=None):
    """Make a list of one or two elements if reasonable."""
    if (lhs is None) and (rhs is None):
        return []
    if lhs is None:
        if is_listing(rhs):
            return rhs
        return [rhs]
    if rhs is None:
        if is_listing(lhs):
            return lhs
        return [lhs]
    if is_listing(lhs) and is_listing(rhs):
        return lhs + rhs
    if is_listing(lhs):
        return lhs + [rhs]
    if is_listing(rhs):
        return [lhs] + rhs
    return [lhs, rhs]

def locate(pth, fn, previous_paths=None):
    """Search for given file from given path downward."""
    if is_listing(pth):
        for ii in pth:
            ret = locate(ii, fn, previous_paths)
            if ret:
                return ret
        return None
    # If path is not given or is empty, assume current path.
    if not pth:
        pth = "."
    # Initialize previous paths on first execution.
    if not previous_paths:
        previous_paths = [os.path.realpath(pth)]
    # Some specific directory trees would take too much time to traverse.
    if pth in IGNORE_PATHS:
        return None
    # Recurse, expect filesystem errors.
    try:
        for ii in os.listdir(pth):
            ret = os.path.normpath(pth + "/" + ii)
            if (isinstance(fn, str) and (ii == fn)) or ((not isinstance(fn, str)) and fn.match(ii)):
                return ret
            elif os.path.isdir(ret):
                real_path = os.path.realpath(ret)
                if real_path not in previous_paths:
                    ret = locate(ret, fn, previous_paths + [real_path])
                    if ret:
                        return ret
    except OSError as ee:  # Permission denied or the like.
        if 13 == ee.errno:
            return None
        raise ee
    return None

def generate_temporary_filename(fname):
    """Generates a temporary filename for given filename."""
    if g_temporary_directory:
        return g_temporary_directory + "/" + os.path.basename(fname)
    return fname

def run_command(lst, decode_output=True):
    """Run program identified by list of command line parameters."""
    if is_verbose():
        print("Executing command: %s" % (" ".join(lst)))
    proc = subprocess.Popen(lst, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (proc_stdout, proc_stderr) = proc.communicate()
    if decode_output and not isinstance(proc_stdout, str):
        proc_stdout = proc_stdout.decode()
    if decode_output and not isinstance(proc_stderr, str):
        proc_stderr = proc_stderr.decode()
    returncode = proc.returncode
    if 0 != proc.returncode:
        raise RuntimeError("command failed: %i, stderr output:\n%s" % (proc.returncode, proc_stderr))
    return (proc_stdout, proc_stderr)

def set_temporary_directory(op):
    """Sets temporary directory."""
    global g_temporary_directory
    if (not op) or (not os.path.isdir(op)):
        return False
    g_temporary_directory = os.path.normpath(op)
    return True

def set_verbose(op):
    """Set verbosity status."""
    global g_verbose
    g_verbose = op
