import argparse
import copy
import os
import re
import shutil
import stat
import subprocess
import sys

from dnload.assembler import Assembler
from dnload.assembler_file import AssemblerFile
from dnload.assembler_segment import AssemblerSegment
from dnload.common import executable_find
from dnload.common import executable_search
from dnload.common import generate_temporary_filename
from dnload.common import get_indent
from dnload.common import is_listing
from dnload.common import is_verbose
from dnload.common import listify
from dnload.common import locate
from dnload.common import run_command
from dnload.common import set_temporary_directory
from dnload.common import set_verbose
from dnload.compiler import Compiler
from dnload.custom_help_formatter import CustomHelpFormatter
from dnload.glsl import Glsl
from dnload.library_definition import g_library_definitions
from dnload.linker import Linker
from dnload.platform_var import g_osarch
from dnload.platform_var import g_osname
from dnload.platform_var import g_osversion
from dnload.platform_var import osarch_is_aarch64
from dnload.platform_var import osarch_is_amd64
from dnload.platform_var import osarch_is_arm32l
from dnload.platform_var import osarch_is_32_bit
from dnload.platform_var import osarch_is_64_bit
from dnload.platform_var import osname_is_freebsd
from dnload.platform_var import osname_is_linux
from dnload.platform_var import PlatformVar
from dnload.platform_var import platform_map
from dnload.platform_var import replace_osarch
from dnload.platform_var import replace_osname
from dnload.platform_var import replace_platform_variable
from dnload.preprocessor import Preprocessor
from dnload.symbol import generate_loader_dlfcn
from dnload.symbol import generate_loader_hash
from dnload.symbol import generate_loader_vanilla
from dnload.symbol import generate_symbol_definitions_direct
from dnload.symbol import generate_symbol_definitions_table
from dnload.symbol import generate_symbol_table
from dnload.symbol_source_database import g_symbol_sources
from dnload.template import Template

########################################
# Globals ##############################
########################################

PATH_MALI = "/usr/lib/arm-linux-gnueabihf/mali-egl"
PATH_VIDEOCORE = "/opt/vc"

VERSION_REVISION = "r14"
VERSION_DATE = "20171017"

g_assembler_ehdr = (
    "ehdr",
    "Elf32_Ehdr or Elf64_Ehdr",
    ("e_ident[EI_MAG0], magic value 0x7F", 1, 0x7F),
    ("e_ident[EI_MAG1] to e_indent[EI_MAG3], magic value \"ELF\"", 1, "\"ELF\""),
    ("e_ident[EI_CLASS], ELFCLASS32 = 1, ELFCLASS64 = 2", 1, PlatformVar("ei_class")),
    ("e_ident[EI_DATA], ELFDATA2LSB = 1, ELFDATA2MSB = 2", 1, 1),
    ("e_ident[EI_VERSION], EV_CURRENT = 1", 1, 1),
    ("e_ident[EI_OSABI], ELFOSABI_SYSV = 0, ELFOSABI_LINUX = 3, ELFOSABI_FREEBSD = 9", 1, PlatformVar("ei_osabi")),
    ("e_ident[EI_ABIVERSION], always 0", 1, 0),
    ("e_indent[EI_MAG10 to EI_MAG15], unused", 1, (0, 0, 0, 0, 0, 0, 0)),
    ("e_type, ET_EXEC = 2", 2, 2),
    ("e_machine, EM_386 = 3, EM_ARM = 40, EM_X86_64 = 62, EM_AARCH64 = 183", 2, PlatformVar("e_machine")),
    ("e_version, EV_CURRENT = 1", 4, 1),
    ("e_entry, execution starting point", PlatformVar("addr"), PlatformVar("start")),
    ("e_phoff, offset from start to program headers", PlatformVar("addr"), "phdr_load - ehdr"),
    ("e_shoff, start of section headers", PlatformVar("addr"), 0),
    ("e_flags, unused", 4, PlatformVar("e_flags")),
    ("e_ehsize, Elf32_Ehdr size", 2, "ehdr_end - ehdr"),
    ("e_phentsize, Elf32_Phdr size", 2, "phdr_load_end - phdr_load"),
    ("e_phnum, Elf32_Phdr count, PT_LOAD, [PT_LOAD (bss)], PT_INTERP, PT_DYNAMIC", 2, PlatformVar("phdr_count")),
    ("e_shentsize, Elf32_Shdr size", 2, PlatformVar("e_shentsize")),  # Merges with load phdr.
    ("e_shnum, Elf32_Shdr count", 2, 0),
    ("e_shstrndx, index of section containing string table of section header names", 2, PlatformVar("e_shstrndx")),
)

g_assembler_phdr32_load_single = (
    "phdr_load",
    "Elf32_Phdr, PT_LOAD",
    ("p_type, PT_LOAD = 1", 4, 1),
    ("p_offset, offset of program start", PlatformVar("addr"), 0),
    ("p_vaddr, program virtual address", PlatformVar("addr"), PlatformVar("entry")),
    ("p_paddr, unused", PlatformVar("addr"), 0),
    ("p_filesz, program size on disk", PlatformVar("addr"), "end - ehdr"),
    ("p_memsz, program size in memory", PlatformVar("addr"), "bss_end - ehdr"),
    ("p_flags, rwx = 7", 4, 7),
    ("p_align, usually 0x1000", PlatformVar("addr"), PlatformVar("memory_page")),
    )

g_assembler_phdr32_load_double = (
    "phdr_load",
    "Elf32_Phdr, PT_LOAD",
    ("p_type, PT_LOAD = 1", 4, 1),
    ("p_offset, offset of program start", PlatformVar("addr"), 0),
    ("p_vaddr, program virtual address", PlatformVar("addr"), PlatformVar("entry")),
    ("p_paddr, unused", PlatformVar("addr"), 0),
    ("p_filesz, program size on disk", PlatformVar("addr"), "end - ehdr"),
    ("p_memsz, program headers size in memory", PlatformVar("addr"), "aligned_end - ehdr"),
    ("p_flags, rwx = 7", 4, 7),
    ("p_align, usually " + str(PlatformVar("memory_page")), PlatformVar("addr"), PlatformVar("memory_page")),
    )

g_assembler_phdr32_load_bss = (
    "phdr_load_bss",
    "Elf32_Phdr, PT_LOAD (.bss)",
    ("p_type, PT_LOAD = 1", 4, 1),
    ("p_offset, offset of fake .bss segment", PlatformVar("addr"), "bss_start - ehdr"),
    ("p_vaddr, program virtual address", PlatformVar("addr"), "bss_start"),
    ("p_paddr, unused", PlatformVar("addr"), 0),
    ("p_filesz, .bss size on disk", PlatformVar("addr"), 0),
    ("p_memsz, .bss size in memory", PlatformVar("addr"), "bss_end - bss_start"),
    ("p_flags, rw = 6", 4, 6),
    ("p_align, usually " + str(PlatformVar("memory_page")), PlatformVar("addr"), PlatformVar("memory_page")),
    )

g_assembler_phdr32_interp = (
    "phdr_interp",
    "Elf32_Phdr, PT_INTERP",
    ("p_type, PT_INTERP = 3", 4, 3),
    ("p_offset, offset of block", PlatformVar("addr"), "interp - ehdr"),
    ("p_vaddr, address of block", PlatformVar("addr"), "interp"),
    ("p_paddr, unused", PlatformVar("addr"), 0),
    ("p_filesz, block size on disk", PlatformVar("addr"), "interp_end - interp"),
    ("p_memsz, block size in memory", PlatformVar("addr"), "interp_end - interp"),
    ("p_flags, ignored", 4, 0),
    ("p_align, 1 for strtab", PlatformVar("addr"), 1),
    )

g_assembler_phdr32_dynamic = (
    "phdr_dynamic",
    "Elf32_Phdr, PT_DYNAMIC",
    ("p_type, PT_DYNAMIC = 2", 4, 2),
    ("p_offset, offset of block", PlatformVar("addr"), "dynamic - ehdr"),
    ("p_vaddr, address of block", PlatformVar("addr"), "dynamic"),
    ("p_paddr, unused", PlatformVar("addr"), 0),
    ("p_filesz, block size on disk", PlatformVar("addr"), "dynamic_end - dynamic"),
    ("p_memsz, block size in memory", PlatformVar("addr"), "dynamic_end - dynamic"),
    ("p_flags, ignored", 4, 21),  # Merges with DT_DEBUG in dynamic section.
    ("p_align", PlatformVar("addr"), 0),
    )

g_assembler_phdr64_load_single = (
    "phdr_load",
    "Elf64_Phdr, PT_LOAD",
    ("p_type, PT_LOAD = 1", 4, 1),
    ("p_flags, rwx = 7", 4, 7),
    ("p_offset, offset of program start", PlatformVar("addr"), 0),
    ("p_vaddr, program virtual address", PlatformVar("addr"), PlatformVar("entry")),
    ("p_paddr, unused", PlatformVar("addr"), 0),
    ("p_filesz, program size on disk", PlatformVar("addr"), "end - ehdr"),
    ("p_memsz, program size in memory", PlatformVar("addr"), "bss_end - ehdr"),
    ("p_align, usually " + str(PlatformVar("memory_page")), PlatformVar("addr"), PlatformVar("memory_page")),
    )

