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
    self.__statement = statement
    # Hierarchy.
    self.addChildren(statement)

  def format(self, force):
    """Return formatted output."""
    return "%s" % (self.__statement.format(force))

  def getStatement(self):
    """Accessor."""
    return self.__statement

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
