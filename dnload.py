#!/usr/bin/env python
"""Script to read C/C++ source input and generate a minimal program."""

import argparse
import platform
import os
import re
import shutil
import subprocess
import stat
import struct
import sys
import textwrap

########################################
# Globals ##############################
########################################

(g_osname, g_osignore1, g_osignore2, g_osignore3, g_osarch, g_osignore4) = platform.uname()
g_verbose = False

VERSION_REVISION = "r12"
VERSION_DATE = "20150624"

ELFLING_OUTPUT = "elfling_output"
ELFLING_PADDING = 10
ELFLING_WORK = "elfling_modelCounters"
ELFLING_UNCOMPRESSED = "_uncompressed"
VIDEOCORE_PATH = "/opt/vc"

########################################
# PlatformVar ##########################
########################################

def get_platform_combinations():
  """Get listing of all possible platform combinations matching current platform."""
  mapped_osname = platform_map(g_osname.lower())
  mapped_osarch = g_osarch.lower()
  ret = [mapped_osname]
  while True:
    ret += [mapped_osarch, mapped_osname + "-" + mapped_osarch]
    mapped_osarch = platform_map_iterate(mapped_osarch)
    if not mapped_osarch:
      break
  return sorted(ret, reverse=True) + ["default"]

class PlatformVar:
  """Platform-dependent variable."""

  def __init__(self, name):
    """Initialize platform variable."""
    self.__name = name

  def get(self):
    """Get value associated with the name."""
    if not self.__name in g_platform_variables:
      raise RuntimeError("unknown platform variable '%s'" % (self.__name))
    current_var = g_platform_variables[self.__name]
    combinations = get_platform_combinations()
    for ii in combinations:
      if ii in current_var:
        return current_var[ii]
    raise RuntimeError("current platform %s not supported for variable '%s'" % (str(combinations), self.__name))

  def deconstructable(self):
    """Tell if this platform value can be deconstructed."""
    return isinstance(self.get(), int)

  def __int__(self):
    """Convert to integer."""
    ret = self.get()
    if not isinstance(ret, int):
      raise ValueError("not an integer platform variable")
    return ret

  def __str__(self):
    """String representation."""
    ret = self.get()
    if isinstance(ret, int):
      return hex(ret)
    return ret

g_platform_mapping = {
  "amd64" : "64-bit",
  "armel" : "32-bit",
  "armv6l" : "armel",
  "armv7l" : "armel",
  "freebsd" : "FreeBSD",
  "i386" : "ia32",
  "i686" : "ia32",
  "ia32" : "32-bit",
  "linux" : "Linux",
  "x86_64" : "amd64",
  }

g_platform_variables = {
  "addr" : { "32-bit" : 4, "64-bit" : 8 },
  "align" : { "32-bit" : 4, "64-bit" : 8, "amd64" : 1, "ia32" : 1 },
  "bom" : { "amd64" : "<", "armel" : "<", "ia32" : "<" },
  "compression" : { "default" : "lzma" },
  "e_flags" : { "default" : 0, "armel" : 0x5000402 },
  "e_machine" : { "amd64" : 62, "armel" : 40, "ia32" : 3 },
  "ei_class" : { "32-bit" : 1, "64-bit" : 2 },
  "ei_osabi" : { "FreeBSD" : 9, "Linux-armel" : 0, "Linux" : 3 },
  "entry" : { "64-bit" : 0x400000, "armel" : 0x10000, "ia32" : 0x4000000 }, # ia32: 0x8048000
  "gl_library" : { "default" : "GL" },
  "interp" : { "FreeBSD" : "\"/libexec/ld-elf.so.1\"", "Linux-armel" : "\"/lib/ld-linux.so.3\"", "Linux-ia32" : "\"/lib/ld-linux.so.2\"", "Linux-amd64" : "\"/lib64/ld-linux-x86-64.so.2\"" },
  "march" : { "amd64" : "core2", "armel" : "armv6t2", "ia32" : "pentium4" },
  "memory_page" : { "32-bit" : 0x1000, "64-bit" : 0x200000 },
  "mpreferred-stack-boundary" : { "armel" : 0, "ia32" : 2, "64-bit" : 4 },
  "phdr_count" : { "default" : 3 },
  "start" : { "default" : "_start" },
  }

def platform_map_iterate(op):
  """Follow platform mapping chain once."""
  if op in g_platform_mapping:
    return g_platform_mapping[op]
  return None

def platform_map(op):
  """Follow platform mapping chain as long as possible."""
  while True:
    found = platform_map_iterate(op)
    if not found:
      break
    op = found
  return op

def replace_platform_variable(name, op):
  """Destroy platform variable, replace with default."""
  if not name in g_platform_variables:
    raise RuntimeError("trying to destroy nonexistent platform variable '%s'" % (name))
  g_platform_variables[name] = { "default" : op }

########################################
# Assembler ############################
########################################

class Assembler:
  """Class used to generate assembler output."""

  def __init__(self, op):
    """Constructor."""
    self.__executable = op
    self.__comment = "#"
    self.__byte = ".byte"
    self.__short = ".short"
    self.__word = ".long"
    self.__quad = ".quad"
    self.__string = ".ascii"
    op = os.path.basename(op)
    if op.startswith("nasm"):
      self.__comment = ";"
      self.__byte = "db"
      self.__short = "dw"
      self.__word = "dd"
      self.__string = "db"

  def assemble(self, src, dst):
    """Assemble a file."""
    cmd = [self.__executable, src, "-o", dst]
    (so, se) = run_command(cmd)
    if 0 < len(se) and is_verbose():
      print(se)

  def format_align(self, op):
    """Get alignmen string."""
    return (".balign %i\n" % (op))

  def format_block_comment(self, desc, length = 40):
    """Get a block-formatted comment."""
    block_text = ""
    for ii in range(length):
      block_text += self.__comment
    block_text += "\n"
    ret = self.__comment
    if desc:
      ret += " " + desc + " "
    for ii in range(len(ret), length):
      ret += self.__comment
    return block_text + ret + "\n" + block_text

  def format_comment(self, op, indent = ""):
    """Get comment string."""
    ret = ""
    if is_listing(op):
      for ii in op:
        if ii:
          ret += indent + self.__comment + " " + ii + "\n"
    elif op:
      ret += indent + self.__comment + " " + op + "\n"
    return ret

  def format_data(self, size, value, indent = ""):
    """Get data element."""
    size = int(size)
    if isinstance(value, int):
      value = hex(value)
    elif is_listing(value):
      value_strings = []
      for ii in value:
        if isinstance(ii, int):
          value_strings += [hex(ii)]
        else:
          value_strings += [str(ii)]
      value = ", ".join(value_strings)
    else:
      value = str(value)
      if value.startswith("\"") and 1 == size:
        return indent + self.__string + " " + value + "\n"
    if 1 == size:
      return indent + self.__byte + " " + value + "\n"
    elif 2 == size:
      return indent + self.__short + " " + value + "\n"
    elif 4 == size:
      return indent + self.__word + " " + value + "\n"
    elif 8 == size:
      return indent + self.__quad + " " + value + "\n"
    else:
      raise NotImplementedError("exporting assembler value of size %i", size)

  def format_equ(self, name, value):
    return ".equ %s, %s\n" % (name, value)

  def format_label(self, op):
    """Generate name labels."""
    if not op:
      return ""
    ret = ""
    if is_listing(op):
      for ii in op:
        ret += ii + ":\n"
    else:
      ret += op + ":\n"
    return ret

########################################
# AssemblerFile ########################
########################################

class AssemblerFile:
  """Assembler file representation."""

  def __init__(self, filename):
    """Constructor, opens and reads a file."""
    fd = open(filename, "r")
    lines = fd.readlines()
    fd.close()
    self.__sections = []
    current_section = AssemblerSection("text")
    ii = 0
    sectionre = re.compile(r'^\s+\.section\s+\"?\.([a-zA-Z0-9_]+)[\.\s]')
    for ii in lines:
      match = sectionre.match(ii)
      if match:
        self.add_sections(current_section)
        current_section = AssemblerSection(match.group(1), ii)
      else:
        current_section.add_line(ii)
    if not current_section.empty():
      self.add_sections(current_section)
    if is_verbose():
      section_names = map(lambda x: x.get_name(), self.__sections)
      print("Read %i sections in '%s': %s" % (len(self.__sections), filename, ", ".join(section_names)))

  def add_sections(self, op):
    """Manually add one or more sections."""
    if(is_listing(op)):
      self.__sections += op
    else:
      self.__sections += [op]

  def generate_fake_bss(self, assembler, und_symbols = None, elfling = None):
    """Remove local labels that would seem to generate .bss, make a fake .bss section."""
    bss = AssemblerSectionBss()
    for ii in self.__sections:
      while True:
        entry = ii.extract_bss(und_symbols)
        if not entry:
          break
        if not entry.is_und_symbol():
          bss.add_element(entry)
    if elfling:
      bss.add_element(AssemblerBssElement(ELFLING_WORK, elfling.get_work_size()))
    bss_size = bss.get_size()
    if 0 < bss.get_alignment():
      pt_load_string = ", second PT_LOAD required"
    else:
      pt_load_string = ", one PT_LOAD sufficient"
    if is_verbose():
      outstr = "Constructed fake .bss segement: "
      if 1073741824 < bss_size:
        print("%s%1.1f Gbytes%s" % (outstr, float(bss_size) / 1073741824.0, pt_load_string))
      elif 1048576 < bss_size:
        print("%s%1.1f Mbytes%s" % (outstr, float(bss_size) / 1048576.0, pt_load_string))
      elif 1024 < bss_size:
        print("%s%1.1f kbytes%s" % (outstr, float(bss_size) / 1024.0, pt_load_string))
      else:
        print("%s%u bytes%s" % (outstr, bss_size, pt_load_string))
    self.add_sections(bss)
    return bss

  def incorporate(self, other, label_name, jump_point_name):
    """Incorporate another assembler file into this, rename entry points."""
    labels = []
    for ii in other.__sections:
      ii.replace_entry_point(jump_point_name)
      labels += ii.gather_labels()
    labels.remove(jump_point_name)
    labels.sort(key=len, reverse=True)
    for ii in other.__sections:
      ii.replace_labels(labels, label_name)
    self.add_sections(other.__sections)

  def sort_sections(self, data_in_front = True):
    """Sort sections into an order that is more easily compressible."""
    text_sections = []
    data_sections = []
    rodata_sections = []
    other_sections = []
    for ii in self.__sections:
      if "text" == ii.get_name():
        text_sections += [ii]
      elif "data" == ii.get_name():
        data_sections += [ii]
      elif "rodata" == ii.get_name():
        rodata_sections += [ii]
      else:
        other_sections += [ii]
    text_section_str = None
    data_section_str = None
    rodata_section_str = None
    other_section_str = None
    if text_sections:
      text_section_str = "%i text" % (len(text_sections))
    if data_sections:
      data_section_str = "%i data" % (len(data_sections))
    if rodata_sections:
      rodata_section_str = "%i rodata" % (len(rodata_sections))
    if other_sections:
      other_section_str = ", ".join(map(lambda x: x.get_name(), other_sections))
    if data_in_front:
      self.__sections = rodata_sections + data_sections + text_sections + other_sections
      output_order = (rodata_section_str, data_section_str, text_section_str, other_section_str)
    else:
      self.__sections = text_sections + rodata_sections + data_sections + other_sections
      output_order = (text_section_str, rodata_section_str, data_section_str, other_section_str)
    if is_verbose():
      print("Sorted sections: " + ", ".join(filter(lambda x: x, output_order)))

  def remove_rodata(self):
    """Remove .rodata sections by merging them into the previous/next .text section."""
    new_sections = []
    previous_text_section = None
    rodata_section = None
    for ii in self.__sections:
      if "text" == ii.get_name():
        previous_text_section = ii
        new_sections += [ii]
      elif "rodata" == ii.get_name():
        if previous_text_section:
          previous_text_section.merge_content(ii)
        else:
          if rodata_section:
            rodata_section.merge_content(ii)
          else:
            rodata_section = ii
      else:
        new_sections += [ii]
    # .rodata sections defined before any .text sections will be merged into the first section.
    if rodata_section:
      rodata_section.merge_content(new_sections[0])
      new_sections[0].replace_content(rodata_section)
    self.__sections = new_sections

  def replace_constant(self, src, dst):
    """Replace constant with a replacement constant."""
    replace_count = 0
    for ii in self.__sections:
      for jj in range(len(ii.content)):
        line = ii.content[jj]
        replaced = re.sub(r'(\$%s|\$%s)' % (src, hex(src)), r'$%s' % hex(dst), line)
        if line != replaced:
          ii.content[jj] = replaced
          replace_count += 1
    if 1 > replace_count:
      raise RuntimeError("could not find constant to be replaced")
    elif 1 < replace_count:
      raise RuntimeError("found constant to be replaced more than once, source destroyed")

  def write(self, op, assembler):
    """Write an output assembler file or append to an existing file."""
    if isinstance(op, str):
      fd = open(op, "w")
      for ii in self.__sections:
        ii.write(fd)
      fd.close()
      if is_verbose():
        print("Wrote assembler source file '%s'." % (op))
    else:
      prefix = assembler.format_block_comment("Program")
      op.write(prefix)
      for ii in self.__sections:
        ii.write(op)

########################################
# AssemblerBssElement ##################
########################################

class AssemblerBssElement:
  """.bss element, representing a memory area that would go to .bss section."""

  def __init__(self, name, size, und_symbols = None):
    """Constructor."""
    self.__name = name
    self.__size = size
    self.__und = (und_symbols and (name in und_symbols))

  def get_name(self):
    """Get name of this."""
    return self.__name

  def get_size(self):
    """Get size of this."""
    return self.__size

  def is_und_symbol(self):
    """Tell if this is an und symbol."""
    return self.__und

  def __eq__(self, rhs):
    """Equality operator."""
    return (self.__name == rhs.get_name()) and (self.__size == rhs.get_size()) and (self.__und == rhs.is_und_symbol())

  def __lt__(self, rhs):
    """Less than operator."""
    if self.__und:
      if not rhs.is_und_symbol():
        return True
    elif rhs.is_und_symbol():
      return False
    return (self.__size < rhs.get_size())

  def __str__(self):
    """String representation."""
    return "(%s, %i, %s)" % (self.__name, self.__size, str(self.__und))

########################################
# AssemblerSection #####################
########################################

