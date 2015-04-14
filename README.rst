########
 dnload
########
------------------------------------------------------
 Minimal binary generator for \*nix operating systems
------------------------------------------------------

.. contents::
    :depth: 3

dnload.py
=========

``dnload.py`` is a script for generating minimal ELF binaries from C code. It serves no practical real-world use case, but can be utilized to aid in the creation of size-limited demoscene productions.

System requirements
===================

The bridging header file can be created on any \*nix or Windows platform with an up-to-date Python installation and a suitable compiler.

Generating a final binary is supported on \*nix platforms only. Due to practical purposes (i.e. the OS of choice of the author), the primary target operating system is FreeBSD. Existence of binutils toolchain (``as``, ``ld``, etc.) on the system is assumed.

The script is self-contained, and should require no external python packages to be installed. Both Python versions 2.7.x and 3.x should work.

For compiling without size optimizations, GLEW and SDL development files are needed. This is subject to change if/when other backends are added.

**Note:** Cross-compilation is not (yet?) supported. Building of binaries must be done on the actual target system. If you want to develop 32-bit software on a 64-bit system, you will need to set up a chroot/jail environment or a virtual machine.

Supported operating systems (for binary compilation)
----------------------------------------------------

* ``FreeBSD``
* ``Linux``
* ``Windows`` (for preprocessing only)

Supported architectures
-----------------------

* ``amd64`` (x86_64)
* ``ia32`` (i386)

Supported compilers
-------------------

* ``clang++``
* ``cl.exe`` (for preprocessing only)
* ``g++``

Usage
=====

The script is used for two purposes:

* Building size-limited binaries directly from C/C++ source on systems,
  where compilation is supported.
* Generating a header file to hide the complexities of size-limited linking. 
  This can be also be on systems where compilation is not supported. The 
  main use of this feature is to allow demo developers to work on other 
  platforms except the main targets. The generated header tries to preserve 
  portability.

Summary of operation
--------------------

When invoked, the script will:

* Probe for suitable compiler, usually `gcc` or `clang`, `cl.exe` on Windows.
* Search for header file it was supposed to generate. By default this is 
  called `dnload.h`.
* Examine the location the header file was found in. If a source file was 
  given on command line, only operate on it. Otherwise take all source files 
  from this location.
* Preprocess the source files with the compiler found earlier.
* Examine preprocessor output and locate all function calls made with a 
  specific prefix. By default this prefix is ``dnload_``.
* Generate a loader code block that locates pointers to given functions.
* Write the header file.

If the script was invoked to additionally generate the binary:

* Search for usual binary utilities in addition to the compiler.
* Compile given source file with flags aiming for small code footprint.
* Perform a series on operations on the compiler output known to further 
  reduce code footprint.
* Link an output binary.
* Possibly strip the generated binary.
* Compress the produced binary and concatenate it with a shell script that 
  will decompress and execute it.

Example program
---------------

To understand how to use the script, a simple example will clarify the operation with more ease than any lengthy explanation would. This tutorial will cover a traditional hello world program.

Use this command to clone the repository::

    svn checkout http://faemiyah-demoscene.googlecode.com/svn/trunk/dnload

The checked out repository will have the ``dnload.py`` script in the root folder. The minimal example is included in the ``src/`` folder and called ``hello_world.cpp``. The example looks like this (removing non-essential comments)::

    #include "dnload.h"

    #if defined(USE_LD)
    int main()
    #else
    void _start()
    #endif
    {
      dnload();
      dnload_puts("Hello World!");
    #if defined(USE_LD)
      return 0;
    #else
      asm_exit();
    #endif
    }

When beginning to work with a project, the first thing needed is to ensure that our header is up to date. To do this, run::

    python dnload.py src/hello_world.cpp -v

This should produce output somewhat akin to this::

    Header file 'dnload.h' found in path 'src/'.
    Trying binary 'g++49'... found
    Trying binary 'sdl-config'... found
    Executing command: sdl-config --cflags
    Analyzing source file 'src/hello_world.cpp'.
    Executing command: g++49 src/hello_world.cpp -D_GNU_SOURCE=1 -D_REENTRANT -D_THREAD_SAFE -DDNLOAD_H -I/usr/local/include -I/usr/local/include/SDL -E
    Symbols found: ['puts']
    Wrote header file 'src/dnload.h'.

