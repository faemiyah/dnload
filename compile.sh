#!/bin/sh

DNLOAD="dnload.py"
if [ ! -f "${DNLOAD}" ] ; then
  echo "${0}: could not find dnload.py"
  exit 1
fi

if [ ! -f "src/dnload.h" ] ; then
  touch src/dnload.h
fi

if [ -d "/usr/lib/arm-linux-gnueabihf/mali-egl" ] ; then # Mali
  python2 "${DNLOAD}" -v src/intro.cpp --rpath "/usr/local/lib" -lc -ldl -lgcc -lm -lEGL -lGLESv2 -lSDL2 -m dlfcn $*
else
  python2 "${DNLOAD}" -v src/intro.cpp $*
fi
if [ $? -ne 0 ] ; then
  echo "${0}: compilation failed"
  exit 1
fi

exit 0
