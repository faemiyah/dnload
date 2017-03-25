from dnload.common import is_verbose
from dnload.glsl_name import interpret_name

########################################
# GlslAccess ###########################
########################################

class GlslAccess:
  """Swizzle operator."""

  def __init__(self, name):
    """Constructor."""
    self.__name = name
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

  def selectSwizzleRgba(self):
    """Select rgba for exporting."""
    self.__swizzle_export = ("r", "g", "b", "a")

  def selectSwizzleXyzw(self):
    """Select xyzw for exporting."""
    self.__swizzle_export = ("x", "y", "z", "w")

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
