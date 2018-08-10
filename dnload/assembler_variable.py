import struct

from dnload.common import get_indent
from dnload.common import is_listing
from dnload.common import listify
from dnload.platform_var import PlatformVar

########################################
# AssemblerVariable ####################
########################################

class AssemblerVariable:
  """One assembler variable."""

  def __init__(self, op, name = None):
    """Constructor."""
    if not is_listing(op):
      raise RuntimeError("only argument passed is not a list")
    self.__desc = op[0]
    self.__size = op[1]
    self.__value = op[2]
    self.__name = name
    self.__original_size = -1
    self.__label_pre = []
    self.__label_post = []
    if 3 < len(op):
      self.add_label_pre(op[3])

  def add_label_pre(self, op):
    """Add pre-label(s)."""
    if is_listing(op):
      self.__label_pre += op
    else:
      self.__label_pre += [op]

  def add_label_post(self, op):
    """Add post-label(s)."""
    if is_listing(op):
      self.__label_post += op
    else:
      self.__label_post += [op]

  def deconstruct(self):
    """Deconstruct into byte stream."""
    lst = []
    if is_listing(self.__value):
      for ii in self.__value:
        if not is_deconstructable(ii):
          break
        lst += self.deconstruct_single(int(ii))
    elif is_deconstructable(self.__value):
      lst = self.deconstruct_single(int(self.__value))
    if 0 >= len(lst):
      return None
    if 1 >= len(lst):
      return [self]
    ret = []
    for ii in range(len(lst)):
      struct_elem = lst[ii]
      if isinstance(struct_elem, str):
        var = AssemblerVariable(("", 1, ord(struct_elem)))
      else:
        var = AssemblerVariable(("", 1, int(struct_elem)))
      if 0 == ii:
        var.__desc = self.__desc
        var.__name = self.__name
        var.__original_size = self.__size
        var.__label_pre = self.__label_pre
      elif len(lst) - 1 == ii:
        var.__label_post = self.__label_post
      ret += [var]
    return ret

  def deconstruct_single(self, op):
    """Desconstruct a single value."""
    bom = str(PlatformVar("bom"))
    int_size = int(self.__size)
    if 1 == int_size:
      return struct.pack(bom + "B", op)
    if 2 == int_size:
      if 0 > op:
        return struct.pack(bom + "h", op)
      else:
        return struct.pack(bom + "H", op)
    elif 4 == int_size:
      if 0 > op:
        return struct.pack(bom + "i", op)
      else:
        return struct.pack(bom + "I", op)
    elif 8 == int_size:
      if 0 > op:
        return struct.pack(bom + "q", op)
      else:
        return struct.pack(bom + "Q", op)
    raise RuntimeError("cannot pack value of size %i" % (int_size))

  def generate_source(self, assembler, indent, label = None):
    """Generate assembler source."""
    ret = ""
    indent = get_indent(indent)
    for ii in self.__label_pre:
      ret += assembler.format_label(ii)
    if isinstance(self.__value, str) and self.__value.startswith("\"") and label and self.__name:
      ret += assembler.format_label("%s_%s" % (label, self.__name))
    formatted_comment = assembler.format_comment(self.__desc, indent)
    formatted_data = assembler.format_data(self.__size, self.__value, indent)
    if formatted_comment:
      ret += formatted_comment
    ret += formatted_data
    for ii in self.__label_post:
      ret += assembler.format_label(ii)
    return ret

  def get_size(self):
    """Accessor."""
    return self.__size

  def mergable(self, op):
    """Tell if the two assembler variables are mergable."""
    if int(self.__size) != int(op.__size):
      return False
    if self.__value != op.__value:
      return False
    return True

  def merge(self, op):
    """Merge two assembler variables into one."""
    self.__desc = listify(self.__desc, op.__desc)
    self.__name = listify(self.__name, op.__name)
    self.__label_pre = listify(self.__label_pre, op.__label_pre)
    self.__label_post = listify(self.__label_post, op.__label_post)

  def reconstruct(self, lst):
    """Reconstruct variable from a listing."""
    original_size = int(self.__original_size)
    self.__original_size = -1
    if 1 >= original_size:
      return False
    if len(lst) < original_size - 1:
      return False
    ret = chr(self.__value)
    for ii in range(original_size - 1):
      op = lst[ii]
      if not op.reconstructable((original_size - 2) == ii):
        return False
      self.__label_post = listify(self.__label_post, op.label_post)
      ret += chr(op.value)
    bom = str(PlatformVar("bom"))
    if 2 == original_size:
      self.__value = struct.unpack(bom + "H", ret)[0]
    elif 4 == original_size:
      self.__value = struct.unpack(bom + "I", ret)[0]
    elif 8 == original_size:
      self.__value = struct.unpack(bom + "Q", ret)[0]
    self.__size = original_size
    return original_size - 1

  def reconstructable(self, accept_label_post):
    """Tell if this is reconstructable."""
    if self.__name:
      return False
    if self.__label_pre:
      return False
    if self.__label_post and not accept_label_post:
      return False
    if "" != self.__desc:
      return False
    if -1 != self.__original_size:
      return False

  def remove_label_pre(self, op):
    """Remove a pre-label."""
    if op in self.__label_pre:
      self.__label_pre.remove(op)

  def remove_label_post(self, op):
    """Remove a post-label."""
    if op in self.__label_post:
      self.__label_post.remove(op)

  def __str__(self):
    """String representation."""
    int_size = int(self.__size)
    if 1 == int_size:
      ret = 'byte:'
    elif 2 == int_size:
      ret = 'short'
    elif 4 == int_size:
      ret = 'long'
    elif 8 == int_size:
      ret = 'quad'
    else:
      raise RuntimeError("unknown size %i in an assembler variable" % (self.__size))
    ret += ': ' + str(self.__value)
    if self.__name:
      ret += " (%s)" % (self.__name)
    if self.__desc:
      ret += " '%s'" % (self.__desc)
    return ret

########################################
# Functions ############################
########################################

def is_deconstructable(op):
  """Tell if a variable can be deconstructed."""
  return isinstance(op, int) or (isinstance(op, PlatformVar) and op.deconstructable())