class AssemblerSection:
  """Section in an existing assembler source file."""

  def __init__(self, section_name, section_tag = None):
    """Constructor."""
    self.__name = section_name
    self.__tag = section_tag
    self.__content = []

  def add_line(self, line):
    """Add one line."""
    self.__content += [line]

  def clear_content(self):
    """Clear all content."""
    self.__content = []

  def crunch(self):
    """Remove all offending content."""
    while True:
      lst = self.want_line(r'\s*\.file\s+(.*)')
      if lst:
        self.erase(lst[0])
        continue
      lst = self.want_line(r'\s*\.globl\s+(.*)')
      if lst:
        self.erase(lst[0])
        continue
      lst = self.want_line(r'\s*\.ident\s+(.*)')
      if lst:
        self.erase(lst[0])
        continue
      lst = self.want_line(r'\s*\.section\s+(.*)')
      if lst:
        self.erase(lst[0])
        continue
      lst = self.want_line(r'\s*\.type\s+(.*)')
      if lst:
        self.erase(lst[0])
        continue
      lst = self.want_line(r'\s*\.size\s+(.*)')
      if lst:
        self.erase(lst[0])
        continue
      lst = self.want_line(r'\s*\.(bss)\s+')
      if lst:
        self.erase(lst[0])
        continue
      lst = self.want_line(r'\s*\.(data)\s+')
      if lst:
        self.erase(lst[0])
        continue
      lst = self.want_line(r'\s*\.(text)\s+')
      if lst:
        self.erase(lst[0])
        continue
      break
    if osarch_is_amd64():
      self.crunch_amd64(lst)
    elif osarch_is_ia32():
      self.crunch_ia32(lst)
    self.__tag = None

  def crunch_amd64(self, lst):
    """Perform platform-dependent crunching."""
    self.crunch_entry_push("_start")
    self.crunch_entry_push(ELFLING_UNCOMPRESSED)
    self.crunch_jump_pop(ELFLING_UNCOMPRESSED)
    lst = self.want_line(r'\s*(int\s+\$0x3|syscall)\s+.*')
    if lst:
      ii = lst[0] + 1
      jj = ii
      while True:
        if len(self.__content) <= jj or re.match(r'\s*\S+\:\s*', self.__content[jj]):
          if is_verbose():
            print("Erasing function footer after '%s': %i lines" % (lst[1], jj - ii))
          self.erase(ii, jj)
          break
        jj += 1

  def crunch_entry_push(self, op):
    """Crunch amd64/ia32 push directives from given line listing."""
    lst = self.want_label(op)
    if not lst:
      return
    ii = lst[0] + 1
    jj = ii
    stack_decrement = 0
    stack_save_decrement = 0
    reinstated_lines = []
    while True:
      current_line = self.__content[jj]
      match = re.match(r'\s*(push\S).*%(\S+)', current_line, re.IGNORECASE)
      if match:
        if is_stack_save_register(match.group(2)):
          stack_save_decrement += get_push_size(match.group(1))
        else:
          stack_decrement += get_push_size(match.group(1))
        jj += 1
        continue;
      # Preserve comment lines as they are.
      match = re.match(r'^\s*[#;].*', current_line, re.IGNORECASE)
      if match:
        reinstated_lines += [current_line]
        jj += 1
        continue
      # Saving stack pointer or sometimes initializing edx seem to be within pushing.
      match = re.match(r'\s*mov.*,\s*%(rbp|ebp|edx).*', current_line, re.IGNORECASE)
      if match:
        if is_stack_save_register(match.group(1)):
          stack_save_decrement = 0
        reinstated_lines += [current_line]
        jj += 1
        continue;
      # xor (zeroing) seems to be inserted in the 'middle' of pushing.
      match = re.match(r'\s*xor.*\s+%(\S+)\s?,.*', current_line, re.IGNORECASE)
      if match:
        reinstated_lines += [current_line]
        jj += 1
        continue
      match = re.match(r'\s*sub.*\s+[^\d]*(\d+),\s*%(rsp|esp)', current_line, re.IGNORECASE)
      if match:
        total_decrement = int(match.group(1)) + stack_decrement + stack_save_decrement
        self.__content[jj] = re.sub(r'\d+', str(total_decrement), current_line)
      break
    if is_verbose():
      print("Erasing function header from '%s': %i lines" % (op, jj - ii - len(reinstated_lines)))
    self.erase(ii, jj)
    self.__content[ii:ii] = reinstated_lines

  def crunch_ia32(self, lst):
    """Perform platform-dependent crunching."""
    self.crunch_entry_push("_start")
    self.crunch_entry_push(ELFLING_UNCOMPRESSED)
    self.crunch_jump_pop(ELFLING_UNCOMPRESSED)
    lst = self.want_line(r'\s*int\s+\$(0x3|0x80)\s+.*')
    if lst:
      ii = lst[0] + 1
      jj = ii
      while True:
        if len(self.__content) <= jj or re.match(r'\s*\S+\:\s*', self.__content[jj]):
          if is_verbose():
            print("Erasing function footer after interrupt '%s': %i lines." % (lst[1], jj - ii))
          self.erase(ii, jj)
          break
        jj += 1

  def crunch_jump_pop(self, op):
    """Crunch popping before a jump."""
    lst = self.want_line(r'\s*(jmp\s+%s)\s+.*' % (op))
    if not lst:
      return
    ii = lst[0]
    jj = ii - 1
    while True:
      if (0 > jj) or not re.match(r'\s*(pop\S).*', self.__content[jj], re.IGNORECASE):
        if is_verbose():
          print("Erasing function footer before jump to '%s': %i lines" % (op, ii - jj - 1))
        self.erase(jj + 1, ii)
        break
      jj -= 1

  def empty(self):
    """Tell if this section is empty."""
    if not self.__content:
      return False
    return True

  def erase(self, first, last = None):
    """Erase lines."""
    if not last:
      last = first + 1
    if first > last:
      return
    self.__content[first:last] = []

  def extract_bss(self, und_symbols):
    """Extract a variable that should go to .bss section."""
    # Test for relevant .globl element.
    found = self.extract_globl_object()
    if found:
      return AssemblerBssElement(found[0], found[1], und_symbols)
    found = self.extract_comm_object()
    if found:
      return AssemblerBssElement(found[0], found[1], und_symbols)
    self.minimal_align()
    self.crunch()
    return None

  def extract_comm_object(self):
    """.comm extract."""
    idx = 0
    while True:
      lst = self.want_line(r'\s*\.local\s+(\S+).*', idx)
      if lst:
        attempt = lst[0]
        name = lst[1]
        idx = attempt + 1
        lst = self.want_line(r'\s*\.comm\s+%s\s*,(.*)' % (name), idx)
        if not lst:
          continue
        size = lst[1]
        match = re.match(r'\s*(\d+)\s*,\s*(\d+).*', size)
        if match:
          size = int(match.group(1))
        else:
          size = int(size)
        self.erase(attempt, lst[0] + 1)
        return (name, size)
      return None

  def extract_globl_object(self):
    """.globl extract."""
    idx = 0
    while True:
      lst = self.want_line(r'\s*\.globl\s+(\S+).*', idx)
      if lst:
        attempt = lst[0]
        name = lst[1]
        idx = attempt + 1
        lst = self.want_line("\s*.type\s+(%s),\s+@object" % (name), idx)
        if not lst:
          continue
        lst = self.want_line("\s*(%s)\:" % (name), lst[0] + 1)
        if not lst:
          continue
        lst = self.want_line("\s*\.zero\s+(\d+)", lst[0] + 1)
        if not lst:
          continue
        self.erase(attempt, lst[0] + 1)
        return (name, int(lst[1]))
      return None

  def gather_labels(self):
    """Gathers all labels."""
    ret = []
    for ii in self.__content:
      match = re.match(r'((\.L|_ZL)[^:,\s\(]+)', ii)
      if match:
        ret += [match.group(1)]
      match = re.match(r'^([^\.:,\s\(]+):', ii)
      if match:
        ret += [match.group(1)]
    return ret

  def get_name(self):
    """Accessor."""
    return self.__name

  def merge_content(self, other):
    """Merge content with another section."""
    self.__content += other.__content

  def minimal_align(self):
    """Remove all .align declarations, replace with desired alignment."""
    desired = int(PlatformVar("align"))
    adjustments = []
    for ii in range(len(self.__content)):
      line = self.__content[ii]
      match = re.match(r'.*\.align\s+(\d+).*', line)
      if match:
        align = int(match.group(1))
        self.__content[ii] = "  .balign %i\n" % (desired)
        # Due to GNU AS compatibility modes, .align may mean different things.
        if osarch_is_amd64() or osarch_is_ia32():
          if desired != align:
            adjustments += ["%i -> %i" % (align, desired)]
        else:
          align = 1 << align
          if desired != align:
            adjustments += ["%i -> %i" % (align, desired)]
    if is_verbose() and adjustments:
      print("Alignment adjustment(%s): %s" % (self.get_name(), ", ".join(adjustments)))

  def replace_content(self, op):
    """Replace content of this section with content of given section."""
    self.__content = op.__content

  def replace_entry_point(self, op):
    """Replaces an entry point with given entry point name from this section, should it exist."""
    lst = self.want_entry_point()
    if lst:
      self.__content[lst[0]] = "%s:\n" % op

  def replace_labels(self, labels, append):
    """Replace all labels."""
    for ii in range(len(self.__content)):
      src = self.__content[ii]
      for jj in labels:
        dst = src.replace(jj, jj + append)
        if dst != src:
          self.__content[ii] = dst
          break

  def want_entry_point(self):
    """Want a line matching the entry point function."""
    return self.want_label("_start")

  def want_label(self, op):
    """Want a label from code."""
    return self.want_line(r'\s*\S*(%s)\S*\:.*' % (op))

  def want_line(self, op, first = 0):
    """Want a line matching regex from object."""
    for ii in range(first, len(self.__content)):
      match = re.match(op, self.__content[ii], re.IGNORECASE)
      if match:
        return (ii, match.group(1))
    return None

  def write(self, fd):
    """Write this section into a file."""
    if self.__tag:
      fd.write(self.__tag)
    for ii in self.__content:
      fd.write(ii)

########################################
# AssemblerSectionAlignment ############
########################################

class AssemblerSectionAlignment(AssemblerSection):
  """Alignment section only meant to provide alignment and label."""

  def __init__(self, alignment, padding, post_label, name = None):
    AssemblerSection.__init__(self, name)
    self.__alignment = alignment
    self.__padding = padding
    self.__post_label = post_label

  def create_content(self, assembler):
    """Generate assembler content."""
    self.clear_content()
    if self.get_name():
      self.add_line(assembler.format_label(self.get_name()))
    # Pad with zero bytes.
    var_line = AssemblerVariable(("", 1, 0)).generate_source(assembler, 1)
    for ii in range(self.__padding):
      self.add_line(var_line)
    if 0 < self.__alignment:
      self.add_line(assembler.format_align(self.__alignment))
    self.add_line(assembler.format_label(self.__post_label))

########################################
# AssemblerSectionBss ##################
########################################

class AssemblerSectionBss(AssemblerSection):
  """.bss section to be appended to the end of assembler source files."""

  def __init__(self):
    """Constructor."""
    AssemblerSection.__init__(self, ".bss")
    self.__elements = []
    self.__size = 0
    self.__und_size = 0

  def add_element(self, op):
    """Add one variable element."""
    if op in self.__elements:
      print("WARNING: trying to add .bss element twice: %s" % (str(element)))
      return
    self.__elements += [op]
    self.__elements.sort()
    self.__size += op.get_size()
    if op.is_und_symbol():
      self.__und_size += op.get_size()

  def create_content(self, assembler, prepend_label = None):
    """Generate assembler content."""
    self.clear_content()
    if prepend_label:
      self.add_line(assembler.format_label(prepend_label))
    if 0 < self.__size:
      self.add_line(assembler.format_align(int(PlatformVar("addr"))))
      self.add_line(assembler.format_label("aligned_end"))
    if 0 < self.get_alignment():
      self.add_line(assembler.format_align(self.get_alignment()))
    self.add_line(assembler.format_label("bss_start"))
    cumulative = 0
    for ii in self.__elements:
      self.add_line(assembler.format_equ(ii.get_name(), "bss_start + %i" % (cumulative)))
      cumulative += ii.get_size()
    self.add_line(assembler.format_equ("bss_end", "bss_start + %i" % (cumulative)))

  def get_alignment(self):
    """Get alignment. May be zero."""
    # TODO: Probably creates incorrect binaries at values very close but less than 128M due to code size.
    if 128 * 1024 * 1024 < self.get_size():
      return int(PlatformVar("memory_page"))
    return 0

  def get_size(self):
    """Get total size."""
    return self.__size

########################################
# AssemblerVariable ####################
########################################

class AssemblerVariable:
  """One assembler variable."""

  def __init__(self, op, name = None):
    """Constructor."""
    if not is_listing(op):
      raise RuntimeError("only argument passed is not a list")
    self.__desc = op[0]
    self.__size = op[1]
    self.__value = op[2]
    self.__name = name
    self.__original_size = -1
    self.__label_pre = []
    self.__label_post = []
    if 3 < len(op):
      self.add_label_pre(op[3])

  def add_label_pre(self, op):
    """Add pre-label(s)."""
    if is_listing(op):
      self.__label_pre += op
    else:
      self.__label_pre += [op]

  def add_label_post(self, op):
    """Add post-label(s)."""
    if is_listing(op):
      self.__label_post += op
    else:
      self.__label_post += [op]

  def deconstruct(self):
    """Deconstruct into byte stream."""
    lst = []
    if is_listing(self.__value):
      for ii in self.__value:
        if not is_deconstructable(ii):
          break
        lst += self.deconstruct_single(int(ii))
    elif is_deconstructable(self.__value):
      lst = self.deconstruct_single(int(self.__value))
    if 0 >= len(lst):
      return None
    if 1 >= len(lst):
      return [self]
    ret = []
    for ii in range(len(lst)):
      struct_elem = lst[ii]
      if isinstance(struct_elem, str):
        var = AssemblerVariable(("", 1, ord(struct_elem)))
      else:
        var = AssemblerVariable(("", 1, int(struct_elem)))
      if 0 == ii:
        var.__desc = self.__desc
        var.__name = self.__name
        var.__original_size = self.__size
        var.__label_pre = self.__label_pre
      elif len(lst) - 1 == ii:
        var.__label_post = self.__label_post
      ret += [var]
    return ret

  def deconstruct_single(self, op):
    """Desconstruct a single value."""
    bom = str(PlatformVar("bom"))
    int_size = int(self.__size)
    if 1 == int_size:
      return struct.pack(bom + "B", op)
    if 2 == int_size:
      if 0 > op:
        return struct.pack(bom + "h", op)
      else:
        return struct.pack(bom + "H", op)
    elif 4 == int_size:
      if 0 > op:
        return struct.pack(bom + "i", op)
      else:
        return struct.pack(bom + "I", op)
    elif 8 == int_size:
      if 0 > op:
        return struct.pack(bom + "q", op)
      else:
        return struct.pack(bom + "Q", op)
    raise RuntimeError("cannot pack value of size %i" % (int_size))

  def generate_source(self, assembler, indent, label = None):
    """Generate assembler source."""
    ret = ""
    indent = get_indent(indent)
    for ii in self.__label_pre:
      ret += assembler.format_label(ii)
    if isinstance(self.__value, str) and self.__value.startswith("\"") and label and self.__name:
      ret += assembler.format_label("%s_%s" % (label, self.__name))
    formatted_comment = assembler.format_comment(self.__desc, indent)
    formatted_data = assembler.format_data(self.__size, self.__value, indent)
    if formatted_comment:
      ret += formatted_comment
    ret += formatted_data
    for ii in self.__label_post:
      ret += assembler.format_label(ii)
    return ret

  def get_size(self):
    """Accessor."""
    return self.__size

  def mergable(self, op):
    """Tell if the two assembler variables are mergable."""
    if int(self.__size) != int(op.__size):
      return False
    if self.__value != op.__value:
      return False
    return True

  def merge(self, op):
    """Merge two assembler variables into one."""
    self.__desc = listify(self.__desc, op.__desc)
    self.__name = listify(self.__name, op.__name)
    self.__label_pre = listify(self.__label_pre, op.__label_pre)
    self.__label_post = listify(self.__label_post, op.__label_post)

  def reconstruct(self, lst):
    """Reconstruct variable from a listing."""
    original_size = int(self.__original_size)
    self.__original_size = -1
    if 1 >= original_size:
      return False
    if len(lst) < original_size - 1:
      return False
    ret = chr(self.__value)
    for ii in range(original_size - 1):
      op = lst[ii]
      if not op.reconstructable((original_size - 2) == ii):
        return False
      self.__label_post = listify(self.__label_post, op.label_post)
      ret += chr(op.value)
    bom = str(PlatformVar("bom"))
    if 2 == original_size:
      self.__value = struct.unpack(bom + "H", ret)[0]
    elif 4 == original_size:
      self.__value = struct.unpack(bom + "I", ret)[0]
    elif 8 == original_size:
      self.__value = struct.unpack(bom + "Q", ret)[0]
    self.__size = original_size
    return original_size - 1

  def reconstructable(self, accept_label_post):
    """Tell if this is reconstructable."""
    if self.__name:
      return False
    if self.__label_pre:
      return False
    if self.__label_post and not accept_label_post:
      return False
    if "" != self.__desc:
      return False
    if -1 != self.__original_size:
      return False

  def remove_label_pre(self, op):
    """Remove a pre-label."""
    if op in self.__label_pre:
      self.__label_pre.remove(op)

  def remove_label_post(self, op):
    """Remove a post-label."""
    if op in self.__label_post:
      self.__label_post.remove(op)

  def __str__(self):
    """String representation."""
    int_size = int(self.__size)
    if 1 == int_size:
      ret = 'byte:'
    elif 2 == int_size:
      ret = 'short'
    elif 4 == int_size:
      ret = 'long'
    elif 8 == int_size:
      ret = 'quad'
    else:
      raise RuntimeError("unknown size %i in an assembler variable" % (self.__size))
    ret += ': ' + str(self.__value)
    if self.__name:
      ret += " (%s)" % (self.__name)
    if self.__desc:
      ret += " '%s'" % (self.__desc)
    return ret

########################################
# AssemblerSegment #####################
########################################

