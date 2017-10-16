from dnload.glsl_block import GlslBlock
from dnload.glsl_block import extract_tokens
from dnload.glsl_block_statement import glsl_parse_statement

########################################
# GlslBlockFlow ########################
########################################

class GlslBlockFlow(GlslBlock):
  """Flow control statement."""

  def __init__(self, statement):
    """Constructor."""
    GlslBlock.__init__(self)
    # Hierarchy.
    self.addChildren(statement)

  def format(self, force):
    """Return formatted output."""
    if len(self._children) != 1:
      raise RuntimeError("GlslBlockFlow::format(), length of children != 1")
    return "".join(map(lambda x: x.format(force), self._children))

########################################
# Functions ############################
########################################

def glsl_parse_flow(source):
  """Parse flow block."""
  (name, terminator, remaining) = extract_tokens(source, ("?n", "?;"))
  if name in ("break", "continue"):
    (statement, discarded) = glsl_parse_statement([name, terminator])
    if discarded:
      raise RuntimeError("discarded elements after flow control statement")
    return (GlslBlockFlow(statement), remaining)
  return (None, source)

def is_glsl_block_flow(op):
  """Tell if given object is GlslBlockFlow."""
  return isinstance(op, GlslBlockFlow)
