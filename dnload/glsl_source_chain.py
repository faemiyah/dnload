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
        self.__chain_name = op.getChainName()
        self.__sources = []
        self.addSource(op)

    def addSource(self, op):
        """Adds a source block."""
        if self.getChainName() != op.getChainName():
            raise RuntimeError("chain name mismatch '%s' vs. '%s'" % (op.getChainName(), self.getChainName()))
        self.__sources = sorted(self.__sources + [op])

    def getChainName(self):
        """Gets the chain name for this source chain."""
        return self.__chain_name

    def getChainLength(self):
        """Gets the length of the source chain."""
        return len(self.__sources)

    def hasSource(self, op):
        """Tests if given source block is contained within this source chain."""
        assert_glsl_block_source(op)
        return op in self.__sources

    def __str__(self):
        """String representation."""
        ret = map(lambda x: "'%s'" % (x.getFilename()), self.__sources)
        return "[%s]" % (" => ".join(ret))
