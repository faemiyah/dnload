from dnload.glsl_block import GlslBlock
from dnload.glsl_block import extract_tokens
from dnload.glsl_block_statement import glsl_parse_statement
from dnload.glsl_paren import GlslParen

########################################
# GlslBlockAssignment ##################
########################################


class GlslBlockAssignment(GlslBlock):
    """Assignment block."""

    def __init__(self, name, lst, assign, statement):
        """Constructor."""
        GlslBlock.__init__(self)
        self.__name = name
        self.__modifiers = lst
        self.__assign = assign
        if self.__assign and (not statement):
            raise RuntimeError("if assigning, must have a statement")
        # Hierarchy.
        self.addNamesUsed(name)
        self.addAccesses(lst)
        if statement:
            self.addChildren(statement)

    def format(self, force):
        """Return formatted output."""
        ret = self.__name.format(force)
        if self.__modifiers:
            ret += "".join([x.format(force) for x in self.__modifiers])
        statements = "".join([x.format(force) for x in self._children])
        if not self.__assign:
            return ret + statements
        return ret + ("%s%s" % (self.__assign.format(force), statements))

    def getName(self):
        """Accessor."""
        return self.__name

    def getStatement(self):
        """Accessor."""
        if len(self._children) != 1:
            raise RuntimeError("GlslBlockAssignment::getStatement(), child count != 1")
        return self._children[0]

    def getTerminator(self):
        """Accessor."""
        if len(self._children) != 1:
            raise RuntimeError("GlslBlockAssignment::getTerminator(), child count not 1")
        return self._children[0].getTerminator()

    def replaceTerminator(self, op):
        """Replace terminator with given element."""
        self._children[0].replaceTerminator(op)

    def __str__(self):
        """String representation."""
        return "Assignment('%s')" % (self.__name.getName())

########################################
# Functions ############################
########################################


def glsl_parse_assignment(source, explicit=True):
    """Parse assignment block."""
    # Must have name. Name must not be just 'return'.
    (name, content) = extract_tokens(source, ("?n",))
    if (not name) or (name == "return"):
        return (None, source)
    # Completely empty assignment. Acceptable if not in explicit mode.
    if (not content) and (not explicit):
        return (GlslBlockAssignment(name, None, None, None), content)
    # Empty assignment.
    (terminator, intermediate) = extract_tokens(content, ("?,|;",))
    if terminator:
        (statement, remaining) = glsl_parse_statement([terminator] + intermediate)
        return (GlslBlockAssignment(name, None, None, statement), remaining)
    # Non-empty assignment. Gather index and swizzle.
    lst = []
    while True:
        (index_scope, remaining) = extract_tokens(content, ("?[",))
        if index_scope:
            lst += [GlslParen("[")] + index_scope + [GlslParen("]")]
            content = remaining
            continue
        (access, remaining) = extract_tokens(content, ("?a",))
        if access:
            lst += [access]
            content = remaining
            continue
        (operator, remaining) = extract_tokens(content, ("?=",))
        if operator:
            content = remaining
            break
        # Can't be an assignment.
        return (None, source)
    # Gather statement.
    (statement, remaining) = glsl_parse_statement(content, explicit)
    if not statement:
        return (None, source)
    return (GlslBlockAssignment(name, lst, operator, statement), remaining)


def is_glsl_block_assignment(op):
    """Tell if given object is GlslBlockAssignment."""
    return isinstance(op, GlslBlockAssignment)
