import re

from dnload.glsl_block import GlslBlock

########################################
# GlslBlock ############################
########################################

class GlslBlockPreprocessor(GlslBlock):
    """Preprocessor block."""

    def __init__(self, source):
        """Constructor."""
        GlslBlock.__init__(self)
        lines = source.strip().split()
        self.__content = " ".join(lines)

    def format(self, force):
        """Return formatted output."""
        return "%s\n" % (self.__content)

    def __str__(self):
        """String representation."""
        return "Preprocessor('%s')" % (self.__content)

########################################
# Globals ##############################
########################################

g_directives = ("version",)

########################################
# Functions ############################
########################################

def glsl_parse_preprocessor(source):
    """Parse preprocessor line."""
    match = re.match(r'^\s*#\s*(\S+)\s+.*$', source)
    if match:
        if match.group(1) in g_directives:
            return GlslBlockPreprocessor(source)
    return None
