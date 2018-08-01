from dnload.glsl_block import GlslBlock
from dnload.glsl_block import extract_tokens

########################################
# GlslBlockPerVertex ###################
########################################


class GlslBlockPerVertex(GlslBlock):
    """gl_PerVertex block."""

    def __init__(self, inout, lst):
        """Constructor."""
        GlslBlock.__init__(self)
        self.__inout = inout
        self.__scope = lst

    def format(self, force):
        """Return formatted output."""
        lst = "".join(map(lambda x: "%s %s;" % (x[0].format(force), x[1].format(force)), self.__scope))
        return "%s gl_PerVertex{%s};" % (self.__inout.format(force), lst)

    def __str__(self):
        """String representation."""
        return "Pervertex(%i)" % (len(self.__scope))

########################################
# Functions ############################
########################################


def glsl_parse_pervertex(source):
    """Parse inout block."""
    (inout, scope, remaining) = extract_tokens(source, ("?o", "gl_PerVertex", "?{", ";"))
    if (not inout) or (not scope):
        return (None, source)
    # Split scope into elements.
    lst = []
    while scope:
        (typeid, name, content) = extract_tokens(scope, ("?t", "?n", ";"))
        if not typeid or not name:
            return (None, source)
        lst += [(typeid, name)]
        scope = content
    return (GlslBlockPerVertex(inout, lst), remaining)