g_assembler_phdr64_load_double = (
    "phdr_load",
    "Elf64_Phdr, PT_LOAD",
    ("p_type, PT_LOAD = 1", 4, 1),
    ("p_flags, rwx = 7", 4, 7),
    ("p_offset, offset of program start", PlatformVar("addr"), 0),
    ("p_vaddr, program virtual address", PlatformVar("addr"), PlatformVar("entry")),
    ("p_paddr, unused", PlatformVar("addr"), 0),
    ("p_filesz, program size on disk", PlatformVar("addr"), "end - ehdr"),
    ("p_memsz, program headers size in memory", PlatformVar("addr"), "aligned_end - ehdr"),
    ("p_align, usually " + str(PlatformVar("memory_page")), PlatformVar("addr"), PlatformVar("memory_page")),
    )

g_assembler_phdr64_load_bss = (
    "phdr_load_bss",
    "Elf64_Phdr, PT_LOAD (.bss)",
    ("p_type, PT_LOAD = 1", 4, 1),
    ("p_flags, rw = 6", 4, 6),
    ("p_offset, offset of fake .bss segment", PlatformVar("addr"), "end - ehdr"),
    ("p_vaddr, program virtual address", PlatformVar("addr"), "bss_start"),
    ("p_paddr, unused", PlatformVar("addr"), 0),
    ("p_filesz, .bss size on disk", PlatformVar("addr"), 0),
    ("p_memsz, .bss size in memory", PlatformVar("addr"), "bss_end - end"),
    ("p_align, usually " + str(PlatformVar("memory_page")), PlatformVar("addr"), PlatformVar("memory_page")),
    )

g_assembler_phdr64_interp = (
    "phdr_interp",
    "Elf64_Phdr, PT_INTERP",
    ("p_type, PT_INTERP = 3", 4, 3),
    ("p_flags, ignored", 4, 0),
    ("p_offset, offset of block", PlatformVar("addr"), "interp - ehdr"),
    ("p_vaddr, address of block", PlatformVar("addr"), "interp"),
    ("p_paddr, unused", PlatformVar("addr"), 0),
    ("p_filesz, block size on disk", PlatformVar("addr"), "interp_end - interp"),
    ("p_memsz, block size in memory", PlatformVar("addr"), "interp_end - interp"),
    ("p_align, 1 for strtab", PlatformVar("addr"), 1),
    )

g_assembler_phdr64_dynamic = (
    "phdr_dynamic",
    "Elf64_Phdr, PT_DYNAMIC",
    ("p_type, PT_DYNAMIC = 2", 4, 2),
    ("p_flags, ignored", 4, 0),
    ("p_offset, offset of block", PlatformVar("addr"), "dynamic - ehdr"),
    ("p_vaddr, address of block", PlatformVar("addr"), "dynamic"),
    ("p_paddr, unused", PlatformVar("addr"), 0),
    ("p_filesz, block size on disk", PlatformVar("addr"), "dynamic_end - dynamic"),
    ("p_memsz, block size in memory", PlatformVar("addr"), "dynamic_end - dynamic"),
    ("p_align", PlatformVar("addr"), 21),  # Merges with DT_DEBUG in dynamic section.
    )

g_assembler_hash = (
    "hash",
    "DT_HASH",
    )

g_assembler_dynamic = (
    "dynamic",
    "PT_DYNAMIC",
    ("d_tag, DT_DEBUG = 21", PlatformVar("addr"), 21),
    ("d_un", PlatformVar("addr"), 0, "dynamic_r_debug"),
    ("d_tag, DT_STRTAB = 5", PlatformVar("addr"), 5),
    ("d_un", PlatformVar("addr"), "strtab"),
    ("d_tag, DT_NULL = 0", PlatformVar("addr"), 0),
    ("d_un", PlatformVar("addr"), 0),
    )

g_assembler_symtab = (
    "symtab",
    "DT_SYMTAB",
    )

g_assembler_interp = (
    "interp",
    "PT_INTERP",
    ("path to interpreter", 1, PlatformVar("interp")),
    ("interpreter terminating zero", 1, 0),
    )

g_assembler_strtab = (
    "strtab",
    "DT_STRTAB",
    ("initial zero", 1, 0),
    )

g_template_header = Template("""#ifndef DNLOAD_H
#define DNLOAD_H\n
/** \\file
 * \\brief Dynamic loader header stub.
 *
 * This file was automatically generated by '[[FILENAME]]'.
 */\n
#if defined(WIN32)
/** \\cond */
#define _USE_MATH_DEFINES
#define NOMINMAX
/** \\endcond */
#else
/** \\cond */
#define GL_GLEXT_PROTOTYPES
/** \\endcond */
#endif\n
#if defined(__cplusplus)
#include <cmath>
#include <cstdio>
#include <cstdlib>
#else
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#endif
[[INCLUDE_FREETYPE]][[INCLUDE_NCURSES]][[INCLUDE_OPENGL]][[INCLUDE_PNG]][[INCLUDE_RAND]][[INCLUDE_SDL]][[INCLUDE_SNDFILE]]
/** Macro stringification helper (adds indirection). */
#define DNLOAD_MACRO_STR_HELPER(op) #op
/** Macro stringification. */
#define DNLOAD_MACRO_STR(op) DNLOAD_MACRO_STR_HELPER(op)\n
#if defined(DNLOAD_GLESV2)
/** Apientry definition (OpenGL ES 2.0). */
#define DNLOAD_APIENTRY GL_APIENTRY
#else
/** Apientry definition (OpenGL). */
#define DNLOAD_APIENTRY GLAPIENTRY
#endif\n
#if (defined(_LP64) && _LP64) || (defined(__LP64__) && __LP64__)
/** Size of pointer in bytes (64-bit). */
#define DNLOAD_POINTER_SIZE 8
#else
/** Size of pointer in bytes (32-bit). */
#define DNLOAD_POINTER_SIZE 4
#endif\n
#if !defined([[DEFINITION_LD]])
/** Error string for when assembler exit procedure is not available. */
#define DNLOAD_ASM_EXIT_ERROR "no assembler exit procedure defined for current operating system or architecture"
/** Perform exit syscall in assembler. */
static void asm_exit(void)
{
#if defined(DNLOAD_NO_DEBUGGER_TRAP)
#if defined(__x86_64__)
#if defined(__FreeBSD__)
    asm("syscall" : /* no output */ : "a"(1) : /* no clobber */);
#elif defined(__linux__)
    asm("syscall" : /* no output */ : "a"(60) : /* no clobber */);
#else
#pragma message DNLOAD_MACRO_STR(DNLOAD_ASM_EXIT_ERROR)
#error
#endif
#elif defined(__i386__)
#if defined(__FreeBSD__) || defined(__linux__)
    asm("int $0x80" : /* no output */ : "a"(1) : /* no clobber */);
#else
#pragma message DNLOAD_MACRO_STR(DNLOAD_ASM_EXIT_ERROR)
#error
#endif
#elif defined(__aarch64__)
#if defined(__linux__)
    register int x8 asm("x8") = 93;
    asm("svc #0" : /* no output */ : "r"(x8) : /* no clobber */);
#else
#pragma message DNLOAD_MACRO_STR(DNLOAD_ASM_EXIT_ERROR)
#error
#endif
#elif defined(__arm__)
#if defined(__linux__)
    register int r7 asm("r7") = 1;
    asm("swi #0" : /* no output */ : "r"(r7) : /* no clobber */);
#else
#pragma message DNLOAD_MACRO_STR(DNLOAD_ASM_EXIT_ERROR)
#error
#endif
#else
#pragma message DNLOAD_MACRO_STR(DNLOAD_ASM_EXIT_ERROR)
#error
#endif
#else
#if defined(__x86_64__) || defined(__i386__)
    asm("int $0x3" : /* no output */ : /* no input */ : /* no clobber */);
#elif defined(__aarch64__)
    asm("brk #1000" : /* no output */ : /* no input */ : /* no clobber */);
#elif defined(__arm__)
    asm(".inst 0xdeff" : /* no output */ : /* no input */ : /* no clobber */);
#else
#pragma message DNLOAD_MACRO_STR(DNLOAD_ASM_EXIT_ERROR)
#error
#endif
#endif
    __builtin_unreachable();
}
#endif\n
#if defined([[DEFINITION_LD]])
/** \\cond */
[[SYMBOL_DEFINITIONS_DIRECT]]
/** \\endcond */
#else
/** \\cond */
[[SYMBOL_DEFINITIONS_TABLE]]
/** \\endcond */[[SYMBOL_TABLE]]
#endif\n
#if defined([[DEFINITION_LD]])
/** \\cond */
#define dnload()
/** \\endcond */
#else
[[LOADER]]
#endif\n
#if defined(__clang__)
/** Visibility declaration for symbols that require it (clang). */
#define DNLOAD_VISIBILITY __attribute__((visibility("default")))
#else
/** Visibility declaration for symbols that require it (gcc). */
#define DNLOAD_VISIBILITY __attribute__((externally_visible,visibility("default")))
#endif\n
#if !defined([[DEFINITION_LD]])
#if defined(__cplusplus)
extern "C"
{
#endif
/** Program entry point. */
void _start() DNLOAD_VISIBILITY;[[UND_SYMBOLS]]
#if defined(__cplusplus)
}
#endif
#endif
#endif
\n""")

