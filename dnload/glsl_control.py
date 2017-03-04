########################################
# GlslControl ##########################
########################################

class GlslControl:
  """GLSL control flow element."""

  def __init__(self, control):
    """Constructor."""
    self.__control = control

  def format(self):
    """Return formatted output."""
    return self.__control

  def __str__(self):
    """String representation."""
    return "GlslControl('%s')" % (self.__control)

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

def interpret_control(source):
  """Try to interpret control flow element."""
  if source in g_control:
    return GlslControl(source)
  return None

def is_glsl_control(op):
  """Tell if token is control flow element."""
  return isinstance(op, GlslControl)
