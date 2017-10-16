import re

from dnload.common import is_listing
from dnload.glsl_access import interpret_access
from dnload.glsl_access import is_glsl_access
from dnload.glsl_control import interpret_control
from dnload.glsl_control import is_glsl_control
from dnload.glsl_int import interpret_int
from dnload.glsl_int import is_glsl_int
from dnload.glsl_int import is_glsl_int_unsigned
from dnload.glsl_inout import interpret_inout
from dnload.glsl_inout import is_glsl_inout
from dnload.glsl_float import interpret_float
from dnload.glsl_float import is_glsl_float
from dnload.glsl_name import interpret_name
from dnload.glsl_name import is_glsl_name
from dnload.glsl_operator import interpret_operator
from dnload.glsl_operator import is_glsl_operator
from dnload.glsl_paren import interpret_paren
from dnload.glsl_paren import is_glsl_paren
from dnload.glsl_terminator import interpret_terminator
from dnload.glsl_terminator import is_glsl_terminator
from dnload.glsl_type import interpret_type
from dnload.glsl_type import is_glsl_type

########################################
# GlslBlock ############################
########################################

class GlslBlock:
  """GLSL block - represents one scope with sub-scopes, function, file, etc."""

  def __init__(self):
    """Constructor."""
    self._children = []
    self.__accesses = []
    self.__names_declared = set()
    self.__names_used = []
    self.__parent = None

  def addAccesses(self, op):
    if is_listing(op):
      for ii in op:
        self.addAccesses(ii)
      return
    if not is_glsl_access(op):
      return
    self.__accesses += [op]

  def addChildren(self, lst, prepend = False):
    """Add another block as a child of this."""
    if not is_listing(lst):
      self.addChildren([lst])
      return
    for ii in lst:
      if not is_glsl_block(ii):
        raise RuntimeError("element '%s' to be added is not of type GlslBlock" % (str(ii)))
      if ii.getParent():
        raise RuntimeError("block '%s' to be added already has parent '%s'" % (str(ii), str(ii.getParent())))
      if prepend:
        self._children = [ii] + self._children
      else:
        self._children += [ii]
      ii.setParent(self)
      if ii.getParent() != self:
        raise RuntimeError("")

  def addNamesDeclared(self, op):
    """Add given names as names declared by this block."""
    if is_listing(op):
      for ii in op:
        self.addNamesDeclared(ii)
      return
    if not is_glsl_name(op):
      return
    if op in self.__names_declared:
      raise RuntimeError("declaring name '%s' twice" % (op))
    self.__names_declared.add(op)

  def addNamesUsed(self, op):
    """Add given names as names used by this block."""
    if is_listing(op):
      for ii in op:
        self.addNamesUsed(ii)
      return
    if not is_glsl_name(op):
      return
    self.__names_used += [op]

  def clearAccesses(self):
    """Clear accesses."""
    self.__accesses = []

  def clearNamesUsed(self):
    """Clear used names."""
    self.__names_used = []

  def collapse(self, other):
    """Default collapse implementation, returns False because no collapse happened."""
    return False

  def collapseRecursive(self):
    """Collapse collapsable elements."""
    ret = 0
    while True:
      if not self.collapseRun():
        break
      ret += 1
    for ii in self._children:
      ret += ii.collapseRecursive()
    return ret

  def collapseRun(self):
    """Perform one collapse run. Return true if collapse was made."""
    for ii in range(len(self._children) - 1):
      vv = self._children[ii]
      ww = self._children[ii + 1]
      if vv.collapse(ww):
        self._children.pop(ii + 1)
        return True
    return False

  def collect(self):
    """Collect all uses of identifiers."""
    ret = []
    for ii in range(len(self._children)):
      vv = self._children[ii]
      for name in vv.getDeclaredNames():
        if name.isLocked():
          continue
        array = vv.collectRecursive(name)
        for jj in range(ii + 1, len(self._children)):
          ww = self._children[jj]
          if ww.hasDeclaredName(name):
            break
          array += ww.collectRecursive(name)
        if not array:
          raise RuntimeError("identifier '%s' never referenced" % (name))
        ret += [[vv] + array]
      ret += vv.collect()
    return ret

  def collectAppend(self, op):
    """Append into already-collected list of identifiers."""
    # Reference name
    name = op[1]
    # Break if the name is declared, instruct upper level to break also.
    if self.hasDeclaredName(name):
      return True
    for ii in self.__names_used:
      if name == ii:
        op.append(ii)
    # Iterate children. Break iteration if a child declares the name.
    for ii in self._children:
      if ii.collectAppend(op):
        return False
    return False

  def collectRecursive(self, name):
    """Collect all uses of given name recursively."""
    ret = self.collectUsed(name)
    for ii in self._children:
      if ii.hasDeclaredName(name):
        return ret
      ret += ii.collectRecursive(name)
    return ret

  def collectUsed(self, name):
    """Collect all uses of given name."""
    ret = []
    for ii in self.__names_used:
      if name == ii:
        ret += [ii]
    return ret

  def expand(self):
    """Default implementation of expand, returns node itself."""
    return [self]

  def expandRecursive(self):
    """Expand all expandable children."""
    while True:
      if not self.expandRun():
        break
    for ii in self._children:
      ii.expandRecursive()

  def expandRun(self):
    """Perform one child expansion run. Return true if expansion was made."""
    for ii in range(len(self._children)):
      array = self._children[ii].expand()
      if 1 < len(array):
        self._children.pop(ii)
        self._children[ii:ii] = array
        for jj in array:
          jj.setParent(self)
        return True
    return False

  def getChildren(self):
    """Accessor."""
    return self._children

  def getDeclaredNames(self):
    """Accessor."""
    return self.__names_declared

  def getParent(self):
    """Accessor."""
    return self.__parent

  def getUsedNames(self):
    """Accessor."""
    return self.__names_used

  def hasChild(self, op):
    """Tell if list of children contains given child."""
    return (op in self._children)

  def hasDeclaredName(self, op):
    """Tell if this declares given name."""
    return op in self.__names_declared

  def hasLockedDeclaredName(self, op):
    """Tell if this declares given name that has been locked."""
    for ii in self.__names_declared:
      if ii.isLocked() and (ii.resolveName() == op):
        return True
    return False

  def hasLockedUsedName(self, op):
    """Tell if this uses given name that has been locked."""
    for ii in self.__names_used:
      if ii.isLocked() and (ii.resolveName() == op):
        return True
    return False

  def hasUsedName(self, op):
    """Tell if given name is used somewhere in this."""
    return op in self.__names_used

  def hasUsedNameExact(self, op):
    """Tell if given name object exactly is used somewhere in this."""
    for ii in self.__names_used:
      if op is ii:
        return True
    return False

  def removeChild(self, op):
    """Remove a child block."""
    for ii in range(len(self._children)):
      if self._children[ii] == op:
        self._children.pop(ii)
        return
    raise RuntimeError("could not find child to remove")

  def removeFromParent(self):
    """Remove this from its parent."""
    self.__parent.removeChild(self)
    self.__parent = None

  def selectSwizzle(self, op):
    """Recursively select swizzle method."""
    # Select here.
    for ii in self.__accesses:
      typeid = ii.getSourceType()
      if typeid:
        if is_glsl_type(typeid) and typeid.isVectorType():
          ii.selectSwizzle(op)
    # Recursively descend to children.
    for ii in self._children:
      ii.selectSwizzle(op)

  def simplify(self, max_simplifys):
    """Default implementation of simplify just recurses into children."""
    return 0

  def setParent(self, op):
    """Set parent of this block."""
    if op and (not op.hasChild(self)):
      raise RuntimeError("GlslBlock::setParent() hierarchy inconsistency")
    self.__parent = op

