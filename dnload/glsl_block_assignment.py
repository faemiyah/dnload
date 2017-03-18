from dnload.glsl_block import GlslBlock
from dnload.glsl_block import extract_tokens
from dnload.glsl_block_statement import glsl_parse_statement
from dnload.glsl_paren import GlslParen

########################################
# GlslBlockAssignment ##################
########################################
 
class GlslBlockAssignment(GlslBlock):
  """Assignment block."""

  def __init__(self, name, lst, assign, statement):
    """Constructor."""
    GlslBlock.__init__(self)
    self.__name = name
    self.__modifiers = lst
    self.__assign = assign
    self.__statement = statement
    if self.__assign and (not self.__statement):
      raise RuntimeError("if assigning, must have a statement")

  def format(self):
    """Return formatted output."""
    ret = self.__name.format()
    if self.__modifiers:
      ret += "".join(map(lambda x: x.format(), self.__modifiers))
    if not self.__assign:
      return ret + self.__statement.format()
    return ret + ("%s%s" % (self.__assign.format(), self.__statement.format()))

  def getStatement(self):
    """Accessor."""
    return self.__statement

  def __str__(self):
    """String representation."""
    return "Assignment(%s)" % (len(self.__name))

########################################
# Functions ############################
########################################
 
def glsl_parse_assignment(source):
  """Parse assignment block."""
  # Must have name.
  (name, content) = extract_tokens(source, ("?n",))
  if not name:
    return (None, source)
  # Empty assignment.
  (terminator, intermediate) = extract_tokens(content, ("?,|;",))
  if terminator:
    (statement, remaining) = glsl_parse_statement([terminator] + intermediate)
    return (GlslBlockAssignment(name, None, None, statement), remaining)
  # Non-empty assignment. Gather index and swizzle.
  lst = []
  while True:
    (index_scope, remaining) = extract_tokens(content, ("?[",))
    if index_scope:
      lst += [GlslParen("[")] + index_scope + [GlslParen("]")]
      content = remaining
      continue
    (access, remaining) = extract_tokens(content, ("?a",))
    if access:
      lst += [access]
      content = remaining
      continue
    (operator, remaining) = extract_tokens(content, ("?=",))
    if operator:
      content = remaining
      break
    # Can't be an assignment.
    return (None, source)
  # Gather statement.
  (statement, remaining) = glsl_parse_statement(content)
  if not statement:
    return (None, source)
  return (GlslBlockAssignment(name, lst, operator, statement), remaining)