class AssemblerSegment:
  """Segment is a collection of variables."""

  def __init__(self, op):
    """Constructor."""
    self.__name = None
    self.__desc = None
    self.__data = []
    if isinstance(op, str):
      self.__name = op
      self.__desc = None
    elif is_listing(op):
      for ii in op:
        if is_listing(ii):
          self.add_data(ii)
        elif not self.__name:
          self.__name = ii
        elif not self.__desc:
          self.__desc = ii
        else:
          raise RuntimeError("too many string arguments for list constructor")
    self.refresh_name_label()
    self.refresh_name_end_label()

  def add_data(self, op):
    """Add data into this segment."""
    self.__data += [AssemblerVariable(op)]
    self.refresh_name_label()
    self.refresh_name_end_label()

  def add_dt_hash(self, op):
    """Add hash dynamic structure."""
    d_tag = AssemblerVariable(("d_tag, DT_HASH = 4", PlatformVar("addr"), 4))
    d_un = AssemblerVariable(("d_un", PlatformVar("addr"), op))
    self.__data[0:0] = [d_tag, d_un]
    self.refresh_name_label()

  def add_dt_needed(self, op):
    """Add requirement to given library."""
    d_tag = AssemblerVariable(("d_tag, DT_NEEDED = 1", PlatformVar("addr"), 1))
    d_un = AssemblerVariable(("d_un, library name offset in strtab", PlatformVar("addr"), "strtab_%s - strtab" % labelify(op)))
    self.__data[0:0] = [d_tag, d_un]
    self.refresh_name_label()

  def add_dt_symtab(self, op):
    """Add symtab dynamic structure."""
    d_tag = AssemblerVariable(("d_tag, DT_SYMTAB = 6", PlatformVar("addr"), 6))
    d_un = AssemblerVariable(("d_un", PlatformVar("addr"), op))
    self.__data[0:0] = [d_tag, d_un]
    self.refresh_name_label()

  def add_hash(self, lst):
    """Generate a minimal DT_HASH based on symbol listing."""
    self.__data = []
    num = len(lst) + 1
    self.add_data(("", 4, 1))
    self.add_data(("", 4, num))
    self.add_data(("", 4, num - 1))
    self.add_data(("", 4, 0))
    if 1 < num:
      for ii in range(num - 1):
        self.add_data(("", 4, ii))

  def add_strtab(self, op):
    """Add a library name."""
    libname = AssemblerVariable(("symbol name string", 1, "\"%s\"" % op), labelify(op))
    terminator = AssemblerVariable(("string terminating zero", 1, 0))
    self.__data[1:1] = [libname, terminator]
    self.refresh_name_end_label()

  def add_symbol_empty(self):
    """Add an empty symbol."""
    if osarch_is_32_bit():
      self.add_data(("empty symbol", 4, (0, 0, 0, 0)))
    elif osarch_is_64_bit():
      self.add_data(("empty symbol", 4, (0, 0)))
      self.add_data(("empty symbol", PlatformVar("addr"), (0, 0)))
    else:
      raise_unknown_address_size()

  def add_symbol_und(self, name):
    """Add a symbol to satisfy UND from external source."""
    label_name = "symtab_" + name
    if osarch_is_32_bit():
      self.add_data(("st_name", 4, "strtab_%s - strtab" % (name)))
      self.add_data(("st_value", PlatformVar("addr"), label_name, label_name))
      self.add_data(("st_size", PlatformVar("addr"), PlatformVar("addr")))
      self.add_data(("st_info", 1, 17))
      self.add_data(("st_other", 1, 0))
      self.add_data(("st_shndx", 2, 1))
    elif osarch_is_64_bit():
      self.add_data(("st_name", 4, "strtab_%s - strtab" % (name)))
      self.add_data(("st_info", 1, 17))
      self.add_data(("st_other", 1, 0))
      self.add_data(("st_shndx", 2, 1))
      self.add_data(("st_value", PlatformVar("addr"), label_name, label_name))
      self.add_data(("st_size", PlatformVar("addr"), PlatformVar("addr")))
    else:
      raise_unknown_address_size()

  def clear_data(self):
    """Clear all data."""
    self.__data = []

  def deconstruct_head(self):
    """Deconstruct this segment (starting from head) into a byte stream."""
    ret = []
    for ii in range(len(self.__data)):
      op = self.__data[ii].deconstruct()
      if not op:
        return (ret, self.__data[ii:])
      ret += op
    return (ret, [])

  def deconstruct_tail(self):
    """Deconstruct this segment (starting from tail) into a byte stream."""
    ret = []
    for ii in range(len(self.__data)):
      op = self.__data[-ii - 1].deconstruct()
      if not op:
        return (self.__data[:len(self.__data) - ii], ret)
      ret = op + ret
    return ([], ret)

  def empty(self):
    """Tell if this segment is empty."""
    return 0 >= len(self.__data)

  def generate_source(self, op):
    """Generate assembler source."""
    ret = op.format_block_comment(self.__desc)
    for ii in self.__data:
      ret += ii.generate_source(op, 1, self.__name)
    return ret

  def merge(self, op):
    """Attempt to merge with given segment."""
    highest_mergable = 0
    (head_src, bytestream_src) = self.deconstruct_tail()
    (bytestream_dst, tail_dst) = op.deconstruct_head()
    for ii in range(min(len(bytestream_src), len(bytestream_dst))):
      mergable = True
      for jj in range(ii + 1):
        if not bytestream_src[-ii - 1 + jj].mergable(bytestream_dst[jj]):
          mergable = False
          break
      if mergable:
        highest_mergable = ii + 1
    if 0 >= highest_mergable:
      return False
    if is_verbose():
      print("Merging headers %s and %s at %i bytes." % (self.__name, op.__name, highest_mergable))
    for ii in range(highest_mergable):
      bytestream_src[-highest_mergable + ii].merge(bytestream_dst[ii])
    bytestream_dst[0:highest_mergable] = []
    self.reconstruct(head_src + bytestream_src)
    op.reconstruct(bytestream_dst + tail_dst)
    return True

  def reconstruct(self, bytestream):
    """Reconstruct data from bytestream."""
    self.__data = []
    while 0 < len(bytestream):
      front = bytestream[0]
      bytestream = bytestream[1:]
      constructed = front.reconstruct(bytestream)
      if constructed:
        bytestream[:constructed] = []
      self.__data += [front]

  def refresh_name_label(self):
    """Add name label to first assembler variable."""
    for ii in self.__data:
      ii.remove_label_pre(self.__name)
    if 0 < len(self.__data):
      self.__data[0].add_label_pre(self.__name)

  def refresh_name_end_label(self):
    """Add a name end label to last assembler variable."""
    end_label = "%s_end" % (self.__name)
    for ii in self.__data:
      ii.remove_label_post(end_label)
    if 0 < len(self.__data):
      self.__data[-1].add_label_post(end_label)

  def size(self):
    """Get cumulative size of data."""
    ret = 0
    for ii in self.__data:
      ret += int(ii.get_size())
    return ret

  def write(self, fd, assembler):
    """Write segment onto disk."""
    if 0 >= len(self.__data):
      raise RuntimeError("segment '%s' is empty" % self.__name)
    fd.write(self.generate_source(assembler))

assembler_ehdr = (
    "ehdr",
    "Elf32_Ehdr or Elf64_Ehdr",
    ("e_ident[EI_MAG0], magic value 0x7F", 1, 0x7F),
    ("e_ident[EI_MAG1] to e_indent[EI_MAG3], magic value \"ELF\"", 1, "\"ELF\""),
    ("e_ident[EI_CLASS], ELFCLASS32 = 1, ELFCLASS64 = 2", 1, PlatformVar("ei_class")),
    ("e_ident[EI_DATA], ELFDATA2LSB = 1, ELFDATA2MSB = 2", 1, 1),
    ("e_ident[EI_VERSION], EV_CURRENT = 1", 1, 1),
    ("e_ident[EI_OSABI], ELFOSABI_SYSV = 0, ELFOSABI_LINUX = 3, ELFOSABI_FREEBSD = 9", 1, PlatformVar("ei_osabi")),
    ("e_ident[EI_ABIVERSION], always 0", 1, 0),
    ("e_indent[EI_MAG10 to EI_MAG15], unused", 1, (0, 0, 0, 0, 0, 0, 0)),
    ("e_type, ET_EXEC = 2", 2, 2),
    ("e_machine, EM_386 = 3, EM_ARM = 40, EM_X86_64 = 62", 2, PlatformVar("e_machine")),
    ("e_version, EV_CURRENT = 1", 4, 1),
    ("e_entry, execution starting point", PlatformVar("addr"), PlatformVar("start")),
    ("e_phoff, offset from start to program headers", PlatformVar("addr"), "phdr_interp - ehdr"),
    ("e_shoff, start of section headers", PlatformVar("addr"), 0),
    ("e_flags, unused", 4, PlatformVar("e_flags")),
    ("e_ehsize, Elf32_Ehdr size", 2, "ehdr_end - ehdr"),
    ("e_phentsize, Elf32_Phdr size", 2, "phdr_interp_end - phdr_interp"),
    ("e_phnum, Elf32_Phdr count, PT_LOAD, [PT_LOAD (bss)], PT_INTERP, PT_DYNAMIC", 2, PlatformVar("phdr_count")),
    ("e_shentsize, Elf32_Shdr size", 2, 0),
    ("e_shnum, Elf32_Shdr count", 2, 0),
    ("e_shstrndx, index of section containing string table of section header names", 2, 0),
    )

assembler_phdr32_interp = (
    "phdr_interp",
    "Elf32_Phdr, PT_INTERP",
    ("p_type, PT_INTERP = 3", 4, 3),
    ("p_offset, offset of block", PlatformVar("addr"), "interp - ehdr"),
    ("p_vaddr, address of block", PlatformVar("addr"), "interp"),
    ("p_paddr, unused", PlatformVar("addr"), 0),
    ("p_filesz, block size on disk", PlatformVar("addr"), "interp_end - interp"),
    ("p_memsz, block size in memory", PlatformVar("addr"), "interp_end - interp"),
    ("p_flags, ignored", 4, 0),
    ("p_align, 1 for strtab", PlatformVar("addr"), 1),
    )

assembler_phdr32_load_single = (
    "phdr_load",
    "Elf32_Phdr, PT_LOAD",
    ("p_type, PT_LOAD = 1", 4, 1),
    ("p_offset, offset of program start", PlatformVar("addr"), 0),
    ("p_vaddr, program virtual address", PlatformVar("addr"), PlatformVar("entry")),
    ("p_paddr, unused", PlatformVar("addr"), 0),
    ("p_filesz, program size on disk", PlatformVar("addr"), "end - ehdr"),
    ("p_memsz, program size in memory", PlatformVar("addr"), "bss_end - ehdr"),
    ("p_flags, rwx = 7", 4, 7),
    ("p_align, usually 0x1000", PlatformVar("addr"), PlatformVar("memory_page")),
    )

assembler_phdr32_load_double = (
    "phdr_load",
    "Elf32_Phdr, PT_LOAD",
    ("p_type, PT_LOAD = 1", 4, 1),
    ("p_offset, offset of program start", PlatformVar("addr"), 0),
    ("p_vaddr, program virtual address", PlatformVar("addr"), PlatformVar("entry")),
    ("p_paddr, unused", PlatformVar("addr"), 0),
    ("p_filesz, program size on disk", PlatformVar("addr"), "end - ehdr"),
    ("p_memsz, program headers size in memory", PlatformVar("addr"), "aligned_end - ehdr"),
    ("p_flags, rwx = 7", 4, 7),
    ("p_align, usually " + str(PlatformVar("memory_page")), PlatformVar("addr"), PlatformVar("memory_page")),
    )

assembler_phdr32_load_bss = (
    "phdr_load_bss",
    "Elf32_Phdr, PT_LOAD (.bss)",
    ("p_type, PT_LOAD = 1", 4, 1),
    ("p_offset, offset of fake .bss segment", PlatformVar("addr"), "bss_start - ehdr"),
    ("p_vaddr, program virtual address", PlatformVar("addr"), "bss_start"),
    ("p_paddr, unused", PlatformVar("addr"), 0),
    ("p_filesz, .bss size on disk", PlatformVar("addr"), 0),
    ("p_memsz, .bss size in memory", PlatformVar("addr"), "bss_end - bss_start"),
    ("p_flags, rw = 6", 4, 6),
    ("p_align, usually " + str(PlatformVar("memory_page")), PlatformVar("addr"), PlatformVar("memory_page")),
    )

assembler_phdr32_dynamic = (
    "phdr_dynamic",
    "Elf32_Phdr, PT_DYNAMIC",
    ("p_type, PT_DYNAMIC = 2", 4, 2),
    ("p_offset, offset of block", PlatformVar("addr"), "dynamic - ehdr"),
    ("p_vaddr, address of block", PlatformVar("addr"), "dynamic"),
    ("p_paddr, unused", PlatformVar("addr"), 0),
    ("p_filesz, block size on disk", PlatformVar("addr"), "dynamic_end - dynamic"),
    ("p_memsz, block size in memory", PlatformVar("addr"), "dynamic_end - dynamic"),
    ("p_flags, ignored", 4, 0),
    ("p_align", PlatformVar("addr"), 1),
    )

assembler_phdr64_interp = (
    "phdr_interp",
    "Elf64_Phdr, PT_INTERP",
    ("p_type, PT_INTERP = 3", 4, 3),
    ("p_flags, ignored", 4, 0),
    ("p_offset, offset of block", PlatformVar("addr"), "interp - ehdr"),
    ("p_vaddr, address of block", PlatformVar("addr"), "interp"),
    ("p_paddr, unused", PlatformVar("addr"), 0),
    ("p_filesz, block size on disk", PlatformVar("addr"), "interp_end - interp"),
    ("p_memsz, block size in memory", PlatformVar("addr"), "interp_end - interp"),
    ("p_align, 1 for strtab", PlatformVar("addr"), 1),
    )

assembler_phdr64_load_single = (
    "phdr_load",
    "Elf64_Phdr, PT_LOAD",
    ("p_type, PT_LOAD = 1", 4, 1),
    ("p_flags, rwx = 7", 4, 7),
    ("p_offset, offset of program start", PlatformVar("addr"), 0),
    ("p_vaddr, program virtual address", PlatformVar("addr"), PlatformVar("entry")),
    ("p_paddr, unused", PlatformVar("addr"), 0),
    ("p_filesz, program size on disk", PlatformVar("addr"), "end - ehdr"),
    ("p_memsz, program size in memory", PlatformVar("addr"), "bss_end - ehdr"),
    ("p_align, usually " + str(PlatformVar("memory_page")), PlatformVar("addr"), PlatformVar("memory_page")),
    )

assembler_phdr64_load_double = (
    "phdr_load",
    "Elf64_Phdr, PT_LOAD",
    ("p_type, PT_LOAD = 1", 4, 1),
    ("p_flags, rwx = 7", 4, 7),
    ("p_offset, offset of program start", PlatformVar("addr"), 0),
    ("p_vaddr, program virtual address", PlatformVar("addr"), PlatformVar("entry")),
    ("p_paddr, unused", PlatformVar("addr"), 0),
    ("p_filesz, program size on disk", PlatformVar("addr"), "end - ehdr"),
    ("p_memsz, program headers size in memory", PlatformVar("addr"), "aligned_end - ehdr"),
    ("p_align, usually " + str(PlatformVar("memory_page")), PlatformVar("addr"), PlatformVar("memory_page")),
    )

assembler_phdr64_load_bss = (
    "phdr_load_bss",
    "Elf64_Phdr, PT_LOAD (.bss)",
    ("p_type, PT_LOAD = 1", 4, 1),
    ("p_flags, rw = 6", 4, 6),
    ("p_offset, offset of fake .bss segment", PlatformVar("addr"), "end - ehdr"),
    ("p_vaddr, program virtual address", PlatformVar("addr"), "bss_start"),
    ("p_paddr, unused", PlatformVar("addr"), 0),
    ("p_filesz, .bss size on disk", PlatformVar("addr"), 0),
    ("p_memsz, .bss size in memory", PlatformVar("addr"), "bss_end - end"),
    ("p_align, usually " + str(PlatformVar("memory_page")), PlatformVar("addr"), PlatformVar("memory_page")),
    )

assembler_phdr64_dynamic = (
    "phdr_dynamic",
    "Elf64_Phdr, PT_DYNAMIC",
    ("p_type, PT_DYNAMIC = 2", 4, 2),
    ("p_flags, ignored", 4, 0),
    ("p_offset, offset of block", PlatformVar("addr"), "dynamic - ehdr"),
    ("p_vaddr, address of block", PlatformVar("addr"), "dynamic"),
    ("p_paddr, unused", PlatformVar("addr"), 0),
    ("p_filesz, block size on disk", PlatformVar("addr"), "dynamic_end - dynamic"),
    ("p_memsz, block size in memory", PlatformVar("addr"), "dynamic_end - dynamic"),
    ("p_align", PlatformVar("addr"), 1),
    )

assembler_hash = (
    "hash",
    "DT_HASH",
    )

assembler_dynamic = (
    "dynamic",
    "PT_DYNAMIC",
    ("d_tag, DT_STRTAB = 5", PlatformVar("addr"), 5),
    ("d_un", PlatformVar("addr"), "strtab"),
    ("d_tag, DT_DEBUG = 21", PlatformVar("addr"), 21),
    ("d_un", PlatformVar("addr"), 0, "dynamic_r_debug"),
    ("d_tag, DT_NULL = 0", PlatformVar("addr"), 0),
    ("d_un", PlatformVar("addr"), 0),
    )

assembler_symtab = (
    "symtab",
    "DT_SYMTAB",
    )

assembler_interp = (
    "interp",
    "PT_INTERP",
    ("path to interpreter", 1, PlatformVar("interp")),
    ("interpreter terminating zero", 1, 0),
    )

assembler_strtab = (
    "strtab",
    "DT_STRTAB",
    ("initial zero", 1, 0),
    )

########################################
# Linker ###############################
########################################

