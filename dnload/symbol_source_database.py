from dnload.common import is_verbose
from dnload.symbol_source import SymbolSource
from dnload.template import Template

########################################
# SymbolSourceDatabase #################
########################################

class SymbolSourceDatabase:
  """Database of different symbol sources that generates missing code."""

  def __init__(self, op):
    """Constructor."""
    self.__symbols = {}
    for ii in op:
      if 5 != len(ii):
        raise RuntimeError("incorrect length for sybol source data: %i" % (len(ii)))
      name = ii[0]
      self.__symbols[name] = SymbolSource(name, ii[1], ii[2], ii[3], ii[4])

  def compile_asm(self, compiler, assembler, required_symbols, fname):
    """Compile given symbols into assembly and return it."""
    source = self.generate_source(required_symbols)
    if not source:
      return None
    fd = open(fname + ".cpp", "w")
    fd.write(source)
    fd.close()
    output_fname = fname + ".S"
    compiler.compile_asm(fname + ".cpp", output_fname)
    return output_fname

  def generate_source(self, required_symbols):
    """Generate C source that contains definitions for given symbols."""
    headers = set()
    prototypes = []
    source = []
    compiled_symbol_names = []
    ii = 0
    while ii < len(required_symbols):
      name = required_symbols[ii]
      if name in self.__symbols:
        sym = self.__symbols[name]
        # Add all dependencies to required symbols list.
        for jj in sym.get_dependencies():
          if not jj in required_symbols:
            required_symbols += [jj]
        # Extend collected source data.
        headers = headers.union(sym.get_headers())
        prototypes += sym.get_prototypes()
        source += [sym.get_source()]
        compiled_symbol_names += [name]
      ii += 1
    if not source:
      return None
    if is_verbose():
      print("%i extra symbols required: %s" % (len(compiled_symbol_names), str(compiled_symbol_names)))
    subst = { "HEADERS" : "\n".join(["#include <%s>" % (x) for x in headers]),
        "PROTOTYPES" : "\n\n".join(prototypes),
        "SOURCE" : "\n\n".join(source)
        }
    return g_template_extra_source.format(subst)

########################################
# Globals ##############################
########################################

g_symbol_sources = SymbolSourceDatabase((
  ("__aeabi_idivmod", "__aeabi_uidivmod", None, "extern \"C\" int __aeabi_idivmod(int, int);",
"""int __aeabi_idivmod(int num, int den)
{
  int quotient_mul = 1;
  int remainder_mul = 1;\n
  if(num < 0)
  {
    remainder_mul = -1;
    num = -num;\n
    if(den < 0)
    {
      den = -den;
    }
    else
    {
      quotient_mul = -1;
    }
  }
  else if(den < 0)
  {
    quotient_mul = -1;
    den = -den;
  }\n
  int ret = __aeabi_uidivmod(static_cast<unsigned>(num), static_cast<unsigned>(den)) * quotient_mul;
  volatile register int r1 asm("r1");
  r1 *= remainder_mul;
  asm("" : /**/ : "r"(r1) : /**/); // output: remainder
  return ret;
}"""),
  ("__aeabi_uidivmod", None, None, "extern \"C\" unsigned __aeabi_uidivmod(unsigned, unsigned);",
"""unsigned __aeabi_uidivmod(unsigned num, unsigned den)
{
  unsigned shift = 1;
  unsigned quotient = 0;\n
  for(;;)
  {
    unsigned next = den << 1;
    if(next > num)
    {
      break;
    }
    den = next;
    shift <<= 1;
  }\n
  while(shift > 0)
  {
    if(den <= num)
    {
      num -= den;
      quotient += shift;
    }
    den >>= 1;
    shift >>= 1;
  }\n
  volatile register int r1 asm("r1") = num;
  asm("" : /**/ : "r"(r1) : /**/); // output: remainder
  return quotient; // r0
}"""),
  ("memset", None, ("cinttypes", "cstring"), None,
"""void* memset(void *ptr, int value, size_t num)
{
  for(size_t ii = 0; (ii < num); ++ii)
  {
    reinterpret_cast<uint8_t*>(ptr)[ii] = static_cast<uint8_t>(value);
  }\n
  return ptr;
}"""),
  # TODO: this is stub from Clang project, replace with smaller but dumber version later.
  ("__powisf2", None, None, "extern \"C\" float __powisf2(float, int);",
"""float __powisf2(float a, int b)
{
    const int recip = b < 0;
    float r = 1;
    while (1)
    {
        if (b & 1)
            r *= a;
        b /= 2;
        if (b == 0)
            break;
        a *= a;
    }
    return recip ? 1/r : r;
}"""),
  ))

g_template_extra_source = Template("""[[HEADERS]]\n
[[PROTOTYPES]]\n
[[SOURCE]]
""")
