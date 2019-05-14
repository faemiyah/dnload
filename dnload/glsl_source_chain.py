from dnload.common import is_verbose
from dnload.glsl_block_source import assert_glsl_block_source
from dnload.glsl_block_source import is_glsl_block_source

########################################
# Globals ##############################
########################################

class GlslSourceChain:
    """Chain of GLSL sources. Can be used to search for source connections."""

    def __init__(self, op):
        """Constructor."""
        self.__sources = []
        self.addSource(op)

    def addSource(self, op):
        """Adds a source block."""
        assert_glsl_block_source(op)
        self.__sources = sorted(self.__sources + [op])

    def hasSource(self, op):
        """Tests if given source block is contained within this source chain."""
        assert_glsl_block_source(op)
        return op in self.__sources

    def __str__(self):
        """String representation."""
        ret = map(lambda x: "'%s'" % (x.getFilename()), self.__sources)
        return "[%s]" % (" => ".join(ret))
