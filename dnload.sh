#!/bin/sh

#
# Note to packagers:
# Change DNLOAD_MODULE_PATH to the system directory when packaging dnload.
#
# For example:
# setconf dnload.sh DNLOAD_MODULE_PATH=/usr/lib/python3.6/site-packages/dnload
#

DNLOAD_MODULE_PATH=dnload

if [ -z $1 ]; then
  echo -e '\n\e[94mdnload \e[92mr14\e[0m'
  cat<<tac

Provide the path to a C++ source file as the first argument.

Example usage:

    dnload intro.cpp

tac
  exit 1
fi

FILENAME="$1"
shift

SRCDIR="$(dirname $FILENAME)"
if [ ! -f "$SRCDIR/dnload.h" ]; then
  touch "$SRCDIR/dnload.h"
fi

if [ -d "/usr/lib/arm-linux-gnueabihf/mali-egl" ]; then # Mali
  python -m dnload -v "$FILENAME" --rpath "/usr/local/lib" -lc -ldl -lgcc -lm -lEGL -lGLESv2 -lSDL2 -m dlfcn "$@"
else
  python -m dnload -v "$FILENAME" "$@"
fi

if [ $? -ne 0 ]; then
  >&2 echo "${0}: compilation failed"
  exit 1
fi
