from dnload.common import is_verbose
from dnload.glsl_block import GlslBlock
from dnload.glsl_block import extract_tokens
from dnload.glsl_type import is_glsl_precision_type_string

########################################
# GlslBlockPrecision ###################
########################################

class GlslBlockPrecision(GlslBlock):
    """Precision block."""

    def __init__(self, typeid):
        """Constructor."""
        GlslBlock.__init__(self)
        self.__typeid = typeid
        # Validate type id.
        if not typeid.getPrecision():
            raise RuntimeError("type '%s' in precision block missing precision qualifier" % (self.__typeid.format()))
        # Type must be in allowed precision types.
        if not is_glsl_precision_type_string(self.getType()):
            raise RuntimeError("invalid type '%s' for precision block" % (self.getType()))

    def format(self, force):
        """Return formatted output."""
        return "precision %s;" % (self.__typeid.format(force))

    def getPrecision(self):
        """Return the precision from type identifier."""
        return self.__typeid.getPrecision()

    def getType(self):
        """Returns the type from the type identifier."""
        return self.__typeid.getType()

    def __str__(self):
        """String representation."""
        return "Precision('%s %s')" % (self.getPrecision(), self.__typeid.getType())

########################################
# Functions ############################
########################################

def glsl_parse_precision(source):
    """Parse precision block."""
    (typeid, remaining) = extract_tokens(source, ("precision", "?t", ";"))
    if typeid:
        return (GlslBlockPrecision(typeid), remaining)
    return (None, source)

def is_glsl_block_precision(op):
    """Tell if given object is GlslBlockPrecision."""
    return isinstance(op, GlslBlockPrecision)