########################################
# Functions ############################
########################################

def check_token(token, req):
  """Check if token is acceptable but do not compare against types."""
  # Check against list, any option is ok.
  if is_listing(req):
    for ii in req:
      if check_token(token, ii):
        return True
    return False
  if not isinstance(req, str):
    raise RuntimeError("request '%s' is not a string" % (str(req)))
  # Tokens are converted to strings for comparison.
  if isinstance(token, str) and (token == req):
    return True
  return (token.format(False) == req)

def extract_scope(tokens, opener):
  """Extract scope from token list. Needs scope opener to already be extracted."""
  if not is_glsl_paren(opener):
    raise RuntimeError("no opener passed to scope extraction")
  paren_count = 1
  ret = []
  for ii in range(len(tokens)):
    elem = tokens[ii]
    if is_glsl_paren(elem):
      paren_count = opener.update(elem, paren_count)
      if 0 >= paren_count:
        return (ret, tokens[ii + 1:])
    ret += [elem]
  # Did not find closing scope element.
  return (None, tokens)

def extract_tokens(tokens, required):
  """Require tokens from token string, return selected elements and the rest of tokens."""
  # If required is just a string, make it a listing of length one.
  if not is_listing(required):
    required = (required,)
  # Generate array for returning on failure.
  failure_array = []
  for ii in required:
    if "?" == ii[:1]:
      failure_array += [None]
  failure_array += [tokens]
  # For straight-out incompatible request, get out immediately.
  if len(required) > len(tokens):
    return failure_array
  # Iterate over requests.
  content = tokens[:]
  required = list(required)
  ret = []
  success = True
  while content and required:
    curr = content.pop(0)
    req = required.pop(0)
    # Token request.
    if "?" == req[:1]:
      desc = req[1:]
      # Extracting scope.
      if desc in ("{", "[", "("):
        if curr.format(False) == desc:
          (scope, remaining) = extract_scope(content, curr)
          if not (scope is None):
            ret += [scope]
            content = remaining
            continue
        # Scope not found.
        return failure_array
      # Extracting singular element.
      validated = validate_token(curr, desc)
      if validated:
        ret += [validated]
      else:
        return failure_array
    # Not a request, compare verbatim. Names can be compared verbatim.
    elif not check_token(curr, req):
      return failure_array
  # Successful, return the remaining elements.
  return ret + [content]

