from dnload.common import is_listing
from dnload.glsl_block import GlslBlock
from dnload.glsl_block import extract_tokens
from dnload.glsl_block_declaration import glsl_parse_declaration
from dnload.glsl_block_statement import glsl_parse_statements

########################################
# GlslBlockControl #####################
########################################
 
class GlslBlockControl(GlslBlock):
  """Control block."""

  def __init__(self, control, declaration, lst):
    """Constructor."""
    GlslBlock.__init__(self)
    self.__control = control
    self.__declaration = declaration
    self.__content = lst
    # Hierarchy.
    if declaration:
      self.addChildren(declaration)
    if lst:
      self.addChildren(lst)

  def format(self, force):
    """Return formatted output."""
    ret = self.__control.format(force)
    # Simple case.
    if not self.__declaration and not self.__content:
      return ret
    # Add declaration and/or content.
    ret += "("
    if self.__declaration:
      ret += self.__declaration.format(force)
    return ret + ("%s)" % ("".join(map(lambda x: x.format(force), self.__content))))

  def __str__(self):
    """String representation."""
    return "Control('%s')" % (self.__control.format(False))

########################################
# Functions ############################
########################################

def glsl_parse_control(source):
  """Parse control block."""
  (control, content) = extract_tokens(source, "?c")
  if not control:
    return (None, source)
  # 'else' is simpler.
  if control.format(False) == "else":
    return (GlslBlockControl(control, None, None), content)
  # Other control structures require scope.
  (scope, remaining) = extract_tokens(content, "?(")
  if not scope:
    return (None, source)
  # 'for' may require declaration at the beginning.
  declaration = None
  if control.format(False) == "for":
    (declaration, intermediate) = glsl_parse_declaration(scope)
    if declaration:
      scope = intermediate
  # Parse the rest of the statements, regardless if declaration was found.
  statements = glsl_parse_statements(scope)
  if not statements:
    return (None, source)
  return (GlslBlockControl(control, declaration, statements), remaining)

def is_glsl_block_control(op):
  """Tell if given object is GlslBlockControl."""
  return isinstance(op, GlslBlockControl)
