#ifndef BSD_RAND_H
#define BSD_RAND_H

/// Definition of an internal type from FreeBSD libc.
#define bsd_u_int unsigned int

#if defined(__cplusplus)
extern "C"
{
#endif

/// BSD rand() implementation.
///
/// Compiled in whenever not using FreeBSD() in which case it can be dynamically loaded.
///
/// https://github.com/freebsd/freebsd/blob/master/lib/libc/stdlib/rand.c
///
/// \return Random number.
int bsd_rand(void);

/// FreeBSD srand() implementation.
///
/// Compiled in whenever not using FreeBSD() in which case it can be dynamically loaded.
///
/// https://github.com/freebsd/freebsd/blob/master/lib/libc/stdlib/rand.c
///
/// \param seed Initializing seed for the random number generator.
void bsd_srand(bsd_u_int seed);

#if defined(DNLOAD_USE_LD)

/// Testing wrapper for bsd_rand().
///
/// Used to confirm bsd_rand() actually matches the FreeBSD rand().
///
/// \return Random number.
int bsd_rand_wrapper(void);

/// Testing wrapper for bsd_srand().
///
/// Used to confirm bsd_srand() actually matches the FreeBSD srand().
///
/// \param seed Initializing seed for the random number generator.
void bsd_srand_wrapper(bsd_u_int seed);

#endif

#if defined(__cplusplus)
}
#endif

#endif
