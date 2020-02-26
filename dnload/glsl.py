import copy
import re

from dnload.common import is_listing
from dnload.common import is_verbose
from dnload.glsl_block_assignment import is_glsl_block_assignment
from dnload.glsl_block_control import is_glsl_block_control
from dnload.glsl_block_declaration import is_glsl_block_declaration
from dnload.glsl_block_function import is_glsl_block_function
from dnload.glsl_block_inout import is_glsl_block_inout
from dnload.glsl_block_inout import is_glsl_block_inout_struct
from dnload.glsl_block_member import is_glsl_block_member
from dnload.glsl_block_precision import is_glsl_block_precision
from dnload.glsl_block_scope import is_glsl_block_scope
from dnload.glsl_block_struct import is_glsl_block_struct
from dnload.glsl_block_source import glsl_read_source
from dnload.glsl_block_source import is_glsl_block_source
from dnload.glsl_block_uniform import is_glsl_block_uniform
from dnload.glsl_name import is_glsl_name
from dnload.glsl_name_strip import is_glsl_name_strip
from dnload.glsl_source_chain import GlslSourceChain

########################################
# Glsl #################################
########################################

class Glsl:
    """GLSL source database."""

    def __init__(self):
        """Constructor."""
        self.__chains = []
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

    def crunch(self, mode="full", max_inlines=-1, max_renames=-1, max_simplifys=-1):
        """Crunch the source code to smaller state."""
        combines = None
        inlines = None
        renames = None
        simplifys = None
        # Expand unless crunching completely disabled.
        if "none" != mode:
            for ii in self.__sources:
                ii.expandRecursive()
            # Perform inlining passes.
            inlines = 0
            while True:
                merged = self.inlinePass((max_inlines < 0) or (inlines < max_inlines))
                # If no inlines succeeded, the result value will be a listing of merged variable names.
                if merged:
                    break
                # Do another inlining round.
                inlines += 1
            # Check that no name is unreferenced.
            if is_verbose():
                for ii in merged:
                    if ii.getNameCount() <= 1:
                        print("WARNING: identifier '%s' never referenced" % (ii.getName().getName()))
            # Perform simplification passes.
            simplifys = 0
            for ii in self.__sources:
                if (0 <= max_simplifys) and (simplifys >= max_simplifys):
                    break
                simplifys += simplify_pass(ii, max_simplifys - simplifys)
            # Set implied precision recursively, this may eliminate precision directives later.
            for ii in self.__chains:
                precision_pass(ii)
            # After all names have been collected, it's possible to select the best swizzle.
            swizzle = self.selectSwizzle()
            for ii in self.__sources:
                ii.selectSwizzle(swizzle)
            # Print number of block merges.
            if is_verbose():
                function_merges = []
                inout_merges = []
                for ii in merged:
                    if ii.getBlockCount() <= 1:
                        continue
                    block = ii.getBlock()
                    elem = "%s(%i)" % (block.getName().getName(), ii.getBlockCount())
                    if is_glsl_block_function(block):
                        function_merges += [elem]
                    elif is_glsl_block_inout(block):
                        inout_merges += [elem]
                    else:
                        raise RuntimeError("unknown merge: %s" % (str(block)))
                if function_merges:
                    print("GLSL function overloads found: %s" % (str(function_merges)))
                if inout_merges:
                    print("GLSL inout connections found: %s" % (str(inout_merges)))
            # Run rename passes until done.
            renames = 0
            for ii in merged:
                if (0 <= max_renames) and (renames >= max_renames):
                    break
                self.renamePass(ii)
                renames += 1
            # Run member rename passes until done.
            for ii in merged:
                block = ii.getBlock()
                if not is_glsl_block_inout_struct(block):
                    continue
                renames += self.renameMembers(block, max_renames - renames)
                # Also rename block type.
                if (0 > max_renames) or (renames < max_renames):
                    self.renameBlockType(ii.getBlockList())
                    renames += 1
            # Perform recombine passes.
            for ii in self.__sources:
                combines = ii.collapseRecursive(mode)
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

    def findCommonChain(self, lhs, rhs):
        """Finds a common chain that contains both given GLSL source files."""
        for ii in self.__chains:
            if ii.hasSource(lhs) and ii.hasSource(rhs):
                return ii
        return None

    def generatePrintOutput(self, plain=False):
        """Format output."""
        ret = []
        for ii in self.__sources:
            if not ii.hasOutputName():
                ret += [ii.generatePrintOutput(plain).strip()]
        return "\n".join(ret)

    def getChainLength(self, op):
        """Gets the length of source chain with given name."""
        for ii in self.__chains:
            if ii.getChainName() == op:
                return ii.getChainLength()
        raise RuntimeError("source chain '%s' not found" % (op))

    def hasInlineConflict(self, block, names):
        """Tell if given block has an inlining conflict."""
        # If block is a listing, just go over all options.
        if is_listing(block):
            for ii in block:
                if self.hasInlineConflict(ii, names):
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

    def hasNameConflict(self, op, name):
        """Search for name conflicts regarding given name."""
        # If the input is a GLSL name strip, iterate over its blocks.
        if is_glsl_name_strip(op):
            for ii in op.getBlockList():
                if self.hasNameConflict(ii, name):
                    return True
            return False
        # If the parent is a source block, may need to check conflicts with other sources first.
        parent = find_parent_scope(op)
        if is_glsl_block_source(parent):
            for ii in self.__sources:
                # Only check other sources.
                if ii != parent:
                    # Checking against header sources always happens.
                    if (not parent.getType()) or (not ii.getType()):
                        if has_name_conflict(ii, op, name):
                            return True
                    # Uniforms clash within the source chain.
                    elif is_glsl_block_uniform(op):
                        chain = self.findCommonChain(ii, parent)
                        if chain:
                            for jj in flatten(ii):
                                if is_glsl_block_uniform(jj) and jj.hasLockedDeclaredName(name):
                                    return True
        # Above checks only work if uniforms are only declared in source scope.
        elif is_glsl_block_uniform(op):
            raise RuntimeError("found uniform block in non-source scope")
        # Always check for conflicts within the parent block anyway.
        return has_name_conflict(parent, op, name)

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

    def inlinePass(self, allow_inline):
        """Run inline pass. Return list of merged names if no inlining could be done."""
        collected = []
        for ii in self.__sources:
            # First pass - collect from generic sources only
            if ii.getType():
                continue
            collect_pass = ii.collect()
            for jj in self.__sources:
                # Second pass - append from non-generic.
                if not jj.getType():
                    continue
                for kk in collect_pass:
                    # Successive sources may only append to names declared on source level.
                    if not is_source_level_name_strip(kk):
                        continue
                    jj.collectAppend(kk)
            collected += collect_pass
        # Second pass - collect from non-generic sources. Do not append.
        for ii in self.__sources:
            if ii.getType():
                collected += ii.collect()
        # Merge multiple matching inout names.
        ret = sorted(self.mergeCollectedNames(collected), reverse=True)
        # Collect all member accesses for members and set them to the blocks.
        for ii in ret:
            block = ii.getBlock()
            if not (is_glsl_block_inout_struct(block) or is_glsl_block_struct(block)):
                continue
            lst = ii.collectMemberAccesses()
            block.setMemberAccesses(lst)
        # If inlining is not allowed, just return.
        if not allow_inline:
            return ret
        # Perform inlining if possible.
        for ii in ret:
            # Merged instances not ok for inlining.
            if ii.getBlockCount() > 1:
                continue
            block = ii.getBlock()
            # Must be declaration to be inlined anywhere.
            if not is_glsl_block_declaration(block):
                continue
            # Must be an inline name to be inlined.
            if not is_inline_name(ii.getName()):
                continue
            names = ii.getNameList()
            # If no inline conflict, perform inline and return nothing to signify another pass can be done.
            if not self.hasInlineConflict(block, names):
                self.inline(block, names)
                return None
        # Return merged list of name strips.
        return ret

    def inventName(self, block, counted):
        """Invent a new name when existing names have run out."""
        for ii in single_character_alphabet():
            if not self.hasNameConflict(block, ii):
                return ii
        # Letter followed by a number. Try more frequent names first.
        ii = 0
        while True:
            for jj in counted:
                name = jj + str(ii)
                if not self.hasNameConflict(block, name):
                    return name
            ii += 1

    def mergeCollectedNames(self, lst):
        """Merge all matching names in the list of collected names."""
        # Merge functions with the same name (overrides) and inout blocks.
        ret = []
        for ii in lst:
            block = ii.getBlock()
            if is_glsl_block_function(block) or is_glsl_block_inout(block):
                found = False
                for jj in ret:
                    if self.mergeCollectedNamesTest(ii, jj):
                        found = True
                        break
                # Do not add to array if already merged into it.
                if found:
                    continue
            ret += [ii]
        # Set proper type information for all elements.
        for ii in ret:
            ii.updateNameTypes()
        return ret

    def mergeCollectedNamesTest(self, lhs, rhs):
        """Try to merge two name strips."""
        lhs_block = lhs.getBlock()
        rhs_block = rhs.getBlock()
        # Function overloads need to check source type.
        if is_glsl_block_function(lhs_block):
            if lhs_block.isMergableWith(rhs_block):
                lhs_source = lhs_block.getSourceFile()
                rhs_source = rhs_block.getSourceFile()
                if (not lhs_source.getType()) or (not rhs_source.getType()) or (lhs_source == rhs_source):
                    lhs.appendTo(rhs)
                    return True
        # Inout connections may be mixed and matched. Programmer has responsibility of using different names.
        elif is_glsl_block_inout(lhs_block):
            if lhs_block.isMergableWith(rhs_block):
                lhs.appendTo(rhs)
                return True
        # Unknown block type.
        else:
            raise RuntimeError("don't know how to merge block %s" % (str(lhs_block)))
        return False

    def parse(self):
        """Parse all source files."""
        # First, assemble glsl chains.
        source_dict = {}
        for ii in self.__sources:
            if ii.isCommonChainName():
                continue
            chain_name = ii.getChainName()
            if chain_name in source_dict:
                source_dict[chain_name].addSource(ii)
            else:
                source_dict[chain_name] = GlslSourceChain(ii)
        for ii in self.__sources:
            if not ii.isCommonChainName():
                continue
            for jj in source_dict.keys():
                source_chain = source_dict[jj]
                if source_chain.isSourceSlotFree(ii):
                    source_chain.addSource(ii)
        self.__chains = source_dict.values()
        if is_verbose():
            print("GLSL source chains: %s" % (" ; ".join(map(lambda x: str(x), self.__chains))))
        # Run parse process on sources.
        for ii in self.__sources:
            ii.parse()

    def read(self, preprocessor, definition_ld, filename, output_name=None, varname=None):
        """Read source file."""
        src = glsl_read_source(preprocessor, definition_ld, filename, output_name, varname)
        self.__sources += [src]

    def renameBlockType(self, block):
        """Rename block type for given name strip."""
        # Select name to rename to.
        if not target_name:
            counted = self.countSorted()
            # Single-character names first.
            for letter in counted:
                if not self.hasNameConflict(block, letter):
                    target_name = letter
                    break
            # None of the letters was free, invent new one.
            if not target_name:
                target_name = self.inventName(block, counted)
        # Listing case.
        if is_listing(block):
            for ii in block:
                self.renameBlock(ii, target_name)
            return
        # Just select first name.
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

    def renamePass(self, op):
        """Perform rename pass for given name strip."""
        block_list = op.getBlockList()
        counted = self.countSorted()
        for letter in counted:
            if not self.hasNameConflict(op, letter):
                op.lockNames(letter)
                return
        # None of the letters was free, invent new one.
        target_name = self.inventName(op, counted)
        op.lockNames(target_name)

    def selectSwizzle(self):
        """Select the swizzle to be used."""
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
        stpq = 0
        if "s" in counted:
            stpq += counted["s"]
        if "t" in counted:
            stpq += counted["t"]
        if "p" in counted:
            stpq += counted["p"]
        if "q" in counted:
            stpq += counted["q"]
        xyzw = 0
        if "x" in counted:
            xyzw += counted["x"]
        if "y" in counted:
            xyzw += counted["y"]
        if "z" in counted:
            xyzw += counted["z"]
        if "w" in counted:
            xyzw += counted["w"]
        if (xyzw >= rgba) and (xyzw >= stpq):
            ret = ("x", "y", "z", "w")
            selected_for = xyzw
            selected_against = "rgba: %i, stpq: %i" % (rgba, stpq)
        elif (stpq >= xyzw) and (stpq >= rgba):
            ret = ("s", "t", "p", "q")
            selected_for = stpq
            selected_against = "rgba: %i, xyzw: %i" % (rgba, xyzw)
        else:
            ret = ("r", "g", "b", "a")
            selected_for = rgba
            selected_against = "stpq: %i, xyzw: %i" % (stpq, xyzw)
        if is_verbose():
            print("Selected GLSL swizzle: %s (%i vs. %s)" % (str(ret), selected_for, selected_against))
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
    """Flattens a block and its children to a sequential array."""
    ret = []
    for ii in block.getChildren():
        ret += [ii]
        ret += flatten(ii)
    return ret

