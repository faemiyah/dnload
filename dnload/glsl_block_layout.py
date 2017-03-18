from dnload.glsl_block import GlslBlock
from dnload.glsl_block import extract_tokens
from dnload.glsl_block import extract_statement

########################################
# GlslBlockLayout ######################
########################################
 
class GlslBlockLayout(GlslBlock):
  """Uniform declaration."""

  def __init__(self, location):
    """Constructor."""
    GlslBlock.__init__(self)
    self.__location = location

  def format(self):
    """Return formatted output."""
    return "layout(location=%s)" % (self.__location.format())

  def __str__(self):
    """String representation."""
    return "Layout(%i)" % (self.__location.getInt())

########################################
# Functions ############################
########################################

def glsl_parse_layout(source):
  """Parse layout block."""
  (scope, remaining) = extract_tokens(source, ("layout", "?("))
  if not scope:
    return (None, source)
  (location, discarded) = extract_tokens(scope, ("location", "=", "?u"))
  if location is None:
    return (None, source)
  return (GlslBlockLayout(location), remaining)
