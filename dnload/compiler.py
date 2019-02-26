import os

from dnload.common import is_listing
from dnload.common import is_verbose
from dnload.common import run_command
from dnload.linker import Linker
from dnload.platform_var import PlatformVar

########################################
# Compiler #############################
########################################

class Compiler(Linker):
    """Compiler used to process C source."""

    def __init__(self, op):
        """Constructor."""
        Linker.__init__(self, op)
        self.__compiler_flags = []
        self.__compiler_flags_generate_asm = []
        self._compiler_flags_extra = []
        self._definitions = []
        self._include_directories = []
        self.generate_standard()

    def add_extra_compiler_flags(self, op):
        """Add extra compiler flags."""
        if is_listing(op):
            for ii in op:
                self.add_extra_compiler_flags(ii)
            return
        if not (op in self._compiler_flags_extra):
            if (not (op in self._include_directories)) and (not (op in self._definitions)):
                self._compiler_flags_extra += [op]

    def compile_asm(self, src, dst, whole_program=False):
        """Compile a file into assembler source."""
        cmd = [self.get_command(), "-S", src, "-o", dst] + self.__standard + self.__compiler_flags + self._compiler_flags_extra + self._definitions + self._include_directories
        if whole_program:
            cmd += self.__compiler_flags_generate_asm
        (so, se) = run_command(cmd)
        if 0 < len(se) and is_verbose():
            print(se)

    def compile_and_link(self, src, dst):
        """Compile and link a file directly."""
        cmd = [self.get_command(), src, "-o", dst] + self.__standard + self.__compiler_flags + self._compiler_flags_extra + self._definitions + self._include_directories + self.get_linker_flags() + self.get_library_directory_list() + self.get_library_list()
        (so, se) = run_command(cmd)
        if 0 < len(se) and is_verbose():
            print(se)

    def generate_compiler_flags(self):
        """Generate compiler flags."""
        self.__compiler_flags = []
        # clang and gcc have some flags in common.
        common_clang_gcc = ["-Os", "-ffast-math", "-fno-asynchronous-unwind-tables", "-fno-exceptions", "-fno-rtti", "-fno-threadsafe-statics", "-fomit-frame-pointer", "-funsafe-math-optimizations", "-fvisibility=hidden", "-march=%s" % (str(PlatformVar("march"))), "-Wall"]
        # Select flags based on compiler.
        if self.is_gcc():
            self.__compiler_flags += common_clang_gcc + ["-fno-enforce-eh-specs", "-fno-implicit-templates", "-fno-stack-protector", "-fno-use-cxa-atexit", "-fno-use-cxa-get-exception-ptr", "-fnothrow-opt"]
            self.__compiler_flags_generate_asm += ["-fno-pic", "-fwhole-program"]
            # Some flags are platform-specific.
            stack_boundary = int(PlatformVar("mpreferred-stack-boundary"))
            if 0 < stack_boundary:
                self.__compiler_flags += ["-mpreferred-stack-boundary=%i" % (stack_boundary)]
        elif self.is_clang():
            self.__compiler_flags += common_clang_gcc
        else:
            raise RuntimeError("compilation not supported with compiler '%s'" % (self.get_command_basename()))

    def generate_standard(self):
        """Generate C++ standard string."""
        if self.command_basename_startswith("g++") or self.command_basename_startswith("gcc"):
            # TODO: For older g++ versions: -std=gnu11 ?
            self.__standard = ["-std=c++11"]
        elif self.command_basename_startswith("clang"):
            self.__standard = ["-std=c++11"]
        else:
            self.__standard = []

    def set_definitions(self, lst):
        """Set definitions."""
        prefix = "-D"
        self._definitions = []
        if self.command_basename_startswith("cl."):
            prefix = "/D"
            self._definitions += [prefix + "WIN32"]
        if isinstance(lst, (list, tuple)):
            for ii in lst:
                self._definitions += [prefix + ii]
        else:
            self._definitions += [prefix + lst]

    def set_include_dirs(self, lst):
        """Set include directory listing."""
        prefix = "-I"
        if self.command_basename_startswith("cl."):
            prefix = "/I"
        self._include_directories = []
        for ii in lst:
            if os.path.isdir(ii):
                new_include_directory = prefix + ii
                if new_include_directory in self._compiler_flags_extra:
                    self._compiler_flags_extra.remove(new_include_directory)
                self._include_directories += [new_include_directory]
