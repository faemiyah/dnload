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
  print("trying return: %s" % (str(map(str, source))))
  (ret, content,) = extract_tokens(source, ("?|return",))
  if not ret:
    print("did not have return")
    return (None, source)
  print("trying statement %s" % (str(map(str, content))))
  (statement, remaining) = glsl_parse_statement(content)
  if not statement or (statement.getTerminator() != ";"):
    print("did not have statement")
    return (None, source)
  return (GlslBlockReturn(statement), remaining)
