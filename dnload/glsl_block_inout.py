from dnload.glsl_block import GlslBlock
from dnload.glsl_block import extract_tokens
from dnload.glsl_block_layout import glsl_parse_layout
from dnload.glsl_block_member import glsl_parse_member_list

########################################
# GlslBlockInOut #######################
########################################

class GlslBlockInOut(GlslBlock):
    """Input (attribute / varying) declaration block."""

    def __init__(self, layout, inout):
        """Constructor."""
        GlslBlock.__init__(self)
        self._layout = layout
        self._inout = inout

    def formatBase(self, force):
        """Return base of formatted output."""
        ret = ""
        if self._layout:
            ret += self._layout.format(force)
        return ret + self._inout.format(force)

    def format(self, force):
        """Return formatted output."""
        return self.formatBase(force) + ";"

    def __str__(self):
        """String representation."""
        return "InOut()"

########################################
# GlslBlockInOutStruct #################
########################################

class GlslBlockInOutStruct(GlslBlockInOut):
    """Input (attribute / varying) struct declaration block."""

    def __init__(self, layout, inout, type_name, members, name, size=0):
        """Constructor."""
        GlslBlockInOut.__init__(self, layout, inout)
        self.__type_name = type_name
        self.__members = members
        self.__name = name
        self.__size = size
        self.__member_accesses = []
        # Hierarchy.
        name.setType(type_name)
        self.addNamesDeclared(name)
        self.addNamesUsed(name)

    def format(self, force):
        """Return formatted output."""
        ret = self.formatBase(force)
        lst = "".join(map(lambda x: x.format(force), self.__members))
        ret += (" %s{%s}%s" % (self.__type_name.format(force), lst, self.__name.format(force)))
        if self.__size:
            ret += "[%s]" % (self.__size.format(force))
        return ret + ";"

    def getMembers(self):
        """Accessor."""
        return self.__members

    def getMemberAccesses(self):
        """Accessor."""
        return self.__member_accesses

    def getName(self):
        """Accessor."""
        return self.__name

    def getTypeName(self):
        """Accessor."""
        return self.__type_name

    def isMergableWith(self, op):
        """Tell if this inout block can be merged with given block."""
        if is_glsl_block_inout_struct(op) and (op.getTypeName() == self.__type_name):
            members1 = sorted(op.getMembers())
            members2 = sorted(self.__members)
            if len(members1) != len(members2):
                return False
            for (ii, jj) in zip(members1, members2):
                if ii.getName() != jj.getName():
                    return False
            return True
        return False

    def setMemberAccesses(self, lst):
        """Set collected member accesses."""
        self.__member_accesses = lst

    def __str__(self):
        """String representation."""
        return "InOutStruct('%s')" % (self.__name.getName())

########################################
# GlslBlockInOutTyped ##################
########################################

class GlslBlockInOutTyped(GlslBlockInOut):
    """Input (attribute / varying) struct declaration block."""

    def __init__(self, layout, inout, typeid, name):
        """Constructor."""
        GlslBlockInOut.__init__(self, layout, inout)
        self.__typeid = typeid
        self.__name = name
        # Hierarchy.
        name.setType(typeid)
        self.addNamesDeclared(name)
        self.addNamesUsed(name)

    def format(self, force):
        """Return formatted output."""
        ret = self.formatBase(force)
        return ret + (" %s %s;" % (self.__typeid.format(force), self.__name.format(force)))

    def getName(self):
        """Accessor."""
        return self.__name

    def getType(self):
        """Accessor."""
        return self.__typeid

    def isMergableWith(self, op):
        """Tell if this inout block can be merged with given block."""
        if is_glsl_block_inout_typed(op) and (op.getName() == self.__name) and (op.getType() == self.__typeid):
            return True
        return False

    def __str__(self):
        """String representation."""
        return "InOutTyped('%s %s')" % (self.__typeid.format(False), self.__name.getName())

########################################
# Functions ############################
########################################

def glsl_parse_inout(source):
    """Parse inout block."""
    (layout, content) = glsl_parse_layout(source)
    if not layout:
        content = source
    # It is possible to have an inout block without anything.
    (inout, remaining) = extract_tokens(content, ("?o", ";"))
    if inout:
        return (GlslBlockInOut(layout, inout), remaining)
    # Scoped version first.
    (inout, type_name, scope, name, intermediate) = extract_tokens(content, ("?o", "?n", "?{", "?n"))
    if inout and type_name and scope and name:
        members = glsl_parse_member_list(scope)
        if not members[0]:
            raise RuntimeError("wat?")
        if not members:
            raise RuntimeError("empty member list for inout struct")
        # May have an array.
        (size, remaining) = extract_tokens(intermediate, ("[", "?u", "]", ";"))
        if size:
            return (GlslBlockInOutStruct(layout, inout, type_name, members, name, size), remaining)
        # Did not have an array.
        (terminator, remaining) = extract_tokens(intermediate, "?|;")
        if terminator:
            return (GlslBlockInOutStruct(layout, inout, type_name, members, name), remaining)
    # Regular inout.
    (inout, typeid, name, remaining) = extract_tokens(content, ("?o", "?t", "?n", ";"))
    if not inout or not typeid or not name:
        return (None, source)
    return (GlslBlockInOutTyped(layout, inout, typeid, name), remaining)

def is_glsl_block_inout(op):
    """Tell if given object is GlslBlockInout."""
    return isinstance(op, GlslBlockInOut)

def is_glsl_block_inout_struct(op):
    """Tell if given object is GlslBlockInoutStruct."""
    return isinstance(op, GlslBlockInOutStruct)

def is_glsl_block_inout_typed(op):
    """Tell if given object is GlslBlockInoutTyped."""
    return isinstance(op, GlslBlockInOutTyped)
