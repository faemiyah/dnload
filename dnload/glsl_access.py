from dnload.common import is_verbose
from dnload.glsl_name import interpret_name
from dnload.glsl_name import is_glsl_name

########################################
# GlslAccess ###########################
########################################

class GlslAccess:
  """Swizzle operator."""

  def __init__(self, name):
    """Constructor."""
    self.__name = name
    self.__source = None
    self.interpretSwizzle()

  def format(self):
    """Return formatted output."""
    return "." + self.__name.format()

  def format(self, force):
    """Return formatted output."""
    ret = "."
    if self.__swizzle:
      if not self.__swizzle_export:
        if force:
          if is_verbose():
            print("WARNING: %s swizzle status unconfirmed" % (str(self)))
          return ret + self.__name.format(force)
        return ""
      return ret + self.generateSwizzle()
    return ret + self.__name.format(force)

  def generateSwizzle(self):
    """Generate exportable swizzled version."""
    if not self.__swizzle_export:
      raise RuntimeError("must have swizzle export selected before genrating")
    ret = ""
    for ii in self.__swizzle:
      ret += self.__swizzle_export[ii]
    return ret

  def getType(self):
    """Access type from name if present."""
    if self.__source and is_glsl_name(self.__source):
      return self.__source.getType()
    return None

  def interpretSwizzle(self):
    """Interpret potential swizzle."""
    self.__swizzle = []
    self.__swizzle_export = None
    for ii in self.__name.getName().split():
      if ii in ("r", "x"):
        self.__swizzle += [0]
      elif ii in ("g", "y"):
        self.__swizzle += [1]
      elif ii in ("b", "z"):
        self.__swizzle += [2]
      elif ii in ("a", "w"):
        self.__swizzle += [3]
      else: # Not a swizzle.
        self.__swizzle = []
        return
    # Check if too long to be a swizzle.
    if 4 < len(self.__swizzle):
      self.__swizzle = []

  def selectSwizzle(self, op):
    """Select swizzle mode  for exporting."""
    if op not in (("r", "g", "b", "a"), ("x", "y", "z", "w")):
      raise RuntimeError("cannot select swizzle '%s'" % (str(op)))
    self.__swizzle_export = op

  def setSource(self, lst):
    """Set source name for access."""
    for ii in reversed(range(len(lst))):
      vv = lst[ii]
      if is_glsl_name(vv) or is_glsl_access(vv):
        self.__source = vv
        return
    raise RuntimeError("could not find source for access")

  def __str__(self):
    """String representation."""
    return "GlslAccess('%s')" % (self.__name.getName())

########################################
# Functions ############################
########################################
 
def interpret_access(source):
  """Try to interpret swizzle element."""
  name = interpret_name(source)
  if name:
    return GlslAccess(name)
  return None

def is_glsl_access(op):
  """Tell if token is member element."""
  return isinstance(op, GlslAccess)
