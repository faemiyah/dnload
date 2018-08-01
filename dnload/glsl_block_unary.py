from dnload.glsl_block import GlslBlock
from dnload.glsl_block import extract_tokens
from dnload.glsl_block_statement import glsl_parse_statement
from dnload.glsl_operator import is_glsl_operator

########################################
# GlslBlockUnary #######################
########################################


class GlslBlockUnary(GlslBlock):
    """Unary statement block."""

    def __init__(self, statement):
        """Constructor."""
        GlslBlock.__init__(self)
        # Hierarchy.
        self.addChildren(statement)

    def format(self, force):
        """Return formatted output."""
        if len(self._children) != 1:
            raise RuntimeError("GlslBlockUnary::format(), child count != 1")
        return "%s" % ("".join(map(lambda x: x.format(force), self._children)))

    def replaceTerminator(self, op):
        """Replace terminator with given operator."""
        self._children[0].replaceTerminator(op)

    def __str__(self):
        """String representation."""
        return "Unary()"

########################################
# Globals ##############################
########################################


g_allowed_operators = (
    "--",
    "++",
)

########################################
# Functions ############################
########################################


def glsl_parse_unary(source):
    """Parse unary block."""
    # Try prefix unary.
    (operator, name, terminator, remaining) = extract_tokens(source, ("?p", "?n", "?;"))
    if operator in g_allowed_operators:
        (statement, discarded) = glsl_parse_statement([operator, name, terminator])
        if discarded:
            raise RuntimeError("discarded elements in prefix unary")
        return (GlslBlockUnary(statement), remaining)
    # Try postfix unary.
    (name, operator, terminator, remaining) = extract_tokens(source, ("?n", "?p", "?;"))
    if operator in g_allowed_operators:
        (statement, discarded) = glsl_parse_statement([name, operator, terminator])
        if discarded:
            raise RuntimeError("discarded elements in postfix unary")
        return (GlslBlockUnary(statement), remaining)
    # No match.
    return (None, source)


def is_glsl_block_unary(op):
    """Tell if given object is GlslBlockUnary."""
    return isinstance(op, GlslBlockUnary)
