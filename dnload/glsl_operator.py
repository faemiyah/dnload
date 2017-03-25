########################################
# GlslOperator #########################
########################################

class GlslOperator:
  """Operator class."""

  def __init__(self, operator):
    """Constructor."""
    self.__operator = operator

  def format(self, force):
    """Return formatted output."""
    return self.__operator

  def get_str(self):
    """Get content string."""
    return self.__operator

  def incorporate(self, operator):
    """Try to incorporate another operator."""
    if operator.get_str() == "=":
      if self.__operator in ("+", "-", "*", "/", "<", ">", "="):
        self.__operator += operator.get_str()
        return True
    elif operator.get_str() == "+":
      if self.__operator == "+":
        self.__operator = "++"
        return True
    elif operator.get_str() == "-":
      if self.__operator == "-":
        self.__operator = "--"
        return True
    return False

  def __str__(self):
    """String representation."""
    return "GlslOperator('%s')" % (self.__operator)

########################################
# Functions ############################
########################################

def interpret_operator(source):
  """Try to interpret an operator."""
  if source in ("+", "-", "*", "/", "<", ">", "="):
    return GlslOperator(source)
  return None

def is_glsl_operator(op):
  """Tell if token is operator."""
  return isinstance(op, GlslOperator)
