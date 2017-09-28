from dnload.common import is_listing
from dnload.glsl_block import GlslBlock
from dnload.glsl_block import extract_tokens

########################################
# GlslBlockParameter ###################
########################################
 
class GlslBlockParameter(GlslBlock):
  """Parameter block."""

  def __init__(self, typeid, name, inout = None):
    """Constructor."""
    GlslBlock.__init__(self)
    self.__typeid = typeid
    self.__name = name
    self.__inout = inout
    # Hierarchy.
    name.setType(typeid)
    self.addNamesDeclared(name)
    self.addNamesUsed(name)

  def format(self, force):
    """Return formatted output."""
    ret = ""
    if self.__inout:
      ret += "%s " % (self.__inout.format(force))
    return ret + "%s %s" % (self.__typeid.format(force), self.__name.format(force))

  def __str__(self):
    """String representation."""
    return "Parameter('%s')" % (self.__name.format(False))

########################################
# Functions ############################
########################################

def glsl_parse_parameter(source):
  """Parse parameter block."""
  (typeid, name, remaining) = extract_tokens(source, ("?t", "?n"))
  if name:
    return (GlslBlockParameter(typeid, name), remaining)
  (inout, typeid, name, remaining) = extract_tokens(source, ("?o", "?t", "?n"))
  if inout:
    # Not all inout directives are acceptable.
    if not (inout.format(False) in ("in", "inout", "out")):
      raise RuntimeError("invalid inout directive for parameter: '%s'" % (inout.format(False)))
    return (GlslBlockParameter(typeid, name, inout), remaining)
  # Not a valid parameter.
  return (None, source)

def glsl_split_parameter_list(source):
  """Splits parameter list on commas."""
  ret = []
  current_parameter = []
  for ii in source:
    if "," == ii:
      ret += [current_parameter]
      current_parameter = []
    else:
      current_parameter += [ii]
  if current_parameter:
    ret += [current_parameter]
  return ret

def glsl_parse_parameter_list(source):
  """Parse list of parameters."""
  # Empty parameter list is ok.
  if is_listing(source) and (0 >= len(source)):
    return []
  ret = []
  parameters = glsl_split_parameter_list(source)
  for ii in parameters:
    (parameter, remaining) = glsl_parse_parameter(ii)
    if not parameter:
      raise RuntimeError("could not parse parameter from '%s'" % (str(map(str, ii))))
    if remaining:
      raise RuntimeError("extra content after parameter: '%s'" % (str(map(str, remaining))))
    ret += [parameter]
  return ret
