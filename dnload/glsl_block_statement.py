from dnload.common import is_listing
from dnload.glsl_block import GlslBlock
from dnload.glsl_block import extract_tokens
from dnload.glsl_paren import is_glsl_paren

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
    self.addNames(lst)

  def format(self):
    """Return formatted output."""
    lst = ""
    if 0 < len(self.__content):
      lst = "".join(map(lambda x: x.format(), self.__content))
    return lst + self.__terminator

  def getTerminator(self):
    """Accessor."""
    return self.__terminator

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
      if 0 > bracket_count:
        raise RuntimeError("negative bracket parity")
      paren_count = elem.updateParen(paren_count)
      if 0 > paren_count:
        raise RuntimeError("negative paren parity")
      if elem.isCurlyBrace():
        raise RuntimeError("scope declaration within statement")
    # Statement end.
    elif (elem in (",", ";")) and (0 >= paren_count) and (0 >= bracket_count):
      return (GlslBlockStatement(lst, elem), source[ii + 1:])
    # Element is going into the statement.
    lst += [elem]
  # Was ok to have a statement without a terminator.
  if not explicit:
    return (GlslBlockStatement(lst), [])
  # Could not detect statement for a reason or another.
  return (None, source)

def glsl_parse_statements(source):
  """Parse multiple statements."""
  lst = []
  while source:
    (block, remaining) = glsl_parse_statement(source, False)
    if block:
      lst += [block]
      source = remaining
      continue
    raise RuntimeError("error parsing statements")
  for ii in lst[:-1]:
    if ";" != ii.getTerminator():
      raise RuntimeError("statement list missing terminator(s) in-between")
  return lst
