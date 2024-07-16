from dnload.glsl_int import interpret_int
from dnload.platform_var import platform_is_gles

########################################
# GlslInt ##############################
########################################

class GlslFloat:
    """GLSL integer."""

    def __init__(self, integer1, integer2):
        """Constructor."""
        if integer2.getSign():
            raise RuntimeError("invalid second integer for float: %s" % (integer2.getStr()))
        self.__integer1 = integer1
        self.__integer2 = integer2
        self.updateNumber()
        self.__sign = integer1.getSign()
        self.__allow_integrify = False
        # Check.
        if float(self.format(False)) != self.__number:
            raise RuntimeError("incorrect float parse: '%f' vs. '%s'" % (self.__number, self.format(False)))

    def format(self, force):
        """Return formatted output."""
        if self.__integer1.getInt() == 0:
            if self.__integer2.getInt() == 0:
                if self.isIntegrifyAllowed():
                    return "0"
                return ".0"
            return self.__sign + "." + self.__integer2.getStr().rstrip("0")
        if (self.__integer2.getInt() == 0) and self.isIntegrifyAllowed():
            return str(self.__integer1.getInt())
        return "%s.%s" % (str(self.__integer1.getInt()), self.__integer2.getStr().rstrip("0"))

    def getFloat(self):
        """Accessor."""
        return self.__number

    def getPrecision(self):
        """Get precision - number of numbers to express."""
        return self.__integer1.getPrecision() + self.__integer2.getPrecision()

    def isIntegrifyAllowed(self):
        """Tell if integrification is allowed?"""
        return self.__allow_integrify and (not platform_is_gles())

    def setAllowIntegrify(self, flag):
        """Set allow integrify flag."""
        self.__allow_integrify = flag

    def requiresTruncation(self):
        """Does this number require truncation?"""
        return True

    def truncatePrecision(self, op):
        """Truncate numeric precision to some value of expressed numbers."""
        used = self.__integer1.truncatePrecision(op)
        if used >= op:
            self.__integer2 = interpret_int("0")
        else:
            self.__integer2.truncatePrecision(op - used)
        self.updateNumber()

    def updateNumber(self):
        """Update the number value."""
        self.__number = float(str(self.__integer1.getStr()) + "." + str(self.__integer2.getStr()))

    def __str__(self):
        """String representation."""
        return "GlslFloat('%s')" % (self.format(False))

########################################
# Functions ############################
########################################

def convert_to_int(source):
    """Convert source to integer or fail."""
    if isinstance(source, str):
        return interpret_int(source)
    if isinstance(source, int):
        return interpret_int(str(source))
    return source

def interpret_float(source1, source2):
    """Try to interpret float."""
    number1 = convert_to_int(source1)
    if not number1:
        raise RuntimeError("not an integer: '%s'" % (source1))
    number2 = convert_to_int(source2)
    if not number2:
        raise RuntimeError("not an integer: '%s'" % (source2))
    return GlslFloat(number1, number2)

def is_glsl_float(op):
    """Tell if token is floating point number."""
    return isinstance(op, GlslFloat)
