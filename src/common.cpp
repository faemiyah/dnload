#include "common.hpp"

using namespace fcmp;

static unsigned g_verbosity = 0;

bool fcmp::is_verbose()
{
  return (0 < g_verbosity);
}

bool fcmp::is_very_verbose()
{
  return (1 < g_verbosity);
}

void fcmp::set_verbosity(unsigned level)
{
  g_verbosity = level;
}