You should now have an up-to date header file, which can be used to build the program. You may take a look at the contents of the header, but it will be explained in detail [#The_quest_for_minimal_ELF_binaries later on].

Building the example without size optimizations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Even when developing an intro, the programmer is hardly interested in building a size-optimized binary every time. For this purpose, everything in the generated header file is wrapped to compile-time guards that allow us to compile the program as normal from Makefiles, Autotools scripts, CMake or even Visual Studio projects.

To do this, we need to set the ``USE_LD`` flag, for example by (replace with your favorite compiler)::

    > clang++ -o src/hello_world src/hello_world.cpp -DUSE_LD -I/usr/local/include `sdl-config --cflags` -O2 -s && ./src/hello_world
Hello World!

**Note:** The include directory and invoking sdl-config are currently necessary since SDL backend is what will be included by the generated headers.

When ``USE_LD`` is turned on, all "tricks" will essentially evaluate to NOP, and all calls made with the reserved ``dnload_`` prefix will simply call the functions as normal.

Compiling the example as a size-optimized binary
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To invoke the script and perform full compilation, use::

    python dnload.py -v src/hello_world.cpp -o hello_world -lc

You might notice the flags are similar to the conventions used in other binary utilities. This is intentional. The command should produce output somewhat similar to this::

    Header file 'dnload.h' found in path 'src/'.
    Trying binary 'g++49'... found
    Trying binary 'sdl-config'... found
    Executing command: sdl-config --cflags
    Trying binary '/usr/local/bin/as'... found
    Trying binary '/usr/local/bin/ld'... found
    Trying binary '/usr/local/bin/strip'... found
    Analyzing source file 'src/hello_world.cpp'.
    Executing command: g++49 src/hello_world.cpp -D_GNU_SOURCE=1 -D_REENTRANT -D_THREAD_SAFE -DDNLOAD_H -I/usr/local/include -I/usr/local/include/SDL -E
    Symbols found: ['puts']
    Wrote header file 'src/dnload.h'.
    Using output file 'src/hello_world' after source file 'src/hello_world.cpp'.
    Linking against libraries: ['c']
    Executing command: g++49 -S src/hello_world.cpp -o src/hello_world.S -Os -ffast-math -fno-asynchronous-unwind-tables -fno-exceptions -fno-rtti -fno-threadsafe-statics -fomit-frame-pointer -fsingle-precision-constant -fwhole-program -march=pentium4 -mpreferred-stack-boundary=2 -Wall -D_GNU_SOURCE=1 -D_REENTRANT -D_THREAD_SAFE -I/usr/local/include -I/usr/local/include/SDL
    Checking for required UND symbols... ['__progname', 'environ']
    Using shared library 'libc.so.7' instead of 'libc.so'.
    Read 5 sections in 'src/hello_world.S': text, rodata, text, text, note
    Erasing function header from '_start': 5 lines
    Erasing function footer after interrupt '0x3': 9 lines.
    Replacing 4-byte alignment with 1-byte alignment.
    Constructed fake .bss segement: 0 bytes, one PT_LOAD sufficient
    Merging headers phdr_dynamic and hash at 4 bytes.
    Merging headers hash and dynamic at 4 bytes.
    Merging headers dynamic and symtab at 15 bytes.
    Merging headers interp and strtab at 1 bytes.
    Size of headers: 245 bytes
    Wrote assembler source 'src/hello_world.combined.S'.
    Executing command: /usr/local/bin/as src/hello_world.combined.S -o src/hello_world.o
    Executing command: /usr/local/bin/ld --verbose
    Wrote linker script 'src/hello_world.ld'.
    Executing command: /usr/local/bin/ld --oformat=binary --entry=0x2000000 src/hello_world.o -o src/hello_world.unprocessed -T src/hello_world.ld
    Executing command: readelf --file-header --program-headers src/hello_world.unprocessed
    Executable size equals PT_LOAD size (411 bytes), no truncation necessary.
    Executing command: xz --format=lzma --lzma1=preset=9e,lc=1,lp=0,pb=0 --stdout src/hello_world.stripped
    Wrote 'src/hello_world': 321 bytes

The actual program output should be::

    > ./src/hello_world
    Hello World!

Including dnload into your project
----------------------------------

First of all, all programs wanting to use the loader will have to include the generated header file::

    #include "dnload.h"

This will internally include the relevant loader and some other header(s) present in the `src/` subdirectory into the project. The user may of course include any other source files necessary, but all function calls should be done through the interface wrapped herein.

To understand what the script does, we will look at the main function::

    #if defined(USE_LD)
    int main()
    #else
    void _start()
    #endif
    {
      dnload();
      dnload_puts("Hello World!");
    #if defined(USE_LD)
      return 0;
    #else
      asm_exit();
    #endif
    }

If the macro ``USE_LD`` would be defined, all this would simply evaluate to a self-explanatory hello world program::

    int main()
    {
      puts("Hello World!")
      return 0;
    }

If ``USE_LD`` is not defined, the program instead uses an entry point named ``_start``. This is because even if using ``main()`` normally, it is not the real entry point into the program. In practice, the linker will generate code that will perform initialization of global variables, environment, etc., and only afterwards pass the control to the main function created by the programmer. The actual entry point generated by the compiler/linker system is traditionally called ``_start``. Since we're aiming for a small binary, we will not be using any automatically generated entry point code, and declare it ourselves.

The two first lines of main function comprise the actual program::

    dnload();
    dnload_puts("Hello World!");

This will perform of dynamic loading of all required symbols (here: only ``puts``) and call the appropriate function pointer. After saying our hellos, the only thing left to do is to exit the program::

    #if defined(USE_LD)
      return 0;
    #else
      asm_exit();
    #endif

Since we already abandoned the default ``main`` procedure, no-one is going to terminate our program. We could make it "return" but that would normally only pass control to the shell provided by the system, we now have nowhere to return to. Thus, we must make a system call [Ref11]_ to terminate the program ourselves. The code that will do this is written into the `dnload header`_ directly as inline assembler. On i386 architecture, it will evaluate into the following single instruction::

    int $3

Note that this is not the traditional exit system call. Instead, it's a trap [ref30]_ that will break into debugger or exit the program if a debugger is not available. It has the advantage of taking less space than moving ``$1`` into ``eax`` and executing a normal ``int $128`` system call. The return value for the program is irrelevant, as the decompressor shell script the program is eventually wrapped in would eventually mask it anyway.

Advanced examples
-----------------

The ``src/`` folder contains two other examples: ``quad.cpp`` and ``intro.cpp``. The quad example will simply open a coder-colored window, whereas the intro example performs (extremely primitive) raycasting and outputs 8-bit music (from very short programs) for a couple of seconds. The intro example can also be compiled with CMake for a interactive program with a 'debug mode'. To compile this, run (you will need Boost, GLEW, libPNG, OpenGL and SDL)::

    cmake . && make clean all && ./src/intro -d -w

This should open a window allowing mouse pan and WASD movement.
You can size-optimize the program with::

    python dnload.py -c src/intro.cpp -lGL -lSDL -v

Have fun!

The quest for minimal ELF binaries
==================================

This section of the documentation explores both the current and historical methods of reducing executable file size on \*nix systems. If you are only interested in the current "best practice" operation of the script, you can skip to `Current compression procedure`_.

Compiler flags
--------------

We can alter the compiler output to produce smaller binaries both by making it actually optimize for size and by altering the output to be more compressable. The command line options would fall into three categories:

* Options that decrease size of generated code or constants.
* Options that (either randomly or unintentionally) produce a smaller or 
  better compressable binary.
* Options that disable language features, making output smaller.

Despite Clang being all the rage nowadays, gcc seems to still produce binaries that size-optimize better. In particular, the script will attempt to use whichever ``g++`` is currently the latest available on FreeBSD (``g++49`` at the time of writing).

**Note:** Any compiler may be specified with the ``-C`` or ``--compiler`` command line option, but compilation is currently only supported with ``gcc`` or ``clang``. ``cl.exe`` may be used to generate the header in Windows.

Using g++, the flags of the first type (just smaller) would be:

* ``-Os``
* ``-ffast-math``
* ``-fomit-frame-pointer``
* ``-fsingle-precision-constant``
* ``-fwhole-program``

These are all self-explanatory. In general, mere ``-Os -ffast-math -fomit-frame-pointer`` seems to do an excellent job.

The following options are of the second type, seeming to consistently produce code that compresses better:

* ``-march=<arch>``: Some subsets of the instruction set seem to yield 
  better results. As an example, on i386 architecture, after permutating
  through all available instruction sets with several different intros, 
  Pentium 4 was usually the best choice.
* ``-mpreferred-stack-boundary=<align>``: Forces the compiler to attempt 
  keeping the stack aligned at 2\^\<align\> bytes. It seems it's 
  advantageous to keep this at the smallest possible value for any given 
  architecture.

Some flags of the third type, which disable fancy language features, are:

* ``-fno-threadsafe-statics``: By default some code is generated to ensure 
  thread-safe initialization of local static variables. This code seems to
  get generated even if no statics actually exist.
* ``-fno-asynchronous-unwind-tables``: Disables generation of stack unwind 
  information that could be used to debug stack contents at locations other
  than at the function call boundary.
* ``-fno-exceptions``: Self-evident.
* ``-fno-rtti``: Self-evident.

**Note:** One could ask why C++ to begin with if we're not using any of its features? The answer is, that it should never be detrimental. After manually disabling all the features that would increase code footprint, we can basically write C using a C++ compiler. In some cases the C++ syntax will be beneficial.

The self-dumping shell script
-----------------------------

Scouring old releases, the first instance of a \*nix 4k using a self-dumping shell script seems to be *helsinki-spiegelberg* by **tsygä** [ref12]_. However, instead of dumping an executable binary, this entry actually unpacks to a source and compiles before execution.

There are some other variants afterwards, but the first use of the modern one-line filedump is found in *Yellow Rose of Texas* by **Fit & Bandwagon** [ref13]_. Consequently, this is also the first "big" Linux 4k intro.

The concept of self-dumping shell script is to have the first n bytes of a file be plain text that will be executed by normal ``sh``-compatible shells. The shell code will:

* Extract the rest of the file using common `*`nix tools (the compressed 
  data starts immediately after the script).
* Write the extracted data as a file into system temporary folder.
* Make the file executable.
* Run it.
* Remove the file after program exits, since that's the proper thing to do.

The header in *Yellow Rose* looks like this::

    dd bs=1 skip=83<$0|gunzip>/tmp/T;cd /tmp;chmod +x T;__GL_FSAA_MODE=4 ./T;rm T;exit

There are multiple programs that crunch classic gzip files to as small sizes as possible, but modern \*nix systems come with better compressors and better tricks. For example, using a trick from *ts/TDA* [ref27]_, redefining HOME allows using the tilde character for clever reduction::

    HOME=/tmp/i;tail -n+2 $0|lzcat>~;chmod +x ~;~;rm ~;exit

This unpack header has gone to 57 bytes (newline for `tail` is needed at the end) from the 66 needed by Marq, but it's still unnecessarily large as it's trying to be nice. If we omit removing the extracted file and allow the compressed garble to flood the screen, we can do the same in 44 bytes::

    HOME=/tmp/i;sed 1d $0|lzcat>~;chmod +x ~;~

One could assume that ``xz`` format would be more advantageous than the earlier `lzma`, but this seems not to be the case as `lzma` compression headers are smaller [ref28]_ [ref29]_.

We use the `xz` toolkit, however, as it allows free customization of the compression parameters. For actual compression parameters, which yields decent results, we use::

    xz --format=lzma --lzma1=preset=9e,lc=1,lp=0,pb=0

At least on our bruteforced tests, this seems to consistently yield the best results for binaries aiming to the 4k threshold.

For academic interest, the script can create its output using nothing besides the unpack header trick. To do this, use the command line flag ``-m vanilla`` (as in ``--method``). This yields us the baseline whencefrom we begin our quest for smaller binaries::

    'src/hello_world.stripped': 1396 bytes
    'src/hello_world': 625 bytes
    'src/intro.stripped': 5048 bytes
    'src/intro': 1629 bytes

**Note:** Unless otherwise mentioned, all sizes, code excerpts and implementation details in this chapter refer to ``FreeBSD-ia32``, which was the original supported platform.

The "stripped" binaries listed above are generated by just removing all non-needed sections from output binaries. These include ``.comment``, ``.eh_frame``, ``.eh_frame_hdr``, ``.fini``, ``.gnu.hash``, ``.gnu.version``, ``.jcr``, ``.note``, ``.note.ABI-tag`` and ``.note.tag``. Using the compiler/linker ``-s`` flag seems to leave some of these in, so ``strip`` is called manually afterwards.

My symbol table is too big - dlopen/dlsym
-----------------------------------------

Besides the modern unpack header, *Yellow Rose* also introduced the concept of using POSIX ``dlopen`` [ref14]_ and ``dlsym`` [ref15]_ to load the OpenGL functions it required.

This is relevant, because the symbol tables consume quite a lot of space. Taking a look into the FreeBSD system headers [ref17]_ we can examine the symbol structs (going into ``.dynsym``)::

    typedef struct {
      Elf32_Word st_name;      /* String table index of name. */
      Elf32_Addr st_value;     /* Symbol value. */
      Elf32_Word st_size;      /* Size of associated object. */
      unsigned char st_info;   /* Type and binding information. */
      unsigned char st_other;  /* Reserved (not used). */
      Elf32_Half st_shndx;     /* Section index of symbol. */
    } Elf32_Sym;

This is 16 bytes per symbol. In addition the linker will generate linkage tables (going into ``.plt``), which seem to be at least 2 instructions per symbol (look at *Prodedure Linkage Table* in the ELF specification part 2 [ref16]_). Global Offset Table adds 4 bytes each. In any case, we're talking roughly 30 bytes per symbol. Not counting the space consumed by the function names themselves.

Luckily, using the forementioned two symbols, we can perform dynamic loading ourselves. *Yellow Rose* loaded only the GL functions this way, but using a clever arrangement of text, we can embed the library information in a text block at practically no cost:

* First string is a library name, terminated by zero.
* Successive strings are function names.
* Two successive zeroes revert to initial state, next string will again be a 
  library name.
* Third successive zero stops loading.

This produces the following loader (using `intro.cpp` example)::

    static const char g_dynstr[] = ""
    "libGL.so\0"
    "glBindProgramPipeline\0"
    "glCreateShaderProgramv\0"
    "glGenProgramPipelines\0"
    "glProgramUniform3fv\0"
    "glRects\0"
    "glUseProgramStages\0"
    "\0libSDL.so\0"
    "SDL_GL_SwapBuffers\0"
    "SDL_Init\0"
    "SDL_OpenAudio\0"
    "SDL_PauseAudio\0"
    "SDL_PollEvent\0"
    "SDL_Quit\0"
    "SDL_SetVideoMode\0"
    "SDL_ShowCursor\0"
    "\0";
    
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
    }

