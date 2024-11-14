#!/bin/sh

DNLOAD="./dnload.py"
if [ ! -f "${DNLOAD}" ] ; then
  echo "${0}: could not find dnload.py"
  exit 1
fi

if [ ! -f "src/dnload.h" ] ; then
  touch src/dnload.h
fi

python "${DNLOAD}" -v -E src/intro.cpp $*
if [ $? -ne 0 ] ; then
  echo "${0}: regenerating symbols failed"
  exit 1
fi

exit 0
