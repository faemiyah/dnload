#!/bin/sh

DNLOAD="dnload"
if [ ! -d "${DNLOAD}" ]; then
  >&2 echo "${0}: could not find dnload"
  exit 1
fi

if [ ! -f "src/dnload.h" ]; then
  touch src/dnload.h
fi

python -m "${DNLOAD}" -v -E src/intro.cpp
if [ $? -ne 0 ]; then
  >&2 echo "${0}: regenerating symbols failed"
  exit 1
fi
