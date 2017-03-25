import re

########################################
# GlslInt ##############################
########################################

class GlslInt:
  """GLSL integer."""

  def __init__(self, source):
    """Constructor."""
    self.__string = source
    self.__number = int(source)

  def format(self, force):
    """Return formatted output."""
    return str(self.__number)

  def getInt(self):
    """Integer representation."""
    return self.__number

  def getStr(self):
    """Access actual string."""
    return self.__string

  def __str__(self):
    """String representation."""
    return "GlslInt('%s')" % (self.__string)

########################################
# Functions ############################
########################################

def interpret_int(source):
  """Try to interpret integer."""
  if re.match(r'^\d+$', source):
    return GlslInt(source)
  return None

def is_glsl_int(op):
  """Tell if token is integer."""
  return isinstance(op, GlslInt)

def is_glsl_int_unsigned(op):
  """Tell if token is integer."""
  return isinstance(op, GlslInt) and (op.getInt() >= 0)
