########################################
# GlslParen ############################
########################################

class GlslParen:
  """Paren construct."""

  def __init__(self, paren):
    """Constructor."""
    self.__paren = paren

  def format(self, force):
    """Return formatted output."""
    return self.__paren

  def getCloser(self):
    """Get closing paren for opening paren."""
    if "{" == self.__paren:
      return "}"
    elif "[" == self.__paren:
      return "]"
    elif "(" == self.__paren:
      return ")"
    raise RuntimeError("not an opening paren: '%s'" % (self.__paren))

  def getParen(self):
    """Accessor."""
    return self.__paren

  def isBracket(self):
    """Tell if this is a bracket."""
    return self.__paren in ("[", "]")

  def isCurlyBrace(self):
    """Tell if this is a curly brace."""
    return self.__paren in ("{", "}")

  def isParen(self):
    """Tell if this is a paren."""
    return self.__paren in ("(", ")")

  def matches(self, other):
    """Tell if this is an opening paren that matches a given other closing paren."""
    if not is_glsl_paren(other):
      return False
    if self.__paren == "(":
      return (other == ")")
    elif self.__paren == "[":
      return (other == "]")
    return False

  def update(self, elem, count):
    """Generic update, update matching paren count only."""
    if self.isBracket():
      return elem.updateBracket(count)
    elif self.isCurlyBrace():
      return elem.updateCurlyBrace(count)
    elif self.isParen():
      return elem.updateParen(count)
    raise RuntimeError("invalid GlslParen")

  def updateBracket(self, count):
    """Update bracket count."""
    if "[" == self.__paren:
      return count + 1
    elif "]" == self.__paren:
      return count - 1
    return count

  def updateCurlyBrace(self, count):
    """Update curly brace count."""
    if "{" == self.__paren:
      return count + 1
    elif "}" == self.__paren:
      return count - 1
    return count

  def updateParen(self, count):
    """Update paren count."""
    if "(" == self.__paren:
      return count + 1
    elif ")" == self.__paren:
      return count - 1
    return count

  def __eq__(self, other):
    """Equals operator."""
    if is_glsl_paren(other) and (self.__paren == other.getParen()):
      return True
    return (self.__paren == other)

  def __ne__(self, other):
    """Not equals operator."""
    return not (self == other)

  def __str__(self):
    """String representation."""
    return "GlslParen('%s')" % (self.__paren)

########################################
# Functions ############################
########################################

def interpret_paren(source):
  """Try to interpret paren element."""
  if source in ("(", "[", "{", ")", "]", "}"):
    return GlslParen(source)
  return None

def is_glsl_paren(op):
  """Tell if token is paren element."""
  return isinstance(op, GlslParen)
