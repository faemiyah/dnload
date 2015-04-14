########
 dnload
########
------------------------------------------------------
 Minimal binary generator for \*nix operating systems
------------------------------------------------------

.. contents:: Table of Contents
    :depth: 3

dnload.py
=========

``dnload.py`` is a script for generating minimal ELF binaries from C code. It serves no practical real-world use case, but can be utilized to aid in the creation of size-limited demoscene productions.

System Requirements
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

Supported Architectures
-----------------------

  * ``amd64`` (x86_64)
  * ``ia32`` (i386)

Supported Compilers
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
    specific prefix. By default this prefix is `dnload_`.
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
-----------------------------------------------

Even when developing an intro, the programmer is hardly interested in building a size-optimized binary every time. For this purpose, everything in the generated header file is wrapped to compile-time guards that allow us to compile the program as normal from Makefiles, Autotools scripts, CMake or even Visual Studio projects.

To do this, we need to set the ``USE_LD`` flag, for example by (replace with your favorite compiler)::

    > clang++ -o src/hello_world src/hello_world.cpp -DUSE_LD -I/usr/local/include `sdl-config --cflags` -O2 -s && ./src/hello_world
Hello World!

**Note:** The include directory and invoking sdl-config are currently necessary since SDL backend is what will be included by the generated headers.

When ``USE_LD`` is turned on, all "tricks" will essentially evaluate to NOP, and all calls made with the reserved ``dnload_`` prefix will simply call the functions as normal.

Compiling the example as a size-optimized binary
------------------------------------------------

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
.. [ref9] http://opensource.org/licenses/BSD-3-Clause New BSD licence
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