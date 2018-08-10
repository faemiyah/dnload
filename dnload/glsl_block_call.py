from dnload.glsl_block import GlslBlock
from dnload.glsl_block import extract_tokens
from dnload.glsl_block_statement import glsl_parse_statements

########################################
# GlslBlockCall ########################
########################################

class GlslBlockCall(GlslBlock):
  """Function call."""

  def __init__(self, name, lst, terminator):
    """Constructor."""
    GlslBlock.__init__(self)
    self.__name = name
    self.__terminator = terminator
    # Hierarchy.
    self.addNamesUsed(name)
    self.addChildren(lst)

  def format(self, force):
    """Return formatted output."""
    lst = "".join([x.format(force) for x in self._children])
    return "%s(%s)%s" % (self.__name.format(force), lst, self.__terminator.format(force))

  def replaceTerminator(self, op):
    """Replace terminator with given element."""
    if not (op in (',', ';')):
      raise RuntimeError("invalid replacement terminator for GlslBlockCall: '%s'" % (op))
    self.__terminator = op

  def __str__(self):
    """String representation."""
    return "Call('%s')" % (self.__name.getName())

########################################
# Functions ############################
########################################

def glsl_parse_call(source):
  """Parse call block."""
  (name, scope, terminator, remaining) = extract_tokens(source, ("?n", "?(", "?;"))
  if not name:
    return (None, source)
  if scope:
    (statements, scope_remaining) = glsl_parse_statements(scope)
    if not statements:
      return (None, source)
    if scope_remaining:
      raise RuntimeError("call scope cannot have remaining elements: '%s'" % str(scope_remaining))
    return (GlslBlockCall(name, statements, terminator), remaining)
  return (GlslBlockCall(name, [], terminator), remaining)

def is_glsl_block_call(op):
  """Tell if given object is GlslBlockCall."""
  return isinstance(op, GlslBlockCall)
