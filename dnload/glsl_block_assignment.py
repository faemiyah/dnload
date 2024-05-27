from dnload.common import listify
from dnload.glsl_block import GlslBlock
from dnload.glsl_block import extract_tokens
from dnload.glsl_block import is_glsl_block
from dnload.glsl_block_array import glsl_parse_array
from dnload.glsl_block_statement import glsl_parse_statement
from dnload.glsl_block_statement import glsl_parse_statements
from dnload.glsl_paren import GlslParen
from dnload.glsl_terminator import GlslTerminator

########################################
# GlslBlockAssignment ##################
########################################

class GlslBlockAssignment(GlslBlock):
    """Assignment block."""

    def __init__(self, name, modifiers, assign, statements, terminator):
        """Constructor."""
        GlslBlock.__init__(self)
        self.__name = name
        self.__modifiers = modifiers
        self.__assign = assign
        self.__statements = listify(statements)
        self.__terminator = terminator
        # Error cases.
        if self.__assign and (not statements):
            raise RuntimeError("if assigning, must have child statements")
        # Hierarchy.
        self.addNamesUsed(name)
        self.addAccesses(modifiers)
        if modifiers:
            for ii in modifiers:
                if is_glsl_block(ii):
                    self.addChildren(ii)
        if statements:
            self.addChildren(statements)

    def format(self, force):
        """Return formatted output."""
        ret = self.__name.format(force)
        if self.__modifiers:
            ret += "".join(map(lambda x: x.format(force), self.__modifiers))
        statements = "".join(map(lambda x: x.format(force), self.__statements))
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
        if len(self.__statements) != 1:
            raise RuntimeError("child count must be 1 for getStatement()")
        return self.__statements[0]

    def getTerminator(self):
        """Accessor."""
        if self.__terminator:
            return self.__terminator
        if len(self.__statements) != 1:
            raise RuntimeError("child count must be 1 for getTerminator()")
        return self.__statements[0].getTerminator()

    def replaceTerminator(self, op):
        """Replace terminator with given element."""
        if self.__terminator:
            self.__terminator = GlslTerminator(op)
            return
        if len(self.__statements) != 1:
            raise RuntimeError("child count must be 1 for replaceTerminator()")
        self.__statements[0].replaceTerminator(op)

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
            (index_scope_statements, discard) = glsl_parse_statements(index_scope)
            if not index_scope_statements:
                raise RuntimeError("parsing indexing scope statements failed")
            modifiers += [GlslParen("[")] + index_scope_statements + [GlslParen("]")]
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
