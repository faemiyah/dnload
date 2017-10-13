from dnload.common import is_verbose
from dnload.glsl_name import interpret_name
from dnload.glsl_name import is_glsl_name
from dnload.glsl_paren import is_glsl_paren

########################################
# GlslAccess ###########################
########################################

class GlslAccess:
  """Swizzle operator."""

  def __init__(self, name):
    """Constructor."""
    self.__name = name
    self.__source = None
    self.__access = None
    self.interpretSwizzle()

  def disableSwizzle(self):
    """Explicitly disable swizzle."""
    self.__swizzle = None

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

  def getAccess(self):
    """Accessor."""
    return self.__access

  def getName(self):
    """Accessor."""
    return self.__name

  def getType(self):
    """Access type from name and then from source if present."""
    name_type = self.__name.getType()
    if name_type:
      return name_type
    return self.getSourceType()

  def getSourceType(self):
    """Access type from source if present."""
    if self.__source:
      return self.__source.getType()
    return None

  def interpretSwizzle(self):
    """Interpret potential swizzle."""
    self.__swizzle = []
    self.__swizzle_export = None
    for ii in list(self.__name.getName()):
      if ii in ("r", "x"):
        self.__swizzle += [0]
      elif ii in ("g", "y"):
        self.__swizzle += [1]
      elif ii in ("b", "z"):
        self.__swizzle += [2]
      elif ii in ("a", "w"):
        self.__swizzle += [3]
      else: # Not a swizzle.
        self.__swizzle = None
        return
    # Check if too long to be a swizzle.
    if 4 < len(self.__swizzle):
      self.__swizzle = None

  def selectSwizzle(self, op):
    """Select swizzle mode  for exporting."""
    if op not in (("r", "g", "b", "a"), ("x", "y", "z", "w")):
      raise RuntimeError("cannot select swizzle '%s'" % (str(op)))
    self.__swizzle_export = op

  def setAccess(self, op):
    """Set given element as accessing this."""
    if self.__access:
      raise RuntimeError("'%s' already has access '%s'" % (str(self), str(self.__access)))
    self.__access = op

  def setSource(self, lst):
    """Set source name for access."""
    bracket_count = 0
    paren_count = 0
    for ii in reversed(range(len(lst))):
      vv = lst[ii]
      if is_glsl_paren(vv):
        if vv.isCurlyBrace():
          raise RuntimeError("curly brace found while looking for source of member")
        vv.updateParen(paren_count)
        vv.updateBracket(bracket_count)
      if (is_glsl_name(vv) or is_glsl_access(vv)) and (0 == bracket_count) and (0 == paren_count):
        self.__source = vv
        vv.setAccess(self)
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
