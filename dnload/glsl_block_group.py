from dnload.glsl_block import GlslBlock

########################################
# GlslBlockGroup #######################
########################################


class GlslBlockGroup(GlslBlock):
    """Group of other blocks. Not parsed, but combined."""

    def __init__(self, block):
        """Constructor."""
        GlslBlock.__init__(self)
        # Assumed block is already within the tree.
        if block.getParent():
            block.removeFromParent()
        self.addChildren(block)

    def format(self, force):
        """Return formatted output."""
        return "".join([x.format(force) for x in self._children])

########################################
# Functions ############################
########################################


def is_glsl_block_group(op):
    """Tell if given object is GlslBlockGroup."""
    return isinstance(op, GlslBlockGroup)
