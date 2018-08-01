########################################
# GlslTerminator #######################
########################################


class GlslTerminator:
    """Terminator class."""

    def __init__(self, source):
        """Constructor."""
        self.__terminator = source

    def format(self, force):
        """Return formatted output."""
        return self.__terminator

    def getTerminator(self):
        """Access terminating character."""
        return self.__terminator

    def __eq__(self, other):
        """Equals operator."""
        if is_glsl_terminator(other):
            return self.__terminator == other.getTerminator()
        return self.getTerminator() == other

    def __ne__(self, other):
        """Not equals operator."""
        return not (self == other)

    def __str__(self):
        """String representation."""
        return "GlslTerminator('%s')" % (self.__terminator)

########################################
# Functions ############################
########################################


def interpret_terminator(source):
    """Try to interpret a terminator."""
    if source == ";":
        return GlslTerminator(source)
    return None


def is_glsl_terminator(op):
    """Tell if token is operator."""
    return isinstance(op, GlslTerminator)
