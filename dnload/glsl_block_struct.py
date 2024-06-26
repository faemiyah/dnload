from dnload.glsl_block import GlslBlock
from dnload.glsl_block import extract_tokens
from dnload.glsl_block_member import glsl_parse_member_list

########################################
# GlslBlockStruct ######################
########################################

class GlslBlockStruct(GlslBlock):
    """Struct declaration."""

    def __init__(self, type_name, members, name=None, size=None):
        """Constructor."""
        GlslBlock.__init__(self)
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
        lst = "".join(map(lambda x: x.format(force), self.__members))
        ret = ("struct %s{%s}" % (self.__type_name.format(force), lst, self.__name.format(force)))
        if self.__name:
            ret += self.__name.format(force)
        if not (self.__size is None):
            if self.__size:
                ret += "[%s]" % (self.__size.format(force))
            else:
                ret += "[]"
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

    def setMemberAccesses(self, lst):
        """Set collected member accesses."""
        self.__member_accesses = lst

    def __str__(self):
        """String representation."""
        return "Struct(%i)" % (len(self.__content))

########################################
# Functions ############################
########################################

def glsl_parse_struct(source):
    """Parse struct block."""
    (type_name, scope, content) = extract_tokens(source, ("struct", "?n", "?{"))
    if not type_name:
        return (None, source)
    # Parse members before examining the rest.
    members = glsl_parse_member_list(scope)
    if not members:
        raise RuntimeError("empty member list for struct")
    # Try name and size.
    (name, size, remaining) = extract_tokens(content, ("?n", "[", "?i", "]", ";"))
    if name and size:
        return (GlslBlockStruct(type_name, members, name, size), remaining)
    (name, terminator, remaining) = extract_tokens(content, ("?n", "[", "]", "?;"))
    if name and terminator:
        return (GlslBlockStruct(type_name, members, name, 0), remaining)
    (name, remaining) = extract_tokens(content, ("?n", ";"))
    if name:
        return (GlslBlockStruct(type_name, members, name), remaining)
    (terminator, remaining) = extract_tokens(content, ("?;",))
    if terminator:
        return (GlslBlockStruct(type_name, members), remaining)
    # Failure.
    return (None, source)

def is_glsl_block_struct(op):
    """Tell if given object is GlslBlockInout."""
    return isinstance(op, GlslBlockStruct)
