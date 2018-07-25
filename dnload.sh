#!/bin/sh
DNLOAD_MODULE_PATH=dnload
if [ -z $1 ]; then
  echo 'dnload 1.0'
  echo
  echo 'Provide the path to a C++ source file as the first argument.'
  echo
  echo 'Example:'
  echo '    dnload intro.cpp'
  echo
  exit 1
fi
FILENAME="$1"
shift
SRCDIR="$(dirname $FILENAME)"
[ -f "$SRCDIR/dnload.h" ] || touch "$SRCDIR/dnload.h"
if [ -d "/usr/lib/arm-linux-gnueabihf/mali-egl" ]; then # Mali
  python3 -m dnload -v "$FILENAME" --rpath "/usr/local/lib" -lc -ldl -lgcc -lm -lEGL -lGLESv2 -lSDL2 -m dlfcn "$@"
else
  python3 -m dnload -v "$FILENAME" "$@"
fi
if [ $? -ne 0 ]; then
  echo "${0}: compilation failed"
  exit 1
fi
