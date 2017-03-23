from dnload.common import is_listing
from dnload.glsl_block import GlslBlock
from dnload.glsl_block import extract_tokens

########################################
# GlslBlockMember ######################
########################################
 
class GlslBlockMember(GlslBlock):
  """Member block."""

  def __init__(self, typeid, name):
    """Constructor."""
    GlslBlock.__init__(self)
    self.__typeid = typeid
    self.__name = name
    # Hierarchy.
    self.addNames(name)

  def format(self):
    """Return formatted output."""
    return "%s %s;" % (self.__typeid.format(), self.__name.format())

  def __str__(self):
    """String representation."""
    return "Member('%s')" % (self.__name)

########################################
# Functions ############################
########################################

def glsl_parse_member(source):
  """Parse member block."""
  (typeid, name, remaining) = extract_tokens(source, ("?t", "?n", ";"))
  if not typeid:
    return (None, source)
  return (GlslBlockMember(typeid, name), remaining)

def glsl_parse_member_list(source):
  """Parse list of members."""
  # Empty member list is ok.
  if is_listing(source) and (0 >= len(source)):
    return []
  (member, content) = glsl_parse_member(source)
  if not member:
    raise RuntimeError("error parsing members: %s" % (str(map(str, source))))
  ret = [member]
  while content:
    (member, remaining) = glsl_parse_member(content);
    if not member:
      raise RuntimeError("error parsing members: %s" % (str(map(str, content))))
    ret += [member]
    content = remaining
  return ret
