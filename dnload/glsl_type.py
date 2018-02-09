import re

########################################
# GlslType #############################
########################################

class GlslType:
  """GLSL type identifier."""

  def __init__(self, modifier, source):
    """Constructor."""
    self.__modifier = modifier
    self.__type = source

  def format(self, force):
    """Return formatted output."""
    if self.__modifier and (not force or (self.__modifier != "const")):
      return "%s %s" % (self.__modifier, self.__type)
    return self.__type

  def isVectorType(self):
    """Tell if this is a vector type (eglible for swizzling)."""
    if re.match(r'^(ivec\d|vec\d)$', self.__type):
      return True
    return False

  def __eq__(self, other):
    """Equals operator."""
    if is_glsl_type(other) and (self.__type == other.__type):
      return True
    return (self.__type == other)

  def __ne__(self, other):
    """Not equals operator."""
    return not (self == other)

  def __str__(self):
    """String representation."""
    return "GlslType('%s')" % (self.__type)

########################################
# Globals ##############################
########################################

g_type_modifiers = (
    "const",
    "flat",
    )

########################################
# Functions ############################
########################################

def match_type_id(op):
  """Tell if given string matches a type."""
  if re.match(r'^(bool|float|int|ivec\d|mat\d|sampler\dD|samplerCube|vec\d|void)$', op):
    return True
  return False

def interpret_type(op1, op2 = None):
  """Try to interpret type identifier."""
  if op2:
    if (op1 in g_type_modifiers) and match_type_id(op2):
      return GlslType(op1, op2)
    return None
  elif match_type_id(op1):
    return GlslType(None, op1)
  return None

def is_glsl_type(op):
  """Tell if token is type identifier."""
  return isinstance(op, GlslType)
