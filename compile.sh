#!/bin/sh

DNLOAD="dnload"
if [ ! -d "${DNLOAD}" ]; then
  >&2 echo "${0}: could not find dnload"
  exit 1
fi

if [ ! -f "src/dnload.h" ]; then
  touch src/dnload.h
fi

if [ -d "/usr/lib/arm-linux-gnueabihf/mali-egl" ] ; then # Mali
  python -m "${DNLOAD}" -v src/intro.cpp --rpath "/usr/local/lib" -lc -ldl -lgcc -lm -lEGL -lGLESv2 -lSDL2 -m dlfcn $*
else
  python -m "${DNLOAD}" -v src/intro.cpp $*
fi

if [ $? -ne 0 ]; then
  >&2 echo "${0}: compilation failed"
  exit 1
fi
