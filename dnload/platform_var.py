import platform
import re

from dnload.common import is_verbose

########################################
# PlatformVar ##########################
########################################

class PlatformVar:
    """Platform-dependent variable."""

    def __init__(self, name, osname = None, osarch = None):
        """Initialize platform variable."""
        self.__name = name
        self.__osname = osname
        self.__osarch = osarch

    def get(self):
        """Get value associated with the name."""
        if self.__name not in g_platform_variables:
            raise RuntimeError("unknown platform variable '%s'" % (self.__name))
        current_var = g_platform_variables[self.__name]
        osname = self.__osname
        if osname is None:
            osname = g_osname
        osarch = self.__osarch
        if osarch is None:
            osarch = g_osarch
        combinations = get_platform_combinations(osname, osarch)
        for ii in combinations:
            if ii in current_var:
                return current_var[ii]
        raise ValueError("current platform %s not supported for variable '%s'" % (str(combinations), self.__name))

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
    (osname, _, osversion, osrelease, osarch, _) = platform.uname()
    # Linux distributions may have more accurate rules than just being Linux.
    if re.search(r'(arch|manjaro|antergos|parabola)', osrelease + osversion, re.I):
        osname = "Arch"
    # Extract proper FreeBSD major version from the OS version.
    match = re.search(r'FreeBSD\s+(\d+)\.\d+', osrelease)
    if match:
        osversion = int(match.group(1))
    return (osname, osarch, osversion)

# Get actual platform names.
(g_osname, g_osarch, g_osversion) = determine_platform()

g_platform_mapping = {
    "aarch64": "64-bit",
    "amd64": "64-bit",
    "arch": "Arch",
    "Arch": "Linux",
    "arm32lhf": "arm32l",
    "arm32l": "32-bit",
    "armv6l": "arm32l",
    "armv6lhf": "arm32lhf",
    "armv7l": "arm32l",
    "armv7lhf": "arm32lhf",
    "freebsd": "FreeBSD",
    "i386": "ia32",
    "i686": "ia32",
    "ia32": "32-bit",
    "linux": "Linux",
    "x86_64": "amd64",
    }

g_platform_variables = {
    "addr": {"32-bit": 4, "64-bit": 8},
    "align": {"default": 4, "amd64": 1, "ia32": 1},
    "bom": {"aarch64": "<", "amd64": "<", "arm32l": "<", "ia32": "<"},
    "compression": {"default": "lzma"},
    "e_flags": {"default": 0, "arm32l": 0x5000400},
    "e_machine": {"aarch64": 183, "amd64": 62, "arm32l": 40, "ia32": 3},
    "e_shentsize": {"default": 0},
    "e_shstrndx": {"default": 0},
    "ei_class": {"32-bit": 1, "64-bit": 2},
    "ei_osabi": {"FreeBSD": 9, "Linux": 3},  # SYSV: 0
    "entry": {"64-bit": 0x400000, "arm32l": 0x10000, "ia32": 0x2000000},  # ia32: 0x8048000
    "function_ceilf": {"default": None, "arm32l": "ceilf"},
    "function_floorf": {"default": None, "arm32l": "floorf"},
    "function_rand": {"default": None},
    "function_srand": {"default": None},
    "gl_library": {"default": "GL"},
    "interp": {"FreeBSD": "\"/libexec/ld-elf.so.1\"", "Linux-aarch64": "\"/lib/ld-linux-aarch64.so.1\"", "Linux-arm32l": "\"/lib/ld-linux.so.3\"", "Linux-arm32lhf": "\"/lib/ld-linux-armhf.so.3\"", "Linux-ia32": "\"/lib/ld-linux.so.2\"", "Linux-amd64": "\"/lib64/ld-linux-x86-64.so.2\""},
    "interp-cross": {"FreeBSD-ia32": "\"/libexec/ld-elf32.so.1\""},
    "march": {"aarch64": "armv8-a", "amd64": "core2", "armv6l": "armv6t2", "armv7l": "armv7", "armv7lhf": "armv7", "ia32": "pentium4"},
    "memory_page": {"32-bit": 0x1000, "64-bit": 0x200000},
    "mpreferred-stack-boundary": {"aarch64": 0, "arm32l": 0, "ia32": 2, "64-bit": 4},
    "phdr_count": {"default": 3},
    "phdr32_dynamic_p_flags": {"default": 0},
    "phdr64_dynamic_p_align": {"default": 0},
    "shelldrop_header": {"Arch": "!/bin/sh\n", "default": ""},
    "shelldrop_tail": {"Arch": "sed 1,2d", "default": "sed 1d"},
    "start": {"default": "_start"},
    }

########################################
# Functions ############################
########################################

def get_platform_combinations(osname, osarch):
    """Get listing of all possible platform combinations matching current platform."""
    # Gather operating system name path.
    osname = platform_map_iterate(osname.lower())
    osnames = []
    while osname:
        osnames += [osname]
        osname = platform_map_iterate(osname)
    # Gather operating system architecture path.
    mapped_osarch = osarch
    osarchs = []
    while osarch:
        osarchs += [osarch]
        osarch = platform_map_iterate(osarch)
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

def osarch_is_aarch64():
    """Check if the architecture maps to aarch64."""
    return osarch_match("aarch64")

def osarch_is_amd64():
    """Check if the architecture maps to amd64."""
    return osarch_match("amd64")

def osarch_is_ia32():
    """Check if the architecture maps to ia32."""
    return osarch_match("ia32")

def osarch_is_arm32l():
    """Check if the architecture maps to arm32l."""
    return osarch_match("arm32l")

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

def osname_is_freebsd():
    """Check if the operating system name maps to FreeBSD."""
    return ("FreeBSD" == g_osname)

def osname_is_linux():
    """Check if the operating system name maps to Linux."""
    return ("Linux" == g_osname)

def platform_is_gles():
    """Check if compiling for the GLES platform (as opposed to regular 'desktop' GL)."""
    return PlatformVar("gl_library").get() in ("GLESv2",)

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
