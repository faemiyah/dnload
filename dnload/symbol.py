from dnload.common import is_verbose
from dnload.platform_var import PlatformVar
from dnload.template import Template

########################################
# Symbol ###############################
########################################

class Symbol:
    """Represents one (function) symbol."""

    def __init__(self, lst, lib):
        """Constructor."""
        self.__returntype = lst[0]
        if isinstance(lst[1], (list, tuple)):
            self.__name = lst[1][0]
            self.__rename = lst[1][1]
        else:
            self.__name = lst[1]
            self.__rename = lst[1]
        self.__symbol_table_name = "df_" + self.__name
        self.__parameters = None
        if 2 < len(lst):
            self.__parameters = lst[2:]
        self.__library = lib

    def create_replacement(self, lib):
        """Create replacement symbol for another library."""
        lst = [self.__returntype, (self.__name, self.__rename)]
        if self.__parameters:
            lst += self.__parameters
        return Symbol(lst, lib)

    def generate_definition(self):
        """Get function definition for given symbol."""
        apientry = ""
        if self.__name[:2] == "gl":
            apientry = "DNLOAD_APIENTRY "
        params = "void"
        if self.__parameters:
            params = ", ".join(self.__parameters)
        return "%s (%s*%s)(%s)" % (self.__returntype, apientry, self.__symbol_table_name, params)

    def generate_prototype(self):
        """Get function prototype for given symbol."""
        apientry = ""
        if self.__name[:2] == "gl":
            apientry = "DNLOAD_APIENTRY "
        params = "void"
        if self.__parameters:
            params = ", ".join(self.__parameters)
        return "(%s (%s*)(%s))" % (self.__returntype, apientry, params)

    def generate_rename_direct(self, prefix):
        """Generate definition to use without a symbol table."""
        if self.is_verbatim():
            return self.generate_rename_verbatim(prefix)
        return "#define %s%s %s" % (prefix, self.__name, self.__rename)

    def generate_rename_tabled(self, prefix):
        """Generate definition to use with a symbol table."""
        if self.is_verbatim():
            return self.generate_rename_verbatim(prefix)
        return "#define %s%s g_symbol_table.%s" % (prefix, self.__name, self.__symbol_table_name)

    def generate_rename_verbatim(self, prefix):
        """Generate 'rename' into itself. Used for functions that are inlined by linker."""
        return "#define %s%s %s" % (prefix, self.__name, self.__name)

    def get_hash(self, hash_function):
        """Get the hash of symbol name."""
        if hash_function == "crc32":
            return hash_crc32(self.__name)
        elif hash_function == "sdbm":
            return hash_sdbm(self.__name)
        raise RuntimeError("cannot hash function name '%s': unknown hash function '%s'" % (self.__name, hash_function))

    def get_library(self):
        """Access library reference."""
        return self.__library

    def get_library_name(self, linker):
        """Get linkable library object name."""
        libname = linker.get_library_name(self.__library.get_name())
        if libname != self.__library.get_name() and is_verbose():
            print("Using shared library '%s' instead of '%s'." % (str(libname), self.__library.get_name()))
        return libname

    def get_name(self):
        """Accessor."""
        return self.__name

    def is_verbatim(self):
        """Tell if this symbol should never be scoured but instead used verbatim."""
        return (self.__rename is None)

    def set_library(self, lib):
        """Replace library with given library."""
        self.__library = lib

    def __lt__(self, rhs):
        """Sorting operator."""
        if self.__library.get_name() < rhs.__library.get_name():
            return True
        elif self.__library.get_name() > rhs.__library.get_name():
            return False
        return self.__name < rhs.__name

    def __str__(self):
        """String representation."""
        return self.__name

########################################
# Globals ##############################
########################################

