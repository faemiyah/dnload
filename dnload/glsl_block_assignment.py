from dnload.glsl_block import GlslBlock
from dnload.glsl_block import extract_tokens
from dnload.glsl_block_statement import glsl_parse_statement

########################################
# GlslBlockAssignment ##################
########################################
 
class GlslBlockAssignment(GlslBlock):
  """Assignment block."""

  def __init__(self, name, swizzle, assign, statement):
    """Constructor."""
    GlslBlock.__init__(self)
    self.__name = name
    self.__swizzle = swizzle
    self.__assign = assign
    self.__statement = statement
    if self.__assign and (not self.__statement):
      raise RuntimeError("if assigning, must have a statement")

  def format(self):
    """Return formatted output."""
    ret = self.__name.format()
    if self.__swizzle:
      ret += self.__swizzle.format()
    if not self.__assign:
      return ret + self.__statement.format()
    return ret + ("%s%s" % (self.__assign.format(), self.__statement.format()))

  def getStatement(self):
    """Accessor."""
    return self.__statement

########################################
# Functions ############################
########################################
 
def glsl_parse_assignment(source):
  """Parse assignment block."""
  # Empty assignment.
  (name, terminator, intermediate) = extract_tokens(source, ("?n", "?,|;"))
  if name and terminator:
    (statement, remaining) = glsl_parse_statement([terminator] + intermediate)
    return (GlslBlockAssignment(name, None, None, statement), remaining)
  # Non-empty assignment.
  (name, operator, intermediate) = extract_tokens(source, ("?n", "?="))
  if name:
    (statement, remaining) = glsl_parse_statement(intermediate)
    if not statement:
      return (None, source)
    return (GlslBlockAssignment(name, None, operator, statement), remaining)
  # Assignment with swizzle.
  (name, swizzle, operator, intermediate) = extract_tokens(source, ("?n", "?s", "?="))
  if (not name) or (not swizzle):
    return (None, source)
  (statement, remaining) = glsl_parse_statement(intermediate)
  if not statement:
    return (None, source)
  return (GlslBlockAssignment(name, swizzle, operator, statement), remaining)
