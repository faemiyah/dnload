import copy

from dnload.common import is_listing
from dnload.glsl_block import GlslBlock
from dnload.glsl_block import extract_tokens
from dnload.glsl_paren import GlslParen
from dnload.glsl_paren import is_glsl_paren
from dnload.glsl_token import token_tree_build
from dnload.glsl_token import token_tree_simplify
from dnload.glsl_operator import is_glsl_operator

########################################
# GlslBlockStatement ###################
########################################
 
class GlslBlockStatement(GlslBlock):
  """Statement block."""

  def __init__(self, lst, terminator = ""):
    """Constructor."""
    GlslBlock.__init__(self)
    self.__content = lst
    self.__terminator = terminator
    if (not is_listing(self.__content)) or (None in self.__content):
      raise RuntimeError("content must be a listing")
    # Hierarchy.
    self.addAccesses(lst)
    self.addNamesUsed(lst)

  def format(self, force):
    """Return formatted output."""
    lst = ""
    if 0 < len(self.__content):
      lst = "".join(map(lambda x: x.format(force), self.__content))
    return lst + self.__terminator.format(force)

  def getTerminator(self):
    """Accessor."""
    return self.__terminator

  def getTokens(self):
    """Accessor."""
    return self.__content

  def replaceTerminator(self, op):
    """Replace terminator with given operator."""
    if not (op in (',', ';')):
      raise RuntimeError("invalid replacement terminator for GlslBlockStatement: '%s'" % (op))
    self.__terminator = op

  def replaceUsedNameExact(self, name, tokens):
    """Replace exact instances of given used name with a list of tokens."""
    ret = 0
    while True:
      if not self.replaceUsedNameExactPass(name, tokens):
        break
      ret += 1
    self.clearAccesses()
    self.clearNamesUsed()
    self.addAccesses(self.__content)
    self.addNamesUsed(self.__content)
    return ret

  def replaceUsedNameExactPass(self, name, tokens):
    """Replace one instance of given used name with a list of tokens."""
    for ii in range(len(self.__content)):
      vv = self.__content[ii]
      if name is vv:
        # Perform deep copy of tokens to prevent same object existing in multiple places.
        self.__content[ii : ii + 1] = [GlslParen("(")] + copy.deepcopy(tokens) + [GlslParen(")")]
        return True
    return False

  def setTerminator(self, op):
    """Set terminating character."""
    self.__terminator = op

  def simplify(self, max_simplifys):
    """Run simplification pass on the statement."""
    ret = 0
    while True:
      if (0 <= max_simplifys) and (ret >= max_simplifys):
        break
      content = simplify_pass(self.__content)
      if not content and self.__content:
        raise RuntimeError("content '%s' simplified to '%s'" % (str(map(str, self.__content)), str(content)))
      if content == self.__content:
        break
      self.__content = content
      self.clearAccesses()
      self.clearNamesUsed()
      self.addAccesses(self.__content)
      self.addNamesUsed(self.__content)
      ret += 1
    return ret

  def __str__(self):
    """String representation."""
    return "Statement(%i)" % (len(self.__content))

########################################
# Functions ############################
########################################

def glsl_parse_statement(source, explicit = True):
  """Parse statement block."""
  bracket_count = 0
  paren_count = 0
  lst = []
  for ii in range(len(source)):
    elem = source[ii]
    # Count all scope-y things.
    if is_glsl_paren(elem):
      bracket_count = elem.updateBracket(bracket_count)
      if bracket_count < 0:
        raise RuntimeError("negative bracket parity")
      paren_count = elem.updateParen(paren_count)
      if paren_count < 0:
        raise RuntimeError("negative paren parity")
      if elem.isCurlyBrace():
        raise RuntimeError("scope declaration within statement")
    # Statement end.
    elif (elem.format(False) in (",", ";")) and (paren_count == 0) and (bracket_count == 0):
      return (GlslBlockStatement(lst, elem), source[ii + 1:])
    # Element is going into the statement.
    lst += [elem]
  # Was ok to have a statement without a terminator.
  if not explicit:
    return (GlslBlockStatement(lst), [])
  # Could not detect statement for a reason or another.
  return (None, source)

def glsl_parse_statements(source, until = None):
  """Parse multiple statements."""
  lst = []
  while source:
    (block, remaining) = glsl_parse_statement(source, False)
    if not block:
      raise RuntimeError("error parsing statements")
    lst += [block]
    # Terminate statement extraction if necessary.
    if until and (block.getTerminator() == until):
      return (lst, remaining)
    source = remaining
  # Everything was parsed.
  return (lst, None)

def simplify_pass(lst):
  """Run simplification pass on tokens."""
  # Build tree and run simplify pass from there.
  if lst:
    tree = token_tree_build(lst)
    if not tree:
      raise RuntimeError("could not build tree from '%s'" % (str(map(str, lst))))
    if token_tree_simplify(tree):
      return tree.flatten()
  # Nothign to simplify, just return original tree.
  return lst
