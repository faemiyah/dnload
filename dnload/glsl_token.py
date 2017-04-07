from dnload.common import is_listing
from dnload.glsl_operator import is_glsl_operator
from dnload.glsl_paren import is_glsl_paren

########################################
# GlslToken ############################
########################################

class GlslToken:
  """Holds single instance of a GLSL token. Actually more of a token container."""

  def __init__(self, token):
    """Constructor."""
    self.__parent = None
    self.__left = []
    self.__middle = []
    self.__right = []
    # Prevent degeneration.
    if is_glsl_token(token):
      single_child = token.getSingleChild()
      if is_glsl_token(single_child):
        single_child.setParent(None)
      self.addMiddle(single_child)
    else:
      self.addMiddle(token)

  def addLeft(self, op):
    """Add left child token."""
    # List case.
    if is_listing(op):
      for ii in op:
        self.addleft(ii)
      return
    # Single case.
    self.__left += [op]
    op.setParent(self)

  def addMiddle(self, op):
    """Add middle child token."""
    # List case.
    if is_listing(op):
      for ii in op:
        self.addMiddle(ii)
      return
    # Tokens added normally.
    if is_glsl_token(op):
      self.__middle += [op]
      op.setParent(self)
    # Non-tokens added as-is.
    else:
      self.__middle += [op]

  def addRight(self, op):
    """Add right child token."""
    # List case.
    if is_listing(op):
      for ii in op:
        self.addRight(ii)
      return
    # Single case.
    self.__right += [op]
    op.setParent(self)

  def flatten(self):
    """Flatten this token into a list."""
    ret = []
    # Left
    for ii in self.__left:
      ret += ii.flatten()
    # Middle may be a token or a listing in itself.
    for ii in self.__middle:
      if is_glsl_token(ii):
        ret += ii.flatten()
      else:
        ret += [ii]
    # Right.
    for ii in self.__right:
      ret += ii.flatten()
    return ret

  def getSingleChild(self):
    """Degeneration preventation. If token only has a single child, return that instead."""
    total = len(self.__left) + len(self.__right)
    if is_listing(self.__middle):
      total += len(self.__middle)
    elif self.__middle:
      total += 1
    # Return single child if there only was exactly one.
    if 1 == total:
      if 1 <= len(self.__left):
        raise RuntimeError("single child inconsistency: left")
      if 1 <= len(self.__right):
        raise RuntimeError("single child inconsistency: right")
      if is_listing(self.__middle):
        return self.__middle[0]
      return self.__middle
    return self

  def setParent(self, op):
    """Set parent."""
    if op and self.__parent and (self.__parent != op):
      raise RuntimeError("hierarchy inconsistency in '%s', parent '%s' over existing '%s'" %
          (str(self), str(op), str(self.__parent)))
    self.__parent = op

  def __str__(self):
    """String representation."""
    if 1 == len(self.__middle):
      return "Token(%i:'%s':%i)" % (len(self.__left), str(self.__middle[0]), len(self.__right))
    return "Token(%i:%i:%i)" % (len(self.__left), len(self.__middle), len(self.__right))

########################################
# Functions ############################
########################################

def is_glsl_token(op):
  """Tell if given object is a GLSL token."""
  return isinstance(op, GlslToken)

def token_tree_build(lst):
  """Builds and balances a token tree from given list."""
  bracket_count = 0
  paren_count = 0
  first_bracket_index = -1
  first_paren_index = -1
  highest_operator = None
  highest_operator_index = -1
  print(str(map(str, lst)))
  for ii in range(len(lst)):
    vv = lst[ii]
    if is_glsl_paren(vv):
      if vv.isBracket():
        bracket_count = vv.updateBracket(bracket_count)
        # Return split on bracket.
        if 0 >= bracket_count:
          if 0 > first_bracket_index:
            raise RuntimeError("bracket inconsistency")
          left = GlslToken(lst[first_bracket_index])
          middle = GlslToken(token_tree_build(lst[first_bracket_index + 1 : ii]))
          right = GlslToken(lst[ii])
          ret = GlslToken(middle)
          ret.addLeft(left)
          ret.addRight(right)
          return token_tree_build(lst[:first_bracket_index] + [ret] + lst[ii + 1:])
        elif 1 == bracket_count:
          first_bracket_index = ii
      elif vv.isParen():
        paren_count = vv.updateParen(paren_count)
        # Return split on paren.
        if 0 >= paren_count:
          if 0 > first_paren_index:
            raise RuntimeError("paren inconsistency")
          left = GlslToken(lst[first_paren_index])
          middle = GlslToken(token_tree_build(lst[first_paren_index + 1 : ii]))
          right = GlslToken(lst[ii])
          ret = GlslToken(middle)
          ret.addLeft(left)
          ret.addRight(right)
          return token_tree_build(lst[:first_paren_index] + [ret] + lst[ii + 1:])
        elif 1 == paren_count:
          print("first paren found!")
          first_paren_index = ii
      else:
        raise RuntimeError("unknown paren object '%s'" % (str(vv)))
    if is_glsl_operator(vv):
      if (not highest_operator) or (highest_operator < vv):
        highest_operator = vv
        highest_operator_index = ii
  # Iteration done. Collect the pieces.
  if highest_operator:
    left = token_tree_build(lst[:highest_operator_index])
    right = token_tree_build(lst[highest_operator_index + 1:])
    ret = GlslToken(highest_operator)
    ret.addLeft(left)
    ret.addRight(right)
    return ret
  # Only option at this point is that the list has no operators and no parens - return as itself.
  return GlslToken(lst)

def token_tree_simplify(op):
  """Perform first found simplify operation for given tree."""
  return False
