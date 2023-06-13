import re
import os

from dnload.common import generate_temporary_filename
from dnload.common import is_verbose
from dnload.common import variablize
from dnload.glsl_block import GlslBlock
from dnload.glsl_block_preprocessor import glsl_parse_preprocessor
from dnload.glsl_block_inout import is_glsl_block_inout_typed
from dnload.glsl_block_uniform import is_glsl_block_uniform
from dnload.glsl_parse import glsl_parse
from dnload.glsl_source_precision import GlslSourcePrecision
from dnload.template import Template

########################################
# Globals ##############################
########################################

g_template_glsl_header = Template("""#ifndef __[[VARIABLE_NAME]]_header__
#define __[[VARIABLE_NAME]]_header__
static const char *[[VARIABLE_NAME]] = \"\"
#if defined([[DEFINITION_LD]])
\"[[FILE_NAME]]\"
#else
[[SOURCE]]
#endif
\"\";[[UNUSED]][[RENAMES]]
#endif
""")

g_template_glsl_print = Template("""#ifndef __[[VARIABLE_NAME]]_header__
#define __[[VARIABLE_NAME]]_header__
static const char* [[VARIABLE_NAME]] = \"\"
[[SOURCE]]
\"\";[[UNUSED]][[RENAMES]]
#endif
""")

g_rename_unused = """
#if !defined(DNLOAD_RENAME_UNUSED)
#if defined(__GNUC__)
#define DNLOAD_RENAME_UNUSED __attribute__((unused))
#else
#define DNLOAD_RENAME_UNUSED
#endif
#endif"""

g_template_glsl_rename_header = Template("""
static const char* [[SOURCE_NAME]]_[[TYPE_NAME]]_[[VARIABLE_NAME]] DNLOAD_RENAME_UNUSED = \"\"
#if defined([[DEFINITION_LD]])
\"[[VARIABLE_NAME]]\"
#else
\"[[RENAME]]\"
#endif
\"\";""")

g_template_glsl_rename_print = Template("""
static const char* [[SOURCE_NAME]]_[[TYPE_NAME]]_[[VARIABLE_NAME]] DNLOAD_RENAME_UNUSED = \"[[RENAME]]\";""")

########################################
# GlslBlockSource ######################
########################################

