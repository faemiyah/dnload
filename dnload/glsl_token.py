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
      return None
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
    # Replace content of this with the result number
    if is_glsl_float(left) or is_glsl_float(right):
      number_string = str(float(result_number))
      (integer_part, decimal_part) = number_string.split(".")
      result_number = interpret_float(integer_part, decimal_part)
    else:
      result_number = interpret_int(str(result_number))
    result_number.truncatePrecision(max(left.getPrecision(), right.getPrecision()))
    return result_number

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

  def collapseIdentity(self):
    """Collapse identity transforms that do not do anything."""
    oper = self.getSingleChildMiddleNonToken()
    if not is_glsl_operator(oper):
      raise RuntimeError("must be an operator to collapse identities")
    left_token = self.getSingleChildLeft()
    right_token = self.getSingleChildRight()
    # If right or left tokens not found, not eligible for identity collapse.
    if (not left_token) or (not right_token):
      return False
    left = left_token.getSingleChild()
    right = right_token.getSingleChild()
    # Can't collapse if either side is in itself an operator.
    if is_glsl_operator(left) or is_glsl_operator(right):
      return False
    # Multiply by one.
    if oper.getOperator() == "*":
      if is_glsl_number(left) and (left.getFloat() == 1.0):
        self.collapseMiddleLeft()
        return True
      if is_glsl_number(right) and (right.getFloat() == 1.0):
        self.collapseMiddleRight()
        return True
    # Divide by one.
    elif oper.getOperator() == "/":
      if is_glsl_number(right) and (right.getFloat() == 1.0):
        self.collapseMiddleRight()
        return True
    # Substract zero.
    elif oper.getOperator() == "-":
      if is_glsl_number(right) and (right.getFloat() == 0.0):
        self.collapseMiddleRight()
        return True
    # Add zero.
    elif oper.getOperator() == "+":
      if is_glsl_number(left) and (left.getFloat() == 0.0):
        self.collapseMiddleLeft()
        return True
      if is_glsl_number(right) and (right.getFloat() == 0.0):
        self.collapseMiddleRight()
        return True
    # No collapses found.
    return False

  def collapseMiddleLeft(self):
    """Collapse left and middle parts of this token."""
    left = self.getSingleChildLeft()
    right = self.getSingleChildRight()
    if (not left) or (not right):
      raise RuntimeError("cannot collapse if both left and right are not single tokens")
    left.removeFromParent()
    right.removeFromParent()
    self.replaceMiddle(right)

  def collapseMiddleRight(self):
    """Collapse left and middle parts of this token."""
    left = self.getSingleChildLeft()
    right = self.getSingleChildRight()
    if (not left) or (not right):
      raise RuntimeError("cannot collapse if both left and right are not single tokens")
    left.removeFromParent()
    right.removeFromParent()
    self.replaceMiddle(left)

  def collapseUp(self):
    """Collapse this token and its parent."""
    # Remove self from parent.
    parent = self.__parent
    self.removeFromParent()
    # Find remaining child of parent, remove it.
    left = parent.getSingleChildLeft()
    right = parent.getSingleChildRight()
    if left and right:
      raise RuntimeError("parent retains both children after removing child")
    remaining = left
    if not remaining:
      remaining = right
    remaining.removeFromParent()
    # Replace parent in its parent with the remaining element.
    parent.replaceInParent(remaining)

  def flatten(self):
    """Flatten this token into a list."""
    ret = []
    # Left
    for ii in self.__left:
      ret += ii.flatten()
    # Middle may be a token or an element.
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

  def findEqualToken(self, orig):
    """Find a token or a number that has equal priority to given token."""
    mid = self.getSingleChildMiddleNonToken()
    if not mid:
      return (None, None)
    if is_glsl_number(mid):
      return (orig, self)
    if is_glsl_operator(mid):
      if mid.getPrecedence() is orig.getPrecedenceIfOperator():
        lt = self.getSingleChildLeft()
        if lt and lt.getSingleChildMiddleNonToken():
          (lt_oper, lt_token) = lt.findEqualToken(self)
          if lt_oper and lt_token:
            return (lt_oper, lt_token)
        rt = self.getSingleChildRight()
        if rt and rt.getSingleChildMiddleNonToken():
          (rt_oper, rt_token) = rt.findEqualToken(self)
          if rt_oper and rt_token:
            return (rt_oper, rt_token)
    return (None, None)

  def findEqualTokenLeft(self, orig):
    """Find a token from the left tree that has equal priority path to this operator."""
    lt = self.getSingleChildLeft()
    if lt and lt.getSingleChildMiddleNonToken():
      return lt.findEqualToken(orig)
    return (None, None)

  def findEqualTokenRight(self, orig):
    """Find a token from the right tree that has equal priority path to this operator."""
    rt = self.getSingleChildRight()
    if rt and rt.getSingleChildMiddleNonToken():
      return rt.findEqualToken(orig)
    return (None, None)

  def findHighestPrioOperatorMiddle(self):
    """Find highest priority operator from elements in the middle."""
    prio = -1
    for ii in self.__middle:
      mid = ii.getSingleChildMiddleNonToken()
      if is_glsl_operator(mid):
        prio = max(prio, mid.getPrecedence())
    return prio

  def findSiblingOperatorLeft(self):
    """Find nearest left operator."""
    if not self.__parent:
      return None
    mid = self.__parent.getSingleChildMiddleNonToken()
    if not is_glsl_operator(mid):
      return None
    if self.__parent.getSingleChildLeft() != self:
      return mid
    return self.__parent.findSiblingOperatorLeft()

  def findSiblingOperatorRight(self):
    """Find nearest right operator."""
    if not self.__parent:
      return None
    mid = self.__parent.getSingleChildMiddleNonToken()
    if not is_glsl_operator(mid):
      return None
    if self.__parent.getSingleChildRight() != self:
      return mid
    return self.__parent.findSiblingOperatorRight()

  def getPrecedenceIfOperator(self):
    """Return precedence if middle element is a single child that is an operator."""
    mid = self.getSingleChildMiddleNonToken()
    if mid and is_glsl_operator(mid):
      return mid.getPrecedence()
    return None

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

  def isSingleChildRight(self):
    """Tell if this is the single, right child of its parent."""
    if self.__parent and (self.__parent.getSingleChildRight() == self):
      return True
    return False

  def isSurroundedByParens(self):
    """Tell if this is a token surrounded by parens."""
    if (len(self.__left) != 1) or (len(self.__right) != 1):
      return False
    left = self.__left[0].getSingleChild()
    right = self.__right[0].getSingleChild()
    return ("(" == left) and (")" == right)

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

  def removeParens(self):
    """Remove enclosing parens if possible."""
    if not self.isSurroundedByParens():
      return False
    # Was enclosed by parens, can remove.
    self.__left[0].removeFromParent()
    self.__right[0].removeFromParent()
    self.__left = []
    self.__right = []
    return True

  def replaceMiddle(self, op):
    """Replace middle content with something that is not a token."""
    self.__middle = []
    self.addMiddle(op)

  def replaceInParent(self, op):
    """Replace this token in its parent with given replacement."""
    parent = self.__parent
    if not parent:
      raise RuntimeError("no parent to replace '%s' with '%s' in" % (str(self), str(op)))
    if parent.getSingleChildLeft() == self:
      self.removeFromParent()
      parent.addLeft(op)
    elif parent.getSingleChildRight() == self:
      self.removeFromParent()
      parent.addRight(op)
    else:
      raise RuntimeError("'%s' is not left or right single child of its parent '%s'" % (str(self), str(parent)))

  def setParent(self, op):
    """Set parent."""
    if op and self.__parent and (self.__parent != op):
      raise RuntimeError("hierarchy inconsistency in '%s', parent '%s' over existing '%s'" %
          (str(self), str(op), str(self.__parent)))
    self.__parent = op

  def simplify(self):
    """Perform any simple simplification and stop."""
    # Remove parens.
    if self.isSurroundedByParens():
      # Single expression.
      if len(self.__middle) == 1:
        middle = self.__middle[0]
        if (not is_glsl_token(middle)) or (len(middle.flatten()) == 1):
          if self.removeParens():
            return True
      # Number or name with access.
      elif len(self.__middle) == 2:
        mid_lt = self.__middle[0].getSingleChild()
        mid_rt = self.__middle[1].getSingleChild()
        if (is_glsl_name(mid_lt) or is_glsl_number(mid_lt)) and is_glsl_access(mid_rt):
          if self.removeParens():
            return True
      # Only contains lower-priority operators compared to outside.
      prio = self.findHighestPrioOperatorMiddle()
      if prio >= 0:
        left = self.findSiblingOperatorLeft()
        right = self.findSiblingOperatorRight()
        if left:
          if left.getPrecedence() > prio:
            if right:
              if right.getPrecedence() >= prio:
                if self.removeParens():
                  return True
            elif self.removeParens():
              return True
        elif right:
          if right.getPrecedence() >= prio:
            if self.removeParens():
              return True
        else:
          if self.removeParens():
            return True
    # Check for allowing simpler representation of constants.
    mid = self.getSingleChildMiddleNonToken()
    if mid and is_glsl_float(mid):
      left = self.findSiblingOperatorLeft()
      right = self.findSiblingOperatorRight()
      if not left and not right:
        if is_glsl_float(mid) and (not mid.isIntegrifyAllowed()):
          mid.setAllowIntegrify(True)
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
    # Perform operations only after removing any possible parens.
    if (len(self.__middle) == 1):
      oper = self.__middle[0]
      if is_glsl_operator(oper) and oper.isApplicable():
        # Try to remove trivial cases.
        if self.collapseIdentity():
          return True
        (left_parent, left_token) = self.findEqualTokenLeft(self)
        (right_parent, right_token) = self.findEqualTokenRight(self)
        if left_parent and left_token and right_parent and right_token:
          # Trivial case - leaf entry that can just be applied.
          if left_parent is right_parent:
            if not (left_parent is self):
              raise RuntimeError("left and right operator resolve as '%s' not matching self '%s'" %
                  (str(left_parent), str(self)))
            result = self.applyOperator(oper, left_token, right_token)
            if not (result is None):
              # Remove sides from parent.
              left_token.removeFromParent()
              right_token.removeFromParent()
              self.__middle = [result]
              return True
          # Nontrivial cases.
          left_oper = left_parent.getSingleChildMiddleNonToken()
          right_oper = right_parent.getSingleChildMiddleNonToken()
          result = None
          # Double divide -> multiply.
          if (left_oper == "/") and (right_oper == "/") and left_token.isSingleChildRight():
            result = self.applyOperator(interpret_operator("*"), left_token, right_token)
          # Same operation -> can be just applied.
          elif left_parent == right_parent:
            result = self.applyOperator(left_oper, left_token, right_token)
          # TODO: further cases.
          # On success, eliminate upper token (left only if necessary) and replace other token with result.
          if result:
            if left_parent is self:
              right_token.collapseUp()
              left_token.replaceMiddle(result)
            else:
              left_token.collapseUp()
              right_token.replaceMiddle(result)
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
  lowest_operator = None
  lowest_operator_index = -1
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
      if (not lowest_operator) or (vv < lowest_operator):
        lowest_operator = vv
        lowest_operator_index = ii
  # Iteration done. Make a tiny subtree on the lowest operator position and continue.
  if lowest_operator:
    ret = GlslToken(lowest_operator)
    left_block = []
    right_block = []
    left = None
    right = None
    # Get extending list left and right.
    if lowest_operator_index >= 2:
      left_block = lst[:(lowest_operator_index - 1)]
    if lowest_operator_index <= len(lst) - 3:
      right_block = lst[(lowest_operator_index + 2):]
    # Check for left existing.
    if lowest_operator_index >= 1:
      left = lst[lowest_operator_index - 1]
      ret.addLeft(left)
    elif not (lowest_operator in ("-", "++", "--", "!")):
      raise RuntimeError("left component nonexistent for operator '%s'" % (str(lowest_operator)))
    # Check for right existing.
    if lowest_operator_index <= len(lst) - 2:
      right = lst[lowest_operator_index + 1]
      ret.addRight(right)
    elif not (lowest_operator in ("++", "--")):
      raise RuntimeError("right component nonexistent for operator '%s'" % (str(lowest_operator)))
    return token_tree_build(left_block + [ret] + right_block)
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
