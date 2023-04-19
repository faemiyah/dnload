from dnload.common import is_verbose
from dnload.glsl_block import GlslBlock
from dnload.glsl_block import extract_tokens
from dnload.glsl_block_assignment import glsl_parse_assignment
from dnload.glsl_block_assignment import is_glsl_block_assignment
from dnload.glsl_block_call import glsl_parse_call
from dnload.glsl_block_call import is_glsl_block_call
from dnload.glsl_block_control import glsl_parse_control
from dnload.glsl_block_control import is_glsl_block_control
from dnload.glsl_block_declaration import glsl_parse_declaration
from dnload.glsl_block_declaration import is_glsl_block_declaration
from dnload.glsl_block_flow import glsl_parse_flow
from dnload.glsl_block_group import GlslBlockGroup
from dnload.glsl_block_group import is_glsl_block_group
from dnload.glsl_block_precision import glsl_parse_precision
from dnload.glsl_block_precision import is_glsl_block_precision
from dnload.glsl_block_return import glsl_parse_return
from dnload.glsl_block_return import is_glsl_block_return
from dnload.glsl_block_unary import glsl_parse_unary
from dnload.glsl_block_unary import is_glsl_block_unary

########################################
# GlslBlockScope #######################
########################################

class GlslBlockScope(GlslBlock):
    """Scope block."""

    def __init__(self, lst, explicit):
        """Constructor."""
        GlslBlock.__init__(self)
        self.__explicit = explicit
        self.__squashable = False
        self.__allow_squash = False
        # Check for degenerate scope.
        if (1 == len(lst)) and is_glsl_block_declaration(lst[0]):
            raise RuntimeError("scope with only block '%s' is degenerate" % (lst[0].format(True)))
        # Check for empty scope (likely an error).
        if 0 >= len(lst):
            if is_verbose():
                print("WARNING: empty scope")
        # Hierarchy.
        self.addChildren(lst)

    def collapseContents(self, mode):
        """Perform comma squash on contents."""
        if mode != "full":
            return False
        # Enable squashing and return.
        if self.__squashable and (not self._children) and (not self.__allow_squash):
            self.__allow_squash = True
            return True
        # Collapse statements into return statements, if possible.
        for ii in range(1, len(self._children)):
            aa = self._children[ii - 1]
            bb = self._children[ii]
            aa_mergable = is_glsl_block_assignment(aa) or is_glsl_block_call(aa) or is_glsl_block_unary(aa)
            bb_mergable = is_glsl_block_return(bb) and (not bb.isEmptyReturn())
            if aa_mergable and bb_mergable:
                aa.replaceTerminator(",")
                aa.removeFromParent()
                bb.addChildren(aa, True)
                return True
        # Comma-collapse other contents, if possible.
        for ii in range(1, len(self._children)):
            aa = self._children[ii - 1]
            bb = self._children[ii]
            aa_mergable = is_glsl_block_assignment(aa) or is_glsl_block_call(aa) or is_glsl_block_unary(aa)
            bb_mergable = is_glsl_block_assignment(bb) or is_glsl_block_call(bb) or is_glsl_block_unary(bb)
            # Assignment can start a group.
            if aa_mergable and bb_mergable:
                vv = GlslBlockGroup(bb)
                self.replaceChild(ii - 1, vv)
                aa.replaceTerminator(",")
                vv.addChildren(aa, True)
                return True
            # Append into group.
            if is_glsl_block_group(aa) and bb_mergable:
                aa.getChildren()[-1].replaceTerminator(",")
                bb.removeFromParent()
                aa.addChildren(bb)
                return True
        return False

    def format(self, force):
        """Return formatted output."""
        ret = "".join(map(lambda x: x.format(force), self._children))
        if (len(self._children) > 1) or (self.__explicit and (not self.__squashable)):
            return "{%s}" % (ret)
        # Empty scope squashing may or may not be allowed.
        if (not ret) and self.__squashable:
            if self.__allow_squash:
                return ";"
            return "{}"
        return ret

    def isExplicit(self):
        """Accessor."""
        return self.__explicit

    def isSquashable(self):
        """Accessor."""
        return self.__squashable

    def setExplicit(self, flag):
        """Set explicit flag."""
        self.__explicit = flag

    def setSquashable(self, flag):
        """Set squashable flag."""
        self.__squashable = flag

    def __str__(self):
        """String representation."""
        return "Scope(%u)" % (len(self._children))

########################################
# Functions ############################
########################################

