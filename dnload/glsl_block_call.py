from dnload.glsl_block import GlslBlock
from dnload.glsl_block import extract_tokens
from dnload.glsl_block_statement import glsl_parse_statements

########################################
# GlslBlockCall ########################
########################################
 
class GlslBlockCall(GlslBlock):
  """Function call."""

  def __init__(self, name, lst):
    """Constructor."""
    GlslBlock.__init__(self)
    self.__name = name
    self.__content = lst
    # Hierarchy.
    self.addNamesUsed(name)
    self.addChildren(lst)

  def format(self, force):
    """Return formatted output."""
    lst = "".join(map(lambda x: x.format(force), self.__content))
    return "%s(%s);" % (self.__name.format(force), lst)

  def __str__(self):
    """String representation."""
    return "Call('%s')" % (self.__name.getName())

########################################
# Functions ############################
########################################

def glsl_parse_call(source):
  """Parse call block."""
  (name, scope, remaining) = extract_tokens(source, ("?n", "?(", ";"))
  if not name:
    return (None, source)
  if scope:
    (statements, scope_remaining) = glsl_parse_statements(scope)
    if not statements:
      return (None, source)
    if scope_remaining:
      raise RuntimeError("call scope cannot have remaining elements: '%s'" % str(scope_remaining))
    return (GlslBlockCall(name, statements), remaining)
  return (GlslBlockCall(name, []), remaining)
