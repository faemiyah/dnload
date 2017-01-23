import platform

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
    if not self.__name in g_platform_variables:
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

(g_osname, g_osignore1, g_osignore2, g_osignore3, g_osarch, g_osignore4) = platform.uname()

g_platform_mapping = {
  "amd64" : "64-bit",
  "armel" : "32-bit",
  "armv6l" : "armel",
  "armv7l" : "armel",
  "freebsd" : "FreeBSD",
  "i386" : "ia32",
  "i686" : "ia32",
  "ia32" : "32-bit",
  "linux" : "Linux",
  "x86_64" : "amd64",
  }

g_platform_variables = {
  "addr" : { "32-bit" : 4, "64-bit" : 8 },
  "align" : { "32-bit" : 4, "64-bit" : 8, "amd64" : 1, "ia32" : 1 },
  "bom" : { "amd64" : "<", "armel" : "<", "ia32" : "<" },
  "compression" : { "default" : "lzma" },
  "e_flags" : { "default" : 0, "armel" : 0x5000402 },
  "e_machine" : { "amd64" : 62, "armel" : 40, "ia32" : 3 },
  "ei_class" : { "32-bit" : 1, "64-bit" : 2 },
  "ei_osabi" : { "FreeBSD" : 9, "Linux-armel" : 0, "Linux" : 3 },
  "entry" : { "64-bit" : 0x400000, "armv6l" : 0x10000, "armv7l" : 0x8000, "ia32" : 0x4000000 }, # ia32: 0x8048000
  "function_rand" : { "default" : None },
  "function_srand" : { "default" : None },
  "gl_library" : { "default" : "GL" },
  "interp" : { "FreeBSD" : "\"/libexec/ld-elf.so.1\"", "Linux-armel" : "\"/lib/ld-linux.so.3\"", "Linux-ia32" : "\"/lib/ld-linux.so.2\"", "Linux-amd64" : "\"/lib64/ld-linux-x86-64.so.2\"" },
  "march" : { "amd64" : "core2", "armv6l" : "armv6t2", "armv7l" : "armv7", "ia32" : "pentium4" },
  "memory_page" : { "32-bit" : 0x1000, "64-bit" : 0x200000 },
  "mpreferred-stack-boundary" : { "armel" : 0, "ia32" : 2, "64-bit" : 4 },
  "phdr_count" : { "default" : 3 },
  "start" : { "default" : "_start" },
  }

########################################
# Functions ############################
########################################

def get_platform_combinations():
  """Get listing of all possible platform combinations matching current platform."""
  mapped_osname = platform_map(g_osname.lower())
  mapped_osarch = g_osarch.lower()
  ret = [mapped_osname]
  while True:
    ret += [mapped_osarch, mapped_osname + "-" + mapped_osarch]
    mapped_osarch = platform_map_iterate(mapped_osarch)
    if not mapped_osarch:
      break
  return sorted(ret, reverse=True) + ["default"]

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

def replace_platform_variable(name, op):
  """Destroy platform variable, replace with default."""
  if not name in g_platform_variables:
    raise RuntimeError("trying to destroy nonexistent platform variable '%s'" % (name))
  g_platform_variables[name] = { "default" : op }
