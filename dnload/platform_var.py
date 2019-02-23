import platform
import re

from dnload.common import is_verbose

########################################
# PlatformVar ##########################
########################################

class PlatformVar:
    """Platform-dependent variable."""

    def __init__(self, name):
        """Initialize platform variable."""
        self.__name = name

    def get(self):
        """Get value associated with the name."""
        if self.__name not in g_platform_variables:
            raise RuntimeError("unknown platform variable '%s'" % (self.__name))
        current_var = g_platform_variables[self.__name]
        combinations = get_platform_combinations()
        for ii in combinations:
            if ii in current_var:
                return current_var[ii]
        raise RuntimeError("current platform %s not supported for variable '%s'" % (str(combinations), self.__name))

    def deconstructable(self):
        """Tell if this platform value can be deconstructed."""
        return isinstance(self.get(), int)

    def __int__(self):
        """Convert to integer."""
        ret = self.get()
        if not isinstance(ret, int):
            raise ValueError("not an integer platform variable")
        return ret

    def __str__(self):
        """String representation."""
        ret = self.get()
        if isinstance(ret, int):
            return "0x%x" % (ret)
        return ret

########################################
# Globals ##############################
########################################

def determine_platform():
    """Determines the current platform."""
    (osname, _, osrelease, osversion, osarch, _) = platform.uname()
    # Linux distributions may have more accurate rules than just being Linux.
    if re.search(r'(arch|manjaro|antergos)', osversion + osarch, re.I):
        osname = "Arch"
    return (osname, osarch)

# Get actual platform names.
(g_osname, g_osarch) = determine_platform()

g_platform_mapping = {
    "amd64": "64-bit",
    "arch": "Arch",
    "Arch": "Linux",
    "arm32l": "32-bit",
    "armv6l": "arm32l",
    "armv7l": "arm32l",
    "freebsd": "FreeBSD",
    "i386": "ia32",
    "i686": "ia32",
    "ia32": "32-bit",
    "linux": "Linux",
    "x86_64": "amd64",
    }

g_platform_variables = {
    "addr": {"32-bit": 4, "64-bit": 8},
    "align": {"32-bit": 4, "64-bit": 8, "amd64": 1, "ia32": 1},
    "bom": {"amd64": "<", "arm32l": "<", "ia32": "<"},
    "compression": {"default": "lzma"},
    "e_flags": {"default": 0, "arm32l": 0x5000402},
    "e_machine": {"amd64": 62, "arm32l": 40, "ia32": 3},
    "ei_class": {"32-bit": 1, "64-bit": 2},
    "ei_osabi": {"FreeBSD": 9, "Linux-arm32l": 0, "Linux": 3},
    "entry": {"64-bit": 0x400000, "armv6l": 0x10000, "armv7l": 0x8000, "ia32": 0x2000000},  # ia32: 0x8048000
    "function_rand": {"default": None},
    "function_srand": {"default": None},
    "gl_library": {"default": "GL"},
    "interp": {"FreeBSD": "\"/libexec/ld-elf.so.1\"", "Linux-arm32l": "\"/lib/ld-linux.so.3\"", "Linux-ia32": "\"/lib/ld-linux.so.2\"", "Linux-amd64": "\"/lib64/ld-linux-x86-64.so.2\""},
    "march": {"amd64": "core2", "armv6l": "armv6t2", "armv7l": "armv7", "ia32": "pentium4"},
    "memory_page": {"32-bit": 0x1000, "64-bit": 0x200000},
    "mpreferred-stack-boundary": {"arm32l": 0, "ia32": 2, "64-bit": 4},
    "phdr_count": {"default": 3},
    "shelldrop_header": {"Arch": "!/bin/sh\n", "default": ""},
    "shelldrop_tail": {"Arch": "sed 1,2d", "default": "sed 1d"},
    "start": {"default": "_start"},
    }

########################################
# Functions ############################
########################################

def get_platform_combinations():
    """Get listing of all possible platform combinations matching current platform."""
    # Gather operating system name path.
    mapped_osname = platform_map_iterate(g_osname.lower())
    osnames = []
    while mapped_osname:
        osnames += [mapped_osname]
        mapped_osname = platform_map_iterate(mapped_osname)
    # Gather operating system architecture path.
    mapped_osarch = g_osarch
    osarchs = []
    while mapped_osarch:
        osarchs += [mapped_osarch]
        mapped_osarch = platform_map_iterate(mapped_osarch)
    # Get permutations.
    ret = []
    for ii in osnames:
        for jj in osarchs:
            ret += ["%s-%s" % (ii, jj)]
    return ret + osnames + osarchs + ["default"]

def osarch_is_32_bit():
    """Check if the architecture is 32-bit."""
    return osarch_match("32-bit")

def osarch_is_64_bit():
    """Check if the architecture is 32-bit."""
    return osarch_match("64-bit")

def osarch_is_amd64():
    """Check if the architecture maps to amd64."""
    return osarch_match("amd64")

def osarch_is_ia32():
    """Check if the architecture maps to ia32."""
    return osarch_match("ia32")

def osarch_match(op):
    """Check if osarch matches some chain resulting in given value."""
    arch = g_osarch
    while True:
        if op == arch:
            return True
        arch = platform_map_iterate(arch)
        if not arch:
            break
    return False

def platform_map_iterate(op):
    """Follow platform mapping chain once."""
    if op in g_platform_mapping:
        return g_platform_mapping[op]
    return None

def platform_map(op):
    """Follow platform mapping chain as long as possible."""
    while True:
        found = platform_map_iterate(op)
        if not found:
            break
        op = found
    return op

def replace_osarch(repl_osarch, reason):
    """Replace osarch with given string."""
    global g_osarch
    if g_osarch == repl_osarch:
        return
    if is_verbose():
        print("%stargeting osarch '%s' instead of '%s'" % (reason, repl_osarch, g_osarch))
    g_osarch = repl_osarch

def replace_osname(repl_osname, reason):
    """Replace osname with given string."""
    global g_osname
    if g_osname == repl_osname:
        return
    if is_verbose():
        print("%stargeting osname '%s' instead of '%s'" % (reason, repl_osname, g_osname))
    g_osname = repl_osname

def replace_platform_variable(name, op):
    """Destroy platform variable, replace with default."""
    if name not in g_platform_variables:
        raise RuntimeError("trying to destroy nonexistent platform variable '%s'" % (name))
    g_platform_variables[name] = {"default": op}
