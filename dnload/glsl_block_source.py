import os

from dnload.common import is_verbose
from dnload.glsl_block import GlslBlock
from dnload.glsl_parse import glsl_parse
from dnload.template import Template

########################################
# Globals ##############################
########################################

g_template_glsl = Template("""static const char *[[VARIABLE_NAME]] = \"\"
#if defined([[DEFINITION_LD]])
\"[[FILE_NAME]]\"
#else
[[SOURCE]]
#endif
\"\";
""")

########################################
# GlslBlockSource ######################
########################################

class GlslBlockSource(GlslBlock):
  """GLSL source file abstraction."""

  def __init__(self, fname, varname, output_name):
    """Constructor."""
    self.__file_name = fname
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

  def format(self, definition_ld):
    """Return formatted output."""
    ret = []
    for ii in self._parse_tree:
      ret += ["\"%s\"" % ii.format()]
    subst = { "DEFINITION_LD" : definition_ld, "FILE_NAME" : os.path.basename(self.__file_name), "SOURCE" : "\n".join(ret), "VARIABLE_NAME" : self.__variable_name }
    return g_template_glsl.format(subst)

  def parse(self):
    """Parse code into blocks and statements."""
    self._parse_tree = glsl_parse(self.__content)

  def write(self, definition_ld):
    """Write compressed output."""
    fd = open(self.__output_name, "w")
    if not fd:
      raise RuntimeError("could not write GLSL header '%s'" % (self.__output_name))
    fd.write(self.format(definition_ld))
    fd.close()
    if is_verbose():
      print("Wrote GLSL header: '%s' => '%s'" % (self.__variable_name, self.__output_name))

  def __str__(self):
    return "'%s' => '%s': %s" % (self.__variable_name, self.__output_name,
        str(map(str, self._parse_tree)))