class Linker:
  """Linker used to link object files."""

  def __init__(self, op):
    """Constructor."""
    self.__command = op
    self.__command_basename = os.path.basename(self.__command)
    self.__library_directories = []
    self.__libraries = []
    self.__linker_flags = []
    self.__linker_script = []

  def command_basename_startswith(self, op):
    """Check if command basename starts with given string."""
    return self.__command_basename.startswith(op)

  def generate_linker_flags(self):
    """Generate linker command for given mode."""
    self.__linker_flags = []
    if self.__command_basename.startswith("g++") or self.__command_basename.startswith("gcc"):
      self.__linker_flags += ["-nostartfiles", "-nostdlib", "-Xlinker", "--strip-all"]
    elif self.__command_basename.startswith("clang"):
      self.__linker_flags += ["-nostdlib", "-Xlinker", "--strip-all"]
    elif self.__command_basename.startswith("ld"):
      dynamic_linker = str(PlatformVar("interp"))
      if dynamic_linker.startswith("\"") and dynamic_linker.endswith("\""):
        dynamic_linker = dynamic_linker[1:-1]
      else:
        raise RuntimeError("dynamic liner definition '%s' should be quoeted" % (dynamic_linker))
      self.__linker_flags += ["-nostdlib", "--strip-all", "--dynamic-linker=%s" % (dynamic_linker)]
    else:
      raise RuntimeError("compilation not supported with compiler '%s'" % (op))

  def get_command(self):
    """Accessor."""
    return self.__command

  def get_library_list(self):
    """Generate link library list libraries."""
    ret = []
    prefix = "-l"
    if self.__command_basename.startswith("cl."):
      prefix = "/l"
    for ii in self.__libraries:
      ret += [prefix + ii]
    return ret

  def get_library_directory_list(self):
    """Set link directory listing."""
    ret = []
    prefix = "-L"
    if self.__command_basename.startswith("cl."):
      prefix = "/L"
    for ii in self.__library_directories:
      ret += [prefix + ii]
    if self.__command_basename.startswith("ld"):
      ret += ["-rpath-link", ":".join(self.__library_directories)]
    return ret

  def get_library_name(self, op):
    """Get actual name of library."""
    if op.startswith("/"):
      return op
    # Check if the library is specified verbatim. If yes, no need to expand.
    if re.match(r'lib.+\.so(\..*)?', op):
      return op
    libname = "lib%s.so" % (op)
    # Shared object may be linker script, if so, it will tell actual shared object.
    for ii in self.__library_directories:
      current_libname = locate(ii, libname)
      if current_libname and file_is_ascii_text(current_libname):
        fd = open(current_libname, "r")
        match = re.search(r'GROUP\s*\(\s*(\S+)\s+', fd.read(), re.MULTILINE)
        fd.close()
        if match:
          ret = os.path.basename(match.group(1))
          if is_verbose():
            print("Using shared library '%s' instead of '%s'." % (ret, libname))
          return ret
    return libname

  def get_linker_flags(self):
    """Accessor."""
    return self.__linker_flags

  def generate_linker_script(self, dst, modify_start = False):
    """Get linker script from linker, improve it, write improved linker script to given file."""
    (so, se) = run_command([self.__command, "--verbose"])
    if 0 < len(se) and is_verbose():
      print(se)
    match = re.match(r'.*linker script\S+\s*\n=+\s+(.*)\s+=+\s*\n.*', so, re.DOTALL)
    if not match:
      raise RuntimeError("could not extract script from linker output")
    ld_script = match.group(1)
    # Remove unwanted symbol definitions one at a time.
    unwanted_symbols = ["__bss_end__", "__bss_start__", "__end__", "__bss_start", "_bss_end__", "_edata", "_end"]
    for ii in unwanted_symbols:
      ld_script = re.sub(r'\n([ \f\r\t\v]+)(%s)(\s*=[^\n]+)\n' % (ii), r'\n\1/*\2\3*/\n', ld_script, re.MULTILINE)
    ld_script = re.sub(r'SEGMENT_START\s*\(\s*(\S+)\s*,\s*\d*x?\d+\s*\)', r'SEGMENT_START(\1, %s)' % (str(PlatformVar("entry"))), ld_script, re.MULTILINE)
    if modify_start:
      ld_script = re.sub(r'(SEGMENT_START.*\S)\s*\+\s*SIZEOF_HEADERS\s*;', r'\1;', ld_script, re.MULTILINE)
    fd = open(dst, "w")
    fd.write(ld_script)
    fd.close()
    if is_verbose():
      print("Wrote linker script '%s'." % (dst))
    return ld_script

  def link(self, src, dst, extra_args = []):
    """Link a file."""
    cmd = [self.__command, src, "-o", dst] + self.__linker_flags + self.get_library_directory_list() + self.get_library_list() + extra_args + self.__linker_script
    (so, se) = run_command(cmd)
    if 0 < len(se) and is_verbose():
      print(se)
    return so

  def link_binary(self, src, dst):
    """Link a binary file with no bells and whistles."""
    cmd = [self.__command, "--entry=" + str(PlatformVar("entry")), src, "-o", dst] + self.__linker_script
    (so, se) = run_command(cmd)
    if 0 < len(se) and is_verbose():
      print(se)
    return so

  def set_libraries(self, lst):
    """Set libraries to link."""
    self.__libraries = lst

  def set_library_directories(self, lst):
    self.__library_directories = []
    for ii in lst:
      if os.path.isdir(ii):
        self.__library_directories += [ii]

  def set_linker_script(self, op):
    """Use given linker script."""
    self.__linker_script = ["-T", op]

########################################
# Compiler #############################
########################################

class Compiler(Linker):
  """Compiler used to process C source."""

  def __init__(self, op):
    """Constructor."""
    Linker.__init__(self, op)
    self.__compiler_flags = []
    self.__compiler_flags_extra = []
    self.__definitions = []
    self.__include_directories = []

  def add_extra_compiler_flags(self, op):
    """Add extra compiler flags."""
    if is_listing(op):
      for ii in op:
        self.add_extra_compiler_flags(ii)
    elif not op in self.__include_directories and not op in self.__definitions:
      self.__compiler_flags_extra += [op]

  def compile_asm(self, src, dst):
    """Compile a file into assembler source."""
    cmd = [self.get_command(), "-S", src, "-o", dst] + self.__compiler_flags + self.__compiler_flags_extra + self.__definitions + self.__include_directories
    (so, se) = run_command(cmd)
    if 0 < len(se) and is_verbose():
      print(se)

  def compile_and_link(self, src, dst):
    """Compile and link a file directly."""
    cmd = [self.get_command(), src, "-o", dst] + self.__compiler_flags + self.__compiler_flags_extra + self.__definitions + self.__include_directories + self.get_linker_flags() + self.get_library_directory_list() + self.get_library_list()
    (so, se) = run_command(cmd)
    if 0 < len(se) and is_verbose():
      print(se)

  def generate_compiler_flags(self):
    """Generate compiler flags."""
    self.__compiler_flags = []
    if self.command_basename_startswith("g++") or self.command_basename_startswith("gcc"):
      self.__compiler_flags += ["-std=c++11", "-Os", "-ffast-math", "-fno-asynchronous-unwind-tables", "-fno-enforce-eh-specs", "-fno-exceptions", "-fno-implicit-templates", "-fno-rtti", "-fno-threadsafe-statics", "-fno-use-cxa-atexit", "-fno-use-cxa-get-exception-ptr", "-fnothrow-opt", "-fomit-frame-pointer", "-funsafe-math-optimizations", "-fvisibility=hidden", "-fwhole-program", "-march=%s" % (str(PlatformVar("march"))), "-Wall"]
      # Some flags are platform-specific.
      stack_boundary = int(PlatformVar("mpreferred-stack-boundary"))
      if 0 < stack_boundary:
        self.__compiler_flags += ["-mpreferred-stack-boundary=%i" % (stack_boundary)]
    elif self.command_basename_startswith("clang"):
      self.__compiler_flags += ["-std=c++11", "-Os", "-ffast-math", "-fno-asynchronous-unwind-tables", "-fno-exceptions", "-fno-rtti", "-fno-threadsafe-statics", "-fomit-frame-pointer", "-funsafe-math-optimizations", "-fvisibility=hidden", "-march=%s" % (str(PlatformVar("march"))), "-Wall"]
    else:
      raise RuntimeError("compilation not supported with compiler '%s'" % (self.get_command_basename()))

  def preprocess(self, op):
    """Preprocess a file, return output."""
    args = [self.get_command(), op] + self.__compiler_flags_extra + self.__definitions + self.__include_directories
    if self.command_basename_startswith("cl."):
      args += ["/E"]
    else:
      args += ["-E"]
    (so, se) = run_command(args)
    if 0 < len(se) and is_verbose():
      print(se)
    return so

  def set_definitions(self, lst):
    """Set definitions."""
    prefix = "-D"
    self.__definitions = []
    if self.command_basename_startswith("cl."):
      prefix = "/D"
      self.__definitions += [prefix + "WIN32"]
    if isinstance(lst, (list, tuple)):
      for ii in lst:
        self.__definitions += [prefix + ii]
    else:
      self.__definitions += [prefix + lst]

  def set_include_dirs(self, lst):
    """Set include directory listing."""
    prefix = "-I"
    if self.command_basename_startswith("cl."):
      prefix = "/I"
    self.__include_directories = []
    for ii in lst:
      if os.path.isdir(ii):
        new_include_directory = prefix + ii
        if new_include_directory in self.__compiler_flags_extra:
          self.__compiler_flags_extra.remove(new_include_directory)
        self.__include_directories += [new_include_directory]

########################################
# Elfling ##############################
########################################

g_template_elfling_source = """#include "elfling_unpack.hpp"
%s\n
/** Working memory area. */
extern uint8_t %s[];\n
/** Compression output area. */
extern uint8_t %s[];\n
#if defined(__cplusplus)
extern "C" {
#endif\n
/** Jump point after decompression. */
extern void %s();\n
#if defined(__cplusplus)
}
#endif
"""

g_template_elfling_main = """
void _start()
{
  elfling_unpack(elfling_weights, elfling_contexts, %i, %s, elfling_input + %i, %s, %i);
  %s();
}\n
"""

class Elfling:
  """Usage class for the elfling packer program from minas/calodox."""

  def __init__(self, op):
    """Constructor."""
    self.__command = op
    self.__contexts = [0]
    self.__data = [0] * (10 + 4)
    self.__weights = [0]
    self.__uncompressed_size = 12345678

  def compress(self, src, dst):
    """Compress given file, starting from entry point and ending at file end."""
    info = readelf_get_info(src)
    starting_size = os.path.getsize(src)
    if starting_size != info["size"]:
      raise RuntimeError("size of file '%s' differs from header claim: %i != %i" %
          (src, starting_size, info["size"]))
    rfd = open(src, "rb")
    wfd = open(dst, "wb")
    data = rfd.read(starting_size)
    wfd.write(data[info["entry"]:])
    rfd.close()
    wfd.close()
    self.__uncompressed_size = len(data) - info["entry"]
    if is_verbose():
      print("Wrote compressable program block '%s': %i bytes" % (dst, self.__uncompressed_size))
    self.__contexts = []
    self.__weights = []
    (so, se) = run_command([self.__command, dst])
    lines = so.split("\n")
    for ii in lines:
      terms = ii.split()
      if terms and terms[0].startswith("Final"):
        compressed_size = int(terms[1])
        for jj in terms[2:]:
          individual_term = jj.split("*")
          self.__weights += [int(individual_term[0], 10)]
          self.__contexts += [int(individual_term[1], 16)]
    if is_verbose():
      print("Program block compressed into '%s': %i bytes" % (dst + ".pack", compressed_size))
      print("Compression weights: %s" % (str(self.__weights)))
      print("Compression contexts: %s" % (str(self.__contexts)))
    rfd = open(dst + ".pack", "rb")
    compressed_contexts = []
    compressed_weights = []
    uncompressed_size = rfd.read(4)
    uncompressed_size = (struct.unpack("I", uncompressed_size))[0]
    if uncompressed_size != self.__uncompressed_size:
      raise RuntimeError("size given to packer does not match size information in file: %i != %i" %
          (self.__uncompressed_size, uncompressed_size))
    context_count = rfd.read(1)
    context_count = (struct.unpack("B", context_count))[0]
    for ii in range(context_count):
      compressed_weights += struct.unpack("B", rfd.read(1))
    for ii in range(context_count):
      compressed_contexts += struct.unpack("B", rfd.read(1))
    if compressed_contexts != self.__contexts:
      raise RuntimeError("contexts reported by packer do not match context information in file: %s != %s" %
          (str(self.__contexts), str(compressed_contexts)))
    if compressed_weights != self.__weights:
      raise RuntimeError("weights reported by packer do not match weight information in file: %s != %s" %
          (str(self.__weights), str(compressed_weights)))
    read_data = rfd.read()
    rfd.close()
    if len(read_data) != compressed_size:
      raise RuntimeError("size reported by packer does not match length of file: %i != %i" %
          (compressed_size, len(read_data)))
    self.__data = []
    for ii in read_data:
      self.__data += struct.unpack("B", ii)

  def generate_c_data_block(self):
    """Generate direct C code for data block."""
    ret = "static const uint8_t elfling_weights[] =\n{\n  "
    for ii in range(len(self.__weights)):
      if 0 < ii:
        ret += ", "
      ret += "%i" % (self.__weights[ii])
    ret += "\n};\n\nstatic const uint8_t elfling_contexts[] =\n{\n  "
    for ii in range(len(self.__contexts)):
      if 0 < ii:
        ret += ", "
      ret += "%i" % (self.__contexts[ii])
    ret += "\n};\n\nstatic const uint8_t elfling_input[] =\n{\n  "
    for ii in range(ELFLING_PADDING):
      if 0 < ii:
        ret += ", "
      ret += "0"
    for ii in self.__data:
      ret += ", %i" % (ii)
    return ret + "\n};"

  def generate_c_source(self, definition):
    """Generate the C uncompressor source."""
    ret = g_template_elfling_source % (self.generate_c_data_block(), ELFLING_WORK, ELFLING_OUTPUT, ELFLING_UNCOMPRESSED)
    ret += g_template_entry_point % (definition)
    ret += g_template_elfling_main % (len(self.__contexts), ELFLING_WORK, self.get_input_offset(), ELFLING_OUTPUT, self.get_uncompressed_size(), ELFLING_UNCOMPRESSED)
    return ret

  def get_contexts(self):
    """Get contexts. Contains dummy data until compression has been ran."""
    return self.__contexts

  def get_input_offset(self):
    """Get the input offset for compressed data."""
    return ELFLING_PADDING + len(self.__data) - 4

  def get_uncompressed_size(self):
    """Get uncompressed size. Contains dummy value until compression has been ran."""
    return self.__uncompressed_size

  def get_weights(self):
    """Get weights. Contains dummy data until compression has been ran."""
    return self.__weights

  def get_work_size(self):
    """Return the working area size required for decompression."""
    # TODO: Extract this value from the source.
    return (4 << 20) * 16

  def has_data(self):
    """Tell if compression has been done."""
    return ([0] != self.__contexts) and ([0] != self.__weights)

  def write_c_source(self, dst, definition):
    """Write elfling uncompressor source into given location."""
    wfd = open(dst, "wt")
    wfd.write(self.generate_c_source(definition))
    wfd.close()

########################################
# Symbol ###############################
########################################

def sdbm_hash(name):
  """Calculate SDBM hash over a string."""
  ret = 0
  for ii in name:
    ret = (ret * 65599 + ord(ii)) & 0xFFFFFFFF
  return hex(ret)

class Symbol:
  """Represents one (function) symbol."""

  def __init__(self, lst, lib):
    """Constructor."""
    self.__returntype = lst[0]
    if isinstance(lst[1], (list, tuple)):
      self.__name = lst[1][0]
      self.__rename = lst[1][1]
    else:
      self.__name = lst[1]
      self.__rename = lst[1]
    self.__hash = sdbm_hash(self.__name)
    self.__parameters = None
    if 2 < len(lst):
      self.__parameters = lst[2:]
    self.__library = lib

  def create_replacement(self, lib):
    """Create replacement symbol for another library."""
    lst = [self.__returntype, (self.__name, self.__rename)]
    if self.__parameters:
      lst += self.__parameters
    return Symbol(lst, lib)

  def generate_definition(self):
    """Get function definition for given symbol."""
    apientry = ""
    if self.__name[:2] == "gl":
      apientry = "DNLOAD_APIENTRY "
    params = "void"
    if self.__parameters:
      params = ", ".join(self.__parameters)
    return "%s (%s*%s)(%s)" % (self.__returntype, apientry, self.__name, params)

  def generate_prototype(self):
    """Get function prototype for given symbol."""
    apientry = ""
    if self.__name[:2] == "gl":
      apientry = "DNLOAD_APIENTRY "
    params = "void"
    if self.__parameters:
      params = ", ".join(self.__parameters)
    return "(%s (%s*)(%s))" % (self.__returntype, apientry, params)

  def generate_rename_direct(self, prefix):
    """Generate definition to use without a symbol table."""
    if self.is_verbatim():
      return self.generate_rename_verbatim(prefix)
    return "#define %s%s %s" % (prefix, self.__name, self.__rename)

  def generate_rename_tabled(self, prefix):
    """Generate definition to use with a symbol table."""
    if self.is_verbatim():
      return self.generate_rename_verbatim(prefix)
    return "#define %s%s g_symbol_table.%s" % (prefix, self.__name, self.__name)

  def generate_rename_verbatim(self, prefix):
    """Generate 'rename' into itself. Used for functions that are inlined by linker."""
    return "#define %s%s %s" % (prefix, self.__name, self.__name)

  def get_hash(self):
    """Get the hash of symbol name."""
    return self.__hash

  def get_library(self):
    """Access library reference."""
    return self.__library

  def get_library_name(self, linker):
    """Get linkable library object name."""
    return linker.get_library_name(self.__library.get_name())

  def get_name(self):
    """Accessor."""
    return self.__name

  def is_verbatim(self):
    """Tell if this symbol should never be scoured but instead used verbatim."""
    return (None == self.__rename)

  def set_library(self, lib):
    """Replace library with given library."""
    self.__library = lib

  def __lt__(self, rhs):
    """Sorting operator."""
    if self.__library.get_name() < rhs.__library.get_name():
      return True
    elif self.__library.get_name() > rhs.__library.get_name():
      return False
    return self.__name < rhs.__name

  def __str__(self):
    """String representation."""
    return self.__name

