#!/usr/bin/env python

import argparse
import os
import re
import sys

(pathname, basename) = os.path.split(__file__)
if pathname and (pathname != "."):
  sys.path.append(pathname + "/..")

from dnload.common import check_executable
from dnload.common import is_verbose
from dnload.common import run_command
from dnload.common import search_executable
from dnload.common import set_verbose
from dnload.custom_help_formatter import CustomHelpFormatter
from dnload.preprocessor import Preprocessor

########################################
# Functions ############################
########################################

def compress_file(compression, src, dst):
  """Compress a file to be a self-extracting file-dumping executable."""
  if "lzma" == compression:
    command = ["xz", "--format=lzma", "--lzma1=preset=9,lc=1,lp=0,nice=273,pb=0", "--stdout"]
  elif "xz" == compression:
    command = ["xz", "--format=xz", "--lzma2=preset=9,lc=1,nice=273,pb=0", "--stdout"]
  else:
    raise RuntimeError("unknown compression format '%s'" % compression)
  (compressed, se) = run_command(command + [src], False)
  wfd = open(dst, "wb")
  wfd.write(compressed)
  wfd.close()
  print("Wrote '%s': %i -> %i bytes" % (dst, os.path.getsize(src), os.path.getsize(dst)))

def extract_shader_payload(preprocessor, src, dst):
  """Extract only the quoted content and write a file."""
  text = preprocessor.preprocess(src)
  match = re.match(r'.*char[^"]+"(.*)"\s*;[^"]+', text, re.MULTILINE | re.DOTALL)
  if not match:
    raise RuntimeError("could not extract shader blob")
  text = re.sub(r'"\s*\n\s*"', "", match.group(1))
  fd = open(dst, "w")
  fd.write(text.replace("\\n", "\n"))
  fd.close()
  if is_verbose():
    print("Wrote shader payload: '%s'" % (dst))

def find_executable(basename, pathname, path = "."):
  """Find executable with basename and pathname."""
  if os.path.exists(path + "/" + basename):
    return os.path.normpath(path + "/" + basename)
  if os.path.exists(path + "/" + pathname):
    return os.path.normpath(path + "/" + pathname + "/" + basename)
  new_path = os.path.normpath(path + "/..")
  if os.path.exists(new_path) and (os.path.realpath(new_path) != os.path.realpath(path)):
    return find_executable(basename, pathname, new_path)
  return None

########################################
# Main #################################
########################################

def main():
  """Main function."""
  default_preprocessor_list = ["cpp", "clang-cpp"]
  preprocessor = None
  
  parser = argparse.ArgumentParser(usage = "GLSL minifying test.", formatter_class = CustomHelpFormatter, add_help = False)
  parser.add_argument("-h", "--help", action = "store_true", help = "Print this help string and exit.")
  parser.add_argument("--preprocessor", default = None, help = "Try to use given preprocessor executable as opposed to autodetect.")
  parser.add_argument("-v", "--verbose", action = "store_true", help = "Print more info about what is being done.")
  parser.add_argument("source", default = [], nargs = "*", help = "Source file(s) to process.")
 
  args = parser.parse_args()

  preprocessor = args.preprocessor

  if args.help:
    print(parser.format_help().strip())
    return 0

  # Verbosity.
  if args.verbose:
    set_verbose(True)

  # Source files to process.
  if not args.source:
    raise RuntimeError("no source files to process")
  source_files = []
  for ii in args.source:
    if re.match(r'.*\.(glsl|vert|geom|frag)$', ii, re.I):
      source_files += [ii]
    else:
      raise RuntimeError("unknown source file: '%s'" % (ii))

  dl = find_executable("dnload.py", "dnload")
  if is_verbose():
    print("found dnload: '%s'" % (dl))
  sm = find_executable("shader_minifier.exe", "Shader_Minifier")
  if is_verbose():
    print("found shader_minifier: '%s'" % (sm))

  # Find preprocessor.
  if preprocessor:
    if not check_executable(preprocessor):
      raise RuntimeError("could not use supplied preprocessor '%s'" % (preprocessor))
  else:
    preprocessor_list = default_preprocessor_list
    if os.name == "nt":
      preprocessor_list = ["cl.exe"] + preprocessor_list
    preprocessor = search_executable(preprocessor_list, "preprocessor")
  if not preprocessor:
    raise RuntimeError("suitable preprocessor not found")
  preprocessor = Preprocessor(preprocessor)

  for ii in source_files:
    fname = "/tmp/" + os.path.basename(ii)
    fname_dn = fname + ".dnload"
    fname_dn_in = fname_dn + ".h"
    fname_dn_out = fname_dn + ".payload"
    fname_sm = fname + ".shaderminifier"
    fname_sm_in = fname_sm + ".h"
    fname_sm_out = fname_sm + ".payload"
    run_command(["python", dl, ii, "-o", fname_dn_in])
    if is_verbose():
      print("Wrote dnload -minified shader: '%s'" % (fname_dn_in))
    run_command(["mono", sm, ii, "-o", fname_sm_in])
    if is_verbose():
      print("Wrote shader_minifier -minified shader: '%s'" % (fname_sm_in))
    extract_shader_payload(preprocessor, fname_dn_in, fname_dn_out)
    extract_shader_payload(preprocessor, fname_sm_in, fname_sm_out)
    compress_file("lzma", fname_dn_out, fname_dn + ".lzma")
    #compress_file("xz", fname_dn_out, fname_dn + ".xz")
    compress_file("lzma", fname_sm_out, fname_sm + ".lzma")
    #compress_file("xz", fname_sm_out, fname_sm + ".xz")

  return 0

########################################
# Entry point ##########################
########################################

if __name__ == "__main__":
  sys.exit(main())
