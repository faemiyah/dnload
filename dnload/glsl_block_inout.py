from dnload.glsl_block import GlslBlock
from dnload.glsl_block import extract_tokens
from dnload.glsl_block_layout import glsl_parse_layout
from dnload.glsl_block_member import glsl_parse_member_list

########################################
# GlslBlockInOut #######################
########################################
 
class GlslBlockInOut(GlslBlock):
  """Input (attribute / varying) declaration block."""

  def __init__(self, layout, inout, typeid, name):
    """Constructor."""
    GlslBlock.__init__(self)
    self.__layout = layout
    self.__inout = inout
    self.__typeid = typeid
    self.__name = name

  def format(self):
    """Return formatted output."""
    ret = ""
    if self.__layout:
      ret += self.__layout.format()
    return ret + "%s %s %s;" % (self.__inout.format(), self.__typeid.format(), self.__name.format())

  def __str__(self):
    """String representation."""
    return "InOut('%s')" % (self.__name.getName())

########################################
# GlslBlockInOutStruct #################
########################################
 
class GlslBlockInOutStruct(GlslBlock):
  """Input (attribute / varying) struct declaration block."""

  def __init__(self, layout, inout, type_name, members, name):
    """Constructor."""
    GlslBlock.__init__(self)
    self.__layout = layout
    self.__inout = inout
    self.__type_name = type_name
    self.__members = members
    self.__name = name

  def format(self):
    """Return formatted output."""
    lst = "".join(map(lambda x: x.format(), self.__members))
    ret = ""
    if self.__layout:
      ret += self.__layout.format()
    return ret + "%s %s{%s}%s;" % (self.__inout.format(), self.__type_name.format(), lst, self.__name.format())

  def __str__(self):
    """String representation."""
    return "InOutStruct('%s')" % (self.__type_name.getName())

########################################
# Functions ############################
########################################

def glsl_parse_inout(source):
  """Parse inout block."""
  (layout, content) = glsl_parse_layout(source)
  if not layout:
    content = source
  # Scoped version first.
  (inout, type_name, scope, name, remaining) = extract_tokens(content, ("?o", "?n", "?{", "?n", ";"))
  if inout and type_name and scope and name:
    members = glsl_parse_member_list(scope)
    if not members:
      raise RuntimeError("empty member list for inout struct")
    return (GlslBlockInOutStruct(layout, inout, type_name, members, name), remaining)
  # Regular inout.
  (inout, typeid, name, remaining) = extract_tokens(content, ("?o", "?t", "?n", ";"))
  if not inout or not typeid or not name:
    return (None, source)
  return (GlslBlockInOut(layout, inout, typeid, name), remaining)
