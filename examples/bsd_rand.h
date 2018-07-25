#ifndef BSD_RAND_H
#define BSD_RAND_H

#define bsd_u_long unsigned long
#define bsd_u_int unsigned int

#if defined(__cplusplus)
extern "C" {
#endif

/** \brief BSD rand() implementation.
 *
 * Compiled in whenever not using FreeBSD() in which case it can be dynamically loaded.
 */
int bsd_rand(void);

/** \brief FreeBSD srand() implementation.
 *
 * Compiled in whenever not using FreeBSD() in which case it can be dynamically loaded.
 */
void bsd_srand(bsd_u_int seed);

/** \brief Testing wrapper for rand().
 *
 * Used to confirm rand() actually matches the FreeBSD rand().
 */
int bsd_rand_wrapper(void);

/** \brief Testing wrapper for srand().
 *
 * Used to confirm srand() actually matches the FreeBSD srand().
 */
void bsd_srand_wrapper(bsd_u_int seed);

#if defined(__cplusplus)
}
#endif

#endif
