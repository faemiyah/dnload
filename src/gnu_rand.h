#ifndef GNU_RAND_H
#define GNU_RAND_H

#if defined(__cplusplus)
extern "C"
{
#endif

/// GNU libc random() function modified to work without an external state.
///
/// glibc internally uses the same function as alias for rand().
///
/// https://sourceware.org/git/?p=glibc.git;a=blob;f=stdlib/random.c;hb=HEAD
/// https://sourceware.org/git/?p=glibc.git;a=blob;f=stdlib/random_r.c;hb=HEAD
///
/// \return Random number.
int gnu_rand(void);

/// GNU libc srandom() function modified to work without an external state.
///
/// glibc internally uses the same function as alias for srand().
///
/// https://sourceware.org/git/?p=glibc.git;a=blob;f=stdlib/random.c;hb=HEAD
/// https://sourceware.org/git/?p=glibc.git;a=blob;f=stdlib/random_r.c;hb=HEAD
///
/// \param seed Initializing seed for the random number generator.
void gnu_srand(unsigned int seed);

#if defined(DNLOAD_USE_LD)

/// Testing wrapper for gnu_rand().
///
/// Used to confirm gnu_rand() actually matches the glibc rand().
///
/// \return Random number.
int gnu_rand_wrapper(void);

/// Testing wrapper for gnu_srand().
///
/// Used to confirm gnu_srand() actually matches the glibc srand().
///
/// \param seed Initializing seed for the random number generator.
void gnu_srand_wrapper(unsigned int seed);

#endif

#if defined(__cplusplus)
}
#endif

#endif