class GlslBlockSource(GlslBlock):
    """GLSL source file abstraction."""

    def __init__(self, definition_ld, filename, output_name=None, varname=None):
        """Constructor."""
        GlslBlock.__init__(self)
        self.__definition_ld = definition_ld
        self.__filename = filename
        self.__basename = os.path.basename(filename)
        self.__output_name = output_name
        self.__variable_name = varname
        self.__content = ""
        # Determine remaining fields from the former.
        self.detectType()

    def detectType(self):
        """Try to detect chain name and type from filename."""
        (self.__chain, self.__type) = detect_shader_type(self.__basename)
        self.__precisions = GlslSourcePrecision(self.__type)
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
        source = self.format(True)
        source = "\n".join(map(lambda x: "\"%s\"" % (x), glsl_to_cstr_readable(source)))
        renames = self.generateRenames(True)
        subst = {"DEFINITION_LD": self.__definition_ld, "FILE_NAME": self.__basename, "SOURCE": source, "VARIABLE_NAME": self.getVariableName(), "RENAMES": renames, "UNUSED": g_rename_unused}
        return g_template_glsl_header.format(subst)

    def generatePrintOutput(self, plain=False):
        """Generate output to be written to output."""
        # Just the shader as-is.
        if plain:
            return self.format(True)
        # Header-like output.
        source = self.format(True)
        source = "\n".join(map(lambda x: "\"%s\"" % (x), glsl_to_cstr_readable(source)))
        renames = self.generateRenames(False)
        subst = {"SOURCE": source, "VARIABLE_NAME": self.getVariableName(), "RENAMES": renames, "UNUSED": g_rename_unused}
        return g_template_glsl_print.format(subst)

    def generateRename(self, type_name, name, rename, header_mode):
        """Generates a single rename string."""
        subst = {"DEFINITION_LD": self.__definition_ld, "SOURCE_NAME": self.getVariableName(), "TYPE_NAME": type_name, "VARIABLE_NAME": name, "RENAME": rename}
        if header_mode:
            return g_template_glsl_rename_header.format(subst)
        return g_template_glsl_rename_print.format(subst)

    def generateRenames(self, header_mode):
        """Generate rename strings."""
        ret = ""
        for ii in self.getChildren():
            if is_glsl_block_inout_typed(ii):
                if (self.getType() == "vertex") and (not ii.getLayout()) and (ii.getInout().isAlwaysInput()):
                    name = ii.getName()
                    ret += self.generateRename("attribute", name.getName(), name.resolveName(), header_mode)
            elif is_glsl_block_uniform(ii):
                if not ii.getLayout():
                    name = ii.getName()
                    ret += self.generateRename("uniform", name.getName(), name.resolveName(), header_mode)
        return ret

    def getBlob(self):
        """Gets source contents as binary blob."""
        source = self.format(True)
        return glsl_to_blob(source)

    def getChainName(self):
        """Accessor."""
        return self.__chain

    def getFilename(self):
        """Accessor."""
        return self.__filename

    def getPrecisions(self):
        """Accessor."""
        return self.__precisions

    def getVariableName(self):
        """Gets the variable name for this GLSL source file."""
        if self.__variable_name:
            return self.__variable_name
        return variablize(self.__basename)

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
        content = fd.read()
        fd.close()
        # Check if first line indicates a variable, if yes, use it.
        match = re.match(r'^\s*(\/\/|\/\*)\s*#\s*([^\*\/\s]+)', content, re.I | re.M)
        if match:
            if self.__variable_name:
                raise RuntimeError("variable name redefinition '%s' vs. '%s' on GLSL source '%s'" % (match.group(2), self.__variable_name, self.getFilename()))
            self.__variable_name = match.group(2)
        # Preprocess actual content.
        self.preprocess(preprocessor, content)

    def write(self):
        """Write compressed output."""
        fd = open(self.__output_name, "w")
        if not fd:
            raise RuntimeError("could not write GLSL header '%s'" % (self.__output_name))
        fd.write(self.generateHeaderOutput())
        fd.close()
        if is_verbose():
            print("Wrote GLSL header: '%s' => '%s'" % (self.getVariableName(), self.__output_name))

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
        return "Source('%s' => '%s')" % (self.__output_name, self.getVariableName())

########################################
# Functions ############################
########################################

def detect_shader_type(op):
    """Detect shader type from filename, if possible."""
    # Try explicit naming by filename ending.
    match = re.match(r'(.*)\.([^\.]+)$', op, re.I)
    if match:
        shader_type = get_shader_type(match.group(2))
        if shader_type:
            return (variablize(match.group(1)), shader_type)
    # Try chain.type.glsl -order.
    match = re.match(r'(.*)[._\-\s](\S+)[._\-\s].*$', op, re.I)
    if match:
        shader_type = get_shader_type(match.group(2))
        if shader_type:
            return (variablize(match.group(1)), shader_type)
    # Try just type and assume default chain name.
    match = re.match(r'^(\S+)[._\-\s].*$', op, re.I)
    if match:
        shader_type = get_shader_type(match.group(1))
        if shader_type:
            return ("default", shader_type)
    # Could not determine anything -> generic header shader.
    return (None, None)

def glsl_to_blob(op):
    """Make GLSL source string into a binary blob."""
    return op.encode("utf-8")

def glsl_to_cstr_readable(op):
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

def glsl_read_source(preprocessor, definition_ld, filename, output_name, varname):
    """Read source into a GLSL source construct."""
    ret = GlslBlockSource(definition_ld, filename, output_name, varname)
    ret.read(preprocessor)
    return ret

def get_shader_type(op):
    """Gets shader type from given string."""
    shader_type = op.lower()
    if shader_type in ("frag", "fragment"):
        return "fragment"
    elif shader_type in ("geom", "geometry"):
        return "geometry"
    elif shader_type in ("vert", "vertex"):
        return "vertex"
    # No type could be detected.
    return None

def is_glsl_block_source(op):
    """Tell if given object is a GLSL source block."""
    return isinstance(op, GlslBlockSource)

def assert_glsl_block_source(op):
    """Asserts that given object is a GLSL source block."""
    if not is_glsl_block_source(op):
        raise RuntimeError("%s is not of type GlslBlockSource" % (str(op)))
