from dnload.assembler_variable import AssemblerVariable
from dnload.common import is_listing
from dnload.common import is_verbose
from dnload.common import labelify
from dnload.platform_var import osarch_is_32_bit
from dnload.platform_var import osarch_is_64_bit
from dnload.platform_var import PlatformVar

########################################
# AssemblerSegment #####################
########################################


class AssemblerSegment:
    """Segment is a collection of variables."""

    def __init__(self, op):
        """Constructor."""
        self.__name = None
        self.__desc = None
        self.__data = []
        if isinstance(op, str):
            self.__name = op
            self.__desc = None
        elif is_listing(op):
            for ii in op:
                if is_listing(ii):
                    self.add_data(ii)
                elif not self.__name:
                    self.__name = ii
                elif not self.__desc:
                    self.__desc = ii
                else:
                    raise RuntimeError("too many string arguments for list constructor")
        self.refresh_name_label()
        self.refresh_name_end_label()

    def add_data(self, op):
        """Add data into this segment."""
        self.__data += [AssemblerVariable(op)]
        self.refresh_name_label()
        self.refresh_name_end_label()

    def add_dt_hash(self, op):
        """Add hash dynamic structure."""
        d_tag = AssemblerVariable(("d_tag, DT_HASH = 4", PlatformVar("addr"), 4))
        d_un = AssemblerVariable(("d_un", PlatformVar("addr"), op))
        self.__data[0:0] = [d_tag, d_un]
        self.refresh_name_label()

    def add_dt_needed(self, op):
        """Add requirement to given library."""
        d_tag = AssemblerVariable(("d_tag, DT_NEEDED = 1", PlatformVar("addr"), 1))
        d_un = AssemblerVariable(("d_un, library name offset in strtab",
                                  PlatformVar("addr"), "strtab_%s - strtab" % labelify(op)))
        self.__data[0:0] = [d_tag, d_un]
        self.refresh_name_label()

    def add_dt_symtab(self, op):
        """Add symtab dynamic structure."""
        d_tag = AssemblerVariable(("d_tag, DT_SYMTAB = 6", PlatformVar("addr"), 6))
        d_un = AssemblerVariable(("d_un", PlatformVar("addr"), op))
        self.__data[0:0] = [d_tag, d_un]
        self.refresh_name_label()

    def add_hash(self, lst):
        """Generate a minimal DT_HASH based on symbol listing."""
        self.__data = []
        num = len(lst) + 1
        self.add_data(("", 4, 1))
        self.add_data(("", 4, num))
        self.add_data(("", 4, num - 1))
        self.add_data(("", 4, 0))
        if 1 < num:
            for ii in range(num - 1):
                self.add_data(("", 4, ii))

    def add_strtab(self, op):
        """Add a library name."""
        libname = AssemblerVariable(("symbol name string", 1, "\"%s\"" % op), labelify(op))
        terminator = AssemblerVariable(("string terminating zero", 1, 0))
        self.__data[1:1] = [libname, terminator]
        self.refresh_name_end_label()

    def add_symbol_empty(self):
        """Add an empty symbol."""
        if osarch_is_32_bit():
            self.add_data(("empty symbol", 4, (0, 0, 0, 0)))
        elif osarch_is_64_bit():
            self.add_data(("empty symbol", 4, (0, 0)))
            self.add_data(("empty symbol", PlatformVar("addr"), (0, 0)))
        else:
            raise_unknown_address_size()

    def add_symbol_und(self, name):
        """Add a symbol to satisfy UND from external source."""
        label_name = "symtab_" + name
        if osarch_is_32_bit():
            self.add_data(("st_name", 4, "strtab_%s - strtab" % (name)))
            self.add_data(("st_value", PlatformVar("addr"), label_name, label_name))
            self.add_data(("st_size", PlatformVar("addr"), PlatformVar("addr")))
            self.add_data(("st_info", 1, 17))
            self.add_data(("st_other", 1, 0))
            self.add_data(("st_shndx", 2, 1))
        elif osarch_is_64_bit():
            self.add_data(("st_name", 4, "strtab_%s - strtab" % (name)))
            self.add_data(("st_info", 1, 17))
            self.add_data(("st_other", 1, 0))
            self.add_data(("st_shndx", 2, 1))
            self.add_data(("st_value", PlatformVar("addr"), label_name, label_name))
            self.add_data(("st_size", PlatformVar("addr"), PlatformVar("addr")))
        else:
            raise_unknown_address_size()

    def clear_data(self):
        """Clear all data."""
        self.__data = []

    def deconstruct_head(self):
        """Deconstruct this segment (starting from head) into a byte stream."""
        ret = []
        for ii in range(len(self.__data)):
            op = self.__data[ii].deconstruct()
            if not op:
                return (ret, self.__data[ii:])
            ret += op
        return (ret, [])

    def deconstruct_tail(self):
        """Deconstruct this segment (starting from tail) into a byte stream."""
        ret = []
        for ii in range(len(self.__data)):
            op = self.__data[-ii - 1].deconstruct()
            if not op:
                return (self.__data[:len(self.__data) - ii], ret)
            ret = op + ret
        return ([], ret)

    def empty(self):
        """Tell if this segment is empty."""
        return 0 >= len(self.__data)

    def generate_source(self, op):
        """Generate assembler source."""
        ret = op.format_block_comment(self.__desc)
        for ii in self.__data:
            ret += ii.generate_source(op, 1, self.__name)
        return ret

    def merge(self, op):
        """Attempt to merge with given segment."""
        highest_mergable = 0
        (head_src, bytestream_src) = self.deconstruct_tail()
        (bytestream_dst, tail_dst) = op.deconstruct_head()
        for ii in range(min(len(bytestream_src), len(bytestream_dst))):
            mergable = True
            for jj in range(ii + 1):
                if not bytestream_src[-ii - 1 + jj].mergable(bytestream_dst[jj]):
                    mergable = False
                    break
            if mergable:
                highest_mergable = ii + 1
        if 0 >= highest_mergable:
            return False
        if is_verbose():
            print("Merging headers %s and %s at %i bytes." % (self.__name, op.__name, highest_mergable))
        for ii in range(highest_mergable):
            bytestream_src[-highest_mergable + ii].merge(bytestream_dst[ii])
        bytestream_dst[0:highest_mergable] = []
        self.reconstruct(head_src + bytestream_src)
        op.reconstruct(bytestream_dst + tail_dst)
        return True

    def reconstruct(self, bytestream):
        """Reconstruct data from bytestream."""
        self.__data = []
        while 0 < len(bytestream):
            front = bytestream[0]
            bytestream = bytestream[1:]
            constructed = front.reconstruct(bytestream)
            if constructed:
                bytestream[:constructed] = []
            self.__data += [front]

    def refresh_name_label(self):
        """Add name label to first assembler variable."""
        for ii in self.__data:
            ii.remove_label_pre(self.__name)
        if 0 < len(self.__data):
            self.__data[0].add_label_pre(self.__name)

    def refresh_name_end_label(self):
        """Add a name end label to last assembler variable."""
        end_label = "%s_end" % (self.__name)
        for ii in self.__data:
            ii.remove_label_post(end_label)
        if 0 < len(self.__data):
            self.__data[-1].add_label_post(end_label)

    def size(self):
        """Get cumulative size of data."""
        ret = 0
        for ii in self.__data:
            ret += int(ii.get_size())
        return ret

    def write(self, fd, assembler):
        """Write segment onto disk."""
        if 0 >= len(self.__data):
            raise RuntimeError("segment '%s' is empty" % self.__name)
        fd.write(self.generate_source(assembler))