g_template_include_freetype = Template("""
#include \"ft2build.h\"
#include FT_FREETYPE_H
""")

g_template_include_ncurses = Template("""
#include \"ncurses.h\"
""")

g_template_include_opengl = Template("""
#if defined(DNLOAD_VIDEOCORE)
#include \"bcm_host.h\"
#include \"EGL/egl.h\"
#endif\n
#if defined([[DEFINITION_LD]])
#if defined(WIN32)
#include \"windows.h\"
#include \"GL/glew.h\"
#include \"GL/glu.h\"
#elif defined(__APPLE__)
#include \"GL/glew.h\"
#include <OpenGL/glu.h>
#else
#if defined(DNLOAD_GLESV2)
#include \"GLES2/gl2.h\"
#include \"GLES2/gl2ext.h\"
#else
#include \"GL/glew.h\"
#include \"GL/glu.h\"
#endif
#endif
#else
#if defined(__APPLE__)
#include <OpenGL/gl.h>
#include <OpenGL/glext.h>
#include <OpenGL/glu.h>
#else
#if defined(DNLOAD_GLESV2)
#include \"GLES2/gl2.h\"
#include \"GLES2/gl2ext.h\"
#else
#include \"GL/gl.h\"
#include \"GL/glext.h\"
#include \"GL/glu.h\"
#endif
#endif
#endif
""")

g_template_include_png = Template("""
#include \"png.h\"
""")

g_template_include_rand = Template("""
#if defined([[DEFINITION_LD]])
#include \"[[HEADER_RAND]]\"
#else
#define DNLOAD_RAND_IMPLEMENTATION_BSD [[RAND_TYPE_BSD]]
#define DNLOAD_RAND_IMPLEMENTATION_GNU [[RAND_TYPE_GNU]]
#if defined(__FreeBSD__)
#if !DNLOAD_RAND_IMPLEMENTATION_BSD
#include \"[[HEADER_RAND]]\"
#include \"[[SOURCE_RAND]]\"
#else
#define bsd_rand rand
#define bsd_srand srand
#endif
#elif defined(__linux__)
#if !DNLOAD_RAND_IMPLEMENTATION_GNU
#include \"[[HEADER_RAND]]\"
#include \"[[SOURCE_RAND]]\"
#else
#define gnu_rand rand
#define gnu_srand srand
#endif
#endif
#endif
""")

g_template_include_sdl = Template("""
#include \"SDL.h\"
#if defined(SDL_INIT_EVERYTHING) && defined(__APPLE__)
#define DNLOAD_MAIN SDL_main
#else
#define DNLOAD_MAIN main
#endif
""")

g_template_include_sndfile = Template("""
#include \"sndfile.h\"
""")

g_template_und_symbols = Template("""
#if defined(__FreeBSD__)
/** Symbol required by libc. */
void *environ DNLOAD_VISIBILITY;
/** Symbol required by libc. */
void *__progname DNLOAD_VISIBILITY;
#endif
""")

########################################
# Functions ############################
########################################

def collect_libraries(libraries, extra_libraries, symbols, compilation_mode):
    """Collect libraries to link against from symbols given."""
    # Collect suggested set of libraries.
    library_set = set()
    for ii in symbols:
        library_set = library_set.union(set([ii.get_library().get_name()]))
    # If nothing was provided, use suggested set of libraries.
    if not libraries:
        if "dlfcn" == compilation_mode:
            raise RuntimeError("cannot autodetect libraries for compilation mode '%s'" % compilation_mode)
        if extra_libraries:
            if is_verbose():
                print("Adding extra libraries due to platform: %s" % (str(extra_libraries)))
            library_set = library_set.union(extra_libraries)
        libraries = list(library_set)
        output_message = "Autodetected libraries to link against: "
    # If libraries were given, warn if something seems to be missing.
    else:
        missing_libraries = library_set.difference(set(libraries))
        if missing_libraries:
            print("WARNING: found symbols suggest libraries: %s" % (str(list(missing_libraries))))
        output_message = "Linking against libraries: "
    # Reorder libraries to ensure there is no problems with library scouring and UND symbols.
    problematic_libraries = ["gcc", "c", "m", "bcm_host"]  # Order is important.
    front = []
    for ii in problematic_libraries:
        if ii in libraries:
            libraries.remove(ii)
            front += [ii]
    # Only use renamed library names if constructing the header manually.
    if "maximum" == compilation_mode:
        ret = list(map(lambda x: collect_libraries_rename(x), front + sorted(libraries)))
    else:
        ret = front + sorted(libraries)
    if is_verbose():
        print("%s%s" % (output_message, str(ret)))
    return ret

def collect_libraries_rename(op):
    """Find replacement name for a library if it's problematic."""
    # TODO: Remove when FreeBSD/Linux handles libGL.so correctly.
    if (("FreeBSD" == g_osname) and (g_osversion < 12)) or ("Linux" == g_osname):
        if "GL" == op:
            return "libGL.so.1"
    # If there's an explicit '.so.' without a 'lib', add the 'lib'.
    if re.search(r'\.so\.', op, re.I) and (not re.match(r'^lib', op, re.I)):
        return "lib%s" % (op)
    return op

def compress_file(compression, filedrop_interp, pretty, src, dst):
    """Compress a file to be a self-extracting file-dumping executable."""
    str_header = PlatformVar("shelldrop_header").get()
    str_tail = PlatformVar("shelldrop_tail").get()
    str_chmod = ""
    str_ld = ""
    str_cleanup = ";exit"
    # If we're calling LD directly, we need to refer to it.
    if filedrop_interp:
        str_ld = filedrop_interp + " "
    # Some platforms need chmod even with explicit interp.
    if (not filedrop_interp) or osname_is_freebsd():
        str_chmod = ";chmod +x $I"
    # 'pretty' script will also remove the file.
    if pretty:
        str_tail = "tail -n+2"
        str_cleanup = ";rm ~;exit"
    # Select filedump type.
    if "lzma" == compression:
        command = ["xz", "--format=lzma", "--lzma1=preset=9,lc=1,lp=0,nice=273,pb=0", "--stdout"]
        str_cat = "lzcat"
    elif "raw" == compression:
        command = ["xz", "-9", "--extreme", "--format=raw", "--stdout"]
        str_cat = "xzcat -F raw"
    elif "xz" == compression:
        command = ["xz", "--format=xz", "--lzma2=preset=9,lc=1,nice=273,pb=0", "--stdout"]
        str_cat = "xzcat"
    else:
        raise RuntimeError("unknown compression format '%s'" % compression)
    # Create the header string.
    header = "%sI=/tmp/i;%s $0|%s>$I%s;%s$I%s" % (str_header, str_tail, str_cat, str_chmod, str_ld, str_cleanup)
    # Compress the file.
    (compressed, se) = run_command(command + [src], False)
    wfd = open(dst, "wb")
    wfd.write((header + "\n").encode())
    wfd.write(compressed)
    wfd.close()
    make_executable(dst)
    print("Wrote '%s': %i bytes" % (dst, os.path.getsize(dst)))

def extract_symbol_names(source, prefix):
    """Analyze given preprocessed C source for symbol names."""
    symbolre = re.compile(r'[\s:;&\|\<\>\=\^\+\-\*/\(\)\?]%s([a-zA-Z0-9_]+)(?=[\s\(])' % (prefix))
    results = symbolre.findall(source, re.MULTILINE)
    ret = set()
    for ii in results:
        symbolset = set()
        symbolset.add(ii)
        ret = ret.union(symbolset)
    return ret

def find_global_tmpdir():
    """Try to find a global temporary directory."""
    if os.path.exists("/tmp"):
        return "/tmp"
    if os.path.exists("/var/tmp"):
        return "/var/tmp"
    return None

def find_library_definition(op):
    """Find library definition with name."""
    for ii in g_library_definitions:
        if ii.get_name() == op:
            return ii
    return None

def find_symbol(op):
    """Find single symbol with name."""
    for ii in g_library_definitions:
        ret = ii.find_symbol(op)
        if ret:
            return ret
    raise RuntimeError("symbol '%s' not known, please add it to the script" % (op))

def find_symbols(lst):
    """Find symbol object(s) corresponding to symbol string(s)."""
    ret = []
    for ii in lst:
        ret += [find_symbol(ii)]
    return ret

