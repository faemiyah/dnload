import re
from dnload.common import is_verbose
from dnload.glsl_type import interpret_type

########################################
# GlslType #############################
########################################

class GlslName:
  """GLSL name identifier."""

  def __init__(self, source):
    """Constructor."""
    self.__name = source
    self.__typeid = None
    self.__rename = None
    self.__access = None
    # Reserved words are considered locked in all cases.
    if self.__name in get_list_locked():
      self.__rename = self.__name
    # Some locked variables have implicit types, set them right away.
    if self.__name in g_vec2:
      self.setType(interpret_type("vec2"))
    elif self.__name in g_vec4:
      self.setType(interpret_type("vec4"))

  def format(self, force):
    """Return formatted output."""
    if not self.__rename:
      if force:
        if is_verbose():
          print("WARNING: %s not locked" % (self))
        return self.__name
      return ""
    return self.__rename

  def getAccess(self):
    """Accessor."""
    return self.__access

  def getName(self):
    """Gets the original, non-renamed name."""
    return self.__name

  def getType(self):
    """Accessor."""
    return self.__typeid

  def isLocked(self):
    """Tell if this is using a locked string."""
    if self.__rename:
      return True
    return False

  def lock(self, op):
    """Lock rename into given name."""
    if self.__rename:
      raise RuntimeError("attempting to lock already locked rename '%s'" % (self.__rename))
    if not isinstance(op, str):
      raise RuntimeError("rename must be string, '%s' given" % (str(op)))
    self.__rename = op

  def resolveName(self):
    """Get resolved name, this is the locked name or original name if not locked."""
    if self.__rename:
      return self.__rename
    return self.__name

  def setAccess(self, op):
    """Set given element as accessing this."""
    if self.__access:
      raise RuntimeError("'%s' already has access '%s'" % (str(self), str(self.__access)))
    self.__access = op

  def setType(self, op):
    """Set type information of this."""
    if self.__typeid and (self.__typeid != op):
      raise RuntimeError("conflicting types '%s' and '%s' for '%s'" % (str(self.__typeid), str(op), self.__name))
    self.__typeid = op

  def __eq__(self, other):
    """Equals operator."""
    if is_glsl_name(other):
      return (other.resolveName() == self.resolveName())
    return (self.resolveName() == other)

  def __ne__(self, other):
    """Not equals operator."""
    return not (self == other)

  def __hash__(self):
    """Hashing operator."""
    return hash(self.__name)

  def __str__(self):
    """String representation."""
    if self.__rename:
      return "GlslName('%s' => '%s')" % (self.__name, self.__rename)
    return "GlslName('%s')" % (self.__name)

########################################
# Globals ##############################
########################################

g_locked = (
    "abs",
    "acos",
    "asin",
    "atan",
    "break",
    "clamp",
    "cos",
    "cross",
    "discard",
    "distance",
    "dot",
    "EmitVertex",
    "EndPrimitive",
    "fract",
    "gl_PerVertex",
    "layout",
    "length",
    "location",
    "log",
    "main",
    "max",
    "max_vertices",
    "min",
    "mix",
    "normalize",
    "pow",
    "reflect",
    "return",
    "sin",
    "smoothstep",
    "sqrt",
    "step",
    "tan",
    "texture",
    "transpose",
    "uniform",
    )

g_primitives = (
    "lines",
    "lines_adjacency",
    "points",
    "triangles",
    "triangle_strip",
    )

g_vec2 = (
    "gl_FragCoord",
    )

g_vec4 = (
    "gl_FragColor",
    "gl_Position",
    )

########################################
# Functions ############################
########################################

def get_list_locked():
  """Get list of all locked words."""
  return g_locked + g_primitives + g_vec2 + g_vec4

def get_list_primitives():
  """Get list of primitive words."""
  return g_primitives

def interpret_name(source):
  """Try to interpret name identifier."""
  # All reserved strings other than names here should have been interpreted before.
  # Names are interpreted last.
  if re.match(r'^([A-Za-z][A-Za-z0-9_]*)$', source, re.I):
    return GlslName(source)
  return None

def is_glsl_name(op):
  """Tell if token is type identifier."""
  return isinstance(op, GlslName)
