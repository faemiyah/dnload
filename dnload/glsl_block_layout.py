from dnload.glsl_block import GlslBlock
from dnload.glsl_block import extract_tokens
from dnload.glsl_name import get_list_primitives

########################################
# GlslBlockLayout ######################
########################################

class GlslBlockLayout(GlslBlock):
    """Uniform declaration."""

    def __init__(self, elements):
        """Constructor."""
        GlslBlock.__init__(self)
        self.__elements = elements

    def format(self, force):
        """Return formatted output."""
        ret = []
        for ii in self.__elements:
            ret += ["".join(map(lambda x: x.format(force), ii))]
        return "layout(%s)" % (",".join(ret))

    def __str__(self):
        """String representation."""
        return "Layout(%i)" % (self.__location.getInt())

########################################
# Functions ############################
########################################

def glsl_parse_layout(source):
    """Parse layout block."""
    (scope, remaining) = extract_tokens(source, ("layout", "?("))
    if not scope:
        return (None, source)
    lst = []
    while scope:
        primitive_selector = "?" + "|".join(get_list_primitives())
        (primitive, intermediate) = extract_tokens(scope, (primitive_selector,))
        if primitive:
            lst += [[primitive]]
            scope = intermediate
            continue
        (name, assignment, value, intermediate) = extract_tokens(scope, ("?|binding|local_size_x|local_size_y|local_size_z|location|max_primitives|max_vertices", "?=", "?u"))
        if name and assignment and value:
            lst += [[name, assignment, value]]
            scope = intermediate
            continue
        (comma, intermediate) = extract_tokens(scope, "?|,")
        if comma:
            scope = intermediate
            continue
        raise RuntimeError("unknown layout directive %s" % (str(list(map(str, scope)))))
    return (GlslBlockLayout(lst), remaining)
