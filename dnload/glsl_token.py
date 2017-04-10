from dnload.common import is_listing
from dnload.glsl_access import is_glsl_access
from dnload.glsl_float import interpret_float
from dnload.glsl_float import is_glsl_float
from dnload.glsl_int import interpret_int
from dnload.glsl_int import is_glsl_int
from dnload.glsl_name import is_glsl_name
from dnload.glsl_operator import is_glsl_operator
from dnload.glsl_operator import interpret_operator
from dnload.glsl_paren import is_glsl_paren
from dnload.glsl_type import is_glsl_type

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
    # Prevent degeneration, collapse chains of single tokens.
    if token:
      token = token_descend(token)
      self.addMiddle(token)

  def addLeft(self, op):
    """Add left child token."""
    # List case.
    if is_listing(op):
      for ii in op:
        self.addleft(ii)
      return
    # Single case.
    if not is_glsl_token(op):
      raise RuntimeError("trying to add left non-token '%s'" % (str(left)))
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
    if not is_glsl_token(op):
      raise RuntimeError("trying to add right non-token '%s'" % (str(left)))
    self.__right += [op]
    op.setParent(self)

  def applyOperator(self, oper, left_token, right_token):
    """Apply operator, collapsing into one number if possible."""
    left = left_token.getSingleChild()
    right = right_token.getSingleChild()
    if (not is_glsl_number(left)) or (not is_glsl_number(right)):
      return False
    # If operator is division and we are a right child of a division, multiply instead.
    if (oper == "/") and self.isSingleChildRight():
      oper = interpret_operator("*")
    # Resolve to float if either is a float.
    if is_glsl_float(left) or is_glsl_float(right):
      left_number = left.getFloat()
      right_number = right.getFloat()
    else:
      left_number = left.getInt()
      right_number = right.getInt()
    if (left_number is None) or (right_number is None):
      raise RuntimeError("error getting number values")
    # Perform operation.
    result_number = oper.applyOperator(left_number, right_number)
    # Remove sides from parent.
    left_token.removeFromParent()
    right_token.removeFromParent()
    # Replace content of this with the result number
    if is_glsl_float(left) or is_glsl_float(right):
      number_string = str(float(result_number))
      (integer_part, decimal_part) = number_string.split(".")
      result_number = interpret_float(integer_part, decimal_part)
    else:
      result_number = interpret_int(str(result_number))
    result_number.truncatePrecision(max(left.getPrecision(), right.getPrecision()))
    self.__middle = [result_number]
    return True

  def collapse(self):
    """Collapse degenerate trees."""
    if (len(self.__left) == 0) and (len(self.__right) == 0) and (len(self.__middle) == 1):
      middle = self.__middle[0]
      if is_glsl_token(middle):
        self.__left = middle.__left
        for ii in self.__left:
          ii.setParent(None)
          ii.setParent(self)
        self.__right = middle.__right
        for ii in self.__right:
          ii.setParent(None)
          ii.setParent(self)
        self.__middle = middle.__middle
        for ii in self.__middle:
          if is_glsl_token(ii):
            ii.setParent(None)
            ii.setParent(self)
        # Retry.
        self.collapse()
        return
    # Descend left.
    for ii in self.__left:
      ii.collapse()
    # Descend right.
    for ii in self.__right:
      ii.collapse()
    # Descend missle.
    for ii in self.__middle:
      if is_glsl_token(ii):
        ii.collapse()

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
      elif ii:
        ret += [ii]
      else:
        raise RuntimeError("empty element found during flatten")
    # Right.
    for ii in self.__right:
      ret += ii.flatten()
    return ret

  def flattenString(self):
    """Flatten this token into a string."""
    ret = ""
    tokens = self.flatten()
    for ii in tokens:
      ret += ii.format(False)
    return ret

  def getSingleChild(self):
    """Degeneration preventation. If token only has a single child, return that instead."""
    lr = len(self.__left) + len(self.__right)
    # If left and right exist, return node itself - there is no single child here.
    if 0 < lr:
      if not self.__middle and ((not self.__left) or (not self.__right)):
        raise RuntimeError("empty middle only allowed if bothe left and right exist")
      return self
    # If left and right did not exist, return middle.
    elif self.__middle:
      if is_listing(self.__middle):
        if 1 >= len(self.__middle):
          return self.__middle[0]
      return self.__middle
    # Should never happen.
    raise RuntimeError("token has no content")

  def getSingleChildLeft(self):
    """Get right child if it's a single token."""
    if (len(self.__left) == 1) and is_glsl_token(self.__left[0]):
      return self.__left[0]
    return None

  def getSingleChildMiddleNonToken(self):
    """Get the single non-token middle child, even if left and right exist."""
    if (len(self.__middle) == 1) and (not is_glsl_token(self.__middle[0])):
      return self.__middle[0]
    return None

  def getSingleChildRight(self):
    """Get right child if it's a single token."""
    if (len(self.__right) == 1) and is_glsl_token(self.__right[0]):
      return self.__right[0]
    return None

  def getWeakerParent(self):
    """Get weaker parent node."""
    global DEBUG
    oper = self.getSingleChild()
    if DEBUG:
      print(str(self.__parent))
    if not is_glsl_operator(oper) or (not self.__parent):
      return None
    parent_oper = self.__parent.getSingleChild()
    if DEBUG:
      print(str(parent_oper))
    if parent_oper.getPrecedence() < oper.getPrecedence():
      raise RuntimeError("priority inversion")
    if parent_oper.getPrecedence() == oper.getPrecedence():
      return self.__parent
    return None

  def getWeakerElementLeft(self):
    """Get weaker element from left."""
    oper = self.getSingleChildMiddleNonToken()
    if not is_glsl_operator(oper):
      return None
    left = self.getSingleChildLeft()
    if not left:
      return None
    left_oper = left.getSingleChild()
    if is_glsl_number(left_oper):
      return left
    # Go right in tree.
    left_oper = left.getSingleChildMiddleNonToken()
    while is_glsl_operator(left_oper) and (left_oper.getPrecedence() == oper.getPrecedence()):
      left = left.getSingleChildRight()
      left_oper = left.getSingleChildMiddleNonToken()
      if is_glsl_number(left_oper):
        return left
    return None

  def getWeakerElementRight(self):
    """Get weaker element from right."""
    oper = self.getSingleChildMiddleNonToken()
    if not is_glsl_operator(oper):
      return None
    right = self.getSingleChildRight()
    if not right:
      return None
    right_oper = right.getSingleChild()
    if is_glsl_number(right_oper):
      return right
    # Go right in tree.
    right_oper = right.getSingleChildMiddleNonToken()
    while is_glsl_operator(right_oper) and (right_oper.getPrecedence() == oper.getPrecedence()):
      right = right.getSingleChildLeft()
      right_oper = right.getSingleChildMiddleNonToken()
      if is_glsl_number(right_oper):
        return right
    return None

  def hasWeakerTreeLeft(self):
    """Tell if a weaker precedence tree exists to the left."""
    elem = self.getWeakerElementLeft()
    return not (elem is None)

  def hasWeakerTreeRight(self):
    """Tell if a weaker precedence tree exists to the right."""
    elem = self.getWeakerElementRight()
    return not (elem is None)

  def isSingleChildRight(self):
    """Tell if this is the single, right child of its parent."""
    if self.__parent and (self.__parent.getSingleChildRight() == self):
      return True
    return False

  def removeChild(self, op):
    """Remove a child from this."""
    for ii in range(len(self.__left)):
      vv = self.__left[ii]
      if vv == op:
        self.__left.pop(ii)
        return
    for ii in range(len(self.__right)):
      vv = self.__right[ii]
      if vv == op:
        self.__right.pop(ii)
        return
    for ii in range(len(self.__middle)):
      vv = self.__middle[ii]
      if vv == op:
        self.__middle.pop(ii)
        return
    raise RuntimeError("could not remove child '%s' from '%s'" % (str(op), str(self)))

  def removeFromParent(self):
    """Remove this from its parent."""
    self.__parent.removeChild(self)
    self.__parent = None

  def setParent(self, op):
    """Set parent."""
    if op and self.__parent and (self.__parent != op):
      raise RuntimeError("hierarchy inconsistency in '%s', parent '%s' over existing '%s'" %
          (str(self), str(op), str(self.__parent)))
    self.__parent = op

  def simplify(self):
    """Perform any simple simplification and stop."""
    global DEBUG
    # Trivial case, single-element expression surrounded by parens.
    if (len(self.__left) == 1) and (len(self.__right) == 1):
      left = self.__left[0].getSingleChild()
      right = self.__right[0].getSingleChild()
      if ("(" == left) and (")" == right):
        if len(self.__middle) == 1:
          middle = self.__middle[0]
          if (not is_glsl_token(middle)) or (len(middle.flatten()) == 1):
            self.__left[0].removeFromParent()
            self.__right[0].removeFromParent()
            self.__left = []
            self.__right = []
            return True
    # Recurse down.
    for ii in self.__left:
      if ii.simplify():
        return True
    for ii in self.__right:
      if ii.simplify():
        return True
    for ii in self.__middle:
      if is_glsl_token(ii):
        if ii.simplify():
          return True
    # Perform operations only after removing any possible parens, highest precedence first due to tree shape.
    if (len(self.__middle) == 1):
      oper = self.__middle[0]
      if is_glsl_operator(oper):
        left_token = None
        right_token = None
        if (len(self.__left) == 1) and self.hasWeakerTreeRight():
          left_token = self.__left[0]
          right_token = self.getWeakerElementRight()
        elif (len(self.__right) == 1) and self.hasWeakerTreeLeft():
          left_token = self.getWeakerElementLeft()
          right_token = self.__right[0]
        elif (len(self.__left) == 1) and (len(self.__right) == 1):
          left_token = self.__left[0]
          right_token = self.__right[0]
        # If we got two terms, operate.
        if left_token and right_token:
          # Try to collapse obvious multiply or divide by ones.
          if oper.getOperator() == "*":
            left = left_token.getSingleChild()
            right = right_token.getSingleChild()
            if is_glsl_number(left) and (left.getFloat() == 1.0):
              left_token.removeFromParent()
              right_token.removeFromParent()
              self.__middle = []
              self.addMiddle(right_token)
              return True
            if is_glsl_number(right) and (right.getFloat() == 1.0):
              left_token.removeFromParent()
              right_token.removeFromParent()
              self.__middle = []
              self.addMiddle(left_token)
              return True
          elif oper.getOperator() == "/":
            right = right_token.getSingleChild()
            if is_glsl_number(right) and (right.getFloat() == 1.0):
              left_token.removeFromParent()
              right_token.removeFromParent()
              self.__middle = []
              self.addMiddle(left_token)
              return True
          # Fall back to normal method
          if self.applyOperator(oper, left_token, right_token):
            return True
    return False

  def __str__(self):
    """String representation."""
    if 1 == len(self.__middle):
      return "Token(%i:'%s':%i)" % (len(self.__left), str(self.__middle[0]), len(self.__right))
    return "Token(%i:%i:%i)" % (len(self.__left), len(self.__middle), len(self.__right))

