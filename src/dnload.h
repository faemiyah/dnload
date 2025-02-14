#ifndef DNLOAD_H
#define DNLOAD_H

/// \file
/// \brief Dynamic loader header stub.
///
/// This file was automatically generated by 'dnload.py'.

#if defined(_WIN32) || defined(_WIN64)
/// \cond
#define _USE_MATH_DEFINES
#define NOMINMAX
/// \endcond
#else
/// \cond
#define GL_GLEXT_PROTOTYPES
/// \endcond
#endif

#if defined(__cplusplus)
#include <cstdint>
#else
#include <stdint.h>
#endif

#if defined(DNLOAD_USE_VIDEOCORE)
#include "bcm_host.h"
#include "EGL/egl.h"
#endif

#if defined(DNLOAD_USE_LD)
#if defined(_WIN32) || defined(_WIN64)
#include "windows.h"
#include "GL/glew.h"
#include "GL/glu.h"
#elif defined(__APPLE__)
#include "GL/glew.h"
#include <OpenGL/glu.h>
#else
#if defined(DNLOAD_USE_GLES)
#if DNLOAD_USE_GLES >= 32
#include "GLES3/gl32.h"
#elif DNLOAD_USE_GLES >= 31
#include "GLES3/gl31.h"
#elif DNLOAD_USE_GLES >= 30
#include "GLES3/gl3.h"
#else
#include "GLES2/gl2.h"
#endif
#include "GLES2/gl2ext.h"
#else
#include "GL/glew.h"
#include "GL/glu.h"
#endif
#endif
#else
#if defined(__APPLE__)
#include <OpenGL/gl.h>
#include <OpenGL/glext.h>
#include <OpenGL/glu.h>
#else
#if defined(DNLOAD_USE_GLES)
#include "GLES2/gl2.h"
#include "GLES2/gl2ext.h"
#else
#include "GL/gl.h"
#include "GL/glext.h"
#include "GL/glu.h"
#endif
#endif
#endif

#include "SDL.h"
#if defined(SDL_INIT_EVERYTHING) && defined(__APPLE__)
#define DNLOAD_MAIN SDL_main
#else
#define DNLOAD_MAIN main
#endif

/// Macro stringification helper (adds indirection).
#define DNLOAD_MACRO_STR_HELPER(op) #op
/// Macro stringification.
#define DNLOAD_MACRO_STR(op) DNLOAD_MACRO_STR_HELPER(op)

#if defined(DNLOAD_USE_GLES)
/// Apientry definition (OpenGL ES 2.0).
#define DNLOAD_APIENTRY GL_APIENTRY
#else
/// Apientry definition (OpenGL).
#define DNLOAD_APIENTRY GLAPIENTRY
#endif

#if (defined(_LP64) && _LP64) || (defined(__LP64__) && __LP64__)
/// Size of pointer in bytes (64-bit).
#define DNLOAD_POINTER_SIZE 8
#else
/// Size of pointer in bytes (32-bit).
#define DNLOAD_POINTER_SIZE 4
#endif

