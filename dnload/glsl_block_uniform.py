from dnload.glsl_block import GlslBlock
from dnload.glsl_block import extract_tokens
from dnload.glsl_block import extract_statement
import re

########################################
# GlslBlockUniform #####################
########################################
 
class GlslBlockUniform(GlslBlock):
  """Uniform declaration."""

  def __init__(self, location, typeid, size, name):
    """Constructor."""
    GlslBlock.__init__(self)
    self.__location = location
    self.__typeid = typeid
    self.__size = size
    self.__name = name

  def format(self):
    """Return formatted output."""
    ret = ""
    if self.__location:
      ret += "layout(location=%s)" % (self.__location.format())
    ret += "uniform " + self.__typeid.format()
    if self.__size:
      ret += "[%s]" % (self.__size.format())
    return ret + " " + self.__name.format() + ";"

  def __str__(self):
    """String representation."""
    return "Uniform('%s')" % (self.__name.getName())

########################################
# Functions ############################
########################################

def glsl_parse_uniform(source):
  """Parse preprocessor block."""
  location = None
  # Extract layout scope in case it has more complex elements.
  (location_scope, content) = extract_tokens(source, ("layout", "?("))
  if location_scope:
    (location, discarded) = extract_tokens(location_scope, ("location", "=", "?u"))
    if location is None:
      return (None, source)
  # Extract actual uniform definition.
  (typeid, content) = extract_tokens(content, ("uniform", "?t"))
  if not typeid:
    return (None, source)
  (size, content) = extract_tokens(content, ("[", "?u", "]"))
  (name, content) = extract_tokens(content, ("?n", ";"))
  if not name:
    return (None, source)
  return (GlslBlockUniform(location, typeid, size, name), content)
