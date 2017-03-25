from glsl_block_source import glsl_read_source

########################################
# Glsl #################################
########################################

class Glsl:
  """GLSL source database."""

  def __init__(self):
    """Constructor."""
    self.__sources = []

  def count(self):
    combined = "".join(map(lambda x: x.format(False), self.__sources))
    ret = {}
    for ii in combined:
      if ii.isalpha():
        if ii in ret:
          ret[ii] += 1
        else:
          ret[ii] = 1
    return ret

  def crunch(self):
    """Crunch the source code to smaller state."""
    # Expand all expandable elements.
    for ii in self.__sources:
      ii.expandRecursive()
    # Collect identifiers.
    collected = []
    for ii in self.__sources:
      collected += ii.collect()
    for ii in collected:
      print(str(map(str, ii)))
    # Recombine combinable elements.
    for ii in self.__sources:
      ii.collapseRecursive()

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
