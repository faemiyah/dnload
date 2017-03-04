from dnload.common import is_verbose
from dnload.glsl_block import GlslBlock
from dnload.glsl_parse import glsl_parse

########################################
# GlslBlockSource ######################
########################################

class GlslBlockSource(GlslBlock):
  """GLSL source file abstraction."""

  def __init__(self, fname, varname, output_name):
    """Constructor."""
    self.__variable_name = varname
    self.__output_name = output_name
    # Read file content.
    fd = open(fname, "r")
    if not fd:
      raise RuntimeError("could not read GLSL source '%s'" % (fname))
    self.__content = fd.read()
    fd.close()
    if is_verbose():
      print("Read GLSL source: '%s'" % (fname))

  def format(self):
    """Return formatted output."""
    ret = []
    for ii in self._parse_tree:
      ret += ["\"%s\"" % ii.format()]
    return "static const char *%s = \"\"\n%s;" % (self.__variable_name, "\n".join(ret))

  def parse(self):
    """Parse code into blocks and statements."""
    self._parse_tree = glsl_parse(self.__content)

  def write(self):
    """Write compressed output."""
    fd = open(self.__output_name, "w")
    if not fd:
      raise RuntimeError("could not write GLSL header '%s'" % (self.__output_name))
    fd.write(self.format())
    fd.close()
    if is_verbose():
      print("Wrote GLSL header: '%s' => '%s'" % (self.__variable_name, self.__output_name))

  def __str__(self):
    return "'%s' => '%s': %s" % (self.__variable_name, self.__output_name,
        str(map(str, self._parse_tree)))