#if defined(__cplusplus)
extern "C"
{
#endif

#if !defined(DNLOAD_USE_LD)
/// Error string for when assembler exit procedure is not available.
#define DNLOAD_ASM_EXIT_ERROR "no assembler exit procedure defined for current operating system or architecture"
/// Perform exit syscall in assembler.
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
#endif

#if defined(DNLOAD_USE_LD)
/// \cond
#define dnload_glLinkProgram glLinkProgram
#define dnload_SDL_GL_SetAttribute SDL_GL_SetAttribute
#define dnload_glUniform3fv glUniform3fv
#define dnload_glGetUniformLocation glGetUniformLocation
#define dnload_SDL_GL_SwapWindow SDL_GL_SwapWindow
#define dnload_SDL_PauseAudio SDL_PauseAudio
#define dnload_glAttachShader glAttachShader
#define dnload_SDL_OpenAudio SDL_OpenAudio
#define dnload_SDL_CreateWindow SDL_CreateWindow
#define dnload_SDL_PollEvent SDL_PollEvent
#define dnload_glCreateShader glCreateShader
#define dnload_SDL_Init SDL_Init
#define dnload_glCreateProgram glCreateProgram
#define dnload_SDL_Quit SDL_Quit
#define dnload_SDL_ShowCursor SDL_ShowCursor
#define dnload_glVertexAttribPointer glVertexAttribPointer
#define dnload_glCompileShader glCompileShader
#define dnload_glShaderSource glShaderSource
#define dnload_glDrawArrays glDrawArrays
#define dnload_glUseProgram glUseProgram
#define dnload_SDL_GL_CreateContext SDL_GL_CreateContext
#define dnload_glEnableVertexAttribArray glEnableVertexAttribArray
/// \endcond
#else
/// \cond
#define dnload_glLinkProgram g_symbol_table.df_glLinkProgram
#define dnload_SDL_GL_SetAttribute g_symbol_table.df_SDL_GL_SetAttribute
#define dnload_glUniform3fv g_symbol_table.df_glUniform3fv
#define dnload_glGetUniformLocation g_symbol_table.df_glGetUniformLocation
#define dnload_SDL_GL_SwapWindow g_symbol_table.df_SDL_GL_SwapWindow
#define dnload_SDL_PauseAudio g_symbol_table.df_SDL_PauseAudio
#define dnload_glAttachShader g_symbol_table.df_glAttachShader
#define dnload_SDL_OpenAudio g_symbol_table.df_SDL_OpenAudio
#define dnload_SDL_CreateWindow g_symbol_table.df_SDL_CreateWindow
#define dnload_SDL_PollEvent g_symbol_table.df_SDL_PollEvent
#define dnload_glCreateShader g_symbol_table.df_glCreateShader
#define dnload_SDL_Init g_symbol_table.df_SDL_Init
#define dnload_glCreateProgram g_symbol_table.df_glCreateProgram
#define dnload_SDL_Quit g_symbol_table.df_SDL_Quit
#define dnload_SDL_ShowCursor g_symbol_table.df_SDL_ShowCursor
#define dnload_glVertexAttribPointer g_symbol_table.df_glVertexAttribPointer
#define dnload_glCompileShader g_symbol_table.df_glCompileShader
#define dnload_glShaderSource g_symbol_table.df_glShaderSource
#define dnload_glDrawArrays g_symbol_table.df_glDrawArrays
#define dnload_glUseProgram g_symbol_table.df_glUseProgram
#define dnload_SDL_GL_CreateContext g_symbol_table.df_SDL_GL_CreateContext
#define dnload_glEnableVertexAttribArray g_symbol_table.df_glEnableVertexAttribArray
/// \endcond
/// Symbol table structure.
///
/// Contains all the symbols required for dynamic linking.
static struct SymbolTableStruct
{
    void (DNLOAD_APIENTRY *df_glLinkProgram)(GLuint);
    int (*df_SDL_GL_SetAttribute)(SDL_GLattr, int);
    void (DNLOAD_APIENTRY *df_glUniform3fv)(GLint, GLsizei, const GLfloat*);
    GLint (DNLOAD_APIENTRY *df_glGetUniformLocation)(GLuint, const GLchar*);
    void (*df_SDL_GL_SwapWindow)(SDL_Window*);
    void (*df_SDL_PauseAudio)(int);
    void (DNLOAD_APIENTRY *df_glAttachShader)(GLuint, GLuint);
    int (*df_SDL_OpenAudio)(SDL_AudioSpec*, SDL_AudioSpec*);
    SDL_Window* (*df_SDL_CreateWindow)(const char*, int, int, int, int, Uint32);
    int (*df_SDL_PollEvent)(SDL_Event*);
    GLuint (DNLOAD_APIENTRY *df_glCreateShader)(GLenum);
    int (*df_SDL_Init)(Uint32);
    GLuint (DNLOAD_APIENTRY *df_glCreateProgram)(void);
    void (*df_SDL_Quit)(void);
    int (*df_SDL_ShowCursor)(int);
    void (DNLOAD_APIENTRY *df_glVertexAttribPointer)(GLuint, GLint, GLenum, GLboolean, GLsizei, const GLvoid*);
    void (DNLOAD_APIENTRY *df_glCompileShader)(GLuint);
    void (DNLOAD_APIENTRY *df_glShaderSource)(GLuint, GLsizei, const GLchar**, const GLint*);
    void (DNLOAD_APIENTRY *df_glDrawArrays)(GLenum, GLint, GLsizei);
    void (DNLOAD_APIENTRY *df_glUseProgram)(GLuint);
    SDL_GLContext (*df_SDL_GL_CreateContext)(SDL_Window*);
    void (DNLOAD_APIENTRY *df_glEnableVertexAttribArray)(GLuint);
} g_symbol_table =
{
    (void (DNLOAD_APIENTRY *)(GLuint))0x133a35c5,
    (int (*)(SDL_GLattr, int))0x1da21ab0,
    (void (DNLOAD_APIENTRY *)(GLint, GLsizei, const GLfloat*))0x223459b4,
    (GLint (DNLOAD_APIENTRY *)(GLuint, const GLchar*))0x25c12218,
    (void (*)(SDL_Window*))0x295bfb59,
    (void (*)(int))0x29f14a4,
    (void (DNLOAD_APIENTRY *)(GLuint, GLuint))0x30b3cfcf,
    (int (*)(SDL_AudioSpec*, SDL_AudioSpec*))0x46fd70c8,
    (SDL_Window* (*)(const char*, int, int, int, int, Uint32))0x4fbea370,
    (int (*)(SDL_Event*))0x64949d97,
    (GLuint (DNLOAD_APIENTRY *)(GLenum))0x6b4ffac6,
    (int (*)(Uint32))0x70d6574,
    (GLuint (DNLOAD_APIENTRY *)(void))0x78721c3,
    (void (*)(void))0x7eb657f3,
    (int (*)(int))0xb88bf697,
    (void (DNLOAD_APIENTRY *)(GLuint, GLint, GLenum, GLboolean, GLsizei, const GLvoid*))0xc443174a,
    (void (DNLOAD_APIENTRY *)(GLuint))0xc5165dd3,
    (void (DNLOAD_APIENTRY *)(GLuint, GLsizei, const GLchar**, const GLint*))0xc609c385,
    (void (DNLOAD_APIENTRY *)(GLenum, GLint, GLsizei))0xcb871c63,
    (void (DNLOAD_APIENTRY *)(GLuint))0xcc55bb62,
    (SDL_GLContext (*)(SDL_Window*))0xdba45bd,
    (void (DNLOAD_APIENTRY *)(GLuint))0xe9e99723,
};
#endif

#if defined(DNLOAD_USE_LD)
/// \cond
#define dnload()
/// \endcond
#else
/// SDBM hash function.
///
/// \param op String to hash.
/// \return Full hash.
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
}
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
/// \param dyn Dynamic section.
/// \param tag Tag to look for.
/// \return Pointer to dynamic element.
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
/// \param dyn Dynamic section.
/// \param tag Tag to look for.
/// \return Address matching given tag.
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
/// \return Link map struct.
static const struct link_map* elf_get_link_map()
{
#if defined(DNLOAD_NO_FIXED_R_DEBUG_ADDRESS)
    // ELF header is in a fixed location in memory.
    const void* ELF_BASE_ADDRESS = (const void*)(
#if defined(__arm__)
            0x10000
#elif defined(__i386__)
            0x2000000
#else
#if (8 != DNLOAD_POINTER_SIZE)
#error "no base address known for current platform"
#endif
            0x400000
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
/// \param lmap Link map.
/// \param ptr Pointer in this link map.
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
/// \param lmap Link map.
/// \param tag Tag to look for.
/// \return Pointer to given section or NULL.
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
/// \param hash Hash of the function name string.
/// \return Symbol found.
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
    for(ii = 0; (22 > ii); ++ii)
    {
        void **iter = ((void**)&g_symbol_table) + ii;
        *iter = dnload_find_symbol(*(uint32_t*)iter);
    }
}
#endif

#if defined(__clang__)
/// Visibility declaration for symbols that require it (clang).
#define DNLOAD_VISIBILITY __attribute__((visibility("default")))
#else
/// Visibility declaration for symbols that require it (gcc).
#define DNLOAD_VISIBILITY __attribute__((externally_visible,visibility("default")))
#endif

#if !defined(DNLOAD_USE_LD)
/// Program entry point.
void _start() DNLOAD_VISIBILITY;
#endif

#if defined(__cplusplus)
}
#endif

#endif