########################################
# Library ##############################
########################################

class LibraryDefinition:
  """Represents one library containing symbols."""

  def __init__(self, name, symbols = []):
    """Constructor."""
    self.__name = name
    self.__symbols = []
    self.add_symbols(symbols)

  def add_symbol(self, sym):
    """Add single symbol."""
    self.__symbols += [sym]

  def add_symbols(self, lst):
    """Add a symbol listing."""
    for ii in lst:
      self.add_symbol(Symbol(ii, self))

  def find_symbol(self, op):
    """Find a symbol by name."""
    for ii in self.__symbols:
      if ii.get_name() == op:
        return ii
    return None

  def get_name(self):
    """Accessor."""
    return str(self.__name)

g_library_definition_c = LibraryDefinition("c", (
  ("void", "free", "void*"),
  ("void*", "malloc", "size_t"),
  ("void*", "memset", "void*", "int", "size_t"),
  ("int", "printf", "const char* __restrict", "..."),
  ("int", "puts", "const char*"),
  ("void", "qsort", "void*", "size_t", "size_t", "int (*)(const void*, const void*)"),
  ("void*", "realloc", "void*", "size_t"),
  ("int", ("rand", "bsd_rand")),
  ("int", "random"),
  ("unsigned", "sleep", "unsigned"),
  ("void", ("srand", "bsd_srand"), "unsigned int"),
  ("void", "srandom", "unsigned int"),
  ))
g_library_definition_bcm_host = LibraryDefinition("bcm_host", (
  ("void", "bcm_host_init"),
  ("DISPMANX_DISPLAY_HANDLE_T", "vc_dispmanx_display_open", "uint32_t"),
  ("DISPMANX_ELEMENT_HANDLE_T", "vc_dispmanx_element_add", "DISPMANX_UPDATE_HANDLE_T", "DISPMANX_DISPLAY_HANDLE_T", "int32_t", "const VC_RECT_T*", "DISPMANX_RESOURCE_HANDLE_T", "const VC_RECT_T*", "DISPMANX_PROTECTION_T", "VC_DISPMANX_ALPHA_T*", "DISPMANX_CLAMP_T*", "DISPMANX_TRANSFORM_T"),
  ("DISPMANX_UPDATE_HANDLE_T", "vc_dispmanx_update_start", "int32_t"),
  ("int", "vc_dispmanx_update_submit_sync", "DISPMANX_UPDATE_HANDLE_T"),
  ("int32_t", "graphics_get_display_size", "const uint16_t", "uint32_t*", "uint32_t*"),
  ))
g_library_definition_egl = LibraryDefinition("EGL", (
  ("EGLBoolean", "eglChooseConfig", "EGLDisplay", "EGLint const*", "EGLConfig*", "EGLint", "EGLint*"),
  ("EGLContext", "eglCreateContext", "EGLDisplay", "EGLConfig", "EGLContext", "EGLint const*"),
  ("EGLSurface", "eglCreateWindowSurface", "EGLDisplay", "EGLConfig", "EGLNativeWindowType", "EGLint const*"),
  ("EGLBoolean", "eglGetConfigs", "EGLDisplay", "EGLConfig*", "EGLint", "EGLint*"),
  ("EGLDisplay", "eglGetDisplay", "NativeDisplayType"),
  ("EGLBoolean", "eglInitialize", "EGLDisplay", "EGLint*", "EGLint*"),
  ("EGLBoolean", "eglMakeCurrent", "EGLDisplay", "EGLSurface", "EGLSurface", "EGLContext"),
  ("EGLBoolean", "eglSwapBuffers", "EGLDisplay", "EGLSurface"),
  ("EGLBoolean", "eglTerminate", "EGLDisplay"),
  ))
g_library_definition_gl = LibraryDefinition(PlatformVar("gl_library"), (
  ("void", "glActiveTexture", "GLenum"),
  ("void", "glAttachShader", "GLuint", "GLuint"),
  ("void", "glBindBuffer", "GLenum", "GLuint"),
  ("void", "glBindFramebuffer", "GLenum", "GLuint"),
  ("void", "glBindProgramPipeline", "GLuint"),
  ("void", "glBindRenderbuffer", "GLenum", "GLuint"),
  ("void", "glBindTexture", "GLenum", "GLuint"),
  ("void", "glBufferData", "GLenum", "GLsizeiptr", "const GLvoid*", "GLenum"),
  ("void", "glClear", "GLbitfield"),
  ("void", "glClearColor", "GLclampf", "GLclampf", "GLclampf", "GLclampf"),
  ("void", "glClearDepthf", "GLclampf"),
  ("void", "glCompileShader", "GLuint"),
  ("GLuint", "glCreateProgram"),
  ("GLuint", "glCreateShader", "GLenum"),
  ("GLuint", "glCreateShaderProgramv", "GLenum", "GLsizei", "const char**"),
  ("void", "glCullFace", "GLenum"),
  ("void", "glDeleteBuffers", "GLsizei", "const GLuint*"),
  ("void", "glDepthFunc", "GLenum"),
  ("void", "glDepthMask", "GLboolean"),
  ("void", "glDisable", "GLenum"),
  ("void", "glDisableVertexAttribArray", "GLuint"),
  ("void", "glDrawArrays", "GLenum", "GLint", "GLsizei"),
  ("void", "glDrawElements", "GLenum", "GLsizei", "GLenum", "const GLvoid*"),
  ("void", "glEnable", "GLenum"),
  ("void", "glEnableVertexAttribArray", "GLuint"),
  ("void", "glFramebufferTexture2D", "GLenum", "GLenum", "GLenum", "GLuint", "GLint"),
  ("void", "glFramebufferRenderbuffer", "GLenum", "GLenum", "GLint", "GLuint"),
  ("void", "glGenerateMipmap", "GLenum"),
  ("void", "glGenBuffers", "GLsizei", "GLuint*"),
  ("void", "glGenFramebuffers", "GLsizei", "GLuint*"),
  ("void", "glGenProgramPipelines", "GLsizei", "GLuint*"),
  ("void", "glGenTextures", "GLsizei", "GLuint*"),
  ("void", "glGenRenderbuffers", "GLsizei", "GLuint*"),
  ("void", "glDeleteTextures", "GLsizei", "GLuint*"),
  ("GLint", "glGetAttribLocation", "GLuint", "const GLchar*"),
  ("GLint", "glGetUniformLocation", "GLuint", "const GLchar*"),
  ("void", "glLineWidth", "GLfloat"),
  ("void", "glLinkProgram", "GLuint"),
  ("void", "glProgramUniform1f", "GLuint", "GLint", "GLfloat"),
  ("void", "glProgramUniform1fv", "GLuint", "GLint", "GLsizei", "const GLfloat*"),
  ("void", "glProgramUniform1i", "GLuint", "GLint", "GLint"),
  ("void", "glProgramUniform2fv", "GLuint", "GLint", "GLsizei", "const GLfloat*"),
  ("void", "glProgramUniform3fv", "GLuint", "GLint", "GLsizei", "const GLfloat*"),
  ("void", "glProgramUniform3iv", "GLint", "GLsizei", "const GLint*"),
  ("void", "glProgramUniform4fv", "GLuint", "GLint", "GLsizei", "const GLfloat*"),
  ("void", "glProgramUniformMatrix3fv", "GLuint", "GLint", "GLsizei", "GLboolean", "const GLfloat*"),
  ("void", "glRectf", "GLfloat", "GLfloat", "GLfloat", "GLfloat"),
  ("void", "glRecti", "GLint", "GLint", "GLint", "GLint"),
  ("void", "glRects", "GLshort", "GLshort", "GLshort", "GLshort"),
  ("void", "glRenderbufferStorage", "GLenum", "GLenum", "GLsizei", "GLsizei"),
  ("void", "glRotatef", "GLfloat", "GLfloat", "GLfloat", "GLfloat"),
  ("void", "glShaderSource", "GLuint", "GLsizei", "const GLchar**", "const GLint*"),
  ("void", "glTexImage2D", "GLenum", "GLint", "GLint", "GLsizei", "GLsizei", "GLint", "GLenum", "GLenum", "const GLvoid*"),
  ("void", "glTexImage2DMultisample", "GLenum", "GLsizei", "GLint", "GLsizei", "GLsizei", "GLboolean"),
  ("void", "glTexImage3D", "GLenum", "GLint", "GLint", "GLsizei", "GLsizei", "GLsizei", "GLint", "GLenum", "GLenum", "const GLvoid*"),
  ("void", "glTexSubImage2D", "GLenum", "GLint", "GLint", "GLint", "GLsizei", "GLsizei", "GLenum", "GLenum", "const GLvoid*"),
  ("void", "glTexSubImage3D", "GLenum", "GLint", "GLint", "GLint", "GLint", "GLsizei", "GLsizei", "GLsizei", "GLenum", "GLenum", "const GLvoid*"),
  ("void", "glTexParameteri", "GLenum", "GLenum", "GLint"),
  ("void", "glUseProgram", "GLuint"),
  ("void", "glUseProgramStages", "GLuint", "GLbitfield", "GLuint"),
  ("void", "glUniform1f", "GLint", "GLfloat"),
  ("void", "glUniform1i", "GLint", "GLint"),
  ("void", "glUniform2f", "GLint", "GLfloat", "GLfloat"),
  ("void", "glUniform2i", "GLint", "GLint", "GLint"),
  ("void", "glUniform3f", "GLint", "GLfloat", "GLfloat", "GLfloat"),
  ("void", "glUniform3i", "GLint", "GLint", "GLint", "GLint"),
  ("void", "glUniform4f", "GLint", "GLfloat", "GLfloat", "GLfloat", "GLfloat"),
  ("void", "glUniform4i", "GLint", "GLint", "GLint", "GLint", "GLint"),
  ("void", "glUniform1fv", "GLint", "GLsizei", "const GLfloat*"),
  ("void", "glUniform2fv", "GLint", "GLsizei", "const GLfloat*"),
  ("void", "glUniform3fv", "GLint", "GLsizei", "const GLfloat*"),
  ("void", "glUniform4fv", "GLint", "GLsizei", "const GLfloat*"),
  ("void", "glUniformMatrix3fv", "GLint", "GLsizei", "GLboolean", "const GLfloat*"),
  ("void", "glUniformMatrix4fv", "GLint", "GLsizei", "GLboolean", "const GLfloat*"),
  ("void", "glVertexAttribPointer", "GLuint", "GLint", "GLenum", "GLboolean", "GLsizei", "const GLvoid*"),
  ("void", "glViewport", "GLint", "GLint", "GLsizei", "GLsizei"),
  ))
g_library_definition_glu = LibraryDefinition("GLU", (
  ("GLint", "gluBuild3DMipmaps", "GLenum", "GLint", "GLsizei", "GLsizei", "GLsizei", "GLenum", "GLenum", "const void*"),
  ))
g_library_definition_m = LibraryDefinition("m", (
  ("double", "acos", "double"),
  ("float", "acosf", "float"),
  ("float", "atanf", "float"),
  ("float", ("ceilf", None), "float"),
  ("float", "cosf", "float"),
  ("float", ("fabsf", None), "float"),
  ("float", ("floorf", None), "float"),
  ("float", ("fmaxf", None), "float", "float"),
  ("float", ("fminf", None), "float", "float"),
  ("float", "fmodf", "float", "float"),
  ("long", "lrintf", "float"),
  ("float", "powf", "float", "float"),
  ("float", "roundf", "float"),
  ("float", "sinf", "float"),
  ("float", ("sqrtf", None), "float"),
  ("float", ("tanf", None), "float"),
  ("float", "tanhf", "float"),
  ))
g_library_definition_sdl = LibraryDefinition("SDL", (
  ("SDL_cond*", "SDL_CreateCond"),
  ("SDL_mutex*", "SDL_CreateMutex"),
  ("SDL_Thread*", "SDL_CreateThread", "int (*)(void*)", "void*"),
  ("int", "SDL_CondSignal", "SDL_cond*"),
  ("int", "SDL_CondWait", "SDL_cond*", "SDL_mutex*"),
  ("void", "SDL_Delay", "Uint32"),
  ("void", "SDL_DestroyCond", "SDL_cond*"),
  ("void", "SDL_DestroyMutex", "SDL_mutex*"),
  ("int", "SDL_mutexP", "SDL_mutex*"),
  ("int", "SDL_mutexV", "SDL_mutex*"),
  ("uint32_t", "SDL_GetTicks"),
  ("void", "SDL_GL_SwapBuffers"),
  ("int", "SDL_Init", "Uint32"),
  ("int", "SDL_OpenAudio", "SDL_AudioSpec*", "SDL_AudioSpec*"),
  ("void", "SDL_PauseAudio", "int"),
  ("int", "SDL_PollEvent", "SDL_Event*"),
  ("void", "SDL_Quit"),
  ("SDL_Surface*", "SDL_SetVideoMode", "int", "int", "int", "Uint32"),
  ("int", "SDL_ShowCursor", "int"),
  ("void", "SDL_WaitThread", "SDL_Thread*", "int*"),
  ))
g_library_definition_sdl2 = LibraryDefinition("SDL2", (
  ("SDL_Renderer*", "SDL_CreateRenderer", "SDL_Window*", "int", "Uint32"),
  ("SDL_Thread*", "SDL_CreateThread", "int (*)(void*)", "const char*", "void*"),
  ("SDL_Window*", "SDL_CreateWindow", "const char*", "int", "int", "int", "int", "Uint32"),
  ("int", "SDL_CreateWindowAndRenderer", "int", "int", "Uint32", "SDL_Window**", "SDL_Renderer**"),
  ("SDL_GLContext", "SDL_GL_CreateContext", "SDL_Window*"),
  ("int", "SDL_LockMutex", "SDL_mutex*"),
  ("void", "SDL_GL_SwapWindow", "SDL_Window*"),
  ("int", "SDL_RenderSetLogicalSize", "SDL_Renderer*", "int", "int"),
  ("int", "SDL_UnlockMutex", "SDL_mutex*"),
  ))

g_library_definitions = (
    g_library_definition_c,
    g_library_definition_bcm_host,
    g_library_definition_egl,
    g_library_definition_gl,
    g_library_definition_glu,
    g_library_definition_m,
    g_library_definition_sdl,
    g_library_definition_sdl2,
    )

########################################
# C header generation ##################
########################################