g_template_loader_dlfcn = Template("""#include <dlfcn.h>
static const char g_dynstr[] = \"\"
[[DLFCN_STRING]];
/// Perform init.
///
/// dlopen/dlsym -style.
static void dnload(void)
{
    char *src = (char*)g_dynstr;
    void **dst = (void**)&g_symbol_table;
    do {
        void *handle = dlopen(src, RTLD_LAZY);
        for(;;)
        {
            while(*(src++));
            if(!*(src))
            {
                break;
            }
            *dst++ = dlsym(handle, src);
        }
    } while(*(++src));
}""")

g_template_hash_function_crc32 = Template("""/// CRC32 hash function.
///
/// \\param op String to hash.
/// \\return Full hash.
static uint32_t dnload_hash(const uint8_t *op)
{
    uint32_t ret = 0;
    for(;;)
    {
        uint32_t cc = *op++;
        if(!cc)
        {
            return ret;
        }
        ret = __builtin_ia32_crc32qi(ret, cc);
    }
}""")

g_template_hash_function_sdbm = Template("""/// SDBM hash function.
///
/// \\param op String to hash.
/// \\return Full hash.
static uint32_t dnload_hash(const uint8_t *op)
{
    uint32_t ret = 0;
    for(;;)
    {
        uint32_t cc = *op++;
        if(!cc)
        {
            return ret;
        }
        ret = ret * 65599 + cc;
    }
}""")

