########################################
# AssemblerBssElement ##################
########################################

class AssemblerBssElement:
    """.bss element, representing a memory area that would go to .bss section."""

    def __init__(self, name, size, und_symbols=None):
        """Constructor."""
        self.__name = name
        self.__size = size
        self.__und = (und_symbols and (name in und_symbols))

    def get_name(self):
        """Get name of this."""
        return self.__name

    def get_size(self):
        """Get size of this."""
        return self.__size

    def is_und_symbol(self):
        """Tell if this is an und symbol."""
        return self.__und

    def __eq__(self, rhs):
        """Equals operator."""
        return (self.__name == rhs.get_name()) and (self.__size == rhs.get_size()) and (self.__und == rhs.is_und_symbol())

    def __lt__(self, rhs):
        """Less than operator."""
        if self.__und:
            if not rhs.is_und_symbol():
                return True
        elif rhs.is_und_symbol():
            return False
        return (self.__size < rhs.get_size())

    def __str__(self):
        """String representation."""
        return "(%s, %i, %s)" % (self.__name, self.__size, str(self.__und))
