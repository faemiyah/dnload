from dnload.assembler_section import AssemblerSection

########################################
# AssemblerSectionAlignment ############
########################################

class AssemblerSectionAlignment(AssemblerSection):
    """Alignment section only meant to provide alignment and label."""

    def __init__(self, alignment, padding, post_label, name=None):
        AssemblerSection.__init__(self, name)
        self.__alignment = alignment
        self.__padding = padding
        self.__post_label = post_label

    def create_content(self, assembler):
        """Generate assembler content."""
        self.clear_content()
        if self.get_name():
            self.add_content(assembler.format_label(self.get_name()))
        # Pad with zero bytes.
        var_line = AssemblerVariable(("", 1, 0)).generate_source(assembler, 1)
        for ii in range(self.__padding):
            self.add_content(var_line)
        if 0 < self.__alignment:
            self.add_content(assembler.format_align(self.__alignment))
        self.add_content(assembler.format_label(self.__post_label))

########################################
# Functions ############################
########################################

def is_assembler_section_alignment(op):
    """Tell if given object is AssemblerSectionAlignment."""
    return isinstance(op, AssemblerSectionAlignment)
