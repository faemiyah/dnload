from dnload.common import is_verbose
from dnload.glsl_type import is_glsl_precision_string
from dnload.glsl_type import is_glsl_precision_type_string

########################################
# GlslSourcePrecision ##################
########################################

class GlslSourcePrecision:
    """GLSL source file precision information."""

    def __init__(self, srctype):
        """Constructor."""
        self.__precisions = {}
        self.__type = srctype

    def getPrecision(self, typeid):
        """Gets precision if it's explicitly set."""
        if typeid in self.__precisions:
            return self.__precisions[typeid]
        # Return fallback precision if possible.
        if self.__type == "fragment":
            if typeid in g_precisions_fragment:
                return g_precisions_fragment[typeid]
        elif self.__type == "vertex":
            if typeid in g_precisions_vertex:
                return g_precisions_vertex[typeid]
        # No match.
        return None

    def setPrecision(self, typeid, precision):
        """Set precision for given type id."""
        if not is_glsl_precision_type_string(typeid):
            raise RuntimeError("invalid type for GLSL precision setting: '%s'" % (typeid))
        if not is_glsl_precision_string(precision):
            raise RuntimeError("invalid GLSL precision string: '%s'" % (precision))
        self.__precisions[typeid] = precision

########################################
# Globals ##############################
########################################

g_precisions_fragment = {
        "int" : "mediump",
        "sampler2D" : "lowp",
        "samplerCube" : "lowp",
        "atomic_uint" : "highp",
        }

g_precisions_vertex = {
        "float" : "highp",
        "int" : "highp",
        "sampler2D" : "lowp",
        "samplerCube" : "lowp",
        "atomic_uint" : "highp",
        }
