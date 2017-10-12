import re

from dnload.common import is_listing
from dnload.common import is_verbose
from dnload.glsl_block_control import is_glsl_block_control
from dnload.glsl_block_declaration import is_glsl_block_declaration
from dnload.glsl_block_function import is_glsl_block_function
from dnload.glsl_block_inout import is_glsl_block_inout
from dnload.glsl_block_inout import is_glsl_block_inout_struct
from dnload.glsl_block_scope import is_glsl_block_scope
from dnload.glsl_block_source import glsl_read_source
from dnload.glsl_block_source import is_glsl_block_source
from dnload.glsl_block_uniform import is_glsl_block_uniform
from dnload.glsl_name import is_glsl_name

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
    lst = []
    # Sort by instance count, length of name, string comparison.
    for kk in counted.keys():
      lst += [(counted[kk], -len(kk), kk)]
    ret = sorted(lst, reverse=True)
    return list(map(lambda x: x[2], ret))

  def crunch(self, mode = "full", max_renames = -1, max_simplifys = -1):
    """Crunch the source code to smaller state."""
    combines = None
    inlines = None
    renames = None
    simplifys = None
    # Expand unless crunching completely disabled.
    if "none" != mode:
      for ii in self.__sources:
        ii.expandRecursive()
    # Rename is optional.
    if "full" == mode:
      inlines = 0
      # Perform inlining passes.
      while True:
        inline_pass_rv = self.inlinePass()
        # Last pass will return a listing of merged variable names.
        if is_listing(inline_pass_rv):
          merged = inline_pass_rv
          break
        # Otherwise what was returned was the number of inlinings done.
        inlines += inline_pass_rv
      # Perform simplification passes.
      simplifys = 0
      for ii in self.__sources:
        if (0 <= max_simplifys) and (simplifys >= max_simplifys):
          break
        simplifys += simplify_pass(ii, max_simplifys - simplifys)
      # Print number of inout merges.
      if is_verbose():
        inout_merges = []
        for ii in merged:
          block = ii[0]
          if is_listing(block):
            inout_merges += [block[0]]
        print("GLSL inout connections found: %s" % (str(map(str, inout_merges))))
      # After all names have been collected, it's possible to collapse swizzles.
      swizzle = self.selectSwizzle()
      for ii in self.__sources:
        ii.selectSwizzle(swizzle)
      # Run rename passes until done.
      renames = 0
      for ii in merged:
        if (0 <= max_renames) and (renames >= max_renames):
          break
        self.renamePass(ii[0], ii[1:])
        renames += 1
      # Run member rename passes until done.
      for ii in merged:
        block = ii[0]
        if is_listing(block):
          block = block[0]
        if not is_glsl_block_inout_struct(block):
          continue
        renames += self.renameMembers(block, max_renames - renames)
        # Also rename block type.
        if (0 > max_renames) or (renames < max_renames):
          self.renameBlock(ii[0])
          renames += 1
    # Recombine unless crunching completely disabled.
    if "none" != mode:
      for ii in self.__sources:
        combines = ii.collapseRecursive()
    # Print summary of operations.
    if is_verbose():
      operations = []
      if inlines:
        operations += ["%i inlines" % (inlines)]
      if simplifys:
        operations += ["%i simplifys" % (simplifys)]
      if renames:
        operations += ["%i renames" % (renames)]
      if combines:
        operations += ["%i combines" % (combines)]
      if operations:
        print("GLSL processing done: %s" % (", ".join(operations)))

  def format(self):
    """Format output."""
    ret = []
    for ii in self.__sources:
      if not ii.hasOutputName():
        ret += [ii.generatePrintOutput()]
    return ret

  def hasInlineConflict(self, block, names):
    """Tell if given block has an inlining conflict."""
    # If block is a listing, just go over all options.
    if is_listing(block):
      for ii in block:
        if self.hasInlineConflict(ii, name):
          return True
      return False
    # Check for inline conflicts within this block.
    parent = find_parent_scope(block)
    if is_glsl_block_source(parent):
      for ii in self.__sources:
        if (ii != parent) and ((not parent.getType()) or (not ii.getType())):
          if has_inline_conflict(ii, block, names):
            return True
    return has_inline_conflict(parent, block, names)

  def hasNameConflict(self, block, name):
    """Tell if given block would have a conflict if renamed into given name."""
    # If block is a listing, just go over all options.
    if is_listing(block):
      for ii in block:
        if self.hasNameConflict(ii, name):
          return True
      return False
    # Check for conflicts within this block.
    parent = find_parent_scope(block)
    if is_glsl_block_source(parent):
      for ii in self.__sources:
        if (ii != parent) and ((not parent.getType()) or (not ii.getType())):
          if has_name_conflict(ii, block, name):
            return True
    return has_name_conflict(parent, block, name)

  def inline(self, block, names):
    """Perform inlining of block into where it is used."""
    ret = 0
    parent = find_parent_scope(block)
    if is_glsl_block_source(parent):
      for ii in self.__sources:
        if (ii != parent) and ((not parent.getType()) or (not ii.getType())):
          ret += inline_instances(ii, block, names)
    ret += inline_instances(parent, block, names)
    block.removeFromParent()
    return ret

  def inlinePass(self):
    """Run inline pass. Return list of merged names if no inlining could be done."""
    # Collect identifiers. First pass - collect from generic sources and append from non-generic.
    collected = []
    for ii in self.__sources:
      if not ii.getType():
        collect_pass = ii.collect()
        for jj in self.__sources:
          if jj.getType():
            for kk in collect_pass:
              jj.collectAppend(kk)
        collected += collect_pass
    # Second pass - collect from non-generic sources. Do not append.
    for ii in self.__sources:
      if ii.getType():
        collected += ii.collect()
    # Merge multiple matching inout names.
    merged = sorted(merge_collected_names(collected), key=len, reverse=True)
    # Collect all member accesses for members and set them to the blocks.
    for ii in merged:
      block = ii[0]
      if is_listing(block):
        block = block[0]
      if not is_glsl_block_inout_struct(block):
        continue
      lst = collect_member_accesses(ii[0], ii[1:])
      block.setMemberAccesses(lst)
    # Perform inlining if possible.
    for ii in range(len(merged)):
      vv = merged[ii]
      block = vv[0]
      if is_listing(block) or (not is_glsl_block_declaration(block)):
        continue
      names = vv[1:]
      if not is_inline_name(names[0]):
        continue
      # If no inline conflict, perform inline and return nothing to signify another pass can be done.
      if not self.hasInlineConflict(block, names):
        return self.inline(block, names)
    # Return merged list.
    return merged

  def inventName(self, counted):
    """Invent a new name when existing names have run out."""
    for ii in range(ord("a"), ord("z") + 1):
      cc = chr(ii)
      if not cc in counted:
        return cc
    for ii in range(ord("A"), ord("Z") + 1):
      cc = chr(ii)
      if not cc in counted:
        return cc
    raise RuntimeError("no free names in single character ascii alphabet")

  def parse(self):
    """Parse all source files."""
    for ii in self.__sources:
      ii.parse()

  def read(self, preprocessor, definition_ld, filename, varname, output_name = None):
    """Read source file."""
    self.__sources += [glsl_read_source(preprocessor, definition_ld, filename, varname, output_name)]

  def renameBlock(self, block, target_name = None):
    """Rename block type."""
    # Select name to rename to.
    if not target_name:
      counted = self.countSorted()
      for letter in counted:
        if not self.hasNameConflict(block, letter):
          target_name = letter
          break
      # If all names conflicted, invent new one.
      if not target_name:
        target_name = self.inventName(counted)
    # Listing case.
    if is_listing(block):
      for ii in block:
        self.renameBlock(ii, target_name)
      return
    # Just select first name.
    counted = self.countSorted()
    block.getTypeName().lock(target_name)

  def renameMembers(self, block, max_renames):
    """Rename all members in given block."""
    lst = block.getMemberAccesses()
    counted = self.countSorted()
    if len(counted) < len(lst):
      raise RuntimeError("having more members than used letters should be impossible")
    renames = len(lst)
    if 0 <= max_renames:
      renames = min(max_renames, renames)
    # Iterate over name types, one at a time.
    for (name_list, letter) in zip(lst[:renames], counted[:renames]):
      for name in name_list:
        name.lock(letter)
    return renames

  def renamePass(self, block, names):
    """Perform rename pass from given block."""
    counted = self.countSorted()
    for letter in counted:
      if not self.hasNameConflict(block, letter):
        for ii in names:
          ii.lock(letter)
        return
    # None of the letters was free, invent new one.
    target_name = self.inventName(counted)
    for ii in names:
      ii.lock(target_name)

  def selectSwizzle(self):
    counted = self.count()
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
    if xyzw >= rgba:
      ret = ("x", "y", "z", "w")
      selected_for = xyzw
      selected_against = rgba
    else:
      ret = ("r", "g", "b", "a")
      selected_for = rgba
      selected_against = xyzw
    if is_verbose():
      print("Selected GLSL swizzle: %s (%i vs. %i)" % (str(ret), selected_for, selected_against))
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

