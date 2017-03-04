from dnload.common import is_verbose

########################################
# GlslSwizzle ##########################
########################################

class GlslSwizzle:
  """Swizzle operator."""

  def __init__(self, string, content):
    """Constructor."""
    self.__string = string
    self.__content = content
    self.__export = None

  def format(self):
    """Return formatted output."""
    if not self.__export:
      if is_verbose():
        print("WARNING: %s not locked" % (self))
      self.select_xyzw()
    ret = "."
    for ii in self.__content:
      ret += self.__export[ii]
    return ret

  def select_rgba(self):
    """Select rgba for exporting."""
    self.__export = ("r", "g", "b", "a")

  def select_xyzw(self):
    """Select xyzw for exporting."""
    self.__export = ("x", "y", "z", "w")

  def __str__(self):
    """String representation."""
    return "GlslSwizzle('%s')" % (self.__string)

########################################
# Functions ############################
########################################
 
def interpret_swizzle(source):
  """Try to interpret swizzle element."""
  content = []
  for ii in list(source):
    if ii in ("r", "x"):
      content += [0]
    elif ii in ("g", "y"):
      content += [1]
    elif ii in ("b", "z"):
      content += [2]
    elif ii in ("a", "w"):
      content += [3]
    else:
      return None
  if len(content) > 4:
    raise RuntimeError("swizzle too long: %i" % (len(content)))
  return GlslSwizzle(source, content)

def is_glsl_swizzle(op):
  """Tell if token is in/out directive element."""
  return isinstance(op, GlslSwizzle)
