from dnload.glsl_block import GlslBlock

########################################
# GlslBlockDefault #####################
########################################


class GlslBlockDefault(GlslBlock):
    """Default 'fallback' GLSL block."""

    def __init__(self, content):
        """Constructor."""
        GlslBlock.__init__(self)
        self.__content = content

    def format(self, force):
        """Return formatted output."""
        ret = []
        for ii in self.__content:
            if isinstance(ii, str):
                ret += [ii]
            else:
                ret += [ii.format()]
        return " ".join(ret)

    def __str__(self):
        """String representation."""
        return "Default(%i)" % (len(self.__content))

########################################
# Functions ############################
########################################


def glsl_parse_default(source):
    """Parse default block, will be output as-is, should never happen."""
    print("WARNING: returning default GLSL block: '%s'" % (str(list(map(str, source)))))
    return [GlslBlockDefault(source)]