def glsl_parse_content(source):
    """Parse generic content."""
    # Nested scopes without extra content make no sense.
    if 2 <= len(source) and ("{" == source[0].format(False)) and ("}" == source[-1].format(False)):
        return glsl_parse_content(source[1:-1])
    # Loop over content.
    ret = []
    while source:
        # Parse scope, allow one-statement scope (will be merged with a control or destroyed later).
        (block, remaining) = glsl_parse_scope(source, False)
        if block:
            ret += [block]
            source = remaining
            continue
        (block, remaining) = glsl_parse_precision(source)
        if block:
            ret += [block]
            source = remaining
            continue
        (block, remaining) = glsl_parse_control(source)
        if block:
            ret += [block]
            source = remaining
            continue
        (block, remaining) = glsl_parse_declaration(source)
        if block:
            ret += [block]
            source = remaining
            continue
        (block, remaining) = glsl_parse_call(source)
        if block:
            ret += [block]
            source = remaining
            continue
        (block, remaining) = glsl_parse_return(source)
        if block:
            ret += [block]
            source = remaining
            continue
        raise RuntimeError("cannot parse content: %s" % (str(map(str, source))))
    # Merge control blocks with following blocks.
    while True:
        if not merge_control_pass(ret):
            break
    # After merging all control blocks, prevent potential errors that could arise from squashing.
    while True:
        if not prevent_squash_pass(ret):
            break
    # Expand scopes of size 1. They are not needed after control merge.
    while True:
        if not expand_scope_pass(ret):
            break
    return ret

def glsl_parse_scope(source, explicit=True):
    """Parse scope block."""
    (content, remaining) = extract_tokens(source, ("?{",))
    if not (content is None):
        return (GlslBlockScope(glsl_parse_content(content), explicit), remaining)
    # If explicit scope is not expected, try legal one-statement scopes.
    elif not explicit:
        (block, remaining) = glsl_parse_flow(source)
        if block:
            return (GlslBlockScope([block], explicit), remaining)
        (block, remaining) = glsl_parse_unary(source)
        if block:
            return (GlslBlockScope([block], explicit), remaining)
        (block, remaining) = glsl_parse_assignment(source)
        if block:
            return (GlslBlockScope([block], explicit), remaining)
    # No scope found.
    return (None, source)

def is_glsl_block_scope(op):
    """Tell if given object is GlslBlockScope."""
    return isinstance(op, GlslBlockScope)

def merge_control_pass(lst):
    """Merge one control block with following block."""
    if len(lst) <= 1:
        return False
    for ii in range(len(lst) - 1):
        vv = lst[ii]
        if (not is_glsl_block_control(vv)) or vv.getTarget():
            continue
        mm = lst[ii + 1]
        # Declaration following control makes no sense.
        if is_glsl_block_declaration(mm):
            raise RuntimeError("'%s' followed by '%s'" % (str(vv), str(mm)))
        # Scope following control must be explicit.
        if is_glsl_block_scope(mm):
            mm.setExplicit(True)
            mm.setSquashable(True)
        vv.setTarget(mm)
        lst.pop(ii + 1)
        return True
    return False

def is_prevent_squash_inner_if_with_else(first, second):
    """Check for and prevent squash of preceding scope with one if and following else."""
    if is_glsl_block_control(first):
        first = first.getTarget()
        if not first:
            return False
    if not is_glsl_block_scope(first):
        return False
    if is_glsl_block_control(second):
        print(second.getControl())
    if (not is_glsl_block_control(second)) or (second.getControl().format(False) != "else"):
        return False
    last_child = first.getChildren()[-1]
    if (not is_glsl_block_control(last_child)) or (last_child.getControl().format(False) != "if"):
        return False
    if not first.isSquashable():
        return False
    first.setSquashable(False)
    return True

def prevent_squash_pass(lst):
    """Prevent squash in cases where it would alter semantics."""
    for ii in range(len(lst) - 1):
        vv = lst[ii]
        mm = lst[ii + 1]
        if is_prevent_squash_inner_if_with_else(vv, mm):
            return True
    return False

def expand_scope_pass(lst):
    """Expand one single-element scope."""
    for ii in range(len(lst)):
        vv = lst[ii]
        if (not is_glsl_block_scope(vv)) or vv.isExplicit():
            continue
        children = vv.getChildren()
        if len(children) != 1:
            continue
        children[0].setParent(None)
        lst[ii] = children[0]
        return True
    return False
