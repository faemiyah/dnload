from dnload.common import listify

########################################
# SymbolSource #########################
########################################


class SymbolSource:
    """Representation of source providing one symbol."""

    def __init__(self, name, dependencies, headers, prototypes, source):
        """Constructor."""
        self.__name = name
        self.__dependencies = listify(dependencies)
        self.__headers = listify(headers)
        self.__prototypes = listify(prototypes)
        self.__source = source

    def get_dependencies(self):
        """Accessor."""
        return self.__dependencies

    def get_headers(self):
        """Accessor."""
        return self.__headers

    def get_name(self):
        """Accessor."""
        return self.__name

    def get_prototypes(self):
        """Accessor."""
        return self.__prototypes

    def get_source(self):
        """Accessor."""
        return self.__source
