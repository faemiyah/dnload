import re

from dnload.glsl_name import is_glsl_name

########################################
# GlslNameStrip ########################
########################################

class GlslNameStrip:
    """Strip of names used for renaming purposes."""

    def __init__(self, block, name):
        """Constructor."""
        self.__blocks = [block]
        self.__names = []
        self.addName(name)

    def addBlock(self, op):
        """Add block to the list of blocks."""
        self.__blocks += [op]

    def addName(self, name):
        """Append one name to the list."""
        if not is_glsl_name(name):
            raise RuntimeError("not a GLSL name: %s" % (str(name)))
        if (self.getNameCount() >= 1) and (name != self.__names[0]):
            raise RuntimeError("trying to append unrelated names: %s != %s" % (str(self.__names[0]), str(name)))
        # Used and declared name lists may contain the exact same name.
        for ii in self.__names:
            if ii is name:
                return
        self.__names += [name]

    def appendTo(self, op):
        """Appends all names into another GLSL name strip."""
        for ii in self.__blocks:
            op.addBlock(ii)
        for ii in self.__names:
            op.addName(ii)

    def getBlock(self):
        """Gets the block that declared the original name."""
        return self.__blocks[0]

    def getBlockCount(self):
        """Gets the number of blocks."""
        return len(self.__blocks)

    def getBlockList(self):
        """Accessor."""
        return self.__blocks

    def getName(self):
        """Gets the declared name associated with this name strip."""
        return self.__names[0]

    def getNameCount(self):
        """Gets the number of names in this name strip."""
        return len(self.__names)

    def getNameList(self):
        """Accessor."""
        return self.__names

    def isUniform(self):
        """Tells if this name strip originates from an uniform block."""
        return is_glsl_block_uniform(self.__blocks[0])

    def lockNames(self, op):
        """Lock all names to given string."""
        for ii in self.__names:
            ii.lock(op)

    def updateNameTypes(self):
        """Update all name types and check for errors."""
        typeid = self.getName().getType()
        if not typeid:
            raise RuntimeError("declared name in GlslNameStrip has no type id")
        for ii in self.__names[1:]:
            found_type = ii.getType()
            if found_type:
                if typeid != found_type:
                    raise RuntimeError("conflicting type found for %s: %s vs. %s" % (str(ii), str(typeid), str(found_type)))
            else:
                ii.setType(typeid)

    def __lt__(lhs, rhs):
        """Comparison operator."""
        return lhs.getNameCount() < rhs.getNameCount()

    def __str__(self):
        """String representation."""
        return "GlslNameStrip('%s', %i)" % (self.getName().getName(), self.getNameCount())

########################################
# Functions ############################
########################################

def is_glsl_name_strip(op):
    """Tells if given object is a GLSL name strip."""
    return isinstance(op, GlslNameStrip)
