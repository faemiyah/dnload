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

  def format(self):
    """Return formatted output."""
    if self.__modifier:
      return "%s %s" % (self.__modifier, self.__type.format())
    return self.__type

  def __str__(self):
    """String representation."""
    return "GlslType('%s')" % (self.__type)

########################################
# Globals ##############################
########################################

g_type_modifiers = ("flat",)

########################################
# Functions ############################
########################################

def match_type_id(op):
  """Tell if given string matches a type."""
  if re.match(r'^(float|int|ivec\d|mat\d|sampler\dD|vec\d|void)$', op):
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
