import argparse
import textwrap

from dnload.common import get_indent

########################################
# CustomHelpFormatter ##################
########################################

class CustomHelpFormatter(argparse.HelpFormatter):
    """Help formatter with necessary changes."""

    def _fill_text(self, text, width, indent):
        """Method override."""
        ret = []
        for ii in text.splitlines():
            ret += [textwrap.fill(ii, width, initial_indent=indent, subsequent_indent=indent)]
        return "\n\n".join(ret)

    def _split_lines(self, text, width):
        """Method override."""
        indent_len = len(get_indent(1))
        ret = []
        for ii in text.splitlines():
            indent = 0
            for jj in range(len(ii)):
                if not ii[jj].isspace():
                    indent = jj
                    break
            lines = textwrap.wrap(ii[indent:], width - jj * indent_len)
            for ii in range(len(lines)):
                lines[ii] = get_indent(indent) + lines[ii]
            ret += lines
        return ret
