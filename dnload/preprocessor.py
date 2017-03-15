from dnload.common import is_verbose
from dnload.common import run_command
from dnload.compiler import Compiler

########################################
# Preprocessor #########################
########################################

class Preprocessor(Compiler):
  """Preprocessor used to preprocess C (or C-style) source."""

  def __init__(self, op):
    """Constructor."""
    Compiler.__init__(self, op)

  def preprocess(self, op):
    """Preprocess a file, return output."""
    args = [self.get_command(), op] + self._compiler_flags_extra + self._definitions + self._include_directories
    if self.command_basename_startswith("cl."):
      args += ["/E"]
    (so, se) = run_command(args)
    if 0 < len(se) and is_verbose():
      print(se)
    return so
