import re

from dnload.platform_var import platform_is_gles

########################################
# GlslType #############################
########################################

class GlslType:
    """GLSL type identifier."""

    def __init__(self, modifier, precision, source):
        """Constructor."""
        self.__modifier = modifier
        self.__precision = precision
        self.__type = source
        self.__implied_precision = None
        # Save the flag so this type may check for errors.
        self.__pseudo_type = match_pseudo_type_id(self.__type)

    def format(self, force):
        """Return formatted output."""
        if self.__pseudo_type:
            raise RuntimeError("trying to format a pseudo type '%s'" % (self.__type))
        ret = ""
        if self.__modifier and ((not force) or (self.__modifier != "const")):
            ret += self.__modifier + " "
        if self.__precision and ((not force) or ((self.__precision != self.__implied_precision) and platform_is_gles())):
            ret += self.__precision + " "
        return ret + self.__type

    def getPrecision(self):
        """Get the precision of the type."""
        return self.__precision

    def getType(self):
        """Get the type identifier of the type."""
        return self.__type

    def getPrecisionType(self):
        """Get the precision type corresponding with this type."""
        if self.__type not in g_type_to_precision_type:
            raise RuntimeError("no known corresponding precision type for '%s'" % (self.__type))
        return g_type_to_precision_type[self.__type]

    def isVectorType(self):
        """Tell if this is a vector type (eglible for swizzling)."""
        if re.match(r'^(uvec\d|ivec\d|vec\d?)$', self.__type):
            return True
        return False

    def setImpliedPrecision(self, precision_state):
        """Set the precision that will be erased."""
        precision_type = self.getPrecisionType()
        self.__implied_precision = precision_state.getPrecision(precision_type)

    def __eq__(self, other):
        """Equals operator."""
        if is_glsl_type(other) and (self.__type == other.__type):
            return True
        return (self.__type == other)

    def __ne__(self, other):
        """Not equals operator."""
        return not (self == other)

    def __str__(self):
        """String representation."""
        return "GlslType('%s')" % (self.__type)

########################################
# Globals ##############################
########################################

g_modifier_strings = (
    "const",
    "flat",
    )

g_precision_strings = (
    "lowp",
    "mediump",
    "highp",
    )

g_type_to_precision_type = {
    "atomic_uint": "atomic_uint",
    "bool": "int",
    "float": "float",
    "int": "int",
    "ivec2": "int",
    "ivec3": "int",
    "ivec4": "int",
    "mat2": "float",
    "mat3": "float",
    "mat4": "float",
    "sampler1D": "sampler1D",
    "sampler1DShadow": "sampler1DShadow",
    "sampler2D": "sampler2D",
    "sampler2DShadow": "sampler2DShadow",
    "sampler3D": "sampler3D",
    "sampler3DShadow": "sampler3DShadow",
    "samplerCube": "samplerCube",
    "samplerCubeShadow": "samplerCubeShadow",
    "uvec2": "int",
    "uvec3": "int",
    "uvec4": "int",
    "uint": "int",
    "uvec2": "int",
    "uvec3": "int",
    "uvec4": "int",
    "vec2": "float",
    "vec3": "float",
    "vec4": "float",
    "void": None,
    }

g_precision_type_strings = filter(lambda x: x, g_type_to_precision_type.values())

########################################
# Functions ############################
########################################

def match_pseudo_type_id(op):
    """Tell if given string matches a pseudo type."""
    if re.match(r'(mat|vec)$', op):
        return True
    return False

def is_glsl_modifier_string(op):
    """Tell if given string is a valid GLSL type modifier string."""
    return op in g_modifier_strings

def is_glsl_precision_string(op):
    """Tell if given string is a valid GLSL precision string."""
    return op in g_precision_strings

def is_glsl_precision_type_string(op):
    """Tell if given string is a valid name for GLSL precision directive type."""
    return op in g_precision_type_strings

def is_glsl_type_string(op):
    """Tell if given string is a valid GLSL type string."""
    return op in g_type_to_precision_type

def interpret_pseudo_type(op):
    """Interpret a pseudo-type that cannot be formatted, but is recognized as a type."""
    if match_pseudo_type_id(op):
        return GlslType(None, None, op)
    return None

def interpret_type(op1, op2=None, op3=None):
    """Try to interpret type identifier."""
    if op3:
        if is_glsl_modifier_string(op1) and is_glsl_precision_string(op2) and is_glsl_type_string(op3):
            return GlslType(op1, op2, op3)
    elif op2:
        if not is_glsl_type_string(op2):
            return None
        if is_glsl_modifier_string(op1):
            return GlslType(op1, None, op2)
        if is_glsl_precision_string(op1):
            return GlslType(None, op1, op2)
    elif is_glsl_type_string(op1):
        return GlslType(None, None, op1)
    return None

def is_glsl_type(op):
    """Tell if token is type identifier."""
    return isinstance(op, GlslType)
