from dnload.glsl_block import GlslBlock
from dnload.glsl_block import extract_tokens

########################################
# GlslBlockInOut #######################
########################################
 
class GlslBlockInOut(GlslBlock):
  """Input (attribute / varying) declaration block."""

  def __init__(self, inout, typeid, name):
    """Constructor."""
    GlslBlock.__init__(self)
    self.__inout = inout
    self.__typeid = typeid
    self.__name = name

  def format(self):
    """Return formatted output."""
    return "%s %s %s;" % (self.__inout.format(), self.__typeid.format(), self.__name.format())

  def __str__(self):
    """String representation."""
    return "InOut('%s')" % (self.__name.getName())

########################################
# Functions ############################
########################################

def glsl_parse_inout(source):
  """Parse inout block."""
  (inout, typeid, name, remaining) = extract_tokens(source, ("?o", "?t", "?n", ";"))
  if not inout or not typeid or not name:
    return (None, source)
  return (GlslBlockInOut(inout, typeid, name), remaining)
