########
 dnload
########
-----------------------------------------------------
 Minimal binary generator for *nix operating systems
-----------------------------------------------------

.. contents:: Table of Contents
    :depth: 3

dnload.py
=========

``dnload.py`` is a script for generating minimal ELF binaries from C code. It serves no practical real-world use case, but can be utilized to aid in the creation of size-limited demoscene productions.

System Requirements
-------------------

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

Use this command to clone the repository:

    svn checkout http://faemiyah-demoscene.googlecode.com/svn/trunk/dnload

The checked out repository will have the ``dnload.py`` script in the root folder. The minimal example is included in the ``src/`` folder and called ``hello_world.cpp``. The example looks like this (removing non-essential comments):

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

When beginning to work with a project, the first thing needed is to ensure that our header is up to date. To do this, run:

    python dnload.py src/hello_world.cpp -v

This should produce output somewhat akin to this:

    Header file 'dnload.h' found in path 'src/'.
    Trying binary 'g++49'... found
    Trying binary 'sdl-config'... found
    Executing command: sdl-config --cflags
    Analyzing source file 'src/hello_world.cpp'.
    Executing command: g++49 src/hello_world.cpp -D_GNU_SOURCE=1 -D_REENTRANT -D_THREAD_SAFE -DDNLOAD_H -I/usr/local/include -I/usr/local/include/SDL -E
    Symbols found: ['puts']
    Wrote header file 'src/dnload.h'.

You should now have an up-to date header file, which can be used to build the program. You may take a look at the contents of the header, but it will be explained in detail [#The_quest_for_minimal_ELF_binaries later on].