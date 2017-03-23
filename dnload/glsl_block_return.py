from dnload.glsl_block import GlslBlock
from dnload.glsl_block import extract_tokens
from dnload.glsl_block_statement import glsl_parse_statement

########################################
# GlslBlockAssignment ##################
########################################
 
class GlslBlockReturn(GlslBlock):
  """Return block."""

  def __init__(self, statement):
    """Constructor."""
    GlslBlock.__init__(self)
    self.__statement = statement
    # Hierarchy.
    self.addChildren(statement)

  def format(self):
    """Return formatted output."""
    return "return %s" % (self.__statement.format())

  def getStatement(self):
    """Accessor."""
    return self.__statement

  def __str__(self):
    """String representation."""
    return "Return()"

########################################
# Functions ############################
########################################
 
def glsl_parse_return(source):
  """Parse return block."""
  (ret, content,) = extract_tokens(source, "?|return")
  if not ret:
    return (None, source)
  (statement, remaining) = glsl_parse_statement(content)
  if not statement or (statement.getTerminator() != ";"):
    return (None, source)
  return (GlslBlockReturn(statement), remaining)
