from glsl_block_source import GlslBlockSource

########################################
# Glsl #################################
########################################

class Glsl:
  """GLSL source database."""

  def __init__(self):
    """Constructor."""
    self.__sources = []

  def parse(self):
    """Parse all source files."""
    for ii in self.__sources:
      ii.parse()

  def read(self, filename, varname, output_name):
    """Read source file."""
    self.__sources += [GlslBlockSource(filename, varname, output_name)]

  def write(self, definition_ld):
    """Write processed source headers."""
    for ii in self.__sources:
      ii.write(definition_ld)

  def __str__(self):
    """String representation."""
    return "\n".join(map(lambda x: str(x), self.__sources))
