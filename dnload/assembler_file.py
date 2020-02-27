import re

from dnload.assembler_section import AssemblerSection
from dnload.assembler_section_alignment import is_assembler_section_alignment
from dnload.assembler_section_bss import AssemblerSectionBss
from dnload.common import is_verbose
from dnload.common import listify

########################################
# AssemblerFile ########################
########################################

class AssemblerFile:
    """Assembler file representation."""

    def __init__(self, fname):
        """Constructor, opens and reads a file."""
        self.__sections = []
        self.__filename = fname
        self.add_source(fname)

    def add_sections(self, op):
        """Manually add one or more sections."""
        self.__sections += listify(op)

    def add_source(self, fname):
        """Add source from an assembler file."""
        fd = open(fname, "r")
        lines = fd.readlines()
        fd.close()
        current_section = AssemblerSection("text")
        sectionre = re.compile(r'^\s*\.section\s+\"?\.([a-zA-Z0-9_]+)[\.\s]')
        directivere = re.compile(r'^\s*\.(bss|data|rodata|text)')
        for ii in lines:
            # Try both expressions first.
            match = sectionre.match(ii)
            if not match:
                match = directivere.match(ii)
            # If match, start new section.
            if match:
                self.add_sections(current_section)
                current_section = AssemblerSection(match.group(1), ii)
            else:
                current_section.add_content(ii)
        if not current_section.empty():
            self.add_sections(current_section)
        if is_verbose():
            section_names = map(lambda x: x.get_name(), self.__sections)
            print("%i sections in '%s': %s" % (len(self.__sections), fname, str(section_names)))

    def crunch(self):
        """Crunch sections, potentially removing dead code."""
        for ii in self.__sections:
            ii.crunch()

    def generate_fake_bss(self, assembler, und_symbols=None, elfling=None):
        """Remove local labels that would seem to generate .bss, make a fake .bss section."""
        bss = AssemblerSectionBss()
        for ii in self.__sections:
            while True:
                entry = ii.extract_bss(und_symbols)
                if not entry:
                    break
                if not entry.is_und_symbol():
                    bss.add_element(entry)
        if elfling:
            bss.add_element(AssemblerBssElement(ELFLING_WORK, elfling.get_work_size()))
        bss_size = bss.get_size()
        if 0 < bss.get_alignment():
            pt_load_string = ", second PT_LOAD required"
        else:
            pt_load_string = ", one PT_LOAD sufficient"
        if is_verbose():
            outstr = "Constructed fake .bss segement: "
            if 1073741824 < bss_size:
                print("%s%1.1f Gbytes%s" % (outstr, float(bss_size) / 1073741824.0, pt_load_string))
            elif 1048576 < bss_size:
                print("%s%1.1f Mbytes%s" % (outstr, float(bss_size) / 1048576.0, pt_load_string))
            elif 1024 < bss_size:
                print("%s%1.1f kbytes%s" % (outstr, float(bss_size) / 1024.0, pt_load_string))
            else:
                print("%s%u bytes%s" % (outstr, bss_size, pt_load_string))
        self.add_sections(bss)
        return bss

    def generate_file_output(self, section_names):
        """Generate output to be written into a file."""
        ret = ""
        allowed_names = []
        denied_names = []
        # If no section_names, allow everything.
        if section_names:
            for ii in section_names:
                if ii.startswith("^"):
                    denied_names += [ii[len("^"):]]
                else:
                    allowed_names += [ii]
        for ii in self.__sections:
            sn = ii.get_name()
            if (sn not in denied_names) and ((not allowed_names) or (sn in allowed_names)):
                ret += ii.generate_file_output()
        return ret

    def getSectionAlignment(self):
        """Accessor."""
        for ii in self.__sections:
            if is_assembler_section_alignment(ii):
                return ii
        return None

    def hasSectionAlignment(self):
        """Tell if an alignment section exists."""
        return not (self.getSectionAlignment() is None)

    def hasEntryPoint(self):
        """Tell if entry point exists somewhere within this file."""
        for ii in self.__sections:
            if ii.want_entry_point():
                return True
        return False

    def incorporate(self, other, label_name=None, jump_point_name=None):
        """Incorporate another assembler file into this, rename entry points."""
        globls = set()
        labels = []
        # Gather global names that cannot be renamed.
        for ii in other.__sections:
            globls = globls.union(ii.gather_globals())
            print(str(globls))
        # Gather all labels.
        for ii in other.__sections:
            if jump_point_name:
                ii.replace_entry_point(jump_point_name)
            labels += ii.gather_labels(globls)
        # Remove jump point if asked to.
        if jump_point_name:
            labels.remove(jump_point_name)
        elif other.hasEntryPoint():
            raise RuntimeError("incorporating '%s': jump point not defined but entry point exists" % (str(other)))
        # Suffix all labels with given label to prevent generated code name clashes.
        if label_name:
            labels.sort(key=len, reverse=True)
            for ii in other.__sections:
                ii.replace_labels(labels, label_name)
        self.add_sections(other.__sections)

    def sort_sections(self, assembler, data_in_front=True):
        """Sort sections into an order that is more easily compressible."""
        text_sections = []
        rodata_sections = []
        data_sections = []
        other_sections = []
        for ii in self.__sections:
            if "text" == ii.get_name():
                text_sections += [ii]
            elif "rodata" == ii.get_name():
                rodata_sections += [ii]
            elif "data" == ii.get_name():
                data_sections += [ii]
            else:
                other_sections += [ii]
        text_section_str = []
        rodata_section_str = []
        data_section_str = []
        other_section_str = []
        if text_sections:
            text_section_str += ["%i text" % (len(text_sections))]
        if rodata_sections:
            rodata_section_str = ["%i rodata" % (len(rodata_sections))]
        if data_sections:
            data_section_str += ["%i data" % (len(data_sections))]
        if other_sections:
            other_section_str = [", ".join(map(lambda x: x.get_name(), other_sections))]
        # Sort data either in front or in the back.
        if data_in_front:
            section_str = rodata_section_str + data_section_str + text_section_str + other_section_str
            self.__sections = rodata_sections + data_sections + text_sections + other_sections
        else:
            section_str = text_section_str + rodata_section_str + data_section_str + other_section_str
            self.__sections = text_sections + rodata_sections + data_sections + other_sections
        if is_verbose():
            print("Sorted sections: " + ", ".join(filter(lambda x: x, section_str)))

    def remove_rodata(self):
        """Remove .rodata sections by merging them into the previous/next .text section."""
        new_sections = []
        previous_text_section = None
        rodata_section = None
        for ii in self.__sections:
            if "text" == ii.get_name():
                previous_text_section = ii
                new_sections += [ii]
            elif "rodata" == ii.get_name():
                if previous_text_section:
                    previous_text_section.merge_content(ii)
                else:
                    if rodata_section:
                        rodata_section.merge_content(ii)
                    else:
                        rodata_section = ii
            else:
                new_sections += [ii]
        # .rodata sections defined before any .text sections will be merged into the first section.
        if rodata_section:
            rodata_section.merge_content(new_sections[0])
            new_sections[0].replace_content(rodata_section)
        self.__sections = new_sections

    def write(self, op, assembler, section_names=None):
        """Write an output assembler file or append to an existing file."""
        output = self.generate_file_output(section_names)
        if not output:
            return False
        if isinstance(op, str):
            fd = open(op, "w")
            fd.write(output)
            fd.close()
            if is_verbose():
                print("Wrote assembler source: '%s'" % (op))
        else:
            prefix = assembler.format_block_comment("sections '%s'" % (str(section_names)))
            op.write(prefix)
            op.write(output)
        return True

    def __str__(self):
        """String representation."""
        return "AssemblerFile('%s')" % (self.__filename)
