from dnload.glsl_block import GlslBlock
from dnload.glsl_block import extract_tokens
from dnload.glsl_block_statement import glsl_parse_statements

########################################
# GlslBlockReturn ######################
########################################

class GlslBlockReturn(GlslBlock):
    """Return block."""

    def __init__(self, lst):
        """Constructor."""
        GlslBlock.__init__(self)
        # Hierarchy.
        self.addChildren(lst)

    def format(self, force):
        """Return formatted output."""
        ret = "".join(map(lambda x: x.format(force), self._children))
        # Statement starting with paren does not need the space.
        if ret[:1] == "(":
            return "return" + ret
        return "return " + ret

    def isEmptyReturn(self):
        """Tell if this return statement is empty."""
        # Return statement is only empty if it only has one child that has no tokens.
        return (len(self._children) == 1) and (not self._children[0].getTokens())

    def __str__(self):
        """String representation."""
        return "Return()"

########################################
# Functions ############################
########################################

def glsl_parse_return(source):
    """Parse return block."""
    (ret, content) = extract_tokens(source, "?|return")
    if not ret:
        return (None, source)
    (statements, remaining) = glsl_parse_statements(content, ";")
    if not statements:
        return (None, source)
    return (GlslBlockReturn(statements), remaining)

def is_glsl_block_return(op):
    """Tell if given object is GlslBlockReturn."""
    return isinstance(op, GlslBlockReturn)