The code snippet reveals a "fake" symbol table with the name ``g_symbol_table``. It is simply a list of function pointers constructed from the prefixed function names found when preprocessing the source file earlier. Depending on the build mode, we will either select the regular function call or redirect to our table. For the hello world example, the code would look like this::

    #if defined(USE_LD)
    #define dnload_puts puts
    #else
    #define dnload_puts g_symbol_table.puts
    static struct SymbolTableStruct
    {
      int (*puts)(const char*);
    } g_symbol_table;
    #endif

To gain access to these functions, we need to link against the standard C library with ``-lc`` flag. On Linux, use ``-ldl`` instead. Additionally on FreeBSD, when using SDL, user must manually link against ``libthr``. Since SDL is not explicitly linked against, it is not pulling the thread library as consequence. It seems threading is not properly initialized unless the dynamic linker gets to load ``libthr``.

Recompiling with ``-m dlfcn``, we get new sizes::

    'hello_world.stripped': 1544 bytes
    'hello_world': 736 bytes
    'intro.stripped': 5076 bytes
    'intro': 1590 bytes

Interestingly, this method does not really seem to be that advantageous at all on modern FreeBSD. Small binaries actually get larger due to additional program logic in the function loading system. On any nontrivial program there is a slight tradeoff in favor of just using plain ``ld`` though.

Import by hash - scouring ELF headers
-------------------------------------

