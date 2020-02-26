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
        if op.isCommonChainName():
            raise RuntimeError("first source added to source chain cannot have a common chain name")
        self.__chain_name = op.getChainName()
        if not self.__chain_name:
            raise RuntimeError("first source added to source chain must have a chain name")
        self.__sources = []
        self.addSource(op)

    def addSource(self, op):
        """Adds a source block."""
        if (not op.isCommonChainName()) and (self.getChainName() != op.getChainName()):
            raise RuntimeError("chain name mismatch '%s' vs. '%s'" % (op.getChainName(), self.getChainName()))
        if not self.isSourceSlotFree(op):
            raise RuntimeError("chain '%s': source slot '%s' already taken" % (self.getChainName(), op.getType()))
        self.__sources = sorted(self.__sources + [op])

    def getChainName(self):
        """Gets the chain name for this source chain."""
        return self.__chain_name

    def getChainLength(self):
        """Gets the length of the source chain."""
        return len(self.__sources)

    def getSources(self):
        """Gets all source files in the source chain."""
        return self.__sources

    def hasSource(self, op):
        """Tests if given source block is contained within this source chain."""
        assert_glsl_block_source(op)
        return op in self.__sources

    def isSourceSlotFree(self, op):
        """Tests if slot for source of given type is not filled."""
        input_type = op.getType()
        # No type -> goes everywhere.
        if not input_type:
            return True
        # Check if given source slot is not taken.
        for ii in self.__sources:
            if ii.getType() == input_type:
                return False
        return True

    def __str__(self):
        """String representation."""
        ret = map(lambda x: "'%s'" % (x.getFilename()), self.__sources)
        return "[%s]" % (" => ".join(ret))