g_template_header_begin = """#ifndef DNLOAD_H
#define DNLOAD_H\n
/** \\file
 * \\brief Dynamic loader header stub.
 *
 * This file was automatically generated by '%s'.
 */\n
#if defined(WIN32)
/** \cond */
#define _USE_MATH_DEFINES
#define NOMINMAX
/** \endcond */
#else
/** \cond */
#define GL_GLEXT_PROTOTYPES
/** \endcond */
#endif\n
#if defined(__cplusplus)
#include <cmath>
#include <cstdlib>
#else
#include <math.h>
#include <stdlib.h>
#endif\n
#if defined(DNLOAD_VIDEOCORE)
#include \"bcm_host.h\"
#include \"EGL/egl.h\"
#endif\n
#if defined(%s)
#if defined(WIN32)
#include \"windows.h\"
#include \"GL/glew.h\"
#include \"GL/glu.h\"
#include \"SDL.h\"
#elif defined(__APPLE__)
#include \"GL/glew.h\"
#include <OpenGL/glu.h>
#include <SDL/SDL.h>
#else
#if defined(DNLOAD_GLESV2)
#include \"GLES2/gl2.h\"
#include \"GLES2/gl2ext.h\"
#else
#include \"GL/glew.h\"
#include \"GL/glu.h\"
#endif
#include \"SDL.h\"
#endif
#include \"bsd_rand.h\"
#else
#if defined(__APPLE__)
#include <OpenGL/gl.h>
#include <OpenGL/glext.h>
#include <OpenGL/glu.h>
#include <SDL/SDL.h>
#else
#if defined(DNLOAD_GLESV2)
#include \"GLES2/gl2.h\"
#include \"GLES2/gl2ext.h\"
#else
#include \"GL/gl.h\"
#include \"GL/glext.h\"
#include \"GL/glu.h\"
#endif
#include \"SDL.h\"
#endif
#endif\n
/** Macro stringification helper (adds indirection). */
#define DNLOAD_MACRO_STR_HELPER(op) #op
/** Macro stringification. */
#define DNLOAD_MACRO_STR(op) DNLOAD_MACRO_STR_HELPER(op)\n
#if defined(DNLOAD_GLESV2)
/** Apientry definition (OpenGL ES 2.0). */
#define DNLOAD_APIENTRY GL_APIENTRY
#else
/** Apientry definition (OpenGL). */
#define DNLOAD_APIENTRY GLAPIENTRY
#endif\n
#if (defined(_LP64) && _LP64) || (defined(__LP64__) && __LP64__)
/** Size of pointer in bytes (64-bit). */
#define DNLOAD_POINTER_SIZE 8
#else
/** Size of pointer in bytes (32-bit). */
#define DNLOAD_POINTER_SIZE 4
#endif\n
#if !defined(%s)
/** Error string for when assembler exit procedure is not available. */
#define DNLOAD_ASM_EXIT_ERROR "no assembler exit procedure defined for current operating system or architecture"
/** Perform exit syscall in assembler. */
static void asm_exit(void)
{
#if !defined(DNLOAD_NO_DEBUGGER_TRAP) && (defined(__x86_64__) || defined(__i386__))
  asm("int $0x3" : /* no output */ : /* no input */ : /* no clobber */);
#elif defined(__x86_64__)
#if defined(__FreeBSD__)
  asm_exit() asm("syscall" : /* no output */ : "a"(1) : /* no clobber */);
#elif defined(__linux__)
  asm_exit() asm("syscall" : /* no output */ : "a"(60) : /* no clobber */);
#else
#pragma message DNLOAD_MACRO_STR(DNLOAD_ASM_EXIT_ERROR)
#error
#endif
#elif defined(__i386__)
#if defined(__FreeBSD__) || defined(__linux__)
  asm("int $0x80" : /* no output */ : "a"(1) : /* no clobber */);
#else
#pragma message DNLOAD_MACRO_STR(DNLOAD_ASM_EXIT_ERROR)
#error
#endif
#elif defined(__arm__)
#if defined(__linux__)
  register int r7 asm("r7") = 1;
  asm("swi #0" : /* no output */ : "r"(r7) : /* no clobber */);
#else
#pragma message DNLOAD_MACRO_STR(DNLOAD_ASM_EXIT_ERROR)
#error
#endif
#else
#pragma message DNLOAD_MACRO_STR(DNLOAD_ASM_EXIT_ERROR)
#error
#endif
}
#endif
"""

g_template_entry_point = """
#if defined(__clang__)
/** Visibility declaration for symbols that require it (clang). */
#define DNLOAD_VISIBILITY __attribute__((visibility("default")))
#else
/** Visibility declaration for symbols that require it (gcc). */
#define DNLOAD_VISIBILITY __attribute__((externally_visible,visibility("default")))
#endif\n
#if !defined(%s)
#if defined(__cplusplus)
extern "C" {
#endif
/** Program entry point. */
void _start() DNLOAD_VISIBILITY;
#if defined(__cplusplus)
}
#endif
#endif
"""

g_template_und_symbols = """
#if !defined(%s) && defined(__FreeBSD__)
#if defined(__cplusplus)
extern "C" {
#endif
/** Symbol required by libc. */
void *environ DNLOAD_VISIBILITY;
/** Symbol required by libc. */
void *__progname DNLOAD_VISIBILITY;
#if defined(__cplusplus)
}
#endif
#endif
"""

g_template_header_end = """
#endif
"""

g_template_loader = """
#if defined(%s)
/** \cond */
#define dnload()
/** \endcond */
#else
%s
#endif
"""

g_template_loader_dlfcn = """#include <dlfcn.h>
static const char g_dynstr[] = \"\"
%s;
/** \\brief Perform init.
 *
 * dlopen/dlsym -style.
 */
static void dnload(void)
{
  char *src = (char*)g_dynstr;
  void **dst = (void**)&g_symbol_table;
  do {
    void *handle = dlopen(src, RTLD_LAZY);
    for(;;)
    {
      while(*(src++));
      if(!*(src))
      {
        break;
      }
      *dst++ = dlsym(handle, src);
    }
  } while(*(++src));
}"""

g_template_loader_hash = """#include <stdint.h>
/** \\brief SDBM hash function.
 *
 * \\param op String to hash.
 * \\return Full hash.
 */
static uint32_t sdbm_hash(const uint8_t *op)
{
  uint32_t ret = 0;
  for(;;)
  {
    uint32_t cc = *op++;
    if(!cc)
    {
      return ret;
    }
    ret = ret * 65599 + cc;
  }
}
#if defined(__FreeBSD__)
#include <sys/link_elf.h>
#elif defined(__linux__)
#include <link.h>
#else
#error "no elf header location known for current platform"
#endif
#if (8 == DNLOAD_POINTER_SIZE)
/** Elf header type. */
typedef Elf64_Ehdr dnload_elf_ehdr_t;
/** Elf program header type. */
typedef Elf64_Phdr dnload_elf_phdr_t;
/** Elf dynamic structure type. */
typedef Elf64_Dyn dnload_elf_dyn_t;
/** Elf symbol table entry type. */
typedef Elf64_Sym dnload_elf_sym_t;
/** Elf dynamic structure tag type. */
typedef Elf64_Sxword dnload_elf_tag_t;
#else
/** Elf header type. */
typedef Elf32_Ehdr dnload_elf_ehdr_t;
/** Elf program header type. */
typedef Elf32_Phdr dnload_elf_phdr_t;
/** Elf dynamic structure type. */
typedef Elf32_Dyn dnload_elf_dyn_t;
/** Elf symbol table entry type. */
typedef Elf32_Sym dnload_elf_sym_t;
/** Elf dynamic structure tag type. */
typedef Elf32_Sword dnload_elf_tag_t;
#endif
/** \\brief ELF base address. */
#define ELF_BASE_ADDRESS %s
/** \\brief Get dynamic section element by tag.
 *
 * \\param dyn Dynamic section.
 * \\param tag Tag to look for.
 * \\return Pointer to dynamic element.
 */
static const dnload_elf_dyn_t* elf_get_dynamic_element_by_tag(const void *dyn, dnload_elf_tag_t tag)
{
  const dnload_elf_dyn_t *dynamic = (const dnload_elf_dyn_t*)dyn;
  do {
    ++dynamic; // First entry in PT_DYNAMIC is probably nothing important.
#if defined(__linux__) && defined(DNLOAD_SAFE_SYMTAB_HANDLING)
    if(0 == dynamic->d_tag)
    {
      return NULL;
    }
#endif
  } while(dynamic->d_tag != tag);
  return dynamic;
}
#if defined(DNLOAD_NO_FIXED_R_DEBUG_ADDRESS) || defined(DNLOAD_SAFE_SYMTAB_HANDLING)
/** \\brief Get the address associated with given tag in a dynamic section.
 *
 * \\param dyn Dynamic section.
 * \\param tag Tag to look for.
 * \\return Address matching given tag.
 */
static const void* elf_get_dynamic_address_by_tag(const void *dyn, dnload_elf_tag_t tag)
{
  const dnload_elf_dyn_t *dynamic = elf_get_dynamic_element_by_tag(dyn, tag);
#if defined(__linux__) && defined(DNLOAD_SAFE_SYMTAB_HANDLING)
  if(NULL == dynamic)
  {
    return NULL;
  }
#endif
  return (const void*)dynamic->d_un.d_ptr;
}
#endif
#if !defined(DNLOAD_NO_FIXED_R_DEBUG_ADDRESS)
/** Link map address, fixed location in ELF headers. */
extern const struct r_debug *dynamic_r_debug;
#endif
/** \\brief Get the program link map.
 *
 * \\return Link map struct.
 */
static const struct link_map* elf_get_link_map()
{
#if defined(DNLOAD_NO_FIXED_R_DEBUG_ADDRESS)
  // ELF header is in a fixed location in memory.
  // First program header is located directly afterwards.
  const dnload_elf_ehdr_t *ehdr = (const dnload_elf_ehdr_t*)ELF_BASE_ADDRESS;
  const dnload_elf_phdr_t *phdr = (const dnload_elf_phdr_t*)((size_t)ehdr + (size_t)ehdr->e_phoff);
  do {
    ++phdr; // Dynamic header is probably never first in PHDR list.
  } while(phdr->p_type != PT_DYNAMIC);
  // Find the debug entry in the dynamic header array.
  {
    const struct r_debug *debug = (const struct r_debug*)elf_get_dynamic_address_by_tag((const void*)phdr->p_vaddr, DT_DEBUG);
    return debug->r_map;
  }
#else
  return dynamic_r_debug->r_map;
#endif
}
/** \\brief Return pointer from link map address.
 *
 * \\param lmap Link map.
 * \\param ptr Pointer in this link map.
 */
static const void* elf_transform_dynamic_address(const struct link_map *lmap, const void *ptr)
{
#if defined(__linux__)
  // Addresses may also be absolute.
  if(ptr >= (void*)(size_t)lmap->l_addr)
  {
    return ptr;
  }
#endif
  return (uint8_t*)ptr + (size_t)lmap->l_addr;
}
#if defined(DNLOAD_SAFE_SYMTAB_HANDLING)
/** \\brief Get address of one dynamic section corresponding to given library.
 *
 * \param lmap Link map.
 * \param tag Tag to look for.
 * \\return Pointer to given section or NULL.
 */
static const void* elf_get_library_dynamic_section(const struct link_map *lmap, dnload_elf_tag_t tag)
{
  return elf_transform_dynamic_address(lmap, elf_get_dynamic_address_by_tag(lmap->l_ld, tag));
}
#endif
/** \\brief Find a symbol in any of the link maps.
 *
 * Should a symbol with name matching the given hash not be present, this function will happily continue until
 * we crash. Size-minimal code has no room for error checking.
 *
 * \\param hash Hash of the function name string.
 * \\return Symbol found.
 */
static void* dnload_find_symbol(uint32_t hash)
{
  const struct link_map* lmap = elf_get_link_map();
#if defined(__linux__) && (8 == DNLOAD_POINTER_SIZE)
  // On 64-bit Linux, the second entry is not usable.
  lmap = lmap->l_next;
#endif
  for(;;)
  {
    // First entry is this object itself, safe to advance first.
    lmap = lmap->l_next;
    {
#if defined(DNLOAD_SAFE_SYMTAB_HANDLING)
      // Find symbol from link map. We need the string table and a corresponding symbol table.
      const char* strtab = (const char*)elf_get_library_dynamic_section(lmap, DT_STRTAB);
      const dnload_elf_sym_t *symtab = (const dnload_elf_sym_t*)elf_get_library_dynamic_section(lmap, DT_SYMTAB);
      const uint32_t* hashtable = (const uint32_t*)elf_get_library_dynamic_section(lmap, DT_HASH);
      unsigned dynsymcount;
      unsigned ii;
#if defined(__linux__)
      if(NULL == hashtable)
      {
        hashtable = (const uint32_t*)elf_get_library_dynamic_section(lmap, DT_GNU_HASH);
        // DT_GNU_HASH symbol counter borrows from FreeBSD rtld-elf implementation.
        dynsymcount = 0;
        {
          unsigned bucket_count = hashtable[0];
          const uint32_t* buckets = hashtable + 4 + ((sizeof(void*) / 4) * hashtable[2]);
          const uint32_t* chain_zero = buckets + bucket_count + hashtable[1];
          for(ii = 0; (ii < bucket_count); ++ii)
          {
            unsigned bkt = buckets[ii];
            if(bkt == 0)
            {
              continue;
            }
            {
              const uint32_t* hashval = chain_zero + bkt;
              do {
                ++dynsymcount;
              } while(0 == (*hashval++ & 1u));              
            }
          }
        }
      }
      else
#endif
      {
        dynsymcount = hashtable[1];
      }
      for(ii = 0; (ii < dynsymcount); ++ii)
      {
        const dnload_elf_sym_t *sym = &symtab[ii];
#else
      // Assume DT_SYMTAB dynamic entry immediately follows DT_STRTAB dynamic entry.
      // Assume DT_STRTAB memory block immediately follows DT_SYMTAB dynamic entry.
      const dnload_elf_dyn_t *dynamic = elf_get_dynamic_element_by_tag(lmap->l_ld, DT_STRTAB);
      const char* strtab = (const char*)elf_transform_dynamic_address(lmap, (const void*)(dynamic->d_un.d_ptr));
      const dnload_elf_sym_t *sym = (const dnload_elf_sym_t*)elf_transform_dynamic_address(lmap, (const void*)((dynamic + 1)->d_un.d_ptr));
      for(; ((void*)sym < (void*)strtab); ++sym)
      {
#endif
        const char *name = strtab + sym->st_name;
#if defined(DNLOAD_SAFE_SYMTAB_HANDLING)
        // UND symbols have valid names but no value.
        if(!sym->st_value)
        {
          continue;
        }
#endif
        if(sdbm_hash((const uint8_t*)name) == hash)
        {
          //if(!sym->st_value)
          //{
          //  printf("incorrect symbol in library '%%s': '%%s'\\n", lmap->l_name, name);
          //}
          return (void*)((const uint8_t*)sym->st_value + (size_t)lmap->l_addr);
        }
      }
    }
  }
}
/** \\brief Perform init.
 *
 * Import by hash - style.
 */
static void dnload(void)
{
  unsigned ii;
  for(ii = 0; (%i > ii); ++ii)
  {
    void **iter = ((void**)&g_symbol_table) + ii;
    *iter = dnload_find_symbol(*(uint32_t*)iter);
  }
}"""

g_template_loader_vanilla = """/** \cond */
#define dnload()
/** \endcond */"""

g_template_symbol_definitions = """
#if defined(%s)
/** \cond */
%s
/** \endcond */
#else
/** \cond */
%s
/** \endcond */
#endif
"""

g_template_symbol_table = """
#if !defined(%s)
/** \\brief Symbol table structure.
 *
 * Contains all the symbols required for dynamic linking.
 */
static struct SymbolTableStruct
{
%s
} g_symbol_table%s;
#endif
"""

def analyze_source(source, prefix):
  """Analyze given preprocessed C source for symbol names."""
  symbolre =  re.compile(r"[\s:;&\|\<\>\=\^\+\-\*/\(\)\?]" + prefix + "([a-zA-Z0-9_]+)(?=[\s\(])")
  results = symbolre.findall(source, re.MULTILINE)
  ret = set()
  for ii in results:
    symbolset = set()
    symbolset.add(ii)
    ret = ret.union(symbolset)
  return ret

def generate_loader(mode, symbols, definition, linker):
  """Generate the loader code."""
  if "vanilla" == mode:
    loader_content = generate_loader_vanilla()
  elif "dlfcn" == mode:
    loader_content = generate_loader_dlfcn(symbols, linker)
  else:
    loader_content = generate_loader_hash(symbols)
  ret = g_template_loader % (definition, loader_content)
  ret += g_template_entry_point % (definition)
  if "maximum" != mode:
    ret += g_template_und_symbols % (definition)
  return ret

def generate_loader_dlfcn(symbols, linker):
  """Generate dlopen/dlsym loader code."""
  dlfcn_string = ""
  current_lib = None
  for ii in symbols:
    symbol_lib = ii.get_library().get_name()
    if current_lib != symbol_lib:
      if current_lib:
        dlfcn_string += "\"\\0%s\\0\"\n" % (ii.get_library_name(linker))
      else:
        dlfcn_string += "\"%s\\0\"\n" % (ii.get_library_name(linker))
      current_lib = symbol_lib
    dlfcn_string += "\"%s\\0\"\n" % (ii)
  dlfcn_string += "\"\\0\""
  return g_template_loader_dlfcn % (dlfcn_string)

def generate_loader_hash(symbols):
  """Generate import by hash loader code."""
  return g_template_loader_hash % (str(PlatformVar("entry")), len(symbols))

def generate_loader_vanilla():
  """Generate loader that actually leaves the loading to the operating system."""
  return g_template_loader_vanilla

def generate_symbol_definitions(mode, symbols, prefix, definition):
  """Generate a listing of definitions from replacement symbols to real symbols."""
  direct = []
  tabled = []
  for ii in symbols:
    direct += [ii.generate_rename_direct(prefix)]
    tabled += [ii.generate_rename_tabled(prefix)]
  if "vanilla" == mode:
    tabled = direct
  return g_template_symbol_definitions % (definition, "\n".join(direct), "\n".join(tabled))

def generate_symbol_struct(mode, symbols, definition):
  """Generate the symbol struct definition."""
  if "vanilla" == mode:
    return ""
  definitions = []
  hashes = []
  symbol_table_content = ""
  for ii in symbols:
    definitions += ["  %s;" % (ii.generate_definition())]
    hashes += ["  %s%s," % (ii.generate_prototype(), ii.get_hash())]
  if "dlfcn" != mode:
    symbol_table_content = " =\n{\n%s\n}" % ("\n".join(hashes))
  return g_template_symbol_table % (definition, "\n".join(definitions), symbol_table_content)

########################################
# Functions ############################
########################################