Even if the cost of function name only is rather little, it still adds up for a large block of data, especially as using ``dlopen`` and ``dlsym`` requires us to have symbol definitions and all the PLT/GOT information required for them in the binary.

Fortunately, there is a better way. In 2008, Pouet users **parcelshit** [ref3]_ and **las/Mercury** [ref4]_ published code to search for symbols in ELF32 shared objects by their hashed names. Some of the code linked in the discussion [ref19]_ seems to be unaccessible by now, but at least the original import-by-hash implementation [ref18]_ (used as proof-of-concept for our implementation) seems to still be available.

The technique essentially takes advantage of the ``DT_DEBUG`` element in the ``.dynamic`` section (when present) that will contain information about linked shared libraries. We simply need to gain access to it.

Programs using ELF will have access to their own headers directly at the program load address (``0x8048000`` by default). The ELF32 header is 52 bytes long, and is immediately followed by an array of program headers. Each program header looks like this (from FreeBSD system headers)::

    typedef struct {
      Elf32_Word  p_type;    /* Entry type. */
      Elf32_Off   p_offset;  /* File offset of contents. */
      Elf32_Addr  p_vaddr;   /* Virtual address in memory image. */
      Elf32_Addr  p_paddr;   /* Physical address (not used). */
      Elf32_Word  p_filesz;  /* Size of contents in file. */
      Elf32_Word  p_memsz;   /* Size of contents in memory. */
      Elf32_Word  p_flags;   /* Access permission flags. */
      Elf32_Word  p_align;   /* Alignment in memory and file. */
    } Elf32_Phdr;

For examining the dynamically loaded elements, we need to look for a program header of type ``PT_DYNAMIC``. Upon finding the header, the ``p_vaddr`` virtual address pointer will point directly to the dynamic section. The dynamic section, then further consists of an array of structures of type ``Elf32_Dyn``, they look like this::

    typedef struct {
      Elf32_Sword  d_tag;   /* Entry type. */
      union {
        Elf32_Word  d_val;  /* Integer value. */
        Elf32_Addr  d_ptr;  /* Address value. */
      } d_un;
    } Elf32_Dyn;

When the dynamic linker passes control to your program, the ``Elf32_Dyn`` structure with the tag ``DT_DEBUG`` will have been filled with a pointer to the debug structure associated with the program. The debug structure looks like this::

    struct r_debug {
      int             r_version;  /* not used */
      struct link_map *r_map;     /* list of loaded images */
      void            (*r_brk)(struct r_debug *, struct link_map *);
                                  /* pointer to break point */
      enum {
        RT_CONSISTENT,            /* things are stable */
        RT_ADD,                   /* adding a shared library */
        RT_DELETE                 /* removing a shared library */
    }                 r_state;
    };

In here, the element ``r_map`` will contain a pointer to a linked list of structures representing shared objects, that is, libraries. They look like this::

    typedef struct link_map {
      caddr_t          l_addr;            /* Base Address of library */
    #ifdef __mips__
      caddr_t          l_offs;            /* Load Offset of library */
    #endif
      const char       *l_name;           /* Absolute Path to Library */
      const void       *l_ld;             /* Pointer to .dynamic in memory */
      struct link_map  *l_next, *l_prev;  /* linked list of of mapped libs */
    } Link_map;

