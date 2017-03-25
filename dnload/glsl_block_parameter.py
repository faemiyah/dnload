from dnload.common import is_listing
from dnload.glsl_block import GlslBlock
from dnload.glsl_block import extract_tokens

########################################
# GlslBlockParameter ###################
########################################
 
class GlslBlockParameter(GlslBlock):
  """Parameter block."""

  def __init__(self, typeid, name):
    """Constructor."""
    GlslBlock.__init__(self)
    self.__typeid = typeid
    self.__name = name
    # Hierarchy.
    self.addNamesDeclared(name)
    self.addNamesUsed(name)

  def format(self, force):
    """Return formatted output."""
    return "%s %s" % (self.__typeid.format(force), self.__name.format(force))

########################################
# Functions ############################
########################################

def glsl_parse_parameter(source):
  """Parse parameter block."""
  (typeid, name, remaining) = extract_tokens(source, ("?t", "?n"))
  if not typeid:
    return (None, source)
  return (GlslBlockParameter(typeid, name), remaining)

def glsl_parse_parameter_list(source):
  """Parse list of parameters."""
  # Empty parameter list is ok.
  if is_listing(source) and (0 >= len(source)):
    return []
  (parameter, content) = glsl_parse_parameter(source)
  if not parameter:
    return (None, source)
  ret = [parameter]
  while content:
    (typeid, name, remaining) = extract_tokens(content, (",", "?t", "?n"))
    if not typeid:
      raise RuntimeError("could not parse parameter declaration from '%s'" % (str(content)))
    ret += [GlslBlockParameter(typeid, name)]
    content = remaining
  return ret
