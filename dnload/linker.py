import os
import re

from dnload.common import file_is_ascii_text
from dnload.common import is_listing
from dnload.common import is_verbose
from dnload.common import listify
from dnload.common import locate
from dnload.common import run_command
from dnload.platform_var import PlatformVar

########################################
# Linker ###############################
########################################

class Linker:
    """Linker used to link object files."""

    def __init__(self, op):
        """Constructor."""
        self.__command = op
        self.__command_basename = os.path.basename(self.__command)
        self.__library_directories = []
        self.__libraries = []
        self.__linker_flags = []
        self.__linker_flags_extra = []
        self.__linker_script = []
        self.__rpath_directories = []

    def addExtraFlags(self, op):
        """Add extra flags to use when linking."""
        if is_listing(op):
            for ii in op:
                self.addExtraFlags(ii)
            return
        if not (op in self.__linker_flags_extra):
            self.__linker_flags_extra += [op]

    def command_basename_startswith(self, op):
        """Check if command basename starts with given string."""
        return self.__command_basename.startswith(op)

    def generate_linker_flags(self):
        """Generate linker command for given mode."""
        self.__linker_flags = []
        if self.__command_basename.startswith("g++") or self.__command_basename.startswith("gcc"):
            self.__linker_flags += ["-nostartfiles", "-nostdlib", "-Xlinker", "--strip-all"]
        elif self.__command_basename.startswith("clang"):
            self.__linker_flags += ["-nostdlib", "-Xlinker", "--strip-all"]
        elif self.__command_basename.startswith("ld"):
            dynamic_linker = str(PlatformVar("interp"))
            if dynamic_linker.startswith("\"") and dynamic_linker.endswith("\""):
                dynamic_linker = dynamic_linker[1:-1]
            else:
                raise RuntimeError("dynamic liner definition '%s' should be quoeted" % (dynamic_linker))
            self.__linker_flags += ["-nostdlib", "--strip-all", "--dynamic-linker=%s" % (dynamic_linker)]
        else:
            raise RuntimeError("compilation not supported with compiler '%s'" % (op))

    def get_command(self):
        """Accessor."""
        return self.__command

    def get_library_list(self):
        """Generate link library list libraries."""
        ret = []
        prefix = "-l"
        if self.__command_basename.startswith("cl."):
            prefix = "/l"
        for ii in self.__libraries:
            ret += [prefix + ii]
        return ret

    def get_library_directory_list(self):
        """Set link directory listing."""
        ret = []
        prefix = "-L"
        rpath_prefix = ["-Xlinker"]
        if self.__command_basename.startswith("cl."):
            prefix = "/L"
        for ii in self.__library_directories:
            ret += [prefix + ii]
        if self.__command_basename.startswith("ld"):
            ret += ["-rpath-link", ":".join(self.__library_directories)]
            rpath_prefix = []
        for ii in self.__rpath_directories:
            ret += rpath_prefix + ["-rpath=%s" % (ii)]
        return ret

    def get_library_name(self, op):
        """Get actual name of library."""
        if op.startswith("/"):
            return op
        # Check if the library is specified verbatim. If yes, no need to expand.
        if re.match(r'lib.+\.so(\..*)?', op):
            return op
        libname = "lib%s.so" % (op)
        # Search in library directories only.
        for ii in self.__library_directories:
            current_libname = locate(ii, libname)
            if not current_libname:
                continue
            # Check if the supposed shared library is a linker script.
            if file_is_ascii_text(current_libname):
                fd = open(current_libname, "r")
                contents = fd.read()
                match = re.search(r'GROUP\s*\(\s*(\S+)\s+', contents, re.MULTILINE)
                fd.close()
                if match:
                    return os.path.basename(match.group(1))
                match = re.search(r'INPUT\(\s*(\S+)(\s*-l(\S+))?\)', contents, re.MULTILINE)
                if match:
                    ret = os.path.basename(match.group(1))
                    # if match.group(2):
                    #     return [ret, "lib%s.so" % (match.group(3))]
                    return ret
            # Stop at first match.
            break
        return libname

    def get_linker_flags(self):
        """Accessor."""
        return self.__linker_flags

    def generate_linker_script(self, dst, modify_start=False):
        """Get linker script from linker, improve it, write improved linker script to given file."""
        (so, se) = run_command([self.__command, "--verbose"] + self.__linker_flags_extra)
        if 0 < len(se) and is_verbose():
            print(se)
        # Linker script is the block of code between lines of multiple '=':s.
        match = re.match(r'.*\n=+\s*\n(.*)\n=+\s*\n.*', so, re.DOTALL)
        if not match:
            raise RuntimeError("could not extract script from linker output")
        ld_script = match.group(1)
        # Remove unwanted symbol definitions one at a time.
        unwanted_symbols = ["__bss_end__", "__bss_start__", "__end__", "__bss_start", "_bss_end__", "_edata", "_end"]
        for ii in unwanted_symbols:
            ld_script = re.sub(r'\n([ \f\r\t\v]+)(%s)(\s*=[^\n]+)\n' % (ii), r'\n\1/*\2\3*/\n', ld_script, re.MULTILINE)
        ld_script = re.sub(r'SEGMENT_START\s*\(\s*(\S+)\s*,\s*\d*x?\d+\s*\)', r'SEGMENT_START(\1, %s)' % (str(PlatformVar("entry"))), ld_script, re.MULTILINE)
        if modify_start:
            ld_script = re.sub(r'(SEGMENT_START.*\S)\s*\+\s*SIZEOF_HEADERS\s*;', r'\1;', ld_script, re.MULTILINE)
        fd = open(dst, "w")
        fd.write(ld_script)
        fd.close()
        if is_verbose():
            print("Wrote linker script '%s'." % (dst))
        return ld_script

    def link(self, src, dst, extra_args=[]):
        """Link a file."""
        cmd = [self.__command, src, "-o", dst] + self.__linker_flags + self.get_library_directory_list() + self.get_library_list() + extra_args + self.__linker_script + self.__linker_flags_extra
        (so, se) = run_command(cmd)
        if 0 < len(se) and is_verbose():
            print(se)
        return so

    def link_binary(self, src, dst):
        """Link a binary file with no bells and whistles."""
        cmd = [self.__command, "--entry=" + str(PlatformVar("entry"))] + listify(src) + ["-o", dst] + self.__linker_script + self.__linker_flags_extra
        (so, se) = run_command(cmd)
        if 0 < len(se) and is_verbose():
            print(se)
        return so

    def set_libraries(self, lst):
        """Set libraries to link."""
        self.__libraries = lst

    def set_library_directories(self, lst):
        self.__library_directories = []
        for ii in lst:
            if os.path.isdir(ii):
                self.__library_directories += [ii]

    def set_linker_script(self, op):
        """Use given linker script."""
        self.__linker_script = ["-T", op]

    def set_rpath_directories(self, lst):
        """Set rpath option."""
        self.__rpath_directories = []
        for ii in lst:
            self.__rpath_directories += [ii]