The field ``l_ld`` in this structure is a pointer to the particular .dynamic section of this shared object. Reading the ELF specification [#References [16]], we also know that:

* All symbols of the shared object are located in the section pointed by tag 
  ``DT_SYMTAB``.
* All symbol names are located in the section pointed by tag ``DT_STRTAB``.
* Symbols names point to offsets from the start of ``DT_STRTAB`` section.
* The total number of symbols in a shared object is the number of chains in 
  the hash table of the shared object.

Using this information, we can simply go through the shared objects, one by one, then go through the symbols in these shared objects, one by one, only stopping when we find a name with a hash matching the hash we want. We can also use the symbol table format defined in the earlier section by storing these hashes at the same location the function pointer is going to get stored at. The only thing that remains to be done is to find a convenient hashing algorithm.

Fortunately, this has been done for us already [ref20]_. There are many good candidates where collisions are improbable enough to be nonexistent. We simply pick the one that produces smallest code. Parcelshit's original code used the DJB hash, which is already good, but in my testing, using SDBM hash produced a smaller binary.

Combining all this, gives us the following proof-of-concept implementation::

    #include <stdint.h>
    #include <sys/link_elf.h> // <link.h> on Linux
    
    #define ELF_BASE_ADDRESS 0x8048000
    
    static uint32_t sdbm_hash(const uint8_t *op)
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
    
    static const void* elf32_get_dynamic_address_by_tag(const void *dyn, Elf32_Sword tag)
    {
      const Elf32_Dyn *dynamic = (Elf32_Dyn*)dyn;
      for(;;)
      {
        if(dynamic->d_tag == tag)
        {
          return (const void*)dynamic->d_un.d_ptr;
        }
        ++dynamic;
      }
    }
    
    static const void* elf32_get_library_dynamic_section(const struct link_map *lmap, Elf32_Sword op)
    {
      const void *ret = elf32_get_dynamic_address_by_tag(lmap->l_ld, op);
      // Sometimes the value is an offset instead of a naked pointer.
      return (ret < (void*)lmap->l_addr) ? (uint8_t*)ret + (size_t)lmap->l_addr : ret;
    }
    
    static const struct link_map* elf32_get_link_map()
    {
      // ELF header is in a fixed location in memory.
      // First program header is located directly afterwards.
      const Elf32_Ehdr *ehdr = (const Elf32_Ehdr*)ELF_BASE_ADDRESS;
      const Elf32_Phdr *phdr = (const Elf32_Phdr*)((size_t)ehdr + (size_t)ehdr->e_phoff);
      // Find the dynamic header by traversing the phdr array.
      for(; (phdr->p_type != PT_DYNAMIC); ++phdr) { }
      // Find the debug entry in the dynamic header array.
      {
        const struct r_debug *debug = (const struct r_debug*)elf32_get_dynamic_address_by_tag((const void*)phdr->p_vaddr, DT_DEBUG);
        return debug->r_map;
      }
    }
    
    static void* dnload_find_symbol(uint32_t hash)
    {
      const struct link_map* lmap = elf32_get_link_map();
      for(;;)
      {
        /* Find symbol from link map. We need the string table and a corresponding symbol table. */
        const char* strtab = (const char*)elf32_get_library_dynamic_section(lmap, DT_STRTAB);
        const Elf32_Sym* symtab = (const Elf32_Sym*)elf32_get_library_dynamic_section(lmap, DT_SYMTAB);
        const uint32_t* hashtable = (const uint32_t*)elf32_get_library_dynamic_section(lmap, DT_HASH);
        unsigned numchains = hashtable[1]; /* Number of symbols. */
        unsigned ii;
        for(ii = 0; (ii < numchains); ++ii)
        {
          const Elf32_Sym* sym = &symtab[ii];
          const char *name = &strtab[sym->st_name];
          if(sdbm_hash((const uint8_t*)name) == hash)
          {
            return (void*)((const uint8_t*)sym->st_value + (size_t)lmap->l_addr);
          }
        }
        lmap = lmap->l_next;
      }
    }
    
    static void dnload(void)
    {
      unsigned ii;
      for(ii = 0; (24 > ii); ++ii)
      {
        void **iter = ((void**)&g_symbol_table) + ii;
        *iter = dnload_find_symbol(*(uint32_t*)iter);
      }
    }

Compiling with ``-m hash`` and linking against normal libraries (as opposed to what was needed with the dlfcn method) gives us new sizes::

    'hello_world.stripped': 1100 bytes
    'hello_world': 556 bytes
    'intro.stripped': 5464 bytes
    'intro': 1356 bytes

Significantly better.

The command line option ``-m hash`` additionally does some low-hanging optimizations such as removing all known unneeded symbols (``_end``, ``_edata`` and ``__bss_start``) and combining ``.rodata`` and ``.text`` into one section to free 40 bytes that would be consumed by a section header. This kind of hacking is, however, ultimately uninteresting as the only real way to further reduce the size is to construct all the ELF headers manually.

Crafting headers manually
-------------------------

There are earlier examples, on manually writing Linux ELF32 headers byte [ref21]_ by byte [ref22]_. These are easily executable even on FreeBSD 32-bit Linux emulation. The also come complete with source code, so one would assume switching between operating systems would be as easy as changing 8th byte of the ELF header into ``ELFOSABI_FREEBSD`` (i.e. 9) and recompiling with ``nasm``. Unfortunately, things are not quite so easy, and binaries constructed  thus will just crash.

However, even if the examples themselves are not usable, they prove that manual hacks are least possible. What we need to do is, have some kind of access into the process of dynamic loading itself, and see what we can do to decrease space. This is all done for us already, quoting manpages of ``ld-elf.so``:

  *The ``ld-elf.so.1`` utility is a self-contained shared object providing run-
  time support for loading and link-editing shared objects into a process' 
  address space. It is also commonly known as the dynamic linker.*

Full operating system sources have already been provided in ``/usr/src``. Recompiling the dynamic linker is as easy as going there and building (but not installing) ``world`` by issuing::

    cd /usr/src && make buildworld

This constructs our dynamic linker in ``/usr/obj/usr/src/libexec/rtld-elf/ld-elf.so.1``, and gives us access to the source in ``/usr/src/libexec/rtld-elf/``.

The authors have been kind enough to *literally* point out where the hacking should begin. ``rtld.c`` line 334::

    /*
     * On entry, the dynamic linker itself has not been relocated yet.
     * Be very careful not to reference any global data until after
     * init_rtld has returned.  It is OK to reference file-scope statics
     * and string constants, and to call static and global functions.
     */

What can I say? Thank you!

We obviously do not want to replace our own rtld with a crappy, hacked version so it's better to use the custom version directly. Reading *A Whirlwind Tutorial on Creating Really Teensy ELF Executables for Linux* [ref2]_ and *Executable and Linkable Format (ELF)* [ref16]_, we can construct the minimal program to do this and start the investigation::

    ehdr:  
      .byte 0x7f                        # e_ident[EI_MAG0], magic value 0x7F  
      .ascii "ELF"                      # e_ident[EI_MAG1] to e_indent[EI_MAG3], magic value "ELF"  
      .byte 0x1                         # e_ident[EI_CLASS], ELFCLASS32 = 1
      .byte 0x1                         # e_ident[EI_DATA], ELFDATA2LSB = 1  
      .byte 0x1                         # e_ident[EI_VERSION], EV_CURRENT = 1
      .byte 0x9                         # e_ident[EI_OSABI], ELFOSABI_LINUX = 3, ELFOSABI_FREEBSD = 9  
      .zero 8                           # e_indent[EI_MAG9 to EI_MAG15], unused
      .short 0x2                        # e_type, ET_EXEC = 2
      .short 0x3                        # e_machine, EM_386 = 3
      .long 0x1                         # e_version, EV_CURRENT = 1
      .long _start                      # e_entry, execution starting point
      .long ehdr_end - ehdr             # e_phoff, offset from start to program headers
      .long 0x0                         # e_shoff, start of section headers
      .long 0x0                         # e_flags, unused
      .short ehdr_end - ehdr            # e_ehsize, Elf32_Ehdr size
      .short phdr_load_end - phdr_load  # e_phentsize, Elf32_Phdr size
      .short 0x2                        # e_phnum, Elf32_Phdr count, PT_LOAD, PT_INTERP = 2
      .short 0x0                        # e_shentsize, Elf32_Shdr size
      .short 0x0                        # e_shnum, Elf32_Shdr count
      .short 0x0                        # e_shstrndx, index of section containing string table of section header names
    ehdr_end:
    
    phdr_load:
      .long 0x1         # p_type, PT_LOAD = 1
      .long 0x0         # p_offset, offset of program start
      .long 0x8048000   # p_vaddr, program virtual address
      .long 0x0         # p_paddr, unused
      .long end - ehdr  # p_filesz, program size on disk
      .long end - ehdr  # p_memsz, program size in memory
      .long 0x7         # p_flags, rwx = 7
      .long 0x1000      # p_align, usually 0x1000
    phdr_load_end:
    
    phdr_interp:
      .long 0x3                  # p_type, PT_INTERP = 3
      .long interp - ehdr        # p_offset, offset of block
      .long interp               # p_vaddr, address of block
      .long 0x0                  # p_paddr, unused
      .long interp_end - interp  # p_filesz, block size on disk
      .long interp_end - interp  # p_memsz, block size in memory
      .long 0x0                  # p_flags, ignored
      .long 0x1                  # p_align, 1 for strtab
    phdr_interp_end:
    
    interp:
      .asciz "/usr/obj/usr/src/libexec/rtld-elf/ld-elf.so.1"
    interp_end:
    
    _start:
      pushl $42
      pushl $0
      movl $1, %eax
      int $128
    end:

You can copypaste the earlier into, say, ``header.S`` and run::

    as -o header.o header.S && ld --oformat=binary -o header header.o && ./header

This should produce::

    ld: warning: cannot find entry symbol _start; defaulting to 0000000008048000
Segmentation fault

Disappointing. But add something, anything, into your custom rtld sources, recompile rtld, and try again. At the time of writing this document, mine says::

    > as -o header.o header.S && ld --oformat=binary --entry=0x8048000 -o header header.o && ./header
    Going to process program header.
    Going to read interp.
    .interp read: /usr/obj/usr/src/libexec/rtld-elf/ld-elf.so.1
    obj->dynamic = 0x0
    Segmentation fault

So that's why it crashes.

From this on, it's all just manual work, instrumenting the dynamic linker and seeing what can be done to minimize size. As this is an ongoing process, we will simply itemize the current findings.

Current compression procedure
-----------------------------

The ``maximum`` compression mode uses certain techniques to decrease binary size, described below.

Section headers and sections
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

These seem to be not needed. At all.

ELF uses the section information for introspection. Names of sections are contained in a specific section, `readelf` will expect fixed section names to decrypt symbol tables, etc.

However, when push comes to shove, the program will still be executed solely based on instructions in program headers and the ``.dynamic`` information. Section headers are 40 bytes a piece. We will have none of that.

Fake .bss section
~~~~~~~~~~~~~~~~~

Traditionally programs put uninitialized but statically reserved memory in a section named ``.bss`` or *Block Started by Symbol* that will be handled by the linker. We naturally do not have anything of the like. However, the program header PT_LOAD provides a possibility to set the size on disk (``p_filesz``) as different from size in memory (``p_memsz``).

Setting these into different sizes will simply cause more memory to be allocated. We parse the variable definitions directly from assembler code and construct virtual locations and pointers 'after' the end-of-file in the following manner (taken from ``quad.cpp`` example)::

    end:
    .balign 4
    aligned_end:
    .equ bss_start, aligned_end + 0
    .equ __progname, bss_start + 0
    .equ environ, bss_start + 4
    .equ g_attribute_quad_a, bss_start + 8
    .equ g_program_quad, bss_start + 12
    .equ _ZL14g_audio_buffer, bss_start + 16
    .equ bss_end, bss_start + 144016

The file size will use ``end`` while the memory size will use ``bss_end``.

**Note:** This will fail with a **bus error** if the size of fake ``.bss`` segment nears 128 megabytes. If this happens, the solution is to do the exact same thing ``ld`` would do - construct another ``PT_LOAD`` segment at the next memory page without the execute flag set and assign all uninitialized memory there instead.

Entry into and exit from ``_start``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As described in `Example program`_ earlier, we take care from entry and exit from the ``_start`` procedure ourselves. The compiler will happily push registers at the beginning and subtract the stack at the end of the function. On i386, this looks like the following (from ``hello_world.cpp`` example)::

    _start:
      pushl %ebp
      pushl %edi
      pushl %esi
      pushl %ebx
    ...
    <_start content here>
    ...
      movl $1,%eax
      int $128
    # 0 "" 2
    #NO_APP
      popl %eax
      addl $12, %esp
      popl %ebx
      popl %esi
      popl %edi
      popl %ebp
      ret

None of the push operations at the beginning or any operations after the system call are necessary. They may be discarded.

Alignment
~~~~~~~~~

Compilers seem to generate alignment directives rather arbitrarily. This is necessary on some architectures, but unnecessarily high alignments are irrelevant.

All alignment takes space on disk. To prevent this, all alignment directives greater than the register width (32 or 64-bit) in the generated assembler source are converted to explicit ``.balign`` directives for 4 or 8 bytes.

**Note:** It turns out that on alignment can sometimes be completely removed by effectively aligning one byte. This is not possible on any architectures where instruction pointer is assumed to be aligned to instruction size, but works at least on `amd64` and on ``ia32``.

Merging headers
~~~~~~~~~~~~~~~

As **Brian Raiter** already noted in *A Whirlwind Tutorial on Creating Really Teensy ELF Executables for Linux* [ref2]_, it does not really seem to matter if the ELF headers overlap. The structures will be assigned addresses exactly based on the offsets given, and they can freely overlap with other structs in memory.

The process of interleaving the structs is automated. This produces, for example, the following::

    Merging headers phdr_dynamic and hash at 4 bytes.
    Merging headers hash and dynamic at 4 bytes.
    Merging headers dynamic and symtab at 15 bytes.
    Merging headers interp and strtab at 1 bytes.

In this particular case, the merging takes advantage of:

* ``.interp`` section is aligned at one-byte boundary. This alignment is the 
  last value of ``PT_INTERP`` phdr. Hash table containing only the symbols 
  required by ``libc`` starts with number 1 (one chain).
* ``.dynamic`` section can start with many numbers. We put the ``PT_NEEDED`` 
  library requirements at the top so it can correctly interleave with the 
  last value of the hash table.
* ``.dynamic`` section ends with the ``PT_NULL`` terminator. Symbol table 
  starts with the null symbol. Size of null terminator is 8 bytes plus 
  varying amount (depends on byte order) of remaining null bytes from the 
  earlier ``DT_DEBUG`` dynamic structure. These can be partially interleaved.
* ``.interp`` section ends with terminating zero for the interpreter string, 
  and ``.strtab`` always starts with a zero as per specification.

**Note:** Interleaving with ``DT_DEBUG`` is dangerous, as the structure will be filled on runtime as seen in `Import by hash - scouring ELF headers`_. In practice, it seems to not cause problems currently.

Entry point
~~~~~~~~~~~

Default ELF entry point is fixed to address ``0x8048000``. This can be changed to a better compressable address.

The only issue here is that specifying ``--entry`` to ``ld`` does not actually change the entry point (it probably would if ``ld`` would also construct the headers). We need to modify linker scripts. This is done the same way as in `Import by hash - scouring ELF headers`_ - make the linker export the full linker script and change the ``SEGMENT_START`` directives into a better constant (``0x2000000`` at the time of writing).

Minimal ``DT_HASH``
~~~~~~~~~~~~~~~~~~~

If symbols are present in the object, a hash table must be present to allow the dynamic linker to look for symbols. Either a GNU hash table or the traditional SYSV ELF hash table could be used. GNU hash table however uses 16 bytes for the mere headers, and does not look all that promising. SYSV hash tables seem to be relatively small. They look like this (all values are unsigned 32-bit integers):

* Number of buckets.
* Number of chains.
* List of indices, size equal to number of buckets.
* List of indices, size equal to number of chains.

In here, the number of buckets serves as the basis of the hashing. Symbol equates into a hash value, that is modulated by number of buckets. Value from given bucket points to an index to start iterating the chain array from. The FreeBSD ``rtld.c`` implementation looks like this::

    for (symnum = obj->buckets[req->hash % obj->nbuckets];
         symnum != STN_UNDEF; symnum = obj->chains[symnum]) {
      if (symnum >= obj->nchains)
        return (ESRCH); /* Bad object */
    
      if (matched_symbol(req, obj, &matchres, symnum)) {
        req->sym_out = matchres.sym_out;
        req->defobj_out = obj;
        return (0);
      }
    }

The obvious solution is to only have one bucket and point it at the end of the chain array, then have the chain array count down from this index, going through the symbols one by one. It is definitely ineffective, but that hardly matters. This results as a generation algorithm as follows:

* Write one integer, number of buckets (1).
* Write one integer, number of symbols plus one.
* Write one integer, pointing at the last symbol index, adding one for the 
  obligatory empty symbol (``STN_UNDEF`` is 0).
* Write a zero, for padding.
* Write an increasing list of integers, starting from 0, ending at index of 
  last symbol minus one (last symbol index was already at the only bucket we 
  had).

The total cost of adding symbols would thus be ``8`` (for dynamic structure referencing ``DT_HASH``) ``+ (4 + numsymbols) * 4`` (for hash itself) ``+ (1 + numsymbols) * 16`` (for symbol structs plus one empty symbol struct) ``+ strlen(symnames)`` bytes.

**Note**: In FreeBSD, where ``libc`` requires symbols ``environ`` and ``__progname`` this would be 99 bytes exactly.

Location of ``r_debug``
~~~~~~~~~~~~~~~~~~~~~~~

When not constructing headers manually, the ``r_debug`` debugger structure containing the link map to iterate over linked shared libraries must be found by examining the program headers, starting right from the entry point.

In his similar project [ref32]_, **minas/Calodox** uses the manually constructed headers to directly know the location into which the dynamic linker will write this address.

After adding a label into the header assembler code, accessing the link map is thus reduced from::

    static const struct link_map* elf_get_link_map()
    {
      const Elf32_Ehdr *ehdr = (const Elf32_Ehdr*)ELF_BASE_ADDRESS;
      const Elf32_Phdr *phdr = (const Elf32_Phdr*)((size_t)ehdr + (size_t)ehdr->e_phoff);
      for(; (phdr->p_type != PT_DYNAMIC); ++phdr) { }
      {
        const struct r_debug *debug = (const struct r_debug*)elf_get_dynamic_address_by_tag((const void*)phdr->p_vaddr, DT_DEBUG);
        return debug->r_map;
      }
    }

Into::

    extern const struct r_debug *dynamic_r_debug;
    #define elf_get_link_map() dynamic_r_debug

Ordering of `DT_STRTAB` and ``DT_SYMTAB``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Logically, before iterating through the symbols in a library, their total amount would be interpreted from that library's hash table. This only takes a bit of space on FreeBSD where (easily interpretable) SYSV hash tables seem to be present in every library. On linux, some libraries only contain GNU hash tables the parsing of which significantly increases code footprint.

Luckily, *minas/calodox* noticed that ``DT_STRTAB`` and ``DT_SYMTAB`` seem to have two interesting relations:

  * Linkers seem to always put ``DT_STRTAB`` directly before ``DT_SYMTAB`` in 
    the dynamic section.
  * Conversely, symbol table seems to always immediately precede string table 
    in program memory.

Additionally:

  * The only program that does not obey these rules is our own binary, which 
    is the first entry in the ELF debug listing.

Using this information, the symbol scourer part of the loader can be reduced into something like this::

    for(;;)
    {
      // First entry is this object itself, safe to advance first.
      lmap = lmap->l_next;
      {
        // Take advantage of DT_STRTAB and DT_SYMTAB orientation in memory.
        const Elf32_Dyn *dynamic = elf_get_dynamic_element_by_tag(lmap->l_ld, DT_STRTAB);
        const char* strtab = (const char*)elf_transform_dynamic_address(lmap, (const void*)(dynamic->d_un.d_ptr));
        const Elf32_Sym *sym = (const dnload_elf_sym_t*)elf_transform_dynamic_address(lmap, (const void*)((dynamic + 1)->d_un.d_ptr));
        for(; ((void*)sym < (void*)strtab); ++sym)
        {
          const char *name = strtab + sym->st_name;
          if(sdbm_hash((const uint8_t*)name) == hash)
          {
            return (void*)((const uint8_t*)sym->st_value + (size_t)lmap->l_addr);
          }
        }
      }
    }

To see the difference compared to actually interpreting the hash, compile using ``--safe-symtab`` command line option.

Empty ``DT_SYMTAB`` (Linux)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Linux ``libc`` does not require the user program to define ``environ`` and ``__progname``. I was initially just leaving the ``hash`` and ``symtab`` segments blank. A blank ``symtab`` consists of just one empty (``NULL``) symbol, which already saves quite a lot of space.

However, as Amand Tihon [ref23]_ points in his own similar project [ref24]_, on Linux the whole of symbol table can be omitted. This is done by having the ``DT_SYMTAB`` dynamic structure entry point to address value ``0`` and by omitting ``DT_HASH`` completely. All in all, this means that size-optimized binaries on Linux are 99 bytes (`Minimal \`\`DT_HASH\`\``_) smaller than on FreeBSD. Interleaving of headers takes away some of this advantage, in practice it seems to be about 30 compressed bytes.

Final sizes
~~~~~~~~~~~

Compiling with all the tricks listed above (using ``-m maximum`` or just omitting the option) gives us::

    'hello_world.stripped': 411 bytes
    'hello_world': 321 bytes
    'intro.stripped': 1609 bytes
    'intro': 1099 bytes

**Note:** Sizes subject to change.

Acknowledgements
================

This script would not have been possible without the prior work done by various other parties. Especially the following entities deserve kudos for their efforts:

* **Marq/Fit** [ref1]_ for the original unpack header and dlopen/dlsym 
  implementation.
* **Brian Raiter** for *A Whirlwind Tutorial on Creating Really Teensy ELF 
  Executables for Linux* [ref2]_ and the insight of interleaving headers.
* **parcelshit** [ref3]_ and **las/Mercury** [ref4]_ for the original ELF32 
  import-by hash algorithm.
* **Hymy** [ref5]_ and **Ye Olde Laptops Posse** [ref6]_ for earlier forays 
  into manual ELF32 header construction.
* **Amand Tihon** [ref23]_ for *BOLD - The Byte Optimized Linker* [ref24]_ and 
  noticing that ``DT_SYMTAB`` can be empty.
* **ts/TDA** [ref26]_ for ``INT 3`` exit, ``HOME=`` -shell script trick, and 
  probably something else.
* **minas/calodox** [ref31]_ for *elfling* [ref32]_ and various symbol 
  scouring tricks.

And:

* **viznut/PWP** [ref7]_ for the series *Experimental music from very short C 
  programs* [ref8]_, a snipped of which is used in one of the examples.

The list might be missing some parties. Please notify me of any errors or omissions, so that people will get the credit they deserve.

Legalese
========

All contained code is licensed under the `new BSD license`_ [ref9]_.

Note that this license only pertains to the code of the script(s) themselves. There are no restrictions imposed on the end products of the script(s) just like there are no restrictions imposed on a binary built with a compiler.

To be honest, even that doesn't really mean anything. Just do whatever you want, but if you improve on the mechanisms, I would prefer to incorporate the improvements.

FAQ
===

No-one runs 32-bit FreeBSD anymore, especially if it's only for curiosities like this. Why bother?
--------------------------------------------------------------------------------------------------

Even on a 64-bit system, you should be able to execute the result file if the compatibility layer is set up correctly. The easiest way to do it is to just install a 32-bit jail [ref10]_ and point ``LD_32_LIBRARY_PATH`` environment variable to the ``/usr/local/lib`` of that jail. This has the added benefit of enabling full 32-bit compatibility and easy cross-compiling.

There are probably easy ways to do the same on Linux, but they are out of the scope of this document.

What about ELF64?
-----------------

It turns out the techniques described in this document are suitable for 64-bit ELF with minor or no changes. No specific new tricks are required.

The script supports ELF64 just the same way it supports ELF32, the description is kept in 32-bit particulars for simplicity of explanation.

What does ``USE_LD`` stand for?
-------------------------------

The name ``USE_LD`` is legacy, which has preserved unchanged from earlier Faemiyah prods. You may change the definition with the ``-d`` or ``--definition`` command line argument when invoking the script.

Do I need to use ``_start``?
----------------------------

When manually creating the program headers, the symbol would not necessarily need to be named ``_start`` - it could be anything, and the name will be stripped out anyway. However, this is a known convention.

What are ``environ`` and ``__progname``?
----------------------------------------

You you looked into the generated header, you might have seen something like this::

    #if defined(__FreeBSD__)
    #if defined(__clang__)
    void *environ;
    void *__progname;
    #else
    void *environ __attribute__((externally_visible));
    void *__progname __attribute__((externally_visible));
    #endif
    #endif

These symbols might seem nonsensical, as they are not used anywhere in the program or the generated code. Taking a look into the standard C library (i.e. ``/lib/libc.so.7``) will clarify their purpose::

    > readelf -a /lib/libc.so.7
    ...
    Symbol table '.dynsym' contains 3079 entries:
       Num:    Value  Size Type    Bind   Vis      Ndx Name
         0: 00000000     0 NOTYPE  LOCAL  DEFAULT  UND 
         1: 00000000     0 NOTYPE  WEAK   DEFAULT  UND _Jv_RegisterClasses
         2: 00000000     0 NOTYPE  GLOBAL DEFAULT  UND __progname
         3: 00000000     0 NOTYPE  GLOBAL DEFAULT  UND environ
    ...

We do not need these symbols, but libc expects them to be present in the binary. In practice, the dynamic linking procedure will fail if the program symbol table does not contain them.

**Note:** These symbols seem to be not needed on Linux.

Why is there an attribute ``externally_visible`` specified for some symbols?
----------------------------------------------------------------------------

The suffix ``__attribute__((externally_visible))`` is present in some symbols defined, most notable in ``_start``. This is due to Gnu C Compiler semantics.

When compiling for binary size, it is necessary to use the ``-fwhole-program`` flag to make g++ discard all irrelevant code. Unfortunately, unless the compiler finds something it needs, this will actually cause it to discard _everything_ within the source file as there is no ``main()`` present to start building a dependency graph from.

This attribute explicitly marks functions as symbols to be externally visible, so the dependency graph build shall include them.

**Note:** Clang does not seem to either require or support this attribute.

TODO
====

* Should probably create the header file in a smart(er) manner if it is not 
  found.
* Add cross-compilation support, at the very least between \*nix systems at 
  the "maximum" operation mode.
* Only SDL/OpenGL supported right now. Should probably also support GLFW.
* Perhaps there are more efficient ways to interleave the header structs? 
  Perhaps this can be permutated?

References
==========

.. [ref1] http://www.pouet.net/user.php?who=4078 Marq/Fit in Pouet]
.. [ref2] http://www.muppetlabs.com/~breadbox/software/tiny/teensy.html A Whirlwind Tutorial on Creating Really Teensy ELF Executables for Linux
.. [ref3] http://www.pouet.net/user.php?who=9348 parcelshit in Pouet
.. [ref4] http://www.pouet.net/user.php?who=4548 las/Mercury in Pouet
.. [ref5] http://www.pouet.net/groups.php?which=11106 Hymy in Pouet
.. [ref6] http://www.pouet.net/groups.php?which=11436 Ye Olde Laptops Posse in Pouet
.. [ref7] http://www.pouet.net/user.php?who=2547 viznut/PWP in Pouet
.. [ref8] https://www.youtube.com/watch?v=tCRPUv8V22o Music from very short programs - the 3rd iteration in Youtube
.. [ref9] http://opensource.org/licenses/BSD-3-Clause New BSD license
.. [ref10] http://www.freebsd.org/doc/handbook/jails.html Chapter 15. Jails in FreeBSD manual
.. [ref11] http://www.freebsd.org/doc/en/books/developers-handbook/x86-system-calls.html Chapter 11.3. System Calls in FreeBSD manual
.. [ref12] http://www.pouet.net/prod.php?which=5021 helsinki-spiegelberg by tsygä in Pouet
.. [ref13] http://www.pouet.net/prod.php?which=10562 Yellow Rose of Texas by Fit & Bandwagon in Pouet
.. [ref14] http://pubs.opengroup.org/onlinepubs/009695399/functions/dlopen.html dlopen specification at The Open Group Base Specifications
.. [ref15] http://pubs.opengroup.org/onlinepubs/009695399/functions/dlsym.html dlsym specification at The Open Group Base Specifications
.. [ref16] http://www.skyfree.org/linux/references/ELF_Format.pdf Executable and Linkable Format (ELF) specification
.. [ref17] http://svnweb.freebsd.org/base/stable/10/sys/sys/ FreeBSD system headers
.. [ref18] http://pastebin.com/f479f8beb parcelshit's original import-by-hash implementation
.. [ref19] http://www.pouet.net/topic.php?which=5392&page=4 Haxxoring the ELF format for 1k/4k stuff -thread on Pouet
.. [ref20] http://programmers.stackexchange.com/questions/49550/which-hashing-algorithm-is-best-for-uniqueness-and-speed Which hashing algorithm is best for uniqueness and speed? - Ian Boyd's answer at Programmers Stack Exchange
.. [ref21] http://www.pouet.net/prod.php?which=61753 Inconsistency by Hymy in Pouet
.. [ref22] http://www.pouet.net/prod.php?which=59264 tutorial2 by Ye Olde Laptops Posse in Pouet
.. [ref23] http://www.alrj.org/ Amand Tihon
.. [ref24] http://www.alrj.org/projects/bold/ BOLD - The Byte Optimized Linker
.. [ref25] https://blogs.oracle.com/ali/entry/gnu_hash_elf_sections GNU Hash ELF Sections by Ali Bahrami
.. [ref26] http://www.pouet.net/user.php?who=58551 ts/TDA in Pouet
.. [ref27] http://www.pouet.net/topic.php?which=10038&page=2#c482906 File-dumping example by ts/TDA
.. [ref28] http://svn.python.org/projects/external/xz-5.0.3/doc/lzma-file-format.txt LZMA file format
.. [ref29] http://tukaani.org/xz/xz-file-format-1.0.4.txt XZ file format
.. [ref30] http://x86.renejeschke.de/html/file_module_x86_id_142.html INT 3 instruction at René Jeschke's x86 instruction set reference mirror
.. [ref31] http://www.pouet.net/user.php?who=6102 minas/calodox in Pouet
.. [ref32] https://github.com/google/elfling elfling

.. _dnload header: https://github.com/trilkk/dnload/blob/master/src/dnload.h
.. _new BSD license: https://github.com/trilkk/dnload/blob/master/LICENCE