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
    # Hierarchy.
    for ii in lst:
      name = ii.getName()
      name.setType(typeid)
      self.addNamesDeclared(name)
    self.addChildren(lst)

  def format(self, force):
    """Return formatted output."""
    return "%s %s" % (self.__typeid.format(force), "".join(map(lambda x: x.format(force), self._children)))

  def collapse(self, other):
    """Collapse another declaration."""
    if is_glsl_declaration(other) and (other.getType() == self.__typeid):
      for ii in other.getChildren():
        ii.setParent(None)
        self.addChildren(ii)
        self.addNamesDeclared(ii.getName())
      for ii in range(len(self._children) - 1):
        vv = self._children[ii]
        vv.getStatement().setTerminator(",")
      return True
    return False

  def expand(self):
    """Expand into multiple declarations."""
    ret = []
    for ii in self._children:
      ii.setParent(None)
      ret += [GlslBlockDeclaration(self.__typeid, [ii])]
    return ret

  def getType(self):
    """Accessor."""
    return self.__typeid

  def __str__(self):
    """String representation."""
    return "Declaration('%s')" % (self.__typeid.format(False))

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

def is_glsl_declaration(op):
  """Tell if given element is a GLSL declaration block."""
  return isinstance(op, GlslBlockDeclaration)
