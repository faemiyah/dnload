########################################
# Globals ##############################
########################################

ELFLING_OUTPUT = "elfling_output"
ELFLING_PADDING = 10
ELFLING_WORK = "elfling_modelCounters"
ELFLING_UNCOMPRESSED = "_uncompressed"

########################################
# Elfling ##############################
########################################

g_template_elfling_source = """#include "elfling_unpack.hpp"
%s\n
/** Working memory area. */
extern uint8_t %s[];\n
/** Compression output area. */
extern uint8_t %s[];\n
#if defined(__cplusplus)
extern "C" {
#endif\n
/** Jump point after decompression. */
extern void %s();\n
#if defined(__cplusplus)
}
#endif
"""

g_template_elfling_main = """
void _start()
{
  elfling_unpack(elfling_weights, elfling_contexts, %i, %s, elfling_input + %i, %s, %i);
  %s();
}\n
"""

class Elfling:
    """Usage class for the elfling packer program from minas/calodox."""

    def __init__(self, op):
        """Constructor."""
        self.__command = op
        self.__contexts = [0]
        self.__data = [0] * (10 + 4)
        self.__weights = [0]
        self.__uncompressed_size = 12345678

    def compress(self, src, dst):
        """Compress given file, starting from entry point and ending at file end."""
        info = readelf_get_info(src)
        starting_size = os.path.getsize(src)
        if starting_size != info["size"]:
            raise RuntimeError("size of file '%s' differs from header claim: %i != %i" %
                               (src, starting_size, info["size"]))
        rfd = open(src, "rb")
        wfd = open(dst, "wb")
        data = rfd.read(starting_size)
        wfd.write(data[info["entry"]:])
        rfd.close()
        wfd.close()
        self.__uncompressed_size = len(data) - info["entry"]
        if is_verbose():
            print("Wrote compressable program block '%s': %i bytes" % (dst, self.__uncompressed_size))
        self.__contexts = []
        self.__weights = []
        (so, se) = run_command([self.__command, dst])
        lines = so.split("\n")
        for ii in lines:
            terms = ii.split()
            if terms and terms[0].startswith("Final"):
                compressed_size = int(terms[1])
                for jj in terms[2:]:
                    individual_term = jj.split("*")
                    self.__weights += [int(individual_term[0], 10)]
                    self.__contexts += [int(individual_term[1], 16)]
        if is_verbose():
            print("Program block compressed into '%s': %i bytes" % (dst + ".pack", compressed_size))
            print("Compression weights: %s" % (str(self.__weights)))
            print("Compression contexts: %s" % (str(self.__contexts)))
        rfd = open(dst + ".pack", "rb")
        compressed_contexts = []
        compressed_weights = []
        uncompressed_size = rfd.read(4)
        uncompressed_size = (struct.unpack("I", uncompressed_size))[0]
        if uncompressed_size != self.__uncompressed_size:
            raise RuntimeError("size given to packer does not match size information in file: %i != %i" %
                               (self.__uncompressed_size, uncompressed_size))
        context_count = rfd.read(1)
        context_count = (struct.unpack("B", context_count))[0]
        for ii in range(context_count):
            compressed_weights += struct.unpack("B", rfd.read(1))
        for ii in range(context_count):
            compressed_contexts += struct.unpack("B", rfd.read(1))
        if compressed_contexts != self.__contexts:
            raise RuntimeError("contexts reported by packer do not match context information in file: %s != %s" %
                               (str(self.__contexts), str(compressed_contexts)))
        if compressed_weights != self.__weights:
            raise RuntimeError("weights reported by packer do not match weight information in file: %s != %s" %
                               (str(self.__weights), str(compressed_weights)))
        read_data = rfd.read()
        rfd.close()
        if len(read_data) != compressed_size:
            raise RuntimeError("size reported by packer does not match length of file: %i != %i" %
                               (compressed_size, len(read_data)))
        self.__data = []
        for ii in read_data:
            self.__data += struct.unpack("B", ii)

    def generate_c_data_block(self):
        """Generate direct C code for data block."""
        ret = "static const uint8_t elfling_weights[] =\n{\n  "
        for ii in range(len(self.__weights)):
            if 0 < ii:
                ret += ", "
            ret += "%i" % (self.__weights[ii])
        ret += "\n};\n\nstatic const uint8_t elfling_contexts[] =\n{\n  "
        for ii in range(len(self.__contexts)):
            if 0 < ii:
                ret += ", "
            ret += "%i" % (self.__contexts[ii])
        ret += "\n};\n\nstatic const uint8_t elfling_input[] =\n{\n  "
        for ii in range(ELFLING_PADDING):
            if 0 < ii:
                ret += ", "
            ret += "0"
        for ii in self.__data:
            ret += ", %i" % (ii)
        return ret + "\n};"

    def generate_c_source(self, definition):
        """Generate the C uncompressor source."""
        ret = g_template_elfling_source % (self.generate_c_data_block(), ELFLING_WORK, ELFLING_OUTPUT, ELFLING_UNCOMPRESSED)
        ret += g_template_entry_point % (definition)
        ret += g_template_elfling_main % (len(self.__contexts), ELFLING_WORK, self.get_input_offset(), ELFLING_OUTPUT, self.get_uncompressed_size(), ELFLING_UNCOMPRESSED)
        return ret

    def get_contexts(self):
        """Get contexts. Contains dummy data until compression has been ran."""
        return self.__contexts

    def get_input_offset(self):
        """Get the input offset for compressed data."""
        return ELFLING_PADDING + len(self.__data) - 4

    def get_uncompressed_size(self):
        """Get uncompressed size. Contains dummy value until compression has been ran."""
        return self.__uncompressed_size

    def get_weights(self):
        """Get weights. Contains dummy data until compression has been ran."""
        return self.__weights

    def get_work_size(self):
        """Return the working area size required for decompression."""
        # TODO: Extract this value from the source.
        return (4 << 20) * 16

    def has_data(self):
        """Tell if compression has been done."""
        return ([0] != self.__contexts) and ([0] != self.__weights)

    def write_c_source(self, dst, definition):
        """Write elfling uncompressor source into given location."""
        wfd = open(dst, "wt")
        wfd.write(self.generate_c_source(definition))
        wfd.close()
