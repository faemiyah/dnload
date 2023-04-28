from dnload.glsl_block import GlslBlock
from dnload.glsl_block import extract_tokens
from dnload.glsl_block_array import glsl_parse_array
from dnload.glsl_block_statement import glsl_parse_statement
from dnload.glsl_block_statement import glsl_parse_statements
from dnload.glsl_paren import GlslParen

########################################
# GlslBlockAssignment ##################
########################################

class GlslBlockAssignment(GlslBlock):
    """Assignment block."""

    def __init__(self, name, lst, assign, children, terminator):
        """Constructor."""
        GlslBlock.__init__(self)
        self.__name = name
        self.__modifiers = lst
        self.__assign = assign
        self.__terminator = terminator
        # Error cases.
        if self.__assign and (not children):
            raise RuntimeError("if assigning, must have child statements")
        # Hierarchy.
        self.addNamesUsed(name)
        self.addAccesses(lst)
        if children:
            self.addChildren(children)

    def format(self, force):
        """Return formatted output."""
        ret = self.__name.format(force)
        if self.__modifiers:
            ret += "".join(map(lambda x: x.format(force), self.__modifiers))
        statements = "".join(map(lambda x: x.format(force), self._children))
        if self.__assign:
            # Having an explicit terminator means there was a listing scope.
            if self.__terminator:
                return ret + ("%s{%s}%s" % (self.__assign.format(force), statements, self.__terminator.format(force)))
            return ret + ("%s%s" % (self.__assign.format(force), statements))
        return ret + statements

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
        if self.__terminator:
            return self.__terminator
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
        return (GlslBlockAssignment(name, None, None, None, None), content)
    # Empty assignment.
    (terminator, intermediate) = extract_tokens(content, ("?,|;",))
    if terminator:
        (statement, remaining) = glsl_parse_statement([terminator] + intermediate)
        return (GlslBlockAssignment(name, None, None, statement, None), remaining)
    # Non-empty assignment. Gather index and swizzle.
    modifiers = []
    while True:
        (index_scope, remaining) = extract_tokens(content, ("?[",))
        # Index scope may be empty, mut may not be None.
        if not index_scope is None:
            modifiers += [GlslParen("[")] + index_scope + [GlslParen("]")]
            content = remaining
            continue
        (access, remaining) = extract_tokens(content, ("?a",))
        if access:
            modifiers += [access]
            content = remaining
            continue
        (operator, remaining) = extract_tokens(content, ("?=",))
        if operator:
            content = remaining
            break
        # Can't be an assignment.
        return (None, source)
    # Try scope assignment.
    (scope, intermediate) = extract_tokens(content, ("?{",))
    if scope:
        (statements, discard) = glsl_parse_statements(scope)
        if (not statements) or discard:
            raise RuntimeError("error parsing statements from assignment scope")
        (terminator, remaining) = extract_tokens(intermediate, ("?,|;",))
        if terminator:
            return (GlslBlockAssignment(name, modifiers, operator, statements, terminator), remaining)
    # Try array assignment.
    (statement, remaining) = glsl_parse_array(content, explicit)
    if statement:
        return (GlslBlockAssignment(name, modifiers, operator, statement, None), remaining)
    # Try statement assignment.
    (statement, remaining) = glsl_parse_statement(content, explicit)
    if statement:
        return (GlslBlockAssignment(name, modifiers, operator, statement, None), remaining)
    # Not a valid assignment.
    return (None, source)

def is_glsl_block_assignment(op):
    """Tell if given object is GlslBlockAssignment."""
    return isinstance(op, GlslBlockAssignment)
