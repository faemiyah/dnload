import os
import re

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

  def __init__(self, definition_ld, filename, varname, output_name):
    """Constructor."""
    self.__definition_ld = definition_ld
    self.__filename = filename
    self.__variable_name = varname
    self.__output_name = output_name
    self.read()

  def format(self):
    """Return formatted output."""
    ret = "".join(map(lambda x: x.format(), self._parse_tree))
    ret = "\n".join(map(lambda x: "\"%s\"" % (x), glsl_cstr_readable(ret)))
    subst = { "DEFINITION_LD" : self.__definition_ld, "FILE_NAME" : os.path.basename(self.__filename), "SOURCE" : ret, "VARIABLE_NAME" : self.__variable_name }
    return g_template_glsl.format(subst)

  def parse(self):
    """Parse code into blocks and statements."""
    self._parse_tree = glsl_parse(self.__content)

  def preprocess(self, content):
    """Preprocess GLSL source content."""
    # First, remove all /* - */.
    content = re.sub(r'(\/\*.*\*\/)', "", content)
    # Declare all supported preprocessing.
    remove_slash = re.compile(r'\/\/.*$')
    pos = re.compile(r'\s*#\s*(if\s+defined\s*\(\s*%s\s*\)|ifdef\s+%s)\s*' % (self.__definition_ld, self.__definition_ld))
    into_pos = re.compile(r'\s*#\s*elif\s+defined\s*\(\s*%s\s*\)\s*' % self.__definition_ld)
    neg = re.compile(r'\s*#\s*(if\s+\!\s*defined\(\s*%s\s*\)|ifndef\s+%s)\s*' % (self.__definition_ld, self.__definition_ld))
    into_neg = re.compile(r'\s*#\s*elif\s+\!\s*defined\s*\(\s*%s\s*\)\s*' % self.__definition_ld)
    invert = re.compile(r'\s*#\s*else\s*')
    end = re.compile(r'\s*#\s*endif\s*')
    # Iterate over source.
    ret = []
    include = []
    for ii in content.split("\n"):
      ii = remove_slash.sub("", ii)
      match = pos.match(ii)
      if match:
        include.push(False)
        continue
      match = neg.match(ii)
      if match:
        include.push(True)
        continue
      match = into_pos.match(ii)
      if match:
        include.pop()
        include.push(False)
        continue
      match = into_neg.match(ii)
      if match:
        include.pop()
        include.push(True)
        continue
      match = invert.match(ii)
      if match:
        val = include.pop()
        include.push(not val)
        continue
      match = end.match(ii)
      if match:
        include.pop()
        continue
      # No match, add line unless denied in the chain.
      if not False in include:
        ret += [ii]
    return "\n".join(ret)

  def read(self):
    """Read file contents."""
    # Read file content.
    fd = open(self.__filename, "r")
    if not fd:
      raise RuntimeError("could not read GLSL source '%s'" % (fname))
    self.__content = self.preprocess(fd.read())
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
