import re

from dnload.glsl_block import GlslBlock
from dnload.platform_var import platform_is_gles

########################################
# GlslBlockPreprocessor ################
########################################

class GlslBlockPreprocessor(GlslBlock):
    """Preprocessor block."""

    def __init__(self, source):
        """Constructor."""
        GlslBlock.__init__(self)
        self.__content = source.strip().split()

    def format(self, force):
        """Return formatted output."""
        return "%s\n" % (" ".join(self.__content))

    def __str__(self):
        """String representation."""
        return "Preprocessor('%s')" % (self.format(False))

########################################
# GlslBlockVersion #####################
########################################

class GlslBlockVersion(GlslBlock):
    """Version block."""

    def __init__(self, source):
        """Constructor."""
        GlslBlock.__init__(self)
        match = g_re_version.match(source)
        if not match:
            raise RuntimeError("invalid version directive: %s" % (source))
        self.__version = int(match.group(1))
        self.__addennum = None
        if match.group(2):
            self.__addennum = match.group(2)

    def get_version_string(self, whitespace = " "):
        """Gets the version string."""
        (converted_version, converted_addennum) = glsl_version_to_platform_version(self.__version, self.__addennum)
        if converted_addennum:
            return "%i%s%s\n" % (converted_version, whitespace, converted_addennum)
        return "%i\n" % (converted_version)

    def format(self, force):
        """Return formatted output."""
        return "#version%s%s\n" % (" ", self.get_version_string())

    def __str__(self):
        """String representation."""
        return "PreprocessorVersion('%s')" % (self.format(False))

########################################
# Globals ##############################
########################################

g_directives = (
        "extension",
        "version",
        )

g_version_matching = (
        ((100, None), (120, None)),
        ((300, "es"), (330, None)),
        )

g_re_preprocessor = re.compile(r'^\s*#\s*(\S+)\s+(.*)$')
g_re_version = re.compile(r'^(\d+)\s*(\S)?$')

########################################
# Functions ############################
########################################

def glsl_version_to_platform_version(version, addennum):
    """Converts given version and addennum to current platform version and addennum."""
    for ii in g_version_matching:
        if platform_is_gles():
            if (ii[1][0] == version) and (ii[1][1] == addennum):
                return (ii[0][0], ii[0][1])
        else:
            if (ii[0][0] == version) and (ii[0][1] == addennum):
                return (ii[1][0], ii[1][1])
    # No match.
    return (version, addennum)

def glsl_parse_preprocessor(source):
    """Parse preprocessor line."""
    match = g_re_preprocessor.match(source)
    if match:
        preprocessor_type = match.group(1)
        if preprocessor_type in g_directives:
            if preprocessor_type == "version":
                return GlslBlockVersion(match.group(2))
            else:
                return GlslBlockPreprocessor(source)
    return None
