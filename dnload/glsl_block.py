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
from dnload.glsl_type import interpret_type
from dnload.glsl_type import is_glsl_type
from dnload.glsl_swizzle import interpret_swizzle
from dnload.glsl_swizzle import is_glsl_swizzle
import re

########################################
# GlslBlock ############################
########################################

class GlslBlock:
  """GLSL block - represents one scope with sub-scopes, function, file, etc."""

  def __init__(self, source = None):
    """Constructor."""
    self._parse_tree = []
    self._source = source
    
########################################
# Functions ############################
########################################

def check_token(token, req):
  """Check if token is acceptable but do not compare against types."""
  if not isinstance(req, str):
    raise RuntimeError("request '%s' is not a string" % (str(req)))
  if isinstance(token, str) and (token == req):
    return True
  if is_glsl_name(token) and token.isLocked() and (token.format() == req):
    return True
  if is_glsl_operator(token) and (token.format() == req):
    return True
  return False

def extract_statement(source):
  """Extracts one statement for parsing."""
  ii = source.find(";")
  if 0 > ii:
    return (None, source)
  ii += 1
  return (tokenize(source[:ii].strip()), source[ii:])

def extract_scope(tokens, opener):
  """Extract scope from token list. Needs scope opener to already be extracted."""
  if "{" == opener:
    closer = "}"
  elif "[" == opener:
    closer = "]"
  elif "(" == opener:
    closer = ")"
  else:
    return (None, tokens)
  # Must find exact matching paren.
  paren_count = 1
  ret = []
  for ii in range(len(tokens)):
    elem = tokens[ii]
    if elem == opener:
      paren_count += 1
    elif elem == closer:
      paren_count -= 1
      if 0 >= paren_count:
        return (ret, tokens[ii + 1:])
    ret += [elem]
  # Did not find closing scope element.
  return (None, tokens)

def extract_tokens(tokens, required):
  """Require tokens from token string, return selected elements and the rest of tokens."""
  #print("'%s' vs:\n%s" % (str(required), str(tokens)))
  ret = []
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
  success = True
  while content and required:
    curr = content.pop(0)
    req = required.pop(0)
    # Token request.
    if "?" == req[:1]:
      desc = req[1:]
      # Extracting scope.
      if desc in ("{", "[", "("):
        if curr == desc:
          (scope, remaining) = extract_scope(content, curr)
          if not (scope is None):
            ret += [scope]
            content = remaining
            continue
          #else:
          #  print("parsing scope failed: '%s' vs. '%s':\n%s" % (curr, desc, str(content)))
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

def tokenize(source):
  """Split statement into tokens."""
  return tokenize_interpret(tokenize_split(source))

def tokenize_interpret(tokens):
  """Interpret a list of preliminary tokens, assembling constructs from them."""
  ret = []
  ii = 0
  while len(tokens) > ii:
    element = tokens[ii]
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
    # Try type.
    typeid = interpret_type(element)
    if typeid:
      ret += [typeid]
      ii += 1
      continue
    # Period may signify swizzle or truncated floating point.
    if "." == tokens[ii] and (ii + 1) < len(tokens):
      decimal = interpret_int(tokens[ii + 1])
      if decimal:
        ret += [interpret_float(0, decimal)]
        ii += 2
        continue
      swizzle = interpret_swizzle(tokens[ii + 1])
      if swizzle:
        ret += [swizzle]
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
  array = re.split(r'([\(\)\[\]\{\}\+\-\*\/\.,;:\=])', source, 1)
  if 3 > len(array):
    return [source]
  return filter(lambda x: x, array[:2]) + tokenize_split(array[2])

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
  # Swizzle.
  elif "s" == validation:
    if not is_glsl_swizzle(token):
      return None
  # Operator =.
  elif validation in ("="):
    if not is_glsl_operator(token) and (token.format() != validation):
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
  # Valid identifier name.
  elif "n" == validation:
    if not is_glsl_name(token):
      return None
  # Select from options.
  elif validation.find("|") >= 0:
    if not token in validation.split("|"):
      return None
  # Unknown validation.
  else:
    raise RuntimeError("unknown token request '%s'" % (validation))
  # On success, return token as-is.
  return token
