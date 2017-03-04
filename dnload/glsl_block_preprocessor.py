from dnload.glsl_block import GlslBlock

########################################
# GlslBlock ############################
########################################

class GlslBlockPreprocessor(GlslBlock):
  """Preprocessor block."""

  def __init__(self, source):
    """Constructor."""
    GlslBlock.__init__(self, source)
    lines = self._source.strip().split()
    self.__content = " ".join(lines)

  def format(self):
    """Return formatted output."""
    return "%s\\n" % (self.__content)

  def __str__(self):
    """String representation."""
    return "Preprocessor('%s')" % (self.__content)
    
########################################
# Functions ############################
########################################

def glsl_parse_preprocessor(source):
  """Parse preprocessor block."""
  if not source.startswith("#"):
    return (None, source)
  return GlslBlockPreprocessor(source)