def generate_binary_minimal(source_file, compiler, assembler, linker, objcopy, elfling, libraries, output_file,
                            additional_sources=[], interp_needed=False, merge_allowed=True):
    """Generate a binary using all possible tricks. Return whether or not reprocess is necessary."""
    output_file_s = generate_temporary_filename(output_file + ".S")
    if source_file:
        compiler.compile_asm(source_file, output_file_s, True)
    segment_ehdr = AssemblerSegment(g_assembler_ehdr)
    segment_dynamic = AssemblerSegment(g_assembler_dynamic)
    segment_hash = AssemblerSegment(g_assembler_hash)
    segment_interp = AssemblerSegment(g_assembler_interp)
    segment_strtab = AssemblerSegment(g_assembler_strtab)
    segment_symtab = AssemblerSegment(g_assembler_symtab)
    # Dynamic and interp depend on address size.
    if osarch_is_32_bit():
        segment_phdr_dynamic = AssemblerSegment(g_assembler_phdr32_dynamic)
        segment_phdr_interp = AssemblerSegment(g_assembler_phdr32_interp)
    elif osarch_is_64_bit():
        segment_phdr_dynamic = AssemblerSegment(g_assembler_phdr64_dynamic)
        segment_phdr_interp = AssemblerSegment(g_assembler_phdr64_interp)
    else:
        raise_unknown_address_size()
    # There may be symbols necessary for addition.
    und_symbols = get_platform_und_symbols()
    if is_listing(und_symbols):
        segment_symtab.add_symbol_empty()
        for ii in und_symbols:
            segment_symtab.add_symbol_und(ii)
        for ii in reversed(und_symbols):
            segment_strtab.add_strtab(ii)
        segment_dynamic.add_dt_symtab("symtab")
        segment_dynamic.add_dt_hash("hash")
        segment_hash.add_hash(und_symbols)
    else:
        segment_dynamic.add_dt_symtab(0)
    # Add libraries.
    for ii in reversed(libraries):
        for jj in listify(linker.get_library_name(ii)):
            segment_dynamic.add_dt_needed(jj)
            segment_strtab.add_strtab(jj)
    # Assembler file generation is more complex when elfling is enabled.
    output_file_final_s = generate_temporary_filename(output_file + ".final.S")
    output_file_final_o = generate_temporary_filename(output_file + ".final.o")
    if elfling:
        asm = generate_elfling(output_file, compiler, elfling, definition_ld)
    else:
        asm = AssemblerFile(output_file_s)
    # Additional sources may have been specified, add them.
    if additional_sources:
        for ii in range(len(additional_sources)):
            fname = additional_sources[ii]
            additional_asm = AssemblerFile(fname)
            asm.incorporate(additional_asm)
    # Assemble content without headers to check for missing symbols.
    if asm.write(output_file_final_s, assembler):
        assembler.assemble(output_file_final_s, output_file_final_o)
        extra_symbols = readelf_list_und_symbols(output_file_final_o)
        output_file_extra = generate_temporary_filename(output_file + ".extra")
        additional_file = g_symbol_sources.compile_asm(compiler, assembler, extra_symbols, output_file_extra)
        # If additional code was needed, add it to our asm source.
        if additional_file:
            additional_asm = AssemblerFile(additional_file)
            asm.incorporate(additional_asm, re.sub(r'[\/\.]', '_', output_file + "_extra"))
    # Sort sections after generation, then crunch the source.
    asm.sort_sections(assembler)
    asm.crunch()
    # May be necessary to have two PT_LOAD headers as opposed to one.
    phdr_count = 2
    segment_phdr_load_bss = None
    bss_section = asm.generate_fake_bss(assembler, und_symbols, elfling)
    if 0 < bss_section.get_alignment():
        if osarch_is_32_bit():
            segment_phdr_load = AssemblerSegment(g_assembler_phdr32_load_double)
            segment_phdr_load_bss = AssemblerSegment(g_assembler_phdr32_load_bss)
        elif osarch_is_64_bit():
            segment_phdr_load = AssemblerSegment(g_assembler_phdr64_load_double)
            segment_phdr_load_bss = AssemblerSegment(g_assembler_phdr64_load_bss)
        else:
            raise_unknown_address_size()
        phdr_count += 1
    else:
        if osarch_is_32_bit():
            segment_phdr_load = AssemblerSegment(g_assembler_phdr32_load_single)
        elif osarch_is_64_bit():
            segment_phdr_load = AssemblerSegment(g_assembler_phdr64_load_single)
        else:
            raise_unknown_address_size()
    # Segments before the phdr array and the first phdr.
    segments_head = [segment_ehdr, segment_phdr_load]
    # Segments that cannot be crunched because the phdrs must be in order.
    segments_mid = []
    if segment_phdr_load_bss:
        segments_mid += segment_phdr_load_bss
    if interp_needed:
        phdr_count += 1
        segments_mid += [segment_phdr_interp]
    # Last phdr and segments after the phdr array.
    segments_tail = [segment_phdr_dynamic, segment_dynamic]
    if is_listing(und_symbols):
        segments_tail += [segment_symtab]
    if is_listing(und_symbols):
        segments_tail += [segment_hash]
    if interp_needed:
        segments_tail += [segment_interp]
    segments_tail += [segment_strtab]
    # Merge all segments if allowed.
    if merge_allowed:
        replace_platform_variable("phdr_count", phdr_count)
        replace_platform_variable("e_shentsize", 1)  # Merges with PT_LOAD.
        if osarch_is_64_bit():
            replace_platform_variable("e_shstrndx", 7)  # Merges with rwx flags.
        segments = merge_segments(segments_head) + segments_mid + merge_segments(segments_tail)
    else:
        segments = segments_head + segments_mid + segments_tail
    # Create content of earlier sections and write source when done.
    if asm.hasSectionAlignment():
        asm.getSectionAlignment().create_content(assembler)
    bss_section.create_content(assembler, "end")
    # Write headers out first.
    fd = open(output_file_final_s, "w")
    header_sizes = 0
    for ii in segments:
        ii.write(fd, assembler)
        header_sizes += ii.size()
    if is_verbose():
        print("Size of headers: %i bytes" % (header_sizes))
    # Write content after headers.
    asm.write(fd, assembler)
    fd.close()
    if is_verbose():
        print("Wrote assembler source: '%s'" % (output_file_final_s))
    # Assemble headers
    assembler.assemble(output_file_final_s, output_file_final_o)
    link_files = [output_file_final_o]
    # Link all generated files.
    output_file_ld = generate_temporary_filename(output_file + ".ld")
    output_file_unprocessed = generate_temporary_filename(output_file + ".unprocessed")
    output_file_stripped = generate_temporary_filename(output_file + ".stripped")
    linker.generate_linker_script(output_file_ld, True)
    linker.set_linker_script(output_file_ld)
    # Some platforms cannot skip the extra objcopy step. Reason unknown.
    if (not osarch_is_aarch64()) and (not osarch_is_arm32l()):
        objcopy = None
    linker.link_binary(objcopy, link_files, output_file_unprocessed)
    if bss_section.get_alignment():
        readelf_zero(output_file_unprocessed, output_file_stripped)
    else:
        readelf_truncate(output_file_unprocessed, output_file_stripped)

def generate_elfling(output_file, compiler, elfling, definition_ld):
    """Generate elfling stub."""
    output_file_s = generate_temporary_filename(output_file + ".S")
    output_file_elfling_cpp = generate_temporary_filename(output_file + ".elfling.cpp")
    output_file_elfling_s = generate_temporary_filename(output_file + ".elfling.S")
    elfling.write_c_source(output_file_elfling_cpp, definition_ld)
    compiler.compile_asm(output_file_elfling.cpp, output_file_elfling_s)
    asm = AssemblerFile(output_file_elfling_s)
    additional_asm = AssemblerFile(output_file_s)
    # Entry point is used as compression start information.
    elfling_align = int(PlatformVar("memory_page"))
    if elfling.has_data():
        alignment_section = AssemblerSectionAlignment(elfling_align, ELFLING_PADDING, ELFLING_OUTPUT, "end")
        set_program_start("_start")
    else:
        alignment_section = AssemblerSectionAlignment(elfling_align, ELFLING_PADDING, ELFLING_OUTPUT)
        set_program_start(ELFLING_OUTPUT)
    asm.add_sections(alignment_section)
    asm.incorporate(additional_asm, "_incorporated", ELFLING_UNCOMPRESSED)
    return asm

def generate_glsl(filenames, preprocessor, definition_ld, mode, inlines, renames, simplifys):
    """Generate GLSL, processing given GLSL source files."""
    glsl_db = Glsl()
    for ii in filenames:
        # If there's a listing, the order is filename, output name, varname
        if is_listing(ii):
            if 3 == len(ii):
                glsl_db.read(preprocessor, definition_ld, ii[0], ii[1], ii[2])
            elif 2 == len(ii):
                glsl_db.read(preprocessor, definition_ld, ii[0], ii[1])
            else:
                raise RuntimeError("invalid glsl file listing input: '%s'" % (str(ii)))
        # Otherwise only filename exists.
        else:
            glsl_db.read(preprocessor, definition_ld, ii)
    glsl_db.parse()
    glsl_db.crunch(mode, inlines, renames, simplifys)
    return glsl_db

