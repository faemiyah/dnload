from dnload.common import is_listing
from dnload.glsl_block import GlslBlock
from dnload.glsl_block import extract_tokens
from dnload.glsl_block_assignment import glsl_parse_assignment
from dnload.glsl_paren import is_glsl_paren

########################################
# GlslBlockParameter ###################
########################################

class GlslBlockParameter(GlslBlock):
  """Parameter block."""

  def __init__(self, inout, typeid, assignment):
    """Constructor."""
    GlslBlock.__init__(self)
    self.__inout = inout
    self.__typeid = typeid
    self.__assignment = assignment
    # Set type of name.
    name = assignment.getName()
    name.setType(typeid)
    # Hierarchy.
    self.addNamesDeclared(name)
    #self.addNamesUsed(name)
    self.addChildren(assignment)

  def format(self, force):
    """Return formatted output."""
    ret = ""
    if self.__inout:
      ret += "%s " % (self.__inout.format(force))
    return ret + "%s %s" % (self.__typeid.format(force), self.__assignment.format(force))

  def __str__(self):
    """String representation."""
    return "Parameter('%s')" % (self.__assignment.getName().format(False))

########################################
# Functions ############################
########################################

def glsl_parse_parameter(source):
  """Parse parameter block."""
  (inout, typeid, content) = extract_tokens(source, ("?o", "?t"))
  if not inout:
    (typeid, content) = extract_tokens(source, ("?t"))
    if not typeid:
      return (None, source)
  (assignment, remaining) = glsl_parse_assignment(content, False)
  if not assignment:
    raise RuntimeError("could not parse assignment from '%s'" % (str(map(str, content))))
  if inout and (not inout.format(False) in ("in", "inout", "out")):
    raise RuntimeError("invalid inout directive for parameter: '%s'" % (inout.format(False)))
  return (GlslBlockParameter(inout, typeid, assignment), remaining)

def glsl_split_parameter_list(source):
  """Splits parameter list on commas."""
  paren_count = 0
  ret = []
  current_parameter = []
  for ii in source:
    # Count parens.
    if is_glsl_paren(ii):
      paren_count = elem.updateParen(paren_count)
      if paren_count < 0:
        raise RuntimeError("negative paren parity")
      if elem.isCurlyBrace():
        raise RuntimeError("scope declaration within parameter")
    # Split to next param if paren count is 0.
    if ("," == ii) and (paren_count == 0):
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