def has_inline_conflict(parent, block, names, comparison=None):
    """Tell if given block has inline conflict."""
    # Iterate over statement names if comparison not present.
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
        for jj in names:
            if ii.hasUsedNameExact(jj):
                uses -= 1
        if 0 >= uses:
            return False
        # Assignment into a name used by the statement makes inlining impossible.
        if found and is_glsl_block_assignment(ii) and ii.getName() == comparison:
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
    return (is_glsl_block_inout(op) or
            is_glsl_block_uniform(op))

def is_glsl_block_precision_relevant(op):
    """Tell if block is something to which precision directive matters."""
    return (is_glsl_block_declaration(op) or
            is_glsl_block_function(op) or
            is_glsl_block_member(op) or
            is_glsl_block_inout(op) or
            is_glsl_block_uniform(op))

def is_inline_name(op):
    """Tell if given name is viable for inlining."""
    if re.match(r'^i_.*$', op.getName(), re.I):
        return True
    return False

def is_source_level_name_strip(op):
    """Tell if given name strip exists in source level."""
    blk = op.getBlock()
    return is_glsl_block_source(blk.getParent())

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

def precision_pass_recursive(block, precision_state):
    """Recursively apply implied precision information on type declarations."""
    if is_glsl_block_precision_relevant(block):
        block.setImpliedPrecision(precision_state)
    # Recurse down.
    for ii in block.getChildren():
        if is_glsl_block_precision(ii):
            precision_state.setPrecision(jj.getType(), jj.getPrecision())
        else:
            precision_pass_recursive(ii, copy.deepcopy(precision_state))