def collect_member_uses(op, uses):
  """Collect member uses from inout struct blocks."""
  # List case.
  if is_listing(op):
    for ii in op:
      collect_member_uses(ii, uses)
    return
  # Actual inout block.
  for ii in op.getMembers():
    name_object = ii.getName()
    name_string = name_object.getName()
    if name_string in uses:
      uses[name_string] += [name_object]
    else:
      uses[name_string] = [name_object]

def collect_member_accesses(block, names):
  """Collect all member name accesses from given block."""
  # First, collect all uses from members.
  uses = {}
  collect_member_uses(block, uses)
  # Then collect all uses from names.
  for ii in range(len(names)):
    vv = names[ii]
    aa = vv.getAccess()
    # Might be just declaration.
    if not aa:
      continue
    aa.disableSwizzle()
    name_object = aa.getName()
    name_string = name_object.getName()
    if not (name_string in uses):
      raise RuntimeError("access '%s' not present outside members" % (str(aa)))
    uses[name_string] += [name_object]
  # Expand uses, set types and sort.
  lst = []
  for kk in uses.keys():
    name_list = uses[kk]
    if 1 >= len(name_list):
      print("WARNING: member '%s' of '%s' not accessed" % (name_list[0].getName(), str(block)))
    typeid = name_list[0].getType()
    if not typeid:
      raise RuntimeError("name '%s' has no type" % (name_list[0]))
    for ii in range(1, len(name_list)):
      name_list[ii].setType(typeid)
    lst += [name_list]
  return sorted(lst, key=len, reverse=True)