def check_executable(op):
  """Check for existence of a single binary."""
  try:
    proc = subprocess.Popen([op], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
  except OSError:
    return False
  try:
    if proc.poll():
      proc.kill()
  except OSError:
    return True
  return True

def collect_libraries(libraries, symbols, compilation_mode):
  """Collect libraries to link against from symbols given."""
  if not libraries:
    if "dlfcn" == compilation_mode:
      raise RuntimeError("cannot autodetect libraries for compilation mode '%s'" % compilation_mode)
    library_set = set()
    for ii in symbols:
      library_set = library_set.union(set([ii.get_library().get_name()]))
    libraries = list(library_set)
    output_message = "Autodetected libraries to link against: "
  else:
    output_message = "Linking against libraries: "
  # Reorder libraries to ensure there is no problems with library scouring and UND symbols.
  problematic_libraries = ["c", "m", "bcm_host"] # Order is important.
  front = []
  for ii in problematic_libraries:
    if ii in libraries:
      libraries.remove(ii)
      front += [ii]
  ret = front + sorted(libraries)
  if is_verbose:
    print("%s%s" % (output_message, str(ret)))
  return ret

def compress_file(compression, pretty, src, dst):
  """Compress a file to be a self-extracting file-dumping executable."""
  str_tail = "sed 1d"
  str_cleanup = ";exit"
  if pretty:
    str_tail = "tail -n+2"
    str_cleanup = ";rm ~;exit"
  if "lzma" == compression:
    command = ["xz", "--format=lzma", "--lzma1=preset=9,lc=1,lp=0,pb=0", "--stdout"]
    header = "HOME=/tmp/i;%s $0|lzcat>~;chmod +x ~;~%s" % (str_tail, str_cleanup)
  elif "raw" == compression:
    command = ["xz", "-9", "--extreme", "--format=raw", "--stdout"]
    header = "HOME=/tmp/i;%s $0|xzcat -F raw>~;chmod +x ~;~%s" % (str_tail, str_cleanup)
  elif "xz" == compression:
    command = ["xz", "--format=xz", "--lzma2=preset=9,lc=1,pb=0", "--stdout"]
    header = "HOME=/tmp/i;%s $0|xzcat>~;chmod +x ~;~%s" % (str_tail, str_cleanup)
  else:
    raise RuntimeError("unknown compression format '%s'" % compression)
  (compressed, se) = run_command(command + [src], False)
  wfd = open(dst, "wb")
  wfd.write((header + "\n").encode())
  wfd.write(compressed)
  wfd.close()
  make_executable(dst)
  print("Wrote '%s': %i bytes" % (dst, os.path.getsize(dst)))

def file_is_ascii_text(op):
  """Check if given file contains nothing but ASCII7 text."""
  if not os.path.isfile(op):
    return False
  fd = open(op, "rb")
  while True:
    line = fd.readline()
    if 0 >= len(line):
      fd.close()
      return True
    try:
      line.decode("ascii")
    except UnicodeDecodeError:
      fd.close()
      return False

def find_library_definition(op):
  """Find library definition with name."""
  for ii in g_library_definitions:
    if ii.get_name() == op:
      return ii
  return None

def find_symbol(op):
  """Find single symbol with name."""
  for ii in g_library_definitions:
    ret = ii.find_symbol(op)
    if ret:
      return ret
  raise RuntimeError("symbol '%s' not known, please add it to the script" % (op))

def find_symbols(lst):
  """Find symbol object(s) corresponding to symbol string(s)."""
  ret = []
  for ii in lst:
    ret += [find_symbol(ii)]
  return ret

def generate_binary_minimal(source_file, compiler, assembler, linker, objcopy, und_symbols, elfling, libraries,
    output_file):
  """Generate a binary using all possible tricks. Return whether or not reprocess is necessary."""
  if source_file:
    compiler.compile_asm(source_file, output_file + ".S")
  segment_ehdr = AssemblerSegment(assembler_ehdr)
  if osarch_is_32_bit():
    segment_phdr_dynamic = AssemblerSegment(assembler_phdr32_dynamic)
    segment_phdr_interp = AssemblerSegment(assembler_phdr32_interp)
  elif osarch_is_64_bit():
    segment_phdr_dynamic = AssemblerSegment(assembler_phdr64_dynamic)
    segment_phdr_interp = AssemblerSegment(assembler_phdr64_interp)
  else:
    raise_unknown_address_size()
  segment_dynamic = AssemblerSegment(assembler_dynamic)
  segment_hash = AssemblerSegment(assembler_hash)
  segment_interp = AssemblerSegment(assembler_interp)
  segment_strtab = AssemblerSegment(assembler_strtab)
  segment_symtab = AssemblerSegment(assembler_symtab)
  # There may be symbols necessary for addition.
  if is_listing(und_symbols):
    segment_symtab.add_symbol_empty()
    for ii in und_symbols:
      segment_symtab.add_symbol_und(ii)
    for ii in reversed(und_symbols):
      segment_strtab.add_strtab(ii)
    segment_dynamic.add_dt_symtab("symtab")
    segment_dynamic.add_dt_hash("hash")
    segment_hash.add_hash(und_symbols)
  else:
    segment_dynamic.add_dt_symtab(0)
  # Add libraries.
  for ii in reversed(libraries):
    library_name = linker.get_library_name(ii)
    segment_dynamic.add_dt_needed(library_name)
    segment_strtab.add_strtab(library_name)
  # Assembler file generation is more complex when elfling is enabled.
  if elfling:
    elfling.write_c_source(output_file + ".elfling.cpp", definition_ld)
    compiler.compile_asm(output_file + ".elfling.cpp", output_file + ".elfling.S")
    asm = AssemblerFile(output_file + ".elfling.S")
    additional_asm = AssemblerFile(output_file + ".S")
    # Entry point is used as compression start information.
    elfling_align = int(PlatformVar("memory_page"))
    if elfling.has_data():
      alignment_section = AssemblerSectionAlignment(elfling_align, ELFLING_PADDING, ELFLING_OUTPUT, "end")
      set_program_start("_start")
    else:
      alignment_section = AssemblerSectionAlignment(elfling_align, ELFLING_PADDING, ELFLING_OUTPUT)
      set_program_start(ELFLING_OUTPUT)
    asm.add_sections(alignment_section)
    asm.incorporate(additional_asm, "_incorporated", ELFLING_UNCOMPRESSED)
  else:
    asm = AssemblerFile(output_file + ".S")
    asm.sort_sections()
  alignment_section = None
  # May be necessary to have two PT_LOAD headers as opposed to one.
  bss_section = asm.generate_fake_bss(assembler, und_symbols, elfling)
  if 0 < bss_section.get_alignment():
    replace_platform_variable("phdr_count", 4)
    if osarch_is_32_bit():
      segment_phdr_load_double = AssemblerSegment(assembler_phdr32_load_double)
      segment_phdr_load_bss = AssemblerSegment(assembler_phdr32_load_bss)
    elif osarch_is_64_bit():
      segment_phdr_load_double = AssemblerSegment(assembler_phdr64_load_double)
      segment_phdr_load_bss = AssemblerSegment(assembler_phdr64_load_bss)
    else:
      raise_unknown_address_size()
    load_segments = [segment_phdr_load_double, segment_phdr_load_bss]
  else:
    if osarch_is_32_bit():
      segment_phdr_load_single = AssemblerSegment(assembler_phdr32_load_single)
    elif osarch_is_64_bit():
      segment_phdr_load_single = AssemblerSegment(assembler_phdr64_load_single)
    else:
      raise_unknown_address_size()
    load_segments = [segment_phdr_load_single]
  # Collapse headers.
  segments_head = [segment_ehdr, segment_phdr_interp]
  segments_tail = [segment_phdr_dynamic]
  if is_listing(und_symbols):
    segments_tail += [segment_hash]
  segments_tail += [segment_dynamic]
  if is_listing(und_symbols):
    segments_tail += [segment_symtab]
  segments_tail += [segment_interp, segment_strtab]
  segments = merge_segments(segments_head) + load_segments + merge_segments(segments_tail)
  # Calculate total size of headers.
  header_sizes = 0
  fd = open(output_file + ".final.S", "w")
  for ii in segments:
    ii.write(fd, assembler)
    header_sizes += ii.size()
  if is_verbose():
    print("Size of headers: %i bytes" % (header_sizes))
  # Create content of earlier sections and write source when done.
  if alignment_section:
    alignment_section.create_content(assembler)
  if elfling and elfling.has_data():
    bss_section.create_content(assembler)
  else:
    bss_section.create_content(assembler, "end")
  asm.write(fd, assembler)
  fd.close()
  if is_verbose():
    print("Wrote assembler source '%s'." % (output_file + ".final.S"))
  assembler.assemble(output_file + ".final.S", output_file + ".o")
  linker.generate_linker_script(output_file + ".ld", True)
  linker.set_linker_script(output_file + ".ld")
  linker.link_binary(output_file + ".o", output_file + ".bin")
  run_command([objcopy, "--output-target=binary", output_file + ".bin", output_file + ".unprocessed"])
  readelf_truncate(output_file + ".unprocessed", output_file + ".stripped")

def get_platform_und_symbols():
  """Get the UND symbols required for this platform."""
  ret = None
  if osname_is_freebsd():
    ret = sorted(["environ", "__progname"])
  if is_verbose():
    print("Checking for required UND symbols... " + str(ret))
  return ret

def labelify(op):
  """Take string as input. Convert into string that passes as label."""
  return re.sub(r'[\/\.]', '_', op)

def listify(lhs, rhs):
  """Make a list of two elements if reasonable."""
  if not lhs:
    return rhs
  if not rhs:
    return lhs
  if is_listing(lhs) and is_listing(rhs):
    return lhs + rhs
  if is_listing(lhs):
    return lhs + [rhs]
  if is_listing(rhs):
    return [lhs] + rhs
  return [lhs, rhs]

def get_indent(op):
  """Get indentation for given level."""
  ret = ""
  for ii in range(op):
    # Would tab be better?
    ret += "  "
  return ret

def get_push_size(op):
  """Get push side increment for given instruction or register."""
  ins = op.lower()
  if ins == 'pushq':
    return 8
  elif ins == 'pushl':
    return 4
  else:
    raise RuntimeError("push size not known for instruction '%s'" % (ins))

def is_stack_save_register(op):
  """Tell if given register is used for saving the stack."""
  return op.lower() in ('rbp', 'ebp')

def is_deconstructable(op):
  """Tell if a variable can be deconstructed."""
  return isinstance(op, int) or (isinstance(op, PlatformVar) and op.deconstructable())

def is_listing(op):
  """Tell if given parameter is a listing."""
  return isinstance(op, (list, tuple))

def is_verbose():
  """Tell if verbose mode is on."""
  return g_verbose

def locate(pth, fn):
  """Search for given file from given path downward."""
  if is_listing(pth):
    for ii in pth:
      ret = locate(ii, fn)
      if ret:
        return ret
    return None
  # Some specific directory trees would take too much time to traverse.
  if pth in ("/lib/modules"): 
    return None
  pthfn = pth + "/" + fn
  if os.path.isfile(pthfn):
    return os.path.normpath(pthfn)
  try:
    for ii in os.listdir(pth):
      iifn = pth + "/" + ii
      if os.path.isdir(iifn):
        ret = locate(iifn, fn)
        if ret:
          return ret
  except OSError as ee: # Permission denied or the like.
    if 13 == ee.errno:
      return None
    raise ee
  return None

def make_executable(op):
  """Make given file executable."""
  if not os.stat(op)[stat.ST_MODE] & stat.S_IXUSR:
    run_command(["chmod", "+x", op])

def merge_segments(lst):
  """Try to merge segments in a given list in-place."""
  ii = 0
  while True:
    jj = ii + 1
    if len(lst) <= jj:
      return lst
    seg1 = lst[ii]
    seg2 = lst[jj]
    if seg1.merge(seg2):
      if seg2.empty():
        del lst[jj]
      else:
        ii += 1
    else:
      ii += 1
  return lst

def osarch_is_32_bit():
  """Check if the architecture is 32-bit."""
  return osarch_match("32-bit")

def osarch_is_64_bit():
  """Check if the architecture is 32-bit."""
  return osarch_match("64-bit")

def osarch_is_amd64():
  """Check if the architecture maps to amd64."""
  return osarch_match("amd64")

def osarch_is_ia32():
  """Check if the architecture maps to ia32."""
  return osarch_match("ia32")

def osarch_match(op):
  """Check if osarch matches some chain resulting in given value."""
  arch = g_osarch
  while True:
    if op == arch:
      return True
    arch = platform_map_iterate(arch)
    if not arch:
      break
  return False

def osname_is_freebsd():
  """Check if the operating system name maps to FreeBSD."""
  return ("FreeBSD" == g_osname)

def osname_is_linux():
  """Check if the operating system name maps to Linux."""
  return ("Linux" == g_osname)

def raise_unknown_address_size():
  """Common function to raise an error if os architecture address size is unknown."""
  raise RuntimeError("platform '%s' addressing size unknown" % (g_osarch))

def readelf_get_info(op):
  """Read information from an ELF file using readelf. Return as dictionary."""
  ret = {}
  (so, se) = run_command(["readelf", "--file-header", "--program-headers", op])
  match = re.search(r'LOAD\s+\S+\s+(\S+)\s+\S+\s+(\S+)\s+\S+\s+RWE', so, re.MULTILINE)
  if match:
    ret["base"] = int(match.group(1), 16)
    ret["size"] = int(match.group(2), 16)
  else:
    raise RuntimeError("could not read first PT_LOAD from executable '%s'" % (op))
  match = re.search(r'Entry\spoint\saddress:\s+(\S+)', so, re.MULTILINE)
  if match:
    ret["entry"] = int(match.group(1), 16) - ret["base"]
  else:
    raise RuntimeError("could not read entry point from executable '%s'" % (op))
  return ret

def readelf_truncate(src, dst):
  """Truncate file to size reported by readelf first PT_LOAD file size."""
  info = readelf_get_info(src)
  size = os.path.getsize(src)
  truncate_size = info["size"]
  if size == truncate_size:
    if is_verbose():
      print("Executable size equals PT_LOAD size (%u bytes), no truncation necessary." % (size))
    shutil.copy(src, dst)
  else:
    if is_verbose():
      print("Truncating file size to PT_LOAD size: %u bytes" % (truncate_size))
    rfd = open(src, "rb")
    wfd = open(dst, "wb")
    wfd.write(rfd.read(truncate_size))
    rfd.close()
    wfd.close()

def replace_conflicting_library(symbols, src_name, dst_name):
  """Replace conflicting library reference in a symbol set if necessary."""
  src_found = any((x.get_library().get_name() == src_name) for x in symbols)
  dst_found = any((x.get_library().get_name() == dst_name) for x in symbols)
  if not (src_found and dst_found):
    return symbols
  if is_verbose():
    print("Resolving library conflict: '%s' => '%s'" % (src_name, dst_name))
  ret = []
  dst = find_library_definition(dst_name)
  for ii in symbols:
    if ii.get_library().get_name() == src_name:
      replacement = dst.find_symbol(ii.get_name())
      if replacement:
        ret += [replacement]
      else:
        new_symbol = ii.create_replacement(dst)
        dst.add_symbol(new_symbol)
        ret += [new_symbol]
    else:
      ret += [ii]
  return ret

def run_command(lst, decode_output = True):
  """Run program identified by list of command line parameters."""
  if is_verbose():
    print("Executing command: %s" % (" ".join(lst)))
  proc = subprocess.Popen(lst, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
  (proc_stdout, proc_stderr) = proc.communicate()
  if decode_output and not isinstance(proc_stdout, str):
    proc_stdout = proc_stdout.decode()
  if decode_output and not isinstance(proc_stderr, str):
    proc_stderr = proc_stderr.decode()
  returncode = proc.returncode
  if 0 != proc.returncode:
    raise RuntimeError("command failed: %i, stderr output:\n%s" % (proc.returncode, proc_stderr))
  return (proc_stdout, proc_stderr)

def search_executable(op, description = None):
  """Check for existence of binary, everything within the list will be tried."""
  checked = []
  ret = None
  if isinstance(op, (list, tuple)):
    for ii in op:
      if not ii in checked:
        if check_executable(ii):
          ret = ii
          break
        else:
          checked += [ii]
  elif isinstance(op, str):
    if not op in checked:
      if check_executable(op):
        ret = op
      checked += [op]
  else:
    raise RuntimeError("weird argument given to executable search: %s" % (str(op)))
  if description and is_verbose():
    output_message = "Looking for '%s' executable... " % (description)
    if ret:
      print("%s'%s'" % (output_message, ret))
    else:
      print("%snot found" % (output_message))
  return ret

def set_program_start(op):
  """Set label to start program execution from."""
  replace_platform_variable("start", op)

def touch(op):
  """Emulate *nix 'touch' command."""
  if not os.path.exists(op):
    if is_verbose():
      print("Creating nonexistent file '%s'." % (op))
    fd = open(op, "w")
    fd.close()
  elif not os.path.isfile(op):
    raise RuntimeError("'%s' exists but is not a normal file" % (op))

########################################
# CustomHelpFormatter ##################
########################################

class CustomHelpFormatter(argparse.HelpFormatter):
  """Help formatter with necessary changes."""

  def _fill_text(self, text, width, indent):
    """Method override."""
    ret = []
    for ii in text.splitlines():
      ret += [textwrap.fill(ii, width, initial_indent=indent, subsequent_indent=indent)]
    return "\n\n".join(ret)

  def _split_lines(self, text, width):
    """Method override."""
    indent_len = len(get_indent(1))
    ret = []
    for ii in text.splitlines():
      indent = 0
      for jj in range(len(ii)):
        if not ii[jj].isspace():
          indent = jj
          break
      lines = textwrap.wrap(ii[indent:], width - jj * indent_len)
      for ii in range(len(lines)):
        lines[ii] = get_indent(indent) + lines[ii]
      ret += lines
    return ret

########################################
# Main #################################
########################################

def main():
  """Main function."""
  global g_osname
  global g_verbose

  assembler = None
  cross_compile = False
  compiler = None
  compression = str(PlatformVar("compression"))
  default_assembler_list = ["/usr/local/bin/as", "as"]
  default_compiler_list = ["g++49", "g++-4.9", "g++48", "g++-4.8", "g++", "clang++"]
  default_linker_list = ["/usr/local/bin/ld", "ld"]
  default_objcopy_list = ["/usr/local/bin/objcopy", "objcopy"]
  default_strip_list = ["/usr/local/bin/strip", "strip"]
  definitions = []
  elfling = None
  include_directories = [VIDEOCORE_PATH + "/include", VIDEOCORE_PATH + "/include/interface/vcos/pthreads", VIDEOCORE_PATH + "/include//interface/vmcs_host/linux", "/usr/include/SDL", "/usr/local/include", "/usr/local/include/SDL"]
  libraries = []
  library_directories = ["/lib", "/lib/x86_64-linux-gnu", VIDEOCORE_PATH + "/lib", "/usr/lib", "/usr/lib/arm-linux-gnueabihf", "/usr/lib/gcc/arm-linux-gnueabihf/4.9/", "/usr/lib/x86_64-linux-gnu", "/usr/local/lib"]
  linker = None
  objcopy = None
  opengl_reason = None
  opengl_version = None
  output_file = None
  sdl_version = 2
  source_files = []
  strip = None
  target_search_path = []

  parser = argparse.ArgumentParser(usage = "%s [args] <source file(s)> [-o output]" % (sys.argv[0]), description = "Size-optimized executable generator for *nix platforms.\nPreprocesses given source file(s) looking for specifically marked function calls, then generates a dynamic loader header file that can be used within these same source files to decrease executable size.\nOptionally also perform the actual compilation of a size-optimized binary after generating the header.", formatter_class = CustomHelpFormatter, add_help = False)
  parser.add_argument("-a", "--abstraction-layer", default = "sdl2", choices = ("sdl1", "sdl2"), help = "Abstraction layer to use.\n(default: %(default))")
  parser.add_argument("-A", "--assembler", help = "Try to use given assembler executable as opposed to autodetect.")
  parser.add_argument("-B", "--objcopy", help = "Try to use given objcopy executable as opposed to autodetect.")
  parser.add_argument("-c", "--create-binary", action = "store_true", help = "Create output file, determine output file name from input file name.")
  parser.add_argument("-C", "--compiler", help = "Try to use given compiler executable as opposed to autodetect.")
  parser.add_argument("-d", "--define", default = "USE_LD", help = "Definition to use for checking whether to use 'safe' mechanism instead of dynamic loading.\n(default: %(default)s)")
  parser.add_argument("-e", "--elfling", action = "store_true", help = "Use elfling packer if available.")
  parser.add_argument("-h", "--help", action = "store_true", help = "Print this help string and exit.")
  parser.add_argument("-I", "--include-directory", action = "append", help = "Add an include directory to be searched for header files.")
  parser.add_argument("-k", "--linker", help = "Try to use given linker executable as opposed to autodetect.")
  parser.add_argument("-l", "--library", action = "append", help = "Add a library to be linked against.")
  parser.add_argument("-L", "--library-directory", action = "append", help = "Add a library directory to be searched for libraries when linking.")
  parser.add_argument("-m", "--method", default = "maximum", choices = ("vanilla", "dlfcn", "hash", "maximum"), help = "Method to use for decreasing output file size:\n\tvanilla:\n\t\tProduce binary normally, use no tricks except unpack header.\n\tdlfcn:\n\t\tUse dlopen/dlsym to decrease size without dependencies to any specific object format.\n\thash:\n\t\tUse knowledge of object file format to perform 'import by hash' loading, but do not break any specifications.\n\tmaximum:\n\t\tUse all available techniques to decrease output file size. Resulting file may violate object file specification.\n(default: %(default)s)")
  parser.add_argument("--nice-exit", action = "store_true", help = "Do not use debugger trap, exit with proper system call.")
  parser.add_argument("--nice-filedump", action = "store_true", help = "Do not use dirty tricks in compression header, also remove filedumped binary when done.")
  parser.add_argument("--no-glesv2", action = "store_true", help = "Do not probe for OpenGL ES 2.0, always assume regular GL.")
  parser.add_argument("-o", "--output-file", help = "Compile a named binary, do not only create a header. If the name specified features a path, it will be used verbatim. Otherwise the binary will be created in the same path as source file(s) compiled.")
  parser.add_argument("-O", "--operating-system", help = "Try to target given operating system insofar cross-compilation is possible.")
  parser.add_argument("-P", "--call-prefix", default = "dnload_", help = "Call prefix to identify desired calls.\n(default: %(default)s)")
  parser.add_argument("--safe-symtab", action = "store_true", help = "Handle DT_SYMTAB in a safe manner.")
  parser.add_argument("-s", "--search-path", action = "append", help = "Directory to search for the header file to generate. May be specified multiple times. If not given, searches paths of source files to compile. If not given and no source files to compile, current path will be used.")
  parser.add_argument("-S", "--strip-binary", help = "Try to use given strip executable as opposed to autodetect.")
  parser.add_argument("-t", "--target", default = "dnload.h", help = "Target header file to look for.\n(default: %(default)s)")
  parser.add_argument("-u", "--unpack-header", choices = ("lzma", "xz"), default = compression, help = "Unpack header to use.\n(default: %(default)s)")
  parser.add_argument("-v", "--verbose", action = "store_true", help = "Print more about what is being done.")
  parser.add_argument("-V", "--version", action = "store_true", help = "Print version and exit.")
  parser.add_argument("source", nargs = "*", help = "Source file(s) to preprocess and/or compile.")
 
  args = parser.parse_args()
  if args.assembler:
    assembler = args.assembler
  if args.create_binary:
    output_file = True
  if args.compiler:
    compiler = args.compiler
  if args.elfling:
    elfling = True
  if args.help:
    print(parser.format_help().strip())
    return 0
  if args.include_directory:
    include_directories += args.include_directory
  if args.linker:
    linker = args.linker
  if args.library:
    libraries += args.library
  if args.library_directory:
    library_directories += args.library_directory
  if args.nice_exit:
    definitions += ["DNLOAD_NO_DEBUGGER_TRAP"]
  if args.objcopy:
    objcopy = args.objcopy
  if args.operating_system:
    new_osname = platform_map(args.operating_system.lower())
    if new_osname != g_osname:
      cross_compile = True
      g_osname = new_osname
  if args.output_file:
    output_file = args.output_file
  if args.safe_symtab:
    definitions += ["DNLOAD_SAFE_SYMTAB_HANDLING"]
  if args.search_path:
    target_search_path += args.search_path
  if args.source:
    source_files += args.source
  if args.strip_binary:
    strip = args.strip_binary
  if args.unpack_header:
    compression = args.unpack_header
  if args.verbose:
    g_verbose = True
  if args.version:
    print("%s %s" % (VERSION_REVISION, VERSION_DATE))
    return 0

  abstraction_layer = args.abstraction_layer
  definition_ld = args.define
  compilation_mode = args.method
  nice_filedump = args.nice_filedump
  no_glesv2 = args.no_glesv2
  symbol_prefix = args.call_prefix
  target = args.target

  if not compilation_mode in ("vanilla", "dlfcn", "hash", "maximum"):
    raise RuntimeError("unknown method '%s'" % (compilation_mode))
  elif "hash" == compilation_mode:
    definitions += ["DNLOAD_NO_FIXED_R_DEBUG_ADDRESS"]

  if not no_glesv2:
    if os.path.exists(VIDEOCORE_PATH):
      definitions += ["DNLOAD_VIDEOCORE"]
      opengl_reason = "'%s' (VideoCore)" % (VIDEOCORE_PATH)
      opengl_version = "ES2"

  if "ES2" == opengl_version:
    definitions += ["DNLOAD_GLESV2"]
    replace_platform_variable("gl_library", "GLESv2")
    if is_verbose():
      print("Assuming OpenGL ES 2.0: %s" % (opengl_reason))

  if 0 >= len(target_search_path):
    for ii in source_files:
      source_path, source_file = os.path.split(os.path.normpath(ii))
      if source_path and not source_path in target_search_path:
        target_search_path += [source_path]
  if 0 >= len(target_search_path):
    target_search_path = ["."]

  target_path, target_file = os.path.split(os.path.normpath(target))
  if target_path:
    if is_verbose():
      print("Using explicit target header file '%s'." % (target))
    touch(target)
  else:
    target_file = locate(target_search_path, target)
    if target_file:
      target = os.path.normpath(target_file)
      target_path, target_file = os.path.split(target)
      if is_verbose():
        print("Header file '%s' found in path '%s/'." % (target_file, target_path))
    else:
      raise RuntimeError("no information where to put header file '%s' - not found in path(s) %s" % (target, str(target_search_path)))

  if 0 >= len(source_files):
    potential_source_files = os.listdir(target_path)
    sourcere = re.compile(r".*(c|cpp)$")
    for ii in potential_source_files:
      if sourcere.match(ii):
        source_files += [target_path + "/" + ii]
    if 0 >= len(source_files):
      raise RuntimeError("could not find any source files in '%s'" % (target_path))

  if compiler:
    if not check_executable(compiler):
      raise RuntimeError("could not use supplied compiler '%s'" % (compiler))
  else:
    compiler_list = default_compiler_list
    if os.name == "nt":
      compiler_list = ["cl.exe"] + compiler_list
    compiler = search_executable(compiler_list, "compiler")
  if not compiler:
    raise RuntimeError("suitable compiler not found")
  compiler = Compiler(compiler)
  compiler.set_definitions(definitions)
  # Some special linker directories may be necessary.
  if compiler.get_command() in ('gcc48', 'g++-4.8'):
    library_directories += ["/usr/lib/gcc/arm-linux-gnueabihf/4.8"]
  compiler.set_include_dirs(include_directories)

  if abstraction_layer in ('sdl1', 'sdl2'):
    sdl_config_executable_name = "sdl2-config"
    if 'sdl1' == abstraction_layer:
      sdl_config_executable_name = "sdl-config"
    sdl_config = search_executable([sdl_config_executable_name], sdl_config_executable_name)
    if sdl_config:
      (sdl_stdout, sdl_stderr) = run_command([sdl_config, "--cflags"])
      compiler.add_extra_compiler_flags(sdl_stdout.split())

  if elfling:
    elfling = search_executable(["elfling-packer", "./elfling-packer"], "elfling-packer")
    if elfling:
      elfling = Elfling(elfling)

  if output_file:
    if assembler:
      if not check_executable(assembler):
        raise RuntimeError("could not use supplied compiler '%s'" % (compiler))
    else:
      assembler = search_executable(default_assembler_list, "assembler")
    if not assembler:
      raise RuntimeError("suitable assembler not found")
    assembler = Assembler(assembler)
    if linker:
      if not check_executable(linker):
        raise RuntimeError("could not use supplied linker '%s'" % (linker))
    else:
      linker = search_executable(default_linker_list, "linker")
    linker = Linker(linker)
    if objcopy:
      if not check_executable(objcopy):
        raise RuntimeError("could not use supplied objcopy executable '%s'" % (objcopy))
    else:
      objcopy = search_executable(default_objcopy_list, "objcopy")
    if strip:
      if not check_executable(strip):
        raise RuntimeError("could not use supplied strip executable '%s'" % (strip))
    else:
      strip = search_executable(default_strip_list, "strip")
    if not strip:
      raise RuntimeError("suitable strip executable not found")

  # Clear target header before parsing to avoid problems.
  fd = open(target, "w")
  fd.write("\n")
  fd.close()

  symbols = set()
  for ii in source_files:
    if is_verbose():
      print("Analyzing source file '%s'." % (ii))
    source = compiler.preprocess(ii)
    source_symbols = analyze_source(source, symbol_prefix)
    symbols = symbols.union(source_symbols)
  symbols = find_symbols(symbols)
  if "dlfcn" == compilation_mode:
    symbols = sorted(symbols)
  elif "maximum" == compilation_mode:
    sortable_symbols = []
    for ii in symbols:
      sortable_symbols += [(ii.get_hash(), ii)]
    symbols = []
    for ii in sorted(sortable_symbols):
      symbols += [ii[1]]
  # Some libraries cannot co-exist, but have some symbols with identical names.
  symbols = replace_conflicting_library(symbols, "SDL", "SDL2")

  real_symbols = filter(lambda x: not x.is_verbatim(), symbols)
  if is_verbose():
    symbol_strings = map(lambda x: str(x), symbols)
    print("Symbols found: %s" % (str(symbol_strings)))
    verbatim_symbols = list(set(symbols) - set(real_symbols))
    if verbatim_symbols and output_file:
      verbatim_symbol_strings = []
      for ii in verbatim_symbols:
        verbatim_symbol_strings += [str(ii)]
      print("Not loading verbatim symbols: %s" % (str(verbatim_symbol_strings)))

  file_contents = g_template_header_begin % (os.path.basename(sys.argv[0]), definition_ld, definition_ld)
  file_contents += generate_symbol_definitions(compilation_mode, symbols, symbol_prefix, definition_ld)
  file_contents += generate_symbol_struct(compilation_mode, real_symbols, definition_ld)
  file_contents += generate_loader(compilation_mode, real_symbols, definition_ld, linker)
  file_contents += g_template_header_end

  fd = open(target, "w")
  fd.write(file_contents)
  fd.close()

  if is_verbose():
    print("Wrote header file '%s'." % (target))

  if output_file:
    if 1 < len(source_files):
      raise RuntimeError("only one source file supported when generating output file")
    source_file = source_files[0]
    if not isinstance(output_file, str):
      output_path, output_basename = os.path.split(source_file)
      output_basename, source_extension = os.path.splitext(output_basename)
      output_file = os.path.normpath(os.path.join(output_path, output_basename))
      if is_verbose():
        print("Using output file '%s' after source file '%s'." % (output_file, source_file))
    else:
      output_file = os.path.normpath(output_file)
      output_path, output_basename = os.path.split(output_file)
      if output_basename == output_file:
        output_path = target_path
      output_file = os.path.normpath(os.path.join(output_path, output_basename))
    libraries = collect_libraries(libraries, real_symbols, compilation_mode)
    compiler.generate_compiler_flags()
    compiler.generate_linker_flags()
    compiler.set_libraries(libraries)
    compiler.set_library_directories(library_directories)
    linker.generate_linker_flags()
    linker.set_libraries(libraries)
    linker.set_library_directories(library_directories)
    if "maximum" == compilation_mode:
      und_symbols = get_platform_und_symbols()
      generate_binary_minimal(source_file, compiler, assembler, linker, objcopy, und_symbols, elfling,
          libraries, output_file)
      # Now have complete binary, may need to reprocess.
      if elfling:
        elfling.compress(output_file + ".stripped", output_file + ".extracted")
        generate_binary_minimal(None, compiler, assembler, linker, objcopy, und_symbols, elfling, libraries,
            output_file)
    elif "hash" == compilation_mode:
      compiler.compile_asm(source_file, output_file + ".S")
      asm = AssemblerFile(output_file + ".S")
      #asm.sort_sections()
      #asm.remove_rodata()
      asm.write(output_file + ".final.S", assembler)
      assembler.assemble(output_file + ".final.S", output_file + ".o")
      linker.generate_linker_script(output_file + ".ld")
      linker.set_linker_script(output_file + ".ld")
      linker.link(output_file + ".o", output_file + ".unprocessed")
    elif "dlfcn" == compilation_mode or "vanilla" == compilation_mode:
      compiler.compile_and_link(source_file, output_file + ".unprocessed")
    else:
      raise RuntimeError("unknown compilation mode: %s" % str(compilation_mode))
    if compilation_mode in ("vanilla", "dlfcn", "hash"):
      shutil.copy(output_file + ".unprocessed", output_file + ".stripped")
      run_command([strip, "-K", ".bss", "-K", ".text", "-K", ".data", "-R", ".comment", "-R", ".eh_frame", "-R", ".eh_frame_hdr", "-R", ".fini", "-R", ".gnu.hash", "-R", ".gnu.version", "-R", ".jcr", "-R", ".note", "-R", ".note.ABI-tag", "-R", ".note.tag", output_file + ".stripped"])
    compress_file(compression, nice_filedump, output_file + ".stripped", output_file)

  return 0

if __name__ == "__main__":
  sys.exit(main())
