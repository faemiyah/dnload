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
    self.__statements = lst
    self.__target = None
    # Hierarchy.
    if declaration:
      self.addChildren(declaration)
    if lst:
      self.addChildren(lst)

  def format(self, force):
    """Return formatted output."""
    if not self.__target:
      raise RuntimeError("control block '%s' has no target" % (str(self)))
    target = self.__target.format(force)
    ret = self.__control.format(force)
    # Simple case.
    if self.__control.format(False) == "else":
      if self.__declaration or self.__statements:
        raise RuntimeError("'%s' should not have declaration or content" % (str(self.__control)))
      if target[:1].isalnum():
        return ret + " " + target
      return ret + target
    # Add declaration and/or content.
    ret += "("
    if self.__declaration:
      ret += self.__declaration.format(force)
    return ret + ("%s)%s" % ("".join([x.format(force) for x in self.__statements]), target))

  def getTarget(self):
    """Accessor."""
    return self.__target

  def setTarget(self, op):
    """Set target block for control, can only be done once."""
    if self.__target:
      raise RuntimeError("control block '%s' already has target" % (str(self)))
    self.__target = op
    self.addChildren(op)

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
  (statements, scope_remaining) = glsl_parse_statements(scope)
  if not statements:
    return (None, source)
  if scope_remaining:
    raise RuntimeError("control scope cannot have remaining elements: '%s'" % str(scope_remaining))
  return (GlslBlockControl(control, declaration, statements), remaining)

def is_glsl_block_control(op):
  """Tell if given object is GlslBlockControl."""
  return isinstance(op, GlslBlockControl)
