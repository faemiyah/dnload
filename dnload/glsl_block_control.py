from dnload.common import is_listing
from dnload.glsl_block import GlslBlock
from dnload.glsl_block import extract_tokens
from dnload.glsl_block_statement import glsl_parse_statements

########################################
# GlslBlockControl #####################
########################################
 
class GlslBlockControl(GlslBlock):
  """Control block."""

  def __init__(self, control, lst):
    """Constructor."""
    GlslBlock.__init__(self)
    self.__control = control
    self.__content = lst

  def format(self):
    """Return formatted output."""
    if not is_listing(self.__content):
      return self.__control.format()
    return "%s(%s)" % (self.__control.format(), "".join(map(lambda x: x.format(), self.__content)))

  def getTerminator(self):
    """Accessor."""
    return self.__terminator

########################################
# Functions ############################
########################################

def glsl_parse_control(source):
  """Parse control block."""
  (control, content) = extract_tokens(source, ("?c",))
  if not control:
    return (None, source)
  # 'else' is simpler.
  if control.format() == "else":
    return (GlslBlockControl(control, None), content)
  # Other control structures require scope.
  (scope, remaining) = extract_tokens(content, ("?(",))
  if not scope:
    return (None, source)
  statements = glsl_parse_statements(scope)
  if not statements:
    return (None, source)
  return (GlslBlockControl(control, statements), remaining)