def flatten(block):
  ret = []
  for ii in block.getChildren():
    ret += [ii]
    ret += flatten(ii)
  return ret

def has_inline_conflict(parent, block, names, comparison = None):
  """Tell if given block has inline conflict."""
  # Iterate over statement names if name not present.
  if not comparison:
    for ii in block.getStatement().getTokens():
      if is_glsl_name(ii) and has_inline_conflict(parent, block, names, ii):
        return True
    return False
  # Search for alterations of name.
  found = False
  uses = len(names)
  for ii in flatten(parent):
    if block == ii:
      found = True
    # If name is found used by this particular block, decrement uses. Can stop iteration at 0 uses.
    for ii in names:
      if ii.hasUsedNameExact(ii):
        uses -= 1
    if 0 >= uses:
      return False
    # Assignment into a name used by the statement makes inlining impossible.
    if found and is_glsl_block_assignment(ii) and ii.getName() == name:
      return True
  return False

def has_name_conflict(parent, block, name):
  """Tell if given block contains a conflict for given name."""
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

def inline_instances(parent, block, names):
  """Inline all instances of block in given parent scope."""
  ret = 0
  tokens = block.getStatement().getTokens()
  for ii in flatten(parent):
    if (ii == block) or (ii.getParent() == block):
      continue
    for jj in names:
      if ii.hasUsedNameExact(jj):
        ret += ii.replaceUsedNameExact(jj, tokens)
  return ret

def is_glsl_block_global(op):
  """Tell if block is somehting of a global concern."""
  return (is_glsl_block_inout(op) or is_glsl_block_uniform(op))

def is_inline_name(op):
  """Tell if given name is viable for inlining."""
  if re.match(r'^i_.*$', op.getName(), re.I):
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
        block = vv[0]
        if is_listing(block):
          block = block[0]
        if is_glsl_block_inout(block) and block.isMergableWith(ii[0]):
          if ii[1] != ii[0].getName():
            raise RuntimeError("inout block inconsistency: '%s' vs. '%s'" % (ii[1], ii[0].getName()))
          if vv[1] != block.getName():
            raise RuntimeError("inout block inconsistency: '%s' vs. '%s'" % (vv[1], vv[0].getName()))
          if is_listing(vv[0]):
            elem = vv[0] + [ii[0]]
          else:
            elem = [vv[0], ii[0]]
          ret[jj] = [elem] + vv[1:] + ii[1:]
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
          raise RuntimeError("conflicting types for '%s': %s" % (str(ii[0]), str([str(typeid), str(found_type)])))
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
    # If scope has control or function as parent, should return that scope instead.
    if is_glsl_block_scope(parent):
      grand = parent.getParent()
      if is_glsl_block_control(grand) or is_glsl_block_function(grand):
        return grand
      return parent
    # Control and function stop ascend even if not grandparents.
    if is_glsl_block_control(parent) or is_glsl_block_function(parent):
      return parent
    block = parent

def simplify_pass(block, max_simplifys):
  """Run simplify pass starting from given root block."""
  ret = 0
  for ii in flatten(block):
    if (max_simplifys >= 0) and (ret >= max_simplifys):
      break
    ret += ii.simplify(max_simplifys - ret)
  return ret
