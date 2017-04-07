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

  def getOperator(self):
    """Get content string."""
    return self.__operator

  def getPrecedence(self):
    """Get operator precedence. Higher is better."""
    if self.__operator in ("?",):
      return 1
    elif self.__operator in ("||",):
      return 2
    elif self.__operator in ("^^",):
      return 3
    elif self.__operator in ("&&",):
      return 4
    elif self.__operator in ("==", "!="):
      return 5
    elif self.__operator in ("<", "<=", ">", ">="):
      return 6
    elif self.__operator in ("+", "-"):
      return 7
    elif self.__operator in ("*", "/"):
      return 8
    elif self.__operator in ("++", "--"):
      return 9
    raise RuntimeError("operator '%s' has no precedence" % (str(self)))

  def isAssignment(self):
    """Tell if this is an assignment operator of any kind."""
    return (self.__operator in ("=", "+=", "-=", "*=", "/="))

  def incorporate(self, operator):
    """Try to incorporate another operator."""
    if operator.getOperator() == "=":
      if self.__operator in ("+", "-", "*", "/", "<", ">", "="):
        self.__operator += operator.getOperator()
        return True
    elif operator.getOperator() == "+":
      if self.__operator == "+":
        self.__operator = "++"
        return True
    elif operator.getOperator() == "-":
      if self.__operator == "-":
        self.__operator = "--"
        return True
    return False

  def __lt__(self, other):
    """Less than operator."""
    if not is_glsl_operator(other):
      raise RuntimeError("comparison against non-operator: '%s' vs. '%s'" % (str(self), str(other)))
    return self.getPrecedence() < other.getPrecedence()

  def __eq__(self, other):
    """Equals operator."""
    if is_glsl_operator(other):
      return self.__operator == other.getOperator()
    return self.getOperator() == other

  def __ne__(self, other):
    """Not equals operator."""
    return not (self == other)

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
