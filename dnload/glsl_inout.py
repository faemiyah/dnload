########################################
# GlslInOut ############################
########################################


class GlslInOut:
    """GLSL in/out directive element."""

    def __init__(self, inout):
        """Constructor."""
        self.__inout = inout

    def format(self, force):
        """Return formatted output."""
        return self.__inout

    def __str__(self):
        """String representation."""
        return "GlslInOut('%s')" % (self.__inout)

########################################
# Globals ##############################
########################################


g_inout = ("attribute",
           "in",
           "inout",
           "out",
           "varying")

########################################
# Functions ############################
########################################


def interpret_inout(source):
    """Try to interpret in/out directive element."""
    if source in g_inout:
        return GlslInOut(source)
    return None


def is_glsl_inout(op):
    """Tell if token is in/out directive element."""
    return isinstance(op, GlslInOut)
