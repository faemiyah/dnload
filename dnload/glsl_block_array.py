from dnload.glsl_block import GlslBlock
from dnload.glsl_block import extract_tokens
from dnload.glsl_block_statement import glsl_parse_statement

########################################
# GlslBlockArray #######################
########################################

class GlslBlockArray(GlslBlock):
    """Array literal block."""

    def __init__(self, typeid, children, terminator):
        """Constructor."""
        GlslBlock.__init__(self)
        self.__typeid = typeid
        self.__terminator = terminator
        # Hierarchy.
        if not children:
            raise RuntimeError("array literal must have children")
        self.addChildren(children)

    def format(self, force):
        """Return formatted output."""
        statements = "".join(map(lambda x: x.format(force), self._children))
        return "%s[](%s)%s" % (self.__typeid.format(force), statements, self.__terminator.format(force))

    def getTerminator(self):
        """Accessor."""
        return self.__terminator

    def replaceTerminator(self, op):
        """Replace terminator with given element."""
        self.__terminator = op

    def __str__(self):
        """String representation."""
        return "Assignment('%s')" % (self.__name.getName())

########################################
# Functions ############################
########################################

def glsl_parse_array(source, explicit=True):
    """Parse array literal block."""
    # Must have name. Name must not be just 'return'.
    (typeid, bracket_scope, paren_scope, content) = extract_tokens(source, ("?t", "?[", "?("))
    if not typeid:
        return (None, source)
    # Bracket scope must be empty.
    if bracket_scope and (len(bracket_scope != 1) or (not is_glsl_type(bracket_scope[0]))):
        raise RuntimeError("illegal contents for array literal bracket scope: %s" % (str(map(lambda x: str(x), bracket_scope))))
    # Parse paren scope.
    statements = []
    while paren_scope:
        (statement, following) = glsl_parse_statement(paren_scope, False)
        if statement:
            statements += [statement]
            paren_scope = following
            continue
        raise RuntimeError("remaining elements cannot be parsed into a statement: %s" % (str(map(lambda x: str(x), paren_scope))))
    # Look for a terminator.
    (terminator, remaining) = extract_tokens(content, "?,|;")
    if terminator:
        return (GlslBlockArray(typeid, statements, terminator), remaining)
    # Return without terminator.
    return (GlslBlockArray(typeid, statements, None), content)

def is_glsl_block_array(op):
    """Tell if given object is GlslBlockArray."""
    return isinstance(op, GlslBlockArray)