g_template_loader_hash = Template("""[[HASH_FUNCTION]]
#if defined(__FreeBSD__)
#include <sys/link_elf.h>
#elif defined(__linux__)
#include <link.h>
#else
#error "no elf header location known for current platform"
#endif
#if (8 == DNLOAD_POINTER_SIZE)
/// Elf header type.
typedef Elf64_Ehdr dnload_elf_ehdr_t;
/// Elf program header type.
typedef Elf64_Phdr dnload_elf_phdr_t;
/// Elf dynamic structure type.
typedef Elf64_Dyn dnload_elf_dyn_t;
/// Elf symbol table entry type.
typedef Elf64_Sym dnload_elf_sym_t;
/// Elf dynamic structure tag type.
typedef Elf64_Sxword dnload_elf_tag_t;
#else
/// Elf header type.
typedef Elf32_Ehdr dnload_elf_ehdr_t;
/// Elf program header type.
typedef Elf32_Phdr dnload_elf_phdr_t;
/// Elf dynamic structure type.
typedef Elf32_Dyn dnload_elf_dyn_t;
/// Elf symbol table entry type.
typedef Elf32_Sym dnload_elf_sym_t;
/// Elf dynamic structure tag type.
typedef Elf32_Sword dnload_elf_tag_t;
#endif
/// Get dynamic section element by tag.
///
/// \\param dyn Dynamic section.
/// \\param tag Tag to look for.
/// \\return Pointer to dynamic element.
static const dnload_elf_dyn_t* elf_get_dynamic_element_by_tag(const void *dyn, dnload_elf_tag_t tag)
{
    const dnload_elf_dyn_t *dynamic = (const dnload_elf_dyn_t*)dyn;
    do {
        ++dynamic; // First entry in PT_DYNAMIC is probably nothing important.
    } while(dynamic->d_tag != tag);
    return dynamic;
}
#if defined(DNLOAD_NO_FIXED_R_DEBUG_ADDRESS) || defined(DNLOAD_SAFE_SYMTAB_HANDLING)
/// Get the address associated with given tag in a dynamic section.
///
/// \\param dyn Dynamic section.
/// \\param tag Tag to look for.
/// \\return Address matching given tag.
static const void* elf_get_dynamic_address_by_tag(const void *dyn, dnload_elf_tag_t tag)
{
    const dnload_elf_dyn_t *dynamic = elf_get_dynamic_element_by_tag(dyn, tag);
    return (const void*)dynamic->d_un.d_ptr;
}
#endif
#if !defined(DNLOAD_NO_FIXED_R_DEBUG_ADDRESS)
/// Link map address, fixed location in ELF headers.
extern const struct r_debug *dynamic_r_debug __attribute__((aligned(1)));
#endif
/// Get the program link map.
///
/// \\return Link map struct.
static const struct link_map* elf_get_link_map()
{
#if defined(DNLOAD_NO_FIXED_R_DEBUG_ADDRESS)
    // ELF header is in a fixed location in memory.
    const void* ELF_BASE_ADDRESS = (const void*)(
#if defined(__arm__)
            [[BASE_ADDRESS_ARM32L]]
#elif defined(__i386__)
            [[BASE_ADDRESS_IA32]]
#else
#if (8 != DNLOAD_POINTER_SIZE)
#error "no base address known for current platform"
#endif
            [[BASE_ADDRESS_64BIT]]
#endif
            );
    // First program header is located directly afterwards.
    const dnload_elf_ehdr_t *ehdr = (const dnload_elf_ehdr_t*)ELF_BASE_ADDRESS;
    const dnload_elf_phdr_t *phdr = (const dnload_elf_phdr_t*)((size_t)ehdr + (size_t)ehdr->e_phoff);
    do {
        ++phdr; // Dynamic header is probably never first in PHDR list.
    } while(phdr->p_type != PT_DYNAMIC);
    // Find the debug entry in the dynamic header array.
    {
        const struct r_debug *debug = (const struct r_debug*)elf_get_dynamic_address_by_tag((const void*)phdr->p_vaddr, DT_DEBUG);
        return debug->r_map;
    }
#else
    return dynamic_r_debug->r_map;
#endif
}
/// Return pointer from link map address.
///
/// \\param lmap Link map.
/// \\param ptr Pointer in this link map.
static const void* elf_transform_dynamic_address(const struct link_map *lmap, const void *ptr)
{
#if defined(__linux__)
    // Addresses may also be absolute.
    if(ptr >= (void*)(size_t)lmap->l_addr)
    {
        return ptr;
    }
#endif
    return (uint8_t*)ptr + (size_t)lmap->l_addr;
}
#if defined(DNLOAD_SAFE_SYMTAB_HANDLING)
/// Get address of one dynamic section corresponding to given library.
///
/// \\param lmap Link map.
/// \\param tag Tag to look for.
/// \\return Pointer to given section or NULL.
static const void* elf_get_library_dynamic_section(const struct link_map *lmap, dnload_elf_tag_t tag)
{
    const void* ptr = elf_get_dynamic_address_by_tag((const dnload_elf_dyn_t*)(lmap->l_ld), tag);
    return elf_transform_dynamic_address(lmap, ptr);
}
#endif
/// Find a symbol in any of the link maps.
///
/// Should a symbol with name matching the given hash not be present, this function will happily continue until
/// we crash. Size-minimal code has no room for error checking.
///
/// \\param hash Hash of the function name string.
/// \\return Symbol found.
static void* dnload_find_symbol(uint32_t hash)
{
    const struct link_map* lmap = elf_get_link_map();
#if defined(__linux__) && (8 == DNLOAD_POINTER_SIZE)
    // On 64-bit Linux, the second entry is not usable.
    lmap = lmap->l_next;
#endif
    for(;;)
    {
        // First entry is this object itself, safe to advance first.
        lmap = lmap->l_next;
        {
#if defined(DNLOAD_SAFE_SYMTAB_HANDLING)
            const dnload_elf_sym_t* symtab = (const dnload_elf_sym_t*)elf_get_library_dynamic_section(lmap, DT_SYMTAB);
            const char* strtab = (char*)elf_get_library_dynamic_section(lmap, DT_STRTAB);
            const dnload_elf_sym_t* symtab_end = (const dnload_elf_sym_t*)strtab;
            // If the section immediately following SYMTAB is not STRTAB, it may be something else.
            {
                const dnload_elf_sym_t *potential_end = (const dnload_elf_sym_t*)elf_get_library_dynamic_section(lmap, DT_VERSYM);
                if(potential_end < symtab_end)
                {
                    symtab_end = potential_end;
                }
            }
#else
            // Assume DT_SYMTAB dynamic entry immediately follows DT_STRTAB dynamic entry.
            // Assume DT_STRTAB memory block immediately follows DT_SYMTAB dynamic entry.
            const dnload_elf_dyn_t *dynamic = elf_get_dynamic_element_by_tag(lmap->l_ld, DT_STRTAB);
            const char* strtab = (const char*)elf_transform_dynamic_address(lmap, (const void*)(dynamic->d_un.d_ptr));
            const dnload_elf_sym_t *symtab_end = (const dnload_elf_sym_t*)strtab;
            ++dynamic;
            const dnload_elf_sym_t *symtab = (const dnload_elf_sym_t*)elf_transform_dynamic_address(lmap, (const void*)(dynamic->d_un.d_ptr));
#endif
            for(const dnload_elf_sym_t *sym = symtab; (sym < symtab_end); ++sym)
            {
                const char *name = strtab + sym->st_name;
                if(dnload_hash((const uint8_t*)name) == hash)
                {
                    void* ret_addr = (void*)((const uint8_t*)sym->st_value + (size_t)lmap->l_addr);
#if defined(__linux__) && (defined(__aarch64__) || defined(__i386__) || defined(__x86_64__))
                    // On Linux and various architectures, need to check for IFUNC.
                    if((sym->st_info & 15) == STT_GNU_IFUNC)
                    {
                        ret_addr = ((void*(*)())ret_addr)();
                    }
#endif
                    return ret_addr;
                }
            }
        }
    }
}
/// Perform init.
///
/// Import by hash - style.
static void dnload(void)
{
    unsigned ii;
    for(ii = 0; ([[SYMBOL_COUNT]] > ii); ++ii)
    {
        void **iter = ((void**)&g_symbol_table) + ii;
        *iter = dnload_find_symbol(*(uint32_t*)iter);
    }
}""")