def is_glsl_block(op):
  """Tell if given object is a Glsl block."""
  return isinstance(op, GlslBlock)

def tokenize(source):
  """Split statement into tokens."""
  return tokenize_interpret(tokenize_split(source))

def tokenize_interpret(tokens):
  """Interpret a list of preliminary tokens, assembling constructs from them."""
  ret = []
  ii = 0
  while len(tokens) > ii:
    element = tokens[ii]
    # Try paren.
    paren = interpret_paren(element)
    if paren:
      ret += [paren]
      ii += 1
      continue
    # Try 2-stage control.
    if (ii + 1) < len(tokens):
      control = interpret_control(element, tokens[ii + 1])
      if control:
        ret += [control]
        ii += 2
        continue
    # Try control.
    control = interpret_control(element)
    if control:
      ret += [control]
      ii += 1
      continue
    # Try in/out.
    inout = interpret_inout(element)
    if inout:
      ret += [inout]
      ii += 1
      continue
    # Try 2-stage type.
    if (ii + 1) < len(tokens):
      typeid = interpret_type(element, tokens[ii + 1])
      if typeid:
        ret += [typeid]
        ii += 2
        continue
    # Try type.
    typeid = interpret_type(element)
    if typeid:
      ret += [typeid]
      ii += 1
      continue
    # Period may signify truncated floating point or member/swizzle access.
    if "." == tokens[ii] and (ii + 1) < len(tokens):
      decimal = interpret_int(tokens[ii + 1])
      if decimal:
        ret += [interpret_float(0, decimal)]
        ii += 2
        continue
      access = interpret_access(tokens[ii + 1])
      if access:
        access.setSource(ret)
        ret += [access]
        ii += 2
        continue
    # Number may be just an integer or floating point.
    number = interpret_int(element)
    if number:
      if (ii + 1) < len(tokens) and "." == tokens[ii + 1]:
        if (ii + 2) < len(tokens):
          decimal = interpret_int(tokens[ii + 2])
          if decimal:
            ret += [interpret_float(number, decimal)]
            ii += 3
            continue
        ret += [interpret_float(number, 0)]
        ii += 2
        continue
      ret += [number]
      ii += 1
      continue
    # Special characters may be operators, up to two in a row.
    operator = interpret_operator(element)
    if operator:
      if (ii + 1) < len(tokens):
        extended_operator = interpret_operator(tokens[ii + 1])
        if extended_operator and operator.incorporate(extended_operator):
          ret += [operator]
          ii += 2
          continue
      ret += [operator]
      ii += 1
      continue
    # Statement terminator.
    terminator = interpret_terminator(element)
    if terminator:
      ret += [terminator]
      ii += 1
      continue
    # Try name identifier last.
    name = interpret_name(element)
    if name:
      ret += [name]
      ii += 1
      continue
    # Fallback is to add token as-is.
    ret += [element]
    ii += 1
  return ret

def tokenize_split(source):
  if not source:
    return []
  ret = []
  array = source.split()
  if 1 < len(array):
    for ii in array:
      ret += tokenize_split(ii)
    return ret
  array = re.split(r'([\(\)\[\]\{\}\+\-\*\/%\|&!\.,;:<>\=])', source, 1)
  if 3 > len(array):
    return [source]
  return list(filter(lambda x: x, array[:2])) + tokenize_split(array[2])

def validate_token(token, validation):
  """Validate that token matches given requirement."""
  # Unsigned int.
  if "u" == validation:
    if not is_glsl_int_unsigned(token):
      return None
  # Int.
  elif "i" == validation:
    if not is_glsl_int(token):
      return None
  # Float.
  elif "f" == validation:
    if not is_glsl_float(token):
      return None
  # Access.
  elif "a" == validation:
    if not is_glsl_access(token):
      return None
  # Operator =.
  elif validation in ("="):
    if (not is_glsl_operator(token)) or (not token.isAssignment()):
      return None
  # Control.
  elif "c" == validation:
    if not is_glsl_control(token):
      return None
  # In/out.
  elif "o" == validation:
    if not is_glsl_inout(token):
      return None
  # Type.
  elif "t" == validation:
    if not is_glsl_type(token):
      return None
  # Terminator.
  elif ";" == validation:
    if not is_glsl_terminator(token):
      return None
  # Valid identifier name.
  elif "n" == validation:
    if not is_glsl_name(token):
      return None
  # Select from options.
  elif validation.find("|") >= 0:
    variations = list(filter(lambda x: x, validation.split("|")))
    if not check_token(token, variations):
      return None
  # Unknown validation.
  else:
    raise RuntimeError("unknown token request '%s'" % (validation))
  # On success, return token as-is.
  return token
