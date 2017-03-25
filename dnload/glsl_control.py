########################################
# GlslControl ##########################
########################################

class GlslControl:
  """GLSL control flow element."""

  def __init__(self, control1, control2 = None):
    """Constructor."""
    self.__control1 = control1
    self.__control2 = control2

  def format(self, force):
    """Return formatted output."""
    if self.__control2:
      return "%s %s" % (self.__control1, self.__control2)
    return self.__control1

  def __str__(self):
    """String representation."""
    if self.__control2:
      return "GlslControl('%s %s')" % (self.__control1, self.__control2)
    return "GlslControl('%s')" % (self.__control1)

########################################
# Globals ##############################
########################################

g_control = ("for",
    "if",
    "else",
    "while")

########################################
# Functions ############################
########################################

def interpret_control(op1, op2 = None):
  """Try to interpret control flow element."""
  if op2:
    if (op1 == "else") and (op2 in g_control):
      if op2 == "else":
        raise RuntimeError("invalid control sequence: '%s %s'" % (op1, op2))
      return GlslControl(op1, op2)
    return None
  elif op1 in g_control:
    return GlslControl(op1)
  return None

def is_glsl_control(op):
  """Tell if token is control flow element."""
  return isinstance(op, GlslControl)
