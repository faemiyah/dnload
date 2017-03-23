from dnload.glsl_block import GlslBlock
from dnload.glsl_block import extract_tokens
from dnload.glsl_block_assignment import glsl_parse_assignment
import re

########################################
# GlslBlockDeclaration #################
########################################
 
class GlslBlockDeclaration(GlslBlock):
  """Variable declaration block."""

  def __init__(self, typeid, lst):
    """Constructor."""
    GlslBlock.__init__(self)
    self.__typeid = typeid
    self.__assignments = lst
    # Hierarchy.
    self.addChildren(lst)

  def format(self):
    """Return formatted output."""
    return "%s %s" % (self.__typeid.format(), "".join(map(lambda x: x.format(), self.__assignments)))

########################################
# Functions ############################
########################################

def glsl_parse_declaration(source):
  """Parse declaration block."""
  (typeid, content) = extract_tokens(source, ("?t",))
  if not typeid:
    return (None, source)
  # Loop until nothing found.
  lst = []
  while True:
    (assignment, remaining) = glsl_parse_assignment(content)
    if assignment:
      lst += [assignment]
      # Might have been last assignement.
      if assignment.getStatement().getTerminator() == ";":
        return (GlslBlockDeclaration(typeid, lst), remaining)
      # Otherwise keep going.
      content = remaining
      continue
    # Unknown element, not a valid declaration.
    return (None, source)