g_template_loader_vanilla = Template("""/// \\cond
#define dnload()
/// \\endcond""")

g_template_symbol_table = Template("""
/// Symbol table structure.
///
/// Contains all the symbols required for dynamic linking.
static struct SymbolTableStruct
{
[[SYMBOL_TABLE_DEFINITION]]
} g_symbol_table[[SYMBOL_TABLE_INITIALIZATION]];""")

########################################
# Functions ############################
########################################

def generate_loader_vanilla():
    """Generate vanilla loader."""
    return g_template_loader_vanilla.format()

def generate_loader_dlfcn(symbols, linker):
    """Generate dlopen/dlsym loader code."""
    dlfcn_string = ""
    current_lib = None
    for ii in symbols:
        symbol_lib = ii.get_library().get_name()
        if current_lib != symbol_lib:
            if current_lib:
                dlfcn_string += "\"\\0%s\\0\"\n" % (ii.get_library_name(linker))
            else:
                dlfcn_string += "\"%s\\0\"\n" % (ii.get_library_name(linker))
            current_lib = symbol_lib
        dlfcn_string += "\"%s\\0\"\n" % (ii)
    subst = {"DLFCN_STRING": dlfcn_string + "\"\\0\""}
    return g_template_loader_dlfcn.format(subst)

def generate_loader_hash(symbols, hash_function):
    """Generate import by hash loader code."""
    subst = {
            "BASE_ADDRESS_64BIT": str(PlatformVar("entry", "", "64-bit")),
            "BASE_ADDRESS_ARM32L": str(PlatformVar("entry", "", "arm32l")),
            "BASE_ADDRESS_IA32": str(PlatformVar("entry", "", "ia32")),
            "SYMBOL_COUNT": str(len(symbols)),
            }
    if hash_function == "crc32":
        subst["HASH_FUNCTION"] = g_template_hash_function_crc32.format()
    elif hash_function == "sdbm":
        subst["HASH_FUNCTION"] = g_template_hash_function_sdbm.format()
    else:
        raise RuntimeError("unknown hash function: '%s'" % (hash_function))
    return g_template_loader_hash.format(subst)

