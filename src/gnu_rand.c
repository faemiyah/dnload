#include "gnu_rand.h"

#include <stdint.h>

/// x**31 + x**3 + 1.
#define TYPE_3          3
/// \see TYPE_3
#define DEG_3           31
/// \see TYPE_3
#define SEP_3           3

/// Random data for GNU random implementation.
///
/// Taken directly from GNU libc's random.c.
/// Equal to calling initstate(1, randtbl, 128);
///
/// https://sourceware.org/git/?p=glibc.git;a=blob;f=stdlib/stdlib.h;hb=HEAD
static int32_t randtbl[DEG_3 + 1] =
{
    TYPE_3,
    -1726662223, 379960547, 1735697613, 1040273694, 1313901226,
    1627687941, -179304937, -2073333483, 1780058412, -1989503057,
    -615974602, 344556628, 939512070, -1249116260, 1507946756,
    -812545463, 154635395, 1388815473, -1926676823, 525320961,
    -1009028674, 968117788, -123449607, 1284210865, 435012392,
    -2017506339, -911064859, -370259173, 1132637927, 1398500161,
    -205601318,
};

/// Random data structure.
///
/// Taken directly from GNU libc's stdlib.h.
///
/// https://sourceware.org/git/?p=glibc.git;a=blob;f=stdlib/stdlib.h;hb=HEAD
struct random_data
{
    /// Front pointer.
    int32_t *fptr;

    /// Rear pointer.
    int32_t *rptr;

    /// Array of state values.
    int32_t *state;

    /// Type of random number generator.
    int rand_type;

    /// Degree of random number generator.
    int rand_deg;

    /// Distance between front and rear.
    int rand_sep;

    /// Pointer behind state table.
    int32_t *end_ptr;
} g_rand_state =
{
    .fptr = &randtbl[SEP_3 + 1],
    .rptr = &randtbl[1],
    .state = &randtbl[1],
    .rand_type = TYPE_3,
    .rand_deg = DEG_3,
    .rand_sep = SEP_3,
    .end_ptr = &randtbl[sizeof (randtbl) / sizeof (randtbl[0])]
};

int gnu_rand(void)
{
    int32_t *state = g_rand_state.state;

#if 0 // Type is never TYPE_0.
    if (g_rand_state->rand_type == TYPE_0)
    {
        int32_t val = ((state[0] * 1103515245U) + 12345U) & 0x7fffffff;
        state[0] = val;
        return val;
    }
#endif

    int32_t *fptr = g_rand_state.fptr;
    int32_t *rptr = g_rand_state.rptr;
    int32_t *end_ptr = g_rand_state.end_ptr;
    uint32_t val = (uint32_t)(*fptr += (int32_t)((uint32_t) *rptr));

    ++fptr;
    if (fptr >= end_ptr)
    {
        fptr = state;
        ++rptr;
    }
    else
    {
        ++rptr;
        if (rptr >= end_ptr)
            rptr = state;
    }
    g_rand_state.fptr = fptr;
    g_rand_state.rptr = rptr;

    // Chucking least random bit.
    return (int)(val >> 1);
}

void gnu_srand(unsigned int seed)
{
    int32_t *state;
    long int i;
    int32_t word;
    int32_t *dst;
    int kc;

    state = g_rand_state.state;
    /* We must make sure the seed is not 0.  Take arbitrarily 1 in this case.  */
    if (seed == 0)
        seed = 1;
    state[0] = (int32_t)seed;
#if 0 // Type is never TYPE_0.
    int type = g_rand_state.rand_type;
    if (type == TYPE_0)
        return;
#endif

    dst = state;
    word = (int32_t)seed;
    kc = g_rand_state.rand_deg;
    for (i = 1; i < kc; ++i)
    {
        /* This does:
           state[i] = (16807 * state[i - 1]) % 2147483647;
           but avoids overflowing 31 bits.  */
        long int hi = word / 127773;
        long int lo = word % 127773;
        word = (int32_t)(16807 * lo - 2836 * hi);
        if (word < 0)
            word += 2147483647;
        *++dst = word;
    }

    g_rand_state.fptr = &state[g_rand_state.rand_sep];
    g_rand_state.rptr = &state[0];
    kc *= 10;
    while (--kc >= 0)
    {
        gnu_rand();
    }
}

#if defined(USE_LD)

#include <stdio.h>
#include <stdlib.h>

int gnu_rand_wrapper(void)
{
    static unsigned cidx = 0;
    int ret = gnu_rand();
    int cmp = rand();

    if(ret != cmp)
    {
        printf("ERROR: rand() inconsistency %i (system) vs %i (gnu) at call number %u\n", cmp, ret, cidx);
    }

    ++cidx;
    return ret;
}

void gnu_srand_wrapper(unsigned int seed)
{
    gnu_srand(seed);
    srand(seed);
}

#endif

