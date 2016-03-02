#!/bin/sh

DNLOAD="./dnload.py"
if [ ! -f "${DNLOAD}" ] ; then
  echo "${0}: could not find dnload.py"
  exit 1
fi

if [ ! -f "src/dnload.h" ] ; then
  touch src/dnload.h
fi

if [ -f "/opt/vc/lib/libbcm_host.so" ] ; then # VideoCore
  python "${DNLOAD}" -c src/intro.cpp -v -lc -lgcc -lm -lbcm_host -lEGL -lGLESv2 -lSDL2 $*
elif [ -d "/usr/lib/arm-linux-gnueabihf/mali-egl" ] ; then # Mali
  python "${DNLOAD}" -c src/intro.cpp -v -lc -lgcc -lm -lEGL -lGLESv2 -lSDL2 $*
else
  python "${DNLOAD}" -c src/intro.cpp -v $*
fi
if [ $? -ne 0 ] ; then
  echo "${0}: compilation failed"
  exit 1
fi

exit 0
