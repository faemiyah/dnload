#include "bsd_rand.h"

#include <stdio.h>
#include <stdlib.h>

/** BSD random var. */
static bsd_u_long bsd_rand_next = 2;

int bsd_rand(void)
{
  /*
   * Compute x = (7^5 * x) mod (2^31 - 1)
   * without overflowing 31 bits:
   *      (2^31 - 1) = 127773 * (7^5) + 2836
   * From "Random number generators: good ones are hard to find",
   * Park and Miller, Communications of the ACM, vol. 31, no. 10,
   * October 1988, p. 1195.
   */
  long hi, lo, x;

  /* Must be in [1, 0x7ffffffe] range at this point. */
  hi = (long)(bsd_rand_next / 127773);
  lo = (long)(bsd_rand_next % 127773);
  x = 16807 * lo - 2836 * hi;
  if (x < 0)
    x += 0x7fffffff;
  bsd_rand_next = (bsd_u_long)x;
  /* Transform to [0, 0x7ffffffd] range. */
  return (int)(x - 1);
}

void bsd_srand(bsd_u_int seed)
{
  /* Transform to [1, 0x7ffffffe] range. */
  bsd_rand_next = (seed % 0x7ffffffe) + 1;
}

int bsd_rand_wrapper(void)
{
  static unsigned cidx = 0;
  int ret = bsd_rand();
  int cmp = rand();

  if(ret != cmp)
  {
    printf("ERROR: rand() inconsistency %i (system) vs %i (custom) at call number %u\n", cmp, ret, cidx);
  }

  ++cidx;
  return ret;
}

void bsd_srand_wrapper(bsd_u_int seed)
{
  bsd_srand(seed);
  srand(seed);
}

