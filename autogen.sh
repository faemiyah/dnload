#!/bin/sh

CFLAGS_PATH="${HOME}/.local/bin/cflags"
ACINCLUDE="${CFLAGS_PATH}/acinclude.m4"
AUTOGEN="${CFLAGS_PATH}/autogen.sh"
DEFAULTS_CMAKE="${CFLAGS_PATH}/defaults.cmake"

diff_copy()
{
    if [ -f "${1}" ] ; then
        if [ -f "${2}" ] ; then
            diff -q "${1}" "${2}"
            if [ "$?" -ne "0" ] ; then
                echo "Replacing ${2} with ${1}"
                cp "${1}" "${2}"
            fi
        else
            echo "Installing ${1} to ${2}"
            cp "${1}" "${2}"
        fi
    fi
}

TARGET_PATH="."
if [ -n "${1}" ] ; then
    if [ -d "${1}" ] ; then
        TARGET_PATH="${1}"
    else
        echo "${0}: ERROR: given parameter ${1} is not a legal path"
        exit 1
    fi
fi

if [ -f "${TARGET_PATH}/acinclude.m4" ] ; then
    diff_copy "${ACINCLUDE}" "${TARGET_PATH}/acinclude.m4"
    autoreconf -fiv
elif [ -f "${TARGET_PATH}/defaults.cmake" ] ; then
    diff_copy "${DEFAULTS_CMAKE}" "${TARGET_PATH}/defaults.cmake"
    if [ -f "${TARGET_PATH}/CMakeCache.txt" ] ; then
        rm -v "${TARGET_PATH}/CMakeCache.txt"
    fi
    for ii in `find ${TARGET_PATH}/ | grep "\(cmake_install.cmake\|CMakeFiles\|Makefile\)$"` ; do
        if [ -d "${ii}" ] ; then
            rm -fRv "${ii}"
        elif [ -f "${ii}" ] ; then
            rm -v "${ii}"
        fi
    done
else
    echo "${0}: ERROR: could not identify build system"
fi

diff_copy "${AUTOGEN}" "${TARGET_PATH}/autogen.sh"

exit 0
