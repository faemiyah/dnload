import re

########################################
# GlslInt ##############################
########################################

class GlslInt:
  """GLSL integer."""

  def __init__(self, source):
    """Constructor."""
    if source[0] in ("-", "+"):
      self.__sign = source[0]
      self.__string = source[1:]
      # Plus sign does not need preservation.
      if self.__sign == "+":
        self.__sign = ""
    else:
      self.__sign = ""
      self.__string = source
    self.__number = int(source)

  def format(self, force):
    """Return formatted output."""
    return str(self.__number)

  def getFloat(self):
    """Floating point representation."""
    return float(self.__number)

  def getInt(self):
    """Integer representation."""
    return self.__number

  def getPrecision(self):
    """Get precision - number of numbers to express."""
    return len(self.__string.strip("+-0"))

  def getSign(self):
    """Access sign, only minus sign is preserved."""
    return self.__sign

  def getStr(self):
    """Access actual string."""
    return self.__sign + self.__string

  def truncatePrecision(self, op):
    """Truncate numeric precision to some value of expressed numbers."""
    # If the number is 0, it has no precision.
    if self.__number == 0:
      return 0
    # Preserve zeroes in front. They are not counted.
    zeroes_front = ""
    rest = self.__string
    for ii in range(len(rest)):
      if self.__string[ii] != "0":
        if ii > 0:
          zeroes_front = rest[:ii]
          rest = rest[ii:]
        break
    # Preserve zeroes in back. Also not counted.
    zeroes_back = ""
    for ii in reversed(range(len(rest))):
      if rest[ii] != "0":
        if ii < (len(rest) - 1):
          zeroes_back = rest[ii + 1:]
          rest = rest[:ii + 1]
        break
    # If length of rest is smaller than truncation, just return it.
    if len(rest) <= op:
      return len(rest)
    # Round the result.
    divisor = pow(10, len(rest) - op)
    rest = str(int(round(float(rest) / float(divisor))) * divisor)
    self.__string = zeroes_front + rest + zeroes_back
    self.__number = int(self.__sign + self.__string)
    return op

  def __str__(self):
    """String representation."""
    return "GlslInt('%s')" % (self.__string)

########################################
# Functions ############################
########################################

def interpret_int(source):
  """Try to interpret integer."""
  if re.match(r'^\-?\d+f?$', source):
    # Suffixing number with 'f' is not allowd according to the spec, but NVidia accepts it.
    if source[-1] == "f":
      print("WARNING: GLSL: discarding number literal suffix for '%s'" % (source))
      return GlslInt(source[:-1])
    return GlslInt(source)
  return None

def is_glsl_int(op):
  """Tell if token is integer."""
  return isinstance(op, GlslInt)

def is_glsl_int_unsigned(op):
  """Tell if token is integer."""
  return isinstance(op, GlslInt) and (op.getInt() >= 0)
