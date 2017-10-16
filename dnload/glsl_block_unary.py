from dnload.glsl_block import GlslBlock
from dnload.glsl_block import extract_tokens
from dnload.glsl_block_statement import glsl_parse_statement
from dnload.glsl_operator import is_glsl_operator

########################################
# GlslBlockUnary #######################
########################################

class GlslBlockUnary(GlslBlock):
  """Unary statement block."""

  def __init__(self, statement):
    """Constructor."""
    GlslBlock.__init__(self)
    # Hierarchy.
    self.addChildren(statement)

  def format(self, force):
    """Return formatted output."""
    if len(self._children) != 1:
      raise RuntimeError("GlslBlockUnary::format(), child count != 1")
    return "%s" % ("".join(map(lambda x: x.format(force), self._children)))

  def replaceTerminator(self, op):
    """Replace terminator with given operator."""
    self._children[0].replaceTerminator(op)

  def __str__(self):
    """String representation."""
    return "Unary()"

########################################
# Globals ##############################
########################################

g_allowed_operators = (
    "--",
    "++",
    )

########################################
# Functions ############################
########################################

def glsl_parse_unary(source):
  """Parse unary block."""
  (statement, remaining) = glsl_parse_statement(source)
  if not statement:
    return (None, source)
  # Unary statement block must start or end with pre- or postfix operator.
  tokens = statement.getTokens()
  if not tokens:
    raise RuntimeError("empty statement parsed")
  if is_glsl_operator(tokens[0]) and (tokens[0].getOperator() in g_allowed_operators):
    return (GlslBlockUnary(statement), remaining)
  if is_glsl_operator(tokens[-1]) and (tokens[-1].getOperator() in g_allowed_operators):
    return (GlslBlockUnary(statement), remaining)
  # Was somehow invalid.
  return (None, source)

def is_glsl_block_unary(op):
  """Tell if given object is GlslBlockUnary."""
  return isinstance(op, GlslBlockUnary)
