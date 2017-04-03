import os

from dnload.common import is_listing
from dnload.common import listify
from dnload.common import run_command

########################################
# Assembler ############################
########################################

class Assembler:
  """Class used to generate assembler output."""

  def __init__(self, op):
    """Constructor."""
    self.__executable = op
    self.__comment = "#"
    self.__byte = ".byte"
    self.__short = ".short"
    self.__word = ".long"
    self.__quad = ".quad"
    self.__string = ".ascii"
    self.__assembler_flags_extra = []
    op = os.path.basename(op)
    if op.startswith("nasm"):
      self.__comment = ";"
      self.__byte = "db"
      self.__short = "dw"
      self.__word = "dd"
      self.__string = "db"

  def addExtraFlags(self, op):
    """Add extra flags to use when assembling."""
    if is_listing(op):
      for ii in op:
        self.addExtraFlags(ii)
      return
    if not (op in self.__assembler_flags_extra):
      self.__assembler_flags_extra += [op]

  def assemble(self, src, dst):
    """Assemble a file."""
    cmd = [self.__executable, src, "-o", dst] + self.__assembler_flags_extra
    (so, se) = run_command(cmd)
    if 0 < len(se) and is_verbose():
      print(se)

  def format_align(self, op):
    """Get alignmen string."""
    return (".balign %i\n" % (op))

  def format_block_comment(self, desc, length = 40):
    """Get a block-formatted comment."""
    block_text = ""
    for ii in range(length):
      block_text += self.__comment
    block_text += "\n"
    ret = self.__comment
    if desc:
      ret += " " + desc + " "
    for ii in range(len(ret), length):
      ret += self.__comment
    return block_text + ret + "\n" + block_text

  def format_comment(self, op, indent = ""):
    """Get comment string."""
    ret = ""
    for ii in listify(op):
      if ii:
        ret += indent + self.__comment + " " + ii + "\n"
    return ret

  def format_data(self, size, value, indent = ""):
    """Get data element."""
    size = int(size)
    value_strings = []
    for ii in listify(value):
      if isinstance(ii, int):
        value_strings += ["0x%x" % (ii)]
      else:
        value_strings += [str(ii)]
    if not value_strings:
      raise RuntimeError("unable to format value: '%s'" % (str(value)))
    value = ", ".join(value_strings)
    if value.startswith("\"") and 1 == size:
      return indent + self.__string + " " + value + "\n"
    if 1 == size:
      return indent + self.__byte + " " + value + "\n"
    elif 2 == size:
      return indent + self.__short + " " + value + "\n"
    elif 4 == size:
      return indent + self.__word + " " + value + "\n"
    elif 8 == size:
      return indent + self.__quad + " " + value + "\n"
    else:
      raise NotImplementedError("exporting assembler value of size %i", size)

  def format_equ(self, name, value):
    return ".globl %s\n.equ %s, %s\n" % (name, name, value)

  def format_label(self, op):
    """Generate name labels."""
    if not op:
      return ""
    ret = ""
    if is_listing(op):
      for ii in op:
        ret += format_label(ii) 
    else:
      ret += ".globl %s\n%s:\n" % (op, op)
    return ret