def precision_pass(chain):
    """Run a precision pass on given source file chain."""
    print(str(chain))
    # Recursively set implied precision for every typeid in the chain.
    chain_precision_state = {}
    for ii in chain.getSources():
        # Overwrite initial precision directives from chain precision state.
        precision_state = ii.getPrecisions()
        for (kk, vv) in chain_precision_state:
            precison_state.setPrecision(kk, vv)
        # Loop over child elements of the source file.
        for jj in ii.getChildren():
            # Check whether to alter the chain precision state.
            if is_glsl_block_precision(jj):
                if not ii.getType():
                    chain_precision_state[jj.getType()] = jj.getPrecision()
                precision_state.setPrecision(jj.getType(), jj.getPrecision())
            # Otherwise recursively iterate downwards.
            else:
                precision_pass_recursive(jj, copy.deepcopy(precision_state))

def single_character_alphabet():
    """Returns an alphabet of single characters, lower and upper case."""
    ret = []
    for ii in range(ord("a"), ord("z") + 1):
        ret += [chr(ii)]
    for ii in range(ord("A"), ord("Z") + 1):
        ret += [chr(ii)]
    return ret

def simplify_pass(block, max_simplifys):
    """Run simplify pass starting from given root block."""
    ret = 0
    for ii in flatten(block):
        if (max_simplifys >= 0) and (ret >= max_simplifys):
            break
        ret += ii.simplify(max_simplifys - ret)
    return ret
