import os

from dnload.common import is_verbose
from dnload.glsl_block import GlslBlock
from dnload.glsl_block_preprocessor import glsl_parse_preprocessor
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

  def __init__(self, definition_ld, filename, varname, output_name):
    """Constructor."""
    self.__definition_ld = definition_ld
    self.__filename = filename
    self.__variable_name = varname
    self.__output_name = output_name
    self.__content = ""
    self._parse_tree = []

  def format(self):
    """Return formatted output."""
    ret = "".join(map(lambda x: x.format(), self._parse_tree))
    ret = "\n".join(map(lambda x: "\"%s\"" % (x), glsl_cstr_readable(ret)))
    subst = { "DEFINITION_LD" : self.__definition_ld, "FILE_NAME" : os.path.basename(self.__filename), "SOURCE" : ret, "VARIABLE_NAME" : self.__variable_name }
    return g_template_glsl.format(subst)

  def parse(self):
    """Parse code into blocks and statements."""
    self._parse_tree += glsl_parse(self.__content)

  def preprocess(self, preprocessor, source):
    """Preprocess GLSL source, store preprocessor directives into parse tree and content."""
    self._parse_tree = []
    content = []
    for ii in source.splitlines():
      block = glsl_parse_preprocessor(ii)
      if block:
        self._parse_tree += [block]
      else:
        content += [ii]
    # Removed known preprocessor directives, write result into intermediate file.
    fname = self.__output_name + ".preprocessed"
    fd = open(fname, "w")
    fd.write(("\n".join(content)).strip())
    fd.close()
    # Preprocess and reassemble content.
    intermediate = preprocessor.preprocess(fname)
    content = []
    for ii in intermediate.splitlines():
      if not ii.strip().startswith("#"):
        content += [ii]
    self.__content = "\n".join(content)

  def read(self, preprocessor):
    """Read file contents."""
    fd = open(self.__filename, "r")
    if not fd:
      raise RuntimeError("could not read GLSL source '%s'" % (fname))
    self.preprocess(preprocessor, fd.read())
    fd.close()
    if is_verbose():
      print("Read GLSL source: '%s'" % (self.__filename))

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

########################################
# Functions ############################
########################################

def glsl_cstr_readable(op):
  """Make GLSL source string into a 'readable' C string array."""
  line = ""
  ret = []
  for ii in op:
    if ";" == ii:
      ret += [line + ii]
      line = ""
      continue
    elif "\n" == ii:
      ret += [line + "\\n"]
      line = ""
      continue
    elif "{" == ii:
      if line:
        ret += [line]
      ret += ["{"]
      line = ""
      continue
    elif "}" == ii:
      if line:
        ret += [line]
      ret += ["}"]
      line = ""
      continue
    line += ii
  if line:
    ret += [line]
  return ret

def glsl_read_source(preprocessor, definition_ld, filename, varname, output_name):
  """Read source into a GLSL source construct."""
  ret = GlslBlockSource(definition_ld, filename, varname, output_name)
  ret.read(preprocessor)
  return ret
