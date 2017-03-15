from glsl_block_source import glsl_read_source

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

  def read(self, preprocessor, definition_ld, filename, varname, output_name):
    """Read source file."""
    self.__sources += [glsl_read_source(preprocessor, definition_ld, filename, varname, output_name)]

  def write(self):
    """Write processed source headers."""
    for ii in self.__sources:
      ii.write()

  def __str__(self):
    """String representation."""
    return "\n".join(map(lambda x: str(x), self.__sources))
