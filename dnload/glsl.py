from dnload.common import is_listing
from dnload.common import is_verbose
from dnload.glsl_block_control import is_glsl_block_control
from dnload.glsl_block_inout import is_glsl_block_inout
from dnload.glsl_block_scope import is_glsl_block_scope
from dnload.glsl_block_source import glsl_read_source
from dnload.glsl_block_uniform import is_glsl_block_uniform

########################################
# Glsl #################################
########################################

class Glsl:
  """GLSL source database."""

  def __init__(self):
    """Constructor."""
    self.__sources = []

  def count(self):
    """Count instances of alpha letters within the code."""
    source = "".join(map(lambda x: x.format(False), self.__sources))
    ret = {}
    for ii in source:
      if ii.isalpha():
        if ii in ret:
          ret[ii] += 1
        else:
          ret[ii] = 1
    return ret

  def countSorted(self):
    """Get sorted listing of counted alpha letters within the code."""
    counted = self.count()
    ret = []
    for kk in counted.keys():
      ret += [(kk, counted[kk])]
    return sorted(ret, key=lambda x: x[1], reverse=True)

  def crunch(self):
    """Crunch the source code to smaller state."""
    # Expand all expandable elements.
    for ii in self.__sources:
      ii.expandRecursive()
    # Collect identifiers.
    collected = []
    for ii in self.__sources:
      collected += ii.collect()
    # Merge multiple matching inout names.
    merged = sorted(merge_collected_names(collected), key=len, reverse=True)
    # After names have been collected, it's possible to collapse swizzles.
    swizzle = self.selectSwizzle()
    for ii in self.__sources:
      ii.selectSwizzle(swizzle)
    # Run rename passes until done.
    while merged:
      self.renamePass(merged[0][0], merged[0][1:])
      merged.pop(0)
    # Recombine combinable elements.
    for ii in self.__sources:
      ii.collapseRecursive()

  def parse(self):
    """Parse all source files."""
    for ii in self.__sources:
      ii.parse()

  def read(self, preprocessor, definition_ld, filename, varname, output_name):
    """Read source file."""
    self.__sources += [glsl_read_source(preprocessor, definition_ld, filename, varname, output_name)]

  def renamePass(self, block, names):
    """Perform rename pass from given block."""
    counted = self.countSorted()
    targets = map(lambda x: x[0], counted)
    for ii in targets:
      if not has_name_conflict(block, ii):
        for jj in names:
          jj.lock(ii)
        return
    raise RuntimeError("TODO: implement inventing a new name")

  def selectSwizzle(self):
    counted = self.count()
    ret = ("r", "g", "b", "a")
    rgba = 0
    if "r" in counted:
      rgba += counted["r"]
    if "g" in counted:
      rgba += counted["g"]
    if "b" in counted:
      rgba += counted["b"]
    if "a" in counted:
      rgba += counted["a"]
    xyzw = 0
    if "x" in counted:
      xyzw += counted["x"]
    if "y" in counted:
      xyzw += counted["y"]
    if "z" in counted:
      xyzw += counted["z"]
    if "w" in counted:
      xyzw += counted["w"]
    print("xyzw: %i, rgba: %i" % (xyzw, rgba))
    if xyzw >= rgba:
      ret = ("x", "y", "z", "w")
    if is_verbose:
      print("Selected GLSL swizzle: %s" % (str(ret)))
    return ret

  def write(self):
    """Write processed source headers."""
    for ii in self.__sources:
      ii.write()

  def __str__(self):
    """String representation."""
    return "\n".join(map(lambda x: str(x), self.__sources))

########################################
# Functions ############################
########################################

def flatten(block):
  ret = []
  for ii in block.getChildren():
    ret += [ii]
    ret += flatten(ii)
  return ret

def is_glsl_block_global(op):
  """Tell if block is somehting of a global concern."""
  return (is_glsl_block_inout(op) or is_glsl_block_uniform(op))

def has_name_conflict(block, name):
  """Tell if given block would have a conflict if renamed into given name."""
  # If block is a listing, just go over all options.
  if is_listing(block):
    for ii in block:
      if has_name_conflict(ii, name):
        return True
    return False
  # Check for conflicts within this block.
  parent = find_parent_scope(block)
  found = False
  for ii in flatten(parent):
    # Declared names take the name out of the scope permanently.
    if ii.hasLockedDeclaredName(name):
      return True
    # Other blocks reserve names from their inception onward.
    if block == ii:
      found = True
    if found and ii.hasLockedUsedName(name):
      return True
  return False

def merge_collected_names(lst):
  """Merge different matching lists in collected names."""
  ret = []
  # First merge multiple same inout blocks to match.
  for ii in lst:
    if is_glsl_block_inout(ii[0]):
      found = False
      for jj in range(len(ret)):
        vv = ret[jj]
        if is_glsl_block_inout(vv[0]) and (ii[1] == vv[1]):
          ret[jj] = [(vv[0], ii[0])] + vv[1:] + ii[1:]
          found = True
          break
      if found:
        continue
    ret += [ii]
  # Then, set proper type information for all elements.
  for ii in ret:
    typeid = None
    for jj in ii[1:]:
      found_type = jj.getType()
      if found_type:
        if typeid and (typeid != found_type):
          raise RuntimeError("conflicting types for '%s': %s" % (str(ii[0]), str([typeid, found_type])))
        typeid = found_type
    for jj in ii[1:]:
      jj.setType(typeid)
  return ret

def find_parent_scope(block):
  """Find parent scope block for given block."""
  while True:
    parent = block.getParent()
    if not parent:
      return block
    if is_glsl_block_control(parent) or is_glsl_block_scope(parent):
      return parent
    block = parent