def generate_glsl_extract(fname, preprocessor, definition_ld, mode, inlines, renames, simplifys):
    """Generate GLSL, extracting from source file."""
    src_path, src_basename = os.path.split(fname)
    if src_path:
        src_path += "/"
    fd = open(fname, "r")
    lines = fd.readlines()
    fd.close()
    filenames = []
    glslre = re.compile(r'#\s*include [\<\"](.*\.glsl)\.(h|hh|hpp|hxx)[\>\"]\s*((\/\*|\/\/)\s*([^\*\/\s]+))?', re.I)
    for ii in lines:
        match = glslre.match(ii)
        if match:
            glsl_path, glsl_base_filename = os.path.split(match.group(1))
            # Try with base path of source file first to limit location.
            glsl_filename = locate(src_path + glsl_path, glsl_base_filename)
            if not glsl_filename:
                glsl_filename = locate(glsl_path, glsl_base_filename)
            if not glsl_filename:
                raise RuntimeError("could not locate GLSL source '%s'" % (glsl_base_filename))
            glsl_output_name = glsl_filename + "." + match.group(2)
            # Varname may or may not exist.
            glsl_varname = match.group(5)
            if glsl_varname:
                filenames += [[glsl_filename, glsl_output_name, glsl_varname]]
            else:
                filenames += [[glsl_filename, glsl_output_name]]
    if filenames:
        glsl_db = generate_glsl(filenames, preprocessor, definition_ld, mode, inlines, renames, simplifys)
        glsl_db.write()

def generate_include_rand(implementation_rand, target_search_path, definition_ld):
    """Generates the rand()/srand() include."""
    regex_rand_header = re.compile(r'%s[-_\s]+rand\.h(h|pp|xx)?' % (implementation_rand))
    regex_rand_source = re.compile(r'%s[-_\s]+rand\.c(c|pp|xx)?' % (implementation_rand))
    header_rand = locate(target_search_path, regex_rand_header)
    source_rand = locate(target_search_path, regex_rand_source)
    if (not header_rand) or (not source_rand):
        raise RuntimeError("could not find rand implementation for '%s'" % (implementation_rand))
    header_rand_path, header_rand = os.path.split(header_rand)
    source_rand_path, source_rand = os.path.split(source_rand)
    if is_verbose:
        print("Using rand() implementation: '%s'" % (header_rand))
    replace_platform_variable("function_rand", "%s_rand" % (implementation_rand))
    replace_platform_variable("function_srand", "%s_srand" % (implementation_rand))
    rand_type_bsd = str(int(implementation_rand == "bsd"))
    rand_type_gnu = str(int(implementation_rand == "gnu"))
    return g_template_include_rand.format({"DEFINITION_LD": definition_ld,
                                           "RAND_TYPE_BSD": rand_type_bsd, "RAND_TYPE_GNU": rand_type_gnu,
                                           "HEADER_RAND": header_rand, "SOURCE_RAND": source_rand})

def get_platform_und_symbols():
    """Get the UND symbols required for this platform."""
    ret = None
    if osname_is_freebsd():
        ret = sorted(["environ", "__progname"])
    if is_verbose():
        print("Checking for required UND symbols... " + str(ret))
    return ret

def make_executable(op):
    """Make given file executable."""
    if not os.stat(op)[stat.ST_MODE] & stat.S_IXUSR:
        run_command(["chmod", "+x", op])

def merge_segments(lst):
    """Try to merge segments in a given list in-place."""
    ii = 0
    while True:
        jj = ii + 1
        if len(lst) <= jj:
            return lst
        seg1 = lst[ii]
        seg2 = lst[jj]
        if seg1.merge(seg2):
            if seg2.empty():
                del lst[jj]
            else:
                ii += 1
        else:
            ii += 1
    return lst

def raise_unknown_address_size():
    """Common function to raise an error if os architecture address size is unknown."""
    raise RuntimeError("platform '%s' addressing size unknown" % (g_osarch))

def readelf_get_info(op):
    """Read information from an ELF file using readelf. Return as dictionary."""
    ret = {}
    (so, se) = run_command(["readelf", "-l", op])
    match = re.search(r'LOAD\s+\S+\s+(\S+)\s+\S+\s+(\S+)\s+\S+\s+RWE', so, re.MULTILINE)
    if match:
        ret["base"] = int(match.group(1), 16)
        ret["size"] = int(match.group(2), 16)
    else:
        raise RuntimeError("could not read first PT_LOAD from executable '%s'" % (op))
    # Entry point is locale-dependant so attempt to read it from the second line.
    match = re.match(r'\s*\n.*EXEC.*\n*.*\s+(0x\S+)\n', so, re.MULTILINE)
    if match:
        ret["entry"] = int(match.group(1), 16) - ret["base"]
    else:
        raise RuntimeError("could not read entry point from executable '%s'" % (op))
    return ret

def readelf_list_und_symbols(op):
    """List UND symbols found from a file."""
    (so, se) = run_command(["readelf", "--symbols", op])
    match = re.findall(r'GLOBAL\s+DEFAULT\s+UND\s+(\S+)\s+', so, re.MULTILINE)
    if match:
        return match
    return None

def readelf_probe(src, dst, size):
    """Probe ELF size, copy source to destination on equal size and return None, or return truncation size."""
    info = readelf_get_info(src)
    truncate_size = info["size"]
    if size == truncate_size:
        if is_verbose():
            print("Executable size equals PT_LOAD size (%u bytes), no operation necessary." % (size))
        shutil.copy(src, dst)
        return None
    return truncate_size

def readelf_truncate(src, dst):
    """Truncate file to size reported by readelf first PT_LOAD file size."""
    size = os.path.getsize(src)
    truncate_size = readelf_probe(src, dst, size)
    if truncate_size is None:
        return
    if is_verbose():
        print("Truncating file size to PT_LOAD size: %u bytes" % (truncate_size))
    rfd = open(src, "rb")
    wfd = open(dst, "wb")
    wfd.write(rfd.read(truncate_size))
    rfd.close()
    wfd.close()

def readelf_zero(src, dst):
    """Zero bytes in ELF file starting from first PT_LOAD size."""
    size = os.path.getsize(src)
    truncate_size = readelf_probe(src, dst, size)
    if truncate_size is None:
        return
    if is_verbose():
        print("Filling file with 0 after PT_LOAD size: %u bytes" % (truncate_size))
    rfd = open(src, "rb")
    wfd = open(dst, "wb")
    wfd.write(rfd.read(truncate_size))
    rfd.close()
    while truncate_size < size - 1:
        wfd.write("\0")
        truncate_size += 1
    wfd.close()

def replace_conflicting_library(symbols, src_name, dst_name):
    """Replace conflicting library reference in a symbol set if necessary."""
    src_found = symbols_has_library(symbols, src_name)
    dst_found = symbols_has_library(symbols, dst_name)
    if not (src_found and dst_found):
        return symbols
    if is_verbose():
        print("Resolving library conflict: '%s' => '%s'" % (src_name, dst_name))
    ret = []
    dst = find_library_definition(dst_name)
    for ii in symbols:
        if ii.get_library().get_name() == src_name:
            replacement = dst.find_symbol(ii.get_name())
            if replacement:
                ret += [replacement]
            else:
                new_symbol = ii.create_replacement(dst)
                dst.add_symbol(new_symbol)
                ret += [new_symbol]
        else:
            ret += [ii]
    return ret

def set_program_start(op):
    """Set label to start program execution from."""
    replace_platform_variable("start", op)

def symbols_has_library(symbols, op):
    """Tell if symbol collection wants to link against any of the given libraries."""
    name_list = listify(op)
    for ii in symbols:
        if ii.get_library().get_name() in name_list:
            return True
    return False

def symbols_has_symbol(symbols, op):
    """Tell if symbol collection has any of the given symbols."""
    name_list = listify(op)
    for ii in symbols:
        if ii.get_name() in name_list:
            return True
    return False

def touch(op):
    """Emulate *nix 'touch' command."""
    if not os.path.exists(op):
        if is_verbose():
            print("Creating nonexistent file '%s'." % (op))
        fd = open(op, "w")
        fd.close()
    elif not os.path.isfile(op):
        raise RuntimeError("'%s' exists but is not a normal file" % (op))

########################################
# Main #################################
########################################