########################################
# Functions ############################
########################################

def get_single_token(op):
  """Return single token element from given list, if possible."""
  if is_glsl_token(op):
    return op.getSingleChild()
  return None

def is_glsl_number(op):
  """Tell if given object is a number."""
  if is_glsl_float(op) or is_glsl_int(op):
    return True
  return False

def is_glsl_token(op):
  """Tell if given object is a GLSL token."""
  return isinstance(op, GlslToken)

def token_descend(token):
  """Descend token or token list."""
  # Single element case.
  if is_glsl_token(token):
    token.setParent(None)
    single = token.getSingleChild()
    if single == token:
      return token
    return token_descend(single)
  # Listing case.
  if is_listing(token):
    for ii in token:
      ii.setParent(None)
      if not is_glsl_token(ii):
        raise RuntimeError("non-token '%s' found in descend" % (str(ii)))
    if len(token) == 1:
      return token_descend(token[0])
  # Could not descend.
  return token

def token_list_create(lst):
  """Build a token list from a given listing, ensuring every element is a token."""
  ret = []
  for ii in lst:
    if not is_glsl_token(ii):
      ret += [GlslToken(ii)]
    elif ii:
      ret += [ii]
  return ret

def token_tree_build(lst):
  """Builds and balances a token tree from given list."""
  # Ensure all list elements are tokens.
  lst = token_list_create(lst)
  # Might be that everything is lost at this point.
  if not lst:
    return None
  # Start iteration over tokenized list.
  bracket_count = 0
  paren_count = 0
  first_bracket_index = -1
  first_paren_index = -1
  highest_operator = None
  highest_operator_index = -1
  for ii in range(len(lst)):
    vv = lst[ii].getSingleChild()
    # Count parens.
    if is_glsl_paren(vv):
      # Bracket case.
      if vv.isBracket():
        new_bracket_count = vv.updateBracket(bracket_count)
        if new_bracket_count == bracket_count:
          raise RuntimeError("wut?")
        bracket_count = new_bracket_count
        # Split on brackets reaching 0.
        if 0 >= bracket_count:
          if 0 > first_bracket_index:
            raise RuntimeError("bracket inconsistency")
          return token_tree_split_paren(lst, first_bracket_index, ii)
        elif (1 == bracket_count) and (0 > first_bracket_index):
          first_bracket_index = ii
      # Paren case.
      elif vv.isParen():
        new_paren_count = vv.updateParen(paren_count)
        if new_paren_count == paren_count:
          raise RuntimeError("wut?")
        paren_count = new_paren_count
        # Split on parens reaching 0.
        if 0 >= paren_count:
          if 0 > first_paren_index:
            raise RuntimeError("paren inconsistency")
          return token_tree_split_paren(lst, first_paren_index, ii)
        elif (1 == paren_count) and (0 > first_paren_index):
          first_paren_index = ii
      # Curly braces impossible.
      else:
        raise RuntimeError("unknown paren object '%s'" % (str(vv)))
    # If we're not within parens, consider operators.
    if is_glsl_operator(vv) and (0 >= bracket_count) and (0 >= paren_count):
      if (not highest_operator) or (highest_operator < vv):
        highest_operator = vv
        highest_operator_index = ii
  # Iteration done. Collect the pieces.
  if highest_operator:
    left = token_tree_build(lst[:highest_operator_index])
    right = token_tree_build(lst[highest_operator_index + 1:])
    ret = GlslToken(highest_operator)
    # Left must exist as long as the operator is not unary minus.
    if left:
      ret.addLeft(left)
    elif not (highest_operator in ("-", "++", "--")):
      raise RuntimeError("left component nonexistent for operator '%s'" % (str(highest_operator)))
    # Right may not exist if this is the child tree of token from unary minus.
    if right:
      ret.addRight(right)
    return ret
  # Only option at this point is that the list has no operators and no parens - return as itself.
  return GlslToken(lst)

def token_tree_simplify(op):
  """Perform first found simplify operation for given tree."""
  op.collapse()
  if op.simplify():
    return True
  return False

def token_tree_split_paren(lst, first, last):
  """Split token tree for parens."""
  # Read types, names or accesses left.
  left = [lst[first]]
  iter_left = first - 1
  while iter_left >= 0:
    prospect = lst[iter_left].getSingleChild()
    if is_glsl_access(prospect) or is_glsl_name(prospect) or is_glsl_type(prospect):
      left = [lst[iter_left]] + left
      iter_left -= 1
    else:
      break
  # Left may be multiple elements.
  if 1 < len(left):
    left = GlslToken(left)
  else:
    left = left[0]
  # It's ok to have empty parens, as opposed to empty brackets.
  middle = token_tree_build(lst[first + 1 : last])
  right = lst[last]
  # Create split.
  ret = GlslToken(middle)
  ret.addLeft(left)
  ret.addRight(right)
  return token_tree_build(lst[:iter_left + 1] + [ret] + lst[last + 1:])
