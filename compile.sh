#!/bin/sh

DNLOAD="dnload"
DNLOAD_MODULE="${DNLOAD}/__init__.py"
if [ -f "./${DNLOAD_MODULE}" ] ; then
  DNLOAD_PATH="."
else
  echo "${0}: could not find dnload module"
  exit 1
fi

if [ -z "${PYTHONPATH}" ] ; then
  PYTHONPATH="${DNLOAD_PATH}"
else
  PYTHONPATH="${PYTHONPATH}:${DNLOAD_PATH}"
fi

if [ ! -f "src/dnload.h" ] ; then
  touch src/dnload.h
fi

if [ -d "/usr/lib/arm-linux-gnueabihf/mali-egl" ] ; then # Mali
  python -m "${DNLOAD}" -c src/intro.cpp -v --rpath "/usr/local/lib" -lc -ldl -lgcc -lm -lEGL -lGLESv2 -lSDL2 -m dlfcn $*
else
  python -m "${DNLOAD}" -c src/intro.cpp -v $*
fi
if [ $? -ne 0 ] ; then
  echo "${0}: compilation failed"
  exit 1
fi

exit 0