def main():
    """Main function."""
    global g_osarch
    global g_osname
    compression = str(PlatformVar("compression"))
    default_assembler_list = ["/usr/local/bin/as", "as"]
    default_compiler_list = ["g++8", "g++-8", "g++7", "g++-7", "g++", "c++"]
    default_linker_list = ["/usr/local/bin/ld", "ld"]
    default_preprocessor_list = ["cpp", "clang-cpp"]
    default_objcopy_list = ["/usr/local/bin/objcopy", "objcopy"]
    default_strip_list = ["/usr/local/bin/strip", "strip"]
    definitions = []
    extra_assembler_flags = []
    extra_compiler_flags = []
    extra_libraries = []
    extra_linker_flags = []
    include_directories = [PATH_VIDEOCORE + "/include", PATH_VIDEOCORE + "/include/interface/vcos/pthreads", PATH_VIDEOCORE + "/include/interface/vmcs_host/linux", "/usr/include/freetype2/", "/usr/include/SDL", "/usr/local/include", "/usr/local/include/freetype2/", "/usr/local/include/SDL"]
    library_directories = ["/lib", "/lib/x86_64-linux-gnu", PATH_VIDEOCORE + "/lib", "/usr/lib", "/usr/lib/arm-linux-gnueabihf", "/usr/lib/gcc/arm-linux-gnueabihf/4.9/", "/usr/lib/x86_64-linux-gnu", "/usr/local/lib"]
    opengl_reason = None
    opengl_version = None
    output_file = None
    program_name = os.path.basename(sys.argv[0])
    sdl_version = 2

    parser = argparse.ArgumentParser(usage="%s [args] <source file(s)> [-o output]" % (program_name), description="Size-optimized executable generator for *nix platforms.\nPreprocesses given source file(s) looking for specifically marked function calls, then generates a dynamic loader header file that can be used within these same source files to decrease executable size.\nOptionally also perform the actual compilation of a size-optimized binary after generating the header.", formatter_class=CustomHelpFormatter, add_help=False)
    parser.add_argument("--32", dest="m32", action="store_true", help="Try to target 32-bit version of the architecture if on a 64-bit system.")
    parser.add_argument("-a", "--abstraction-layer", choices=("sdl1", "sdl2"), help="Specify abstraction layer to use instead of autodetecting.")
    parser.add_argument("-A", "--assembler", default=None, help="Try to use given assembler executable as opposed to autodetect.")
    parser.add_argument("-B", "--objcopy", default=None, help="Try to use given objcopy executable as opposed to autodetect.")
    parser.add_argument("-C", "--compiler", default=None, help="Try to use given compiler executable as opposed to autodetect.")
    parser.add_argument("-d", "--definition-ld", default="USE_LD", help="Definition to use for checking whether to use 'safe' mechanism instead of dynamic loading.\n(default: %(default)s)")
    parser.add_argument("-D", "--define", default=[], action="append", help="Additional preprocessor definition.")
    parser.add_argument("-e", "--elfling", action="store_true", help="Use elfling packer if available.")
    parser.add_argument("-E", "--preprocess-only", action="store_true", help="Preprocess only, do not generate compiled output.")
    parser.add_argument("-F", "--filedrop-mode", default="auto", choices=("header", "native", "cross", "auto"), help="File dropping and interpreter calling mode.\n\theader:\n\t\tAdd explicit PT_INTERP header into the binary.\n\tnative:\n\t\tCall dynamic linker for the native platform.\n\tcross:\n\t\tCall dynamic linker assuming cross-platform emulation.\n\tauto:\n\t\tTry to autodetect and create the smallest binary to be ran on current machine.\n(default: %(default)s)")
    parser.add_argument("-h", "--help", action="store_true", help="Print this help string and exit.")
    parser.add_argument("-I", "--include-directory", default=[], action="append", help="Add an include directory to be searched for header files.")
    parser.add_argument("--interp", default=None, type=str, help="Use given interpreter as opposed to platform default.")
    parser.add_argument("-k", "--linker", default=None, help="Try to use given linker executable as opposed to autodetect.")
    parser.add_argument("-l", "--library", default=[], action="append", help="Add a library to be linked against.")
    parser.add_argument("-L", "--library-directory", default=[], action="append", help="Add a library directory to be searched for libraries when linking.")
    parser.add_argument("-m", "--method", default="maximum", choices=("vanilla", "dlfcn", "hash", "maximum"), help="Method to use for decreasing output file size:\n\tvanilla:\n\t\tProduce binary normally, use no tricks except unpack header.\n\tdlfcn:\n\t\tUse dlopen/dlsym to decrease size without dependencies to any specific object format.\n\thash:\n\t\tUse knowledge of object file format to perform 'import by hash' loading, but do not break any specifications.\n\tmaximum:\n\t\tUse all available techniques to decrease output file size. Resulting file may violate object file specification.\n(default: %(default)s)")
    parser.add_argument("--march", type=str, help="When compiling code, use given architecture as opposed to autodetect.")
    parser.add_argument("--nice-exit", action="store_true", help="Do not use debugger trap, exit with proper system call.")
    parser.add_argument("--nice-filedump", action="store_true", help="Do not use dirty tricks in compression header, also remove filedumped binary when done.")
    parser.add_argument("--no-glesv2", action="store_true", help="Do not probe for OpenGL ES 2.0, always assume regular GL.")
    parser.add_argument("--merge-headers", default="auto", choices=("yes", "no", "auto"), help="ELF header merging policy:\n\tno:\n\t\tHeaders concatenated sequentially.\n\tyes:\n\t\tTry to interleave headers to decrease file size.\n\tauto:\n\t\tUse interleaving if target platform allows.\n(default: %(default)s)")
    parser.add_argument("--glsl-mode", default="full", choices=("none", "nosquash", "full"), help="GLSL crunching mode.\n\tnone:\n\t\tJust remove whitespace.\n\tnosquash:\n\t\tRefrain from squashing statements together, otherwise same as full.\n\tfull:\n\t\tTry to minimize file size by any means necessary.\n(default: %(default)s)")
    parser.add_argument("--glsl-inlines", default=-1, type=int, help="Maximum number of inline operations to do for GLSL.\n(default: unlimited)")
    parser.add_argument("--glsl-renames", default=-1, type=int, help="Maximum number of rename operations to do for GLSL.\n(default: unlimited)")
    parser.add_argument("--glsl-simplifys", default=-1, type=int, help="Maximum number of simplify operations to do for GLSL.\n(default: unlimited)")
    parser.add_argument("--linux", action="store_true", help="Try to target Linux if not in Linux. Equal to '-O linux'.")
    parser.add_argument("-o", "--output-file", default=[], nargs="*", help="Name of output file to generate\nIf the name specified features a path, it will be used verbatim. Otherwise the binary will be created in the same path as source file(s) compiled.\nIf only processing GLSL files, this parameter can be specified multiple times, but must be specified exactly once per input GLSL file.")
    parser.add_argument("-O", "--operating-system", help="Try to target given operating system insofar cross-compilation is possible.")
    parser.add_argument("-P", "--call-prefix", default="dnload_", help="Call prefix to identify desired calls.\n(default: %(default)s)")
    parser.add_argument("--preprocessor", default=None, help="Try to use given preprocessor executable as opposed to autodetect.")
    parser.add_argument("--rand", default="bsd", choices=("bsd", "gnu"), help="rand() implementation to use.\n(default: %(default)s)")
    parser.add_argument("--rpath", default=[], action="append", help="Extra rpath locations for linking.")
    parser.add_argument("--symtab-mode", default="auto", choices=("auto", "safe", "unsafe"), help="Method for scouring DT_SYMTAB:\n\tsafe:\n\t\tMake less assumptions about header layout.\n\tunsafe:\n\t\tAssume optimal header layout to decrease code size.\n\tauto:\n\t\tTry to autodetect based on target platform.\n(default: %(default)s)")
    parser.add_argument("-s", "--search-path", default=[], action="append", help="Directory to search for the header file to generate. May be specified multiple times. If not given, searches paths of source files to compile. If not given and no source files to compile, current path will be used.")
    parser.add_argument("-S", "--strip-binary", default=None, help="Try to use given strip executable as opposed to autodetect.")
    parser.add_argument("-t", "--target", default="dnload.h", help="Target header file to look for.\n(default: %(default)s)")
    parser.add_argument("-T", "--temporary-directory", default=None, help="Directory to store temporary files in.\n(default: autodetect)")
    parser.add_argument("-u", "--unpack-header", default=compression, choices=("lzma", "xz"), help="Unpack header to use.\n(default: %(default)s)")
    parser.add_argument("--verbatim", action="store_true", help="Perform select actions in a more verbatim manner:\n\t* Print GLSL to output without C header formatting.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Print more info about what is being done.")
    parser.add_argument("-V", "--version", action="store_true", help="Print version and exit.")
    parser.add_argument("source", default=[], nargs="*", help="Source file(s) to preprocess and/or compile.")

    args = parser.parse_args()

    # Early exit.
    if args.help:
        print(parser.format_help().strip())
        return 0
    if args.version:
        print("%s %s" % (VERSION_REVISION, VERSION_DATE))
        return 0

    abstraction_layer = listify(args.abstraction_layer)
    assembler = args.assembler
    compiler = args.compiler
    definition_ld = args.definition_ld
    definitions += args.define
    compilation_mode = args.method
    compression = args.unpack_header
    elfling = args.elfling
    glsl_inlines = args.glsl_inlines
    glsl_renames = args.glsl_renames
    glsl_simplifys = args.glsl_simplifys
    glsl_mode = args.glsl_mode
    implementation_rand = args.rand
    include_directories += args.include_directory
    libraries = args.library
    library_directories += args.library_directory
    linker = args.linker
    nice_filedump = args.nice_filedump
    no_glesv2 = args.no_glesv2
    objcopy = args.objcopy
    output_file_list = args.output_file
    preprocessor = args.preprocessor
    rpath = args.rpath
    strip = args.strip_binary
    symbol_prefix = args.call_prefix
    target = args.target
    target_search_path = args.search_path

    # Verbosity.
    if args.verbose:
        set_verbose(True)

    # Definitions.
    if args.nice_exit:
        definitions += ["DNLOAD_NO_DEBUGGER_TRAP"]

    # Custom interpreter.
    if args.interp:
        interp = args.interp
        if not re.match(r'^\".*\"$', interp):
            interp = "\"%s\"" % (args.interp)
        replace_platform_variable("interp", interp)

    # Source files to process.
    if not args.source:
        raise RuntimeError("no source files to process")
    source_files = []
    source_files_additional = []
    source_files_glsl = []
    for ii in args.source:
        if re.match(r'.*\.(c|cpp)$', ii, re.I):
            source_files += [ii]
        elif re.match(r'.*\.(asm|s)$', ii, re.I):
            source_files_additional += [ii]
        elif re.match(r'.*\.(glsl|vert|geom|frag)$', ii, re.I):
            source_files_glsl += [ii]
        else:
            raise RuntimeError("unknown source file: '%s'" % (ii))

    # Additinonal include and source directories files based on source files.
    if not target_search_path:
        for ii in source_files:
            source_path, source_file = os.path.split(os.path.normpath(ii))
            if source_path:
                if source_path not in target_search_path:
                    target_search_path += [source_path]
                if source_path not in include_directories:
                    include_directories += [source_path]
    if not target_search_path:
        target_search_path = ["."]

    # Temporary directory.
    if not set_temporary_directory(args.temporary_directory):
        if args.temporary_directory:
            print("WARNING: supplied temporary directory '%s' not usable, autodetecting" % (args.temporary_directory))
        regex_tmpdir = re.compile(r'(build|cmakefiles)', re.I)
        found_tmpdir = locate(None, regex_tmpdir)
        # Local tmpdir not found, try global.
        if not found_tmpdir:
            found_tmpdir = find_global_tmpdir()
        if set_temporary_directory(found_tmpdir) and is_verbose():
            print("Using temporary directory '%s/'." % (found_tmpdir))

    # GLES check (as opposed to plain desktop GL)
    gles_reason = None
    if not no_glesv2:
        if os.path.exists(PATH_MALI):
            extra_libraries += ["EGL"]
            definitions += ["DNLOAD_MALI"]
            gles_reason = "'%s' (Mali)" % (PATH_MALI)
        if os.path.exists(PATH_VIDEOCORE):
            definitions += ["DNLOAD_VIDEOCORE"]
            gles_reason = "'%s' (VideoCore)" % (PATH_VIDEOCORE)
            if 'armv7l' == g_osarch:
                replace_osarch("armv6l", "Workaround (Raspberry Pi): ")
    if gles_reason:
        definitions += ["DNLOAD_GLESV2"]
        replace_platform_variable("gl_library", "GLESv2")
        if is_verbose():
            print("Assuming OpenGL ES 2.0: %s" % (gles_reason))

    # Find preprocessor.
    preprocessor_list = default_preprocessor_list
    if os.name == "nt":
        preprocessor_list = ["cl.exe"] + preprocessor_list
    preprocessor = Preprocessor(executable_find(preprocessor, preprocessor_list, "preprocessor"))
    preprocessor.set_definitions(definitions)
    preprocessor.set_include_dirs(include_directories)

    # Process GLSL source if given.
    if source_files_glsl:
        if source_files or source_files_additional:
            raise RuntimeError("can not combine GLSL source files %s with other source files %s" % (str(source_files_glsl), str(source_files + source_files_additional)))
        if output_file_list and (len(output_file_list) != len(source_files_glsl)):
            raise RuntimeError("specified output files '%s' must match input glsl files '%s'" % (str(output_file_list), str(source_files_glsl)))
        if output_file_list:
            source_files_glsl = zip(source_files_glsl, output_file_list)
        glsl_db = generate_glsl(source_files_glsl, preprocessor, definition_ld, glsl_mode, glsl_inlines, glsl_renames, glsl_simplifys)
        if output_file_list:
            glsl_db.write()
        else:
            print(glsl_db.generatePrintOutput(args.verbatim))
        sys.exit(0)
    # If no GLSL, there must be exactly one output file or nothing.
    elif output_file_list:
        if len(output_file_list) > 1:
            raise RuntimeError("more than one output file specified: %s" % (str(output_file_list)))
        output_file = output_file_list[0]

    # Check for armhf interp as opposed to default.
    if g_osarch in ("armv6l", "armv7l"):
        current_interp = str(PlatformVar("interp"))[1:-1]
        if os.path.exists("/lib/ld-linux-armhf.so.3") and (not os.path.exists(current_interp)):
            replace_osarch(g_osarch + "hf", "Workaround (armhf ABI): ")

    # Check if cross interpreter is necessary before selecting to cross-compile or not.
    if args.filedrop_mode == "auto":
        if osarch_is_arm32l():
            args.filedrop_mode = "header"
        elif osarch_is_64_bit() and args.m32:
            args.filedrop_mode = "cross"
        else:
            args.filedrop_mode = "native"
        if is_verbose():
            print("Autodetected filedrop mode: '%s'" % (args.filedrop_mode))

    # Cross-compile 32-bit arguments.
    if args.m32:
        if osarch_is_32_bit():
            print("WARNING: ignoring 32-bit compile, osarch '%s' already 32-bit" % (g_osarch))
        elif osarch_is_amd64():
            replace_osarch("ia32", "Cross-compile: ")
            extra_assembler_flags = ["--32"]
            extra_compiler_flags = ["-m32"]
            if osname_is_freebsd():
                extra_linker_flags = ["-melf_i386_fbsd"]
            else:
                extra_linker_flags = ["-melf_i386"]
        else:
            raise RuntimeError("cannot attempt 32-bit compile for osarch '%s'" % (g_osarch))
    if args.march:
        if is_verbose:
            print("Using explicit march: '%s'" % (args.march))
        replace_platform_variable("march", args.march)
    # Cross-compile OS arguments.
    if args.linux:
        if args.operating_system:
            print("WARNING: overriding cross operating system choice with 'linux'")
        args.operating_system = "linux"
    if args.operating_system:
        new_osname = platform_map(args.operating_system.lower())
        replace_osname(new_osname, "Cross-compile:")
    elif osname_is_linux():
        # Linux does not care about ei_osabi - systems emulating Linux do.
        replace_platform_variable("ei_osabi", 0)

    # Select interpreter.
    filedrop_interp = None
    interp_needed = False
    if args.filedrop_mode == "cross":
        try:
            filedrop_interp = str(PlatformVar("interp-cross"))
        except ValueError as ee:
            filedrop_interp = str(PlatformVar("interp"))
    elif args.filedrop_mode == "native":
        filedrop_interp = str(PlatformVar("interp"))
    else:
        if args.filedrop_mode != "header":
            raise RuntimeError("unknown filedrop mode: '%s'" % (args.filedrop_mode))
        interp_needed = True
    if filedrop_interp:
        filedrop_interp = filedrop_interp.strip("\"")

    # Symtab handling depends on selected operating system.
    if args.symtab_mode == "auto":
        if osname_is_freebsd():
            args.symtab_mode = "safe"
        else:
            args.symtab_mode = "unsafe"
        if is_verbose():
            print("Autodetected symtab mode: '%s'" % (args.symtab_mode))
    if args.symtab_mode == "safe":
        definitions += ["DNLOAD_SAFE_SYMTAB_HANDLING"]

    # Header merging depends on target platform.
    if args.merge_headers == "auto":
        if osname_is_freebsd() and args.filedrop_mode == "header":
            args.merge_headers = "no"
        else:
            args.merge_headers = "yes"
        if is_verbose():
            print("Autodetected header merge mode: '%s'" % (args.merge_headers))
    if args.merge_headers == "yes":
        args.merge_headers = True
    else:
        args.merge_headers = False

    if compilation_mode not in ("vanilla", "dlfcn", "hash", "maximum"):
        raise RuntimeError("unknown method '%s'" % (compilation_mode))
    elif "hash" == compilation_mode:
        definitions += ["DNLOAD_NO_FIXED_R_DEBUG_ADDRESS"]

    target_path, target_file = os.path.split(os.path.normpath(target))
    if target_path:
        if is_verbose():
            print("Using explicit target header file '%s'." % (target))
    else:
        target_file = locate(target_search_path, target)
        if target_file:
            target = os.path.normpath(target_file)
            target_path, target_file = os.path.split(target)
            if is_verbose():
                print("Found header file: '%s'" % (target))
        else:
            raise RuntimeError("no information where to put header file '%s' - not found in path(s) %s" % (target, str(target_search_path)))
    # Erase contents of the header after it has been found.
    touch(target)

    # Clear target header before parsing to avoid problems.
    fd = open(target, "w")
    fd.write("\n")
    fd.close()
    if is_verbose():
        print("Analyzing source files: %s" % (str(source_files)))
    # Prepare GLSL headers before preprocessing.
    for ii in source_files:
        generate_glsl_extract(ii, preprocessor, definition_ld, glsl_mode, glsl_inlines, glsl_renames, glsl_simplifys)
    # Search symbols from source files.
    symbols = set()
    for ii in source_files:
        source = preprocessor.preprocess(ii)
        source_symbols = extract_symbol_names(source, symbol_prefix)
        symbols = symbols.union(source_symbols)
    symbols = find_symbols(symbols)
    if "dlfcn" == compilation_mode:
        symbols = sorted(symbols)
    elif "maximum" == compilation_mode:
        sortable_symbols = []
        for ii in symbols:
            sortable_symbols += [(ii.get_hash(), ii)]
        symbols = []
        for ii in sorted(sortable_symbols):
            symbols += [ii[1]]
    # Some libraries cannot co-exist, but have some symbols with identical names.
    symbols = replace_conflicting_library(symbols, "SDL", "SDL2")
    # Filter real symbols (as separate from implicit).
    real_symbols = list(filter(lambda x: not x.is_verbatim(), symbols))
    if is_verbose():
        symbol_strings = list(map(lambda x: str(x), symbols))
        print("%i symbols found: %s" % (len(symbols), str(symbol_strings)))
        verbatim_symbols = list(set(symbols) - set(real_symbols))
        if verbatim_symbols and output_file:
            verbatim_symbol_strings = []
            for ii in verbatim_symbols:
                verbatim_symbol_strings += [str(ii)]
            print("Not loading verbatim symbols: %s" % (str(verbatim_symbol_strings)))
    # Header includes.
    subst = {}
    if symbols_has_library(symbols, "freetype"):
        subst["INCLUDE_FREETYPE"] = g_template_include_freetype.format()
    if symbols_has_library(symbols, "ncurses"):
        subst["INCLUDE_NCURSES"] = g_template_include_ncurses.format()
    if symbols_has_library(symbols, ("GL", "GLESv2")):
        subst["INCLUDE_OPENGL"] = g_template_include_opengl.format({"DEFINITION_LD": definition_ld})
    if symbols_has_library(symbols, "png"):
        subst["INCLUDE_PNG"] = g_template_include_png.format()
    if symbols_has_library(symbols, ("SDL", "SDL2")):
        subst["INCLUDE_SDL"] = g_template_include_sdl.format()
    if symbols_has_library(symbols, "sndfile"):
        subst["INCLUDE_SNDFILE"] = g_template_include_sndfile.format()
    # Workarounds for specific symbol implementations - must be done before symbol definitions.
    if symbols_has_symbol(symbols, "rand"):
        subst["INCLUDE_RAND"] = generate_include_rand(implementation_rand, target_search_path, definition_ld)
    # Symbol definitions.
    symbol_definitions_direct = generate_symbol_definitions_direct(symbols, symbol_prefix)
    subst["SYMBOL_DEFINITIONS_DIRECT"] = symbol_definitions_direct
    if "vanilla" == compilation_mode:
        subst["SYMBOL_DEFINITIONS_TABLE"] = symbol_definitions_direct
    else:
        symbol_definitions_table = generate_symbol_definitions_table(symbols, symbol_prefix)
        symbol_table = generate_symbol_table(compilation_mode, real_symbols)
        subst["SYMBOL_DEFINITIONS_TABLE"] = symbol_definitions_table
        subst["SYMBOL_TABLE"] = symbol_table
    # Loader and UND symbols.
    if "vanilla" == compilation_mode:
        subst["LOADER"] = generate_loader_vanilla()
    elif "dlfcn" == compilation_mode:
        subst["LOADER"] = generate_loader_dlfcn(real_symbols, linker)
    else:
        subst["LOADER"] = generate_loader_hash(real_symbols)
    if "maximum" != compilation_mode:
        subst["UND_SYMBOLS"] = g_template_und_symbols.format()
    # Add remaining simple substitutions and generate file contents.
    subst["DEFINITION_LD"] = definition_ld
    subst["FILENAME"] = program_name
    file_contents = g_template_header.format(subst)
    # Write target file.
    fd = open(target, "w")
    fd.write(file_contents)
    fd.close()
    if is_verbose():
        print("Wrote header file: '%s'" % (target))
    # Early exit if preprocess only.
    if args.preprocess_only:
        sys.exit(0)
    # Not only preprocessing, ensure the sources are ok.
    if 1 < len(source_files):
        raise RuntimeError("only one source file supported when generating output file")

    # TODO: deprecated
    if elfling:
        elfling = executable_search(["elfling-packer", "./elfling-packer"], "elfling-packer")
        if elfling:
            elfling = Elfling(elfling)

    # Find compiler.
    compiler_list = default_compiler_list
    if os.name == "nt":
        compiler_list = ["cl.exe"] + compiler_list
    compiler = Compiler(executable_find(compiler, compiler_list, "compiler"))
    compiler.set_definitions(definitions)
    compiler.set_include_dirs(include_directories)
    if extra_compiler_flags:
        compiler.add_extra_compiler_flags(extra_compiler_flags)
    # Some compilers require extra library dirs.
    library_directories += compiler.get_extra_library_directories()

    # Find assembler.
    assembler = Assembler(executable_find(assembler, default_assembler_list, "assembler"))
    if extra_assembler_flags:
        assembler.addExtraFlags(extra_assembler_flags)

    # Find linker.
    linker = Linker(executable_find(linker, default_linker_list, "linker"))
    if extra_linker_flags:
        linker.addExtraFlags(extra_linker_flags)

    # Determine abstraction layer if it's not been set.
    if not abstraction_layer:
        if symbols_has_library(symbols, "SDL"):
            abstraction_layer += ["sdl1"]
        if symbols_has_library(symbols, "SDL2"):
            abstraction_layer += ["sdl2"]
    if 1 < len(abstraction_layer):
        raise RuntimeError("conflicting abstraction layers detected: %s" % (str(abstraction_layer)))
    if "sdl2" in abstraction_layer:
        (sdl_stdout, sdl_stderr) = run_command(["sdl2-config", "--cflags"])
        compiler.add_extra_compiler_flags(sdl_stdout.split())
    elif "sdl1" in abstraction_layer:
        (sdl_stdout, sdl_stderr) = run_command(["sdl-config", "--cflags"])
        compiler.add_extra_compiler_flags(sdl_stdout.split())

    # Determine output file.
    if output_file:
        output_file = os.path.normpath(output_file)
    else:
        output_path, output_basename = os.path.split(source_files[0])
        output_basename, source_extension = os.path.splitext(output_basename)
        output_file = os.path.normpath(os.path.join(output_path, output_basename))
        if is_verbose():
            print("Using output file '%s' after source file '%s'." % (output_file, source_file))

    source_file = source_files[0]
    libraries = collect_libraries(libraries, extra_libraries, real_symbols, compilation_mode)
    compiler.generate_compiler_flags()
    compiler.generate_linker_flags()
    compiler.set_libraries(libraries)
    compiler.set_library_directories(library_directories)
    compiler.set_rpath_directories(rpath)
    linker.generate_linker_flags()
    linker.set_libraries(libraries)
    linker.set_library_directories(library_directories)
    linker.set_rpath_directories(rpath)
    if "maximum" == compilation_mode:
        objcopy = executable_find(objcopy, default_objcopy_list, "objcopy")
        generate_binary_minimal(source_file, compiler, assembler, linker, objcopy, elfling, libraries, output_file,
                                source_files_additional, interp_needed, args.merge_headers)
        # Now have complete binary, may need to reprocess.
        if elfling:
            output_file_stripped = generate_temporary_filename(output_file + ".stripped")
            output_file_extracted = generate_temporary_filename(output_file + ".extracted")
            elfling.compress(output_file_stripped, output_file_extracted)
            generate_binary_minimal(None, compiler, assembler, linker, objcopy, elfling, libraries, output_file,
                                    source_files_additional, interp_needed, args.merge_headers)
    elif "hash" == compilation_mode:
        output_file_s = generate_temporary_filename(output_file + ".S")
        output_file_final_s = generate_temporary_filename(output_file + ".final.S")
        output_file_o = generate_temporary_filename(output_file + ".o")
        output_file_ld = generate_temporary_filename(output_file + ".ld")
        output_file_unprocessed = generate_temporary_filename(output_file + ".unprocessed")
        compiler.compile_asm(source_file, output_file_s)
        asm = AssemblerFile(output_file_s)
        # asm.sort_sections()
        # asm.remove_rodata()
        asm.write(output_file_final_s, assembler)
        assembler.assemble(output_file_final_s, output_file_o)
        linker.generate_linker_script(output_file_ld)
        linker.set_linker_script(output_file_ld)
        linker.link(output_file_o, output_file_unprocessed)
    elif "dlfcn" == compilation_mode or "vanilla" == compilation_mode:
        output_file_unprocessed = generate_temporary_filename(output_file + ".unprocessed")
        compiler.compile_and_link(source_file, output_file_unprocessed)
    else:
        raise RuntimeError("unknown compilation mode: %s" % str(compilation_mode))
    # Potentially perform last strip, then compress.
    output_file_stripped = generate_temporary_filename(output_file + ".stripped")
    if compilation_mode in ("vanilla", "dlfcn", "hash"):
        strip = executable_find(strip, default_strip_list, "strip")
        shutil.copy(output_file_unprocessed, output_file_stripped)
        run_command([strip, "-K", ".bss", "-K", ".text", "-K", ".data", "-R", ".comment", "-R", ".eh_frame", "-R", ".eh_frame_hdr", "-R", ".fini", "-R", ".gnu.hash", "-R", ".gnu.version", "-R", ".jcr", "-R", ".note", "-R", ".note.ABI-tag", "-R", ".note.tag", output_file_stripped])
    compress_file(compression, filedrop_interp, nice_filedump, output_file_stripped, output_file)

    return 0

########################################
# Entry point ##########################
########################################

if __name__ == "__main__":
    sys.exit(main())
