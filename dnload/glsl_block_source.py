import re
import os

from dnload.common import generate_temporary_filename
from dnload.common import is_verbose
from dnload.glsl_block import GlslBlock
from dnload.glsl_block_preprocessor import glsl_parse_preprocessor
from dnload.glsl_parse import glsl_parse
from dnload.template import Template

########################################
# Globals ##############################
########################################

g_template_glsl_header = Template("""static const char *[[VARIABLE_NAME]] = \"\"
#if defined([[DEFINITION_LD]])
\"[[FILE_NAME]]\"
#else
[[SOURCE]]
#endif
\"\";
""")

g_template_glsl_print = Template("""#ifndef __[[VARIABLE_NAME]]_header__
#define __[[VARIABLE_NAME]]_header__
static const char *[[VARIABLE_NAME]] = \"\"
[[SOURCE]]
\"\";
#endif
""")

########################################
# GlslBlockSource ######################
########################################

class GlslBlockSource(GlslBlock):
    """GLSL source file abstraction."""

    def __init__(self, definition_ld, filename, varname, output_name=None):
        """Constructor."""
        GlslBlock.__init__(self)
        self.__definition_ld = definition_ld
        self.__filename = filename
        self.__variable_name = varname
        self.__output_name = output_name
        self.__content = ""
        self.detectType()

    def detectType(self):
        """Try to detect chain name and type from filename."""
        self.__chain = None
        self.__type = None
        match = re.match(r'(.*)[._\-\s](\S+)[._\-\s].*', self.__filename, re.I)
        if match:
            self.__chain = extract_chain_name(match.group(1))
            shader_type = match.group(2).lower()
            if shader_type in ("frag", "fragment"):
                self.__type = "fragment"
            elif shader_type in ("geom", "geometry"):
                self.__type = "geometry"
            elif shader_type in ("vert", "vertex"):
                self.__type = "vertex"
        if is_verbose():
            output_message = "Shader file '%s' type" % (self.__filename)
            if self.__type:
                print(output_message + (": '%s'" % (self.__type)))
            else:
                print(output_message + " not detected, assuming generic.")

    def format(self, force):
        """Return formatted output."""
        return "".join(map(lambda x: x.format(force), self._children))

    def generateHeaderOutput(self):
        """Generate output to be written into a file."""
        ret = self.format(True)
        ret = "\n".join(map(lambda x: "\"%s\"" % (x), glsl_cstr_readable(ret)))
        subst = {"DEFINITION_LD": self.__definition_ld, "FILE_NAME": os.path.basename(self.__filename), "SOURCE": ret, "VARIABLE_NAME": self.__variable_name}
        return g_template_glsl_header.format(subst)

    def generatePrintOutput(self):
        """Generate output to be written to output."""
        ret = self.format(True)
        ret = "\n".join(map(lambda x: "\"%s\"" % (x), glsl_cstr_readable(ret)))
        subst = {"SOURCE": ret, "VARIABLE_NAME": self.__variable_name}
        return g_template_glsl_print.format(subst)

    def getChainName(self):
        """Accessor."""
        return self.__chain

    def getFilename(self):
        """Accessor."""
        return self.__filename

    def getType(self):
        """Access type of this shader file. May be empty."""
        return self.__type

    def hasOutputName(self):
        """Tells if output name has been set."""
        return not (self.__output_name is None)

    def isCommonChainName(self):
        """Checks if the chain name for this source is for a common chain."""
        chain_name = self.getChainName()
        source_type = self.getType()
        # If there's no chain name, it's common by default.
        if not chain_name:
            if source_type:
                raise RuntimeError("GLSL source block has no chain name but has type '%s'" % (source_type))
            return True
        # Chain name exists -> test against common names.
        if not source_type:
            raise RuntimeError("GLSL source block has a chain name '%s' but no type" % (chain_name))
        return chain_name.lower() in ("all", "common", "default")

    def parse(self):
        """Parse code into blocks and statements."""
        array = glsl_parse(self.__content)
        # Hierarchy.
        self.addChildren(array)

    def preprocess(self, preprocessor, source):
        """Preprocess GLSL source, store preprocessor directives into parse tree and content."""
        content = []
        for ii in source.splitlines():
            block = glsl_parse_preprocessor(ii)
            if block:
                self.addChildren(block)
            else:
                content += [ii]
        # Removed known preprocessor directives, write result into intermediate file.
        fname = generate_temporary_filename(self.__filename + ".preprocessed")
        fd = open(fname, "w")
        fd.write(("\n".join(content)).strip())
        fd.close()
        # Preprocess and reassemble content.
        intermediate = preprocessor.preprocess(fname)
        content = []
        for ii in intermediate.splitlines():
            if not ii.strip().startswith("#"):
                content += [ii]
        self.__content = "\n".join(content)

    def read(self, preprocessor):
        """Read file contents."""
        fd = open(self.__filename, "r")
        if not fd:
            raise RuntimeError("could not read GLSL source '%s'" % (fname))
        self.preprocess(preprocessor, fd.read())
        fd.close()

    def write(self):
        """Write compressed output."""
        fd = open(self.__output_name, "w")
        if not fd:
            raise RuntimeError("could not write GLSL header '%s'" % (self.__output_name))
        fd.write(self.generateHeaderOutput())
        fd.close()
        if is_verbose():
            print("Wrote GLSL header: '%s' => '%s'" % (self.__variable_name, self.__output_name))

    def __lt__(lhs, rhs):
        """Comparison operator."""
        lhs_type = lhs.getType()
        rhs_type = rhs.getType()
        if (not lhs_type) and rhs_type:
            return True
        elif lhs_type and (not rhs_type):
            return False
        lhs_common = lhs.isCommonChainName()
        rhs_common = rhs.isCommonChainName()
        if lhs_common and (not rhs_common):
            return True
        elif (not lhs_common) and rhs_common:
            return False
        return glsl_file_type_value(lhs.getType()) < glsl_file_type_value(rhs.getType())

    def __str__(self):
        return "Source('%s' => '%s')" % (self.__output_name, self.__variable_name)

########################################
# Functions ############################
########################################

def extract_chain_name(op):
    """Extracts chain name from given filename part."""
    return os.path.basename(op)

def glsl_cstr_readable(op):
    """Make GLSL source string into a 'readable' C string array."""
    line = ""
    ret = []
    for ii in op:
        if ";" == ii:
            ret += [line + ii]
            line = ""
            continue
        elif "\n" == ii:
            ret += [line + "\\n"]
            line = ""
            continue
        elif "{" == ii:
            if line:
                ret += [line]
            ret += ["{"]
            line = ""
            continue
        elif "}" == ii:
            if line:
                ret += [line]
            ret += ["}"]
            line = ""
            continue
        line += ii
    if line:
        ret += [line]
    return ret

def glsl_file_type_value(op):
    """Gets file type value for given file type."""
    if op == "vertex":
        return 0
    elif op == "geometry":
        return 1
    elif op == "fragment":
        return 2
    raise RuntimeError("unknown GLSL file type: %s" % (op))

def glsl_read_source(preprocessor, definition_ld, filename, varname, output_name):
    """Read source into a GLSL source construct."""
    ret = GlslBlockSource(definition_ld, filename, varname, output_name)
    ret.read(preprocessor)
    return ret

def is_glsl_block_source(op):
    """Tell if given object is a GLSL source block."""
    return isinstance(op, GlslBlockSource)

def assert_glsl_block_source(op):
    """Asserts that given object is a GLSL source block."""
    if not is_glsl_block_source(op):
        raise RuntimeError("%s is not of type GlslBlockSource" % (str(op)))
