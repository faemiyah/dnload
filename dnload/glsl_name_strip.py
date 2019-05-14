import re
from dnload.glsl_block_uniform import is_glsl_block_uniform

########################################
# GlslNameStrip ########################
########################################

class GlslNameStrip:
    """Strip of names used for renaming purposes."""

    def __init__(self, block, name):
        """Constructor."""
        self.__block = block
        self.__names = [name]

    def append(self, name):
        """Append one name to the list."""
        self.__names += [name]

    def isUniform(self):
        """Tells if this name strip originates from an uniform block."""
        return is_glsl_block_uniform(self.__block)

    def isPotentialInoutMatch(self, op):
        """Tells if another name strip is in the same source chain (but in another source file)."""



########################################
# Functions ############################
########################################

