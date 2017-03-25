from dnload.glsl_int import interpret_int

########################################
# GlslInt ##############################
########################################

class GlslFloat:
  """GLSL integer."""

  def __init__(self, integer1, integer2):
    """Constructor."""
    self.__integer1 = integer1
    self.__integer2 = integer2

  def format(self, force):
    """Return formatted output."""
    if 0 == self.__integer1.getInt():
      if 0 == self.__integer2.getInt():
        return ".0"
      return "." + self.__integer2.getStr().rstrip("0")
    return "%s.%s" % (str(self.__integer1.getInt()), self.__integer2.getStr().rstrip("0"))
  
  def __str__(self):
    """String representation."""
    return "GlslFloat('%s.%s')" % (self.__integer1.format(False), self.__integer2.format(False))
    
########################################
# Functions ############################
########################################

def convert_to_int(source):
  """Convert source to integer or fail."""
  if isinstance(source, str):
    return interpret_int(source)
  if isinstance(source, int):
    return interpret_int(str(source))
  return source

def interpret_float(source1, source2):
  """Try to interpret float."""
  number1 = convert_to_int(source1)
  if not number1:
    raise RuntimeError("not an integer: '%s'" % (source1))
  number2 = convert_to_int(source2)
  if not number2:
    raise RuntimeError("not an integer: '%s'" % (source2))
  return GlslFloat(number1, number2)

def is_glsl_float(op):
  """Tell if token is floating point number."""
  return isinstance(op, GlslFloat)
