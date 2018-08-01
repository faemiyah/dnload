from dnload.common import is_listing
from dnload.glsl_block import GlslBlock
from dnload.glsl_block import extract_tokens
from dnload.glsl_block_parameter import glsl_parse_parameter_list
from dnload.glsl_block_scope import glsl_parse_scope

########################################
# GlslBlockFunction ####################
########################################


class GlslBlockFunction(GlslBlock):
    """Function block."""

    def __init__(self, typeid, name, lst, scope):
        """Constructor."""
        GlslBlock.__init__(self)
        self.__typeid = typeid
        self.__name = name
        self.__parameters = lst
        self.__scope = scope
        if not is_listing(self.__parameters):
            raise RuntimeError("parameters must be a listing")
        # Hierarchy.
        name.setType(typeid)
        self.addNamesDeclared(name)
        self.addNamesUsed(name)
        self.addChildren(lst)
        self.addChildren(scope)

    def format(self, force):
        """Return formatted output."""
        lst = ""
        if 0 < len(self.__parameters):
            lst = ",".join(map(lambda x: x.format(force), self.__parameters))
        return "%s %s(%s)%s" % (self.__typeid.format(force), self.__name.format(force), lst, self.__scope.format(force))

    def getName(self):
        """Accessor."""
        return self.__name

    def getType(self):
        """Accessor."""
        return self.__typeid

    def __str__(self):
        """String representation."""
        return "Function('%s')" % (self.__name.getName())

########################################
# Functions ############################
########################################


def glsl_parse_function(source):
    """Parse function block."""
    (typeid, name, param_scope, content) = extract_tokens(source, ("?t", "?n", "?("))
    if (not typeid) or (not name) or (param_scope is None):
        return (None, source)
    parameters = glsl_parse_parameter_list(param_scope)
    if parameters is None:
        return (None, source)
    (scope, remaining) = glsl_parse_scope(content)
    if not scope:
        return (None, source)
    return (GlslBlockFunction(typeid, name, parameters, scope), remaining)


def is_glsl_block_function(op):
    """Tell if given object is a GLSL function block."""
    return isinstance(op, GlslBlockFunction)