def generate_symbol_definitions_direct(symbols, prefix):
    """Generate a listing of definitions to point to real symbols."""
    ret = []
    for ii in symbols:
        ret += [ii.generate_rename_direct(prefix)]
    return "\n".join(ret)

def generate_symbol_definitions_table(symbols, prefix):
    """Generate a listing of symbol definitions for symbol table."""
    ret = []
    for ii in symbols:
        ret += [ii.generate_rename_tabled(prefix)]
    return "\n".join(ret)

def generate_symbol_table(mode, symbols, hash_function):
    """Generate the symbol struct definition."""
    definitions = []
    hashes = []
    subst = {}
    symbol_table_content = ""
    for ii in symbols:
        definitions += ["    %s;" % (ii.generate_definition())]
        hashes += ["    %s%s," % (ii.generate_prototype(), ii.get_hash(hash_function))]
    if "dlfcn" != mode:
        subst["SYMBOL_TABLE_INITIALIZATION"] = " =\n{\n%s\n}" % ("\n".join(hashes))
    subst["SYMBOL_TABLE_DEFINITION"] = "\n".join(definitions)
    return g_template_symbol_table.format(subst)

def str_xor(lhs, rhs):
    """Calculate xor for binary strings."""
    if len(lhs) != len(rhs):
        raise RuntimeError("XOR strings '%s' and '%s' are not of same length")
    ret = ""
    for ii, jj in zip(lhs, rhs):
        if ii == jj:
            ret += "0"
        else:
            ret += "1"
    return ret

def str_mod2_rem(lhs, rhs):
    """Calculate remainder modulo 2 for binary strings."""
    if len(lhs) < len(rhs):
        raise RuntimeError("MOD2 strings '%s' and '%s' are not of same length")
    while True:
        diff = len(lhs) - len(rhs)
        if lhs[0] != "0":
            lhs = str_xor(lhs, rhs + ("0" * diff))[1:]
        else:
            lhs = lhs[1:]
        if diff <= 0:
            break
    return lhs

def hash_crc32(name):
    """Calculate CRC32 hash over a string."""
    #CRC32 instruction for 8-bit source operand and 32-bit destination operand:
    #TEMP1[7-0] ← BIT_REFLECT8(SRC[7-0])
    #TEMP2[31-0]←BIT_REFLECT32 (DEST[31-0])
    #TEMP3[39-0]←TEMP1[7-0] « 32
    #TEMP4[39-0]←TEMP2[31-0] « 8
    #TEMP5[39-0]←TEMP3[39-0] XOR TEMP4[39-0]
    #TEMP6[31-0]←TEMP5[39-0] MOD2 11EDC6F41H
    #DEST[31-0]←BIT_REFLECT (TEMP6[31-0])
    ret = 0
    for ii in name:
        tmp1 = format(ord(ii), 'b')
        tmp2 = format(ret, 'b')
        tmp3 = (("0" * (8 - len(tmp1))) + tmp1)[::-1] + ("0" * 32)
        tmp4 = (("0" * (32 - len(tmp2))) + tmp2)[::-1] + ("0" * 8)
        tmp5 = str_xor(tmp3, tmp4)
        tmp6 = str_mod2_rem(tmp5, format(0x11EDC6F41, 'b'))
        ret = int((tmp6[-32:])[::-1], 2)
    return "0x%x" % (ret)

def hash_sdbm(name):
    """Calculate SDBM hash over a string."""
    ret = 0
    for ii in name:
        ret = (ret * 65599 + ord(ii)) & 0xFFFFFFFF
    return "0x%x" % (ret)
