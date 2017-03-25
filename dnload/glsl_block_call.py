from dnload.glsl_block import GlslBlock
from dnload.glsl_block import extract_tokens

########################################
# GlslBlockCall ########################
########################################
 
class GlslBlockCall(GlslBlock):
  """Function call."""

  def __init__(self, name, scope):
    """Constructor."""
    GlslBlock.__init__(self)
    self.__name = name
    self.__scope = scope
    # Hierarchy.
    self.addNamesUsed(name)
    self.addChildren(scope)

  def format(self, force):
    """Return formatted output."""
    lst = "".join(map(lambda x: x.format(force), self.__scope))
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
  if name and (not (scope is None)):
    return (GlslBlockCall(name, scope), remaining)
  return (None, source)
