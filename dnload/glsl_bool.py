import re

########################################
# GlslBool #############################
########################################

class GlslBool:
    """GLSL boolean."""

    def __init__(self, source):
        """Constructor."""
        if source == "true":
            self.__string = source
            self.__number = True
        elif source == "false":
            self.__string = source
            self.__number = False
        else:
            raise RuntimeError("not a GLSL boolean string: '%s'" % (source))

    def format(self, force):
        """Return formatted output."""
        return str(self.__string)

    def getBool(self):
        """Integer representation."""
        return self.__number

    def requiresTruncation(self):
        """Does this number require truncation?"""
        return False

    def __str__(self):
        """String representation."""
        return "GlslBool('%s')" % (self.__string)

########################################
# Functions ############################
########################################

def interpret_bool(source):
    """Try to interpret boolean."""
    if re.match(r'^(false|true)$', source):
        return GlslBool(source)
    return None

def is_glsl_bool(op):
    """Tell if token is integer."""
    return isinstance(op, GlslBool)
