#ifndef DNLOAD_EGL_H
#define DNLOAD_EGL_H

#include <stdio.h>

#include "EGL/egl.h"
#include "EGL/eglext.h"

#if defined(__cplusplus)
extern "C"
{
#endif

/** \brief Terminate EGL connection.
 *
 * Wrapped since the termination may also fail.
 *
 * \param egl_display EGL display to terminate connection on.
 */
static void egl_terminate(EGLDisplay egl_display)
{
  EGLBoolean result = dnload_eglTerminate(egl_display);
#if defined(USE_LD)
  if(!result)
  {
    fprintf(stderr, "eglTerminate(): %i\n", eglGetError());
  }
#else
  (void)result;
#endif
}

/** \brief Init EGL display.
 *
 * \param native_window Native window given to EGL.
 * \param out_display EGL display target.
 * \param out_surface EGL surface target.
 * \return Success value.
 */
static EGLBoolean egl_init(EGLNativeWindowType native_window, EGLDisplay *out_display, EGLSurface *out_surface)
{
  static const EGLint desired_config[] =
  {
    EGL_RED_SIZE, 8,
    EGL_GREEN_SIZE, 8,
    EGL_BLUE_SIZE, 8,
    EGL_ALPHA_SIZE, 8,
    EGL_SURFACE_TYPE, EGL_WINDOW_BIT,
    EGL_NONE
  };
  static const EGLint context_attributes[] =
  {
    EGL_CONTEXT_CLIENT_VERSION, 2,
    EGL_NONE
  };
  EGLConfig acquired_config;
  EGLContext context;
  EGLDisplay display;
  EGLSurface surface;
  EGLint config_count;
  EGLBoolean result;

  display =   dnload_eglGetDisplay(EGL_DEFAULT_DISPLAY);
#if defined(USE_LD)
  if(EGL_NO_DISPLAY == display)
  {
    fprintf(stderr, "eglGetDisplay(): %p\n", display);
    return EGL_FALSE;
  }
#else
  (void)result;
#endif

  result =   dnload_eglInitialize(display, NULL, NULL);
#if defined(USE_LD)
  if(!result)
  {
    egl_terminate(display);
    fprintf(stderr, "eglInitialize(): %i\n", eglGetError());
    return EGL_FALSE;
  }
#else
  (void)result;
#endif

  result =   dnload_eglChooseConfig(display, desired_config, &acquired_config, 1, &config_count);
#if defined(USE_LD)
  if(!result || (0 >= config_count))
  {
    egl_terminate(display);
    fprintf(stderr, "eglChooseConfig(): %i\n", eglGetError());
    return EGL_FALSE;
  }
#else
  (void)result;
#endif

  surface =   dnload_eglCreateWindowSurface(display, acquired_config, native_window, NULL);
#if defined(USE_LD)
  if(EGL_NO_SURFACE == surface)
  {
    egl_terminate(display);
    fprintf(stderr, "eglChooseConfig(): %i\n", eglGetError());
    return EGL_FALSE;
  }
#else
  (void)result;
#endif

  context =   dnload_eglCreateContext(display, acquired_config, EGL_NO_CONTEXT, context_attributes);
#if defined(USE_LD)
  if(EGL_NO_CONTEXT == context)
  {
    egl_terminate(display);
    fprintf(stderr, "eglCreateContext(): %i\n", eglGetError());
    return EGL_FALSE;
  }
#else
  (void)result;
#endif

  result =   dnload_eglMakeCurrent(display, surface, surface, context);
#if defined(USE_LD)
  if(!result)
  {
    egl_terminate(display);
    fprintf(stderr, "eglMakeCurrent(): %i\n", eglGetError());
    return EGL_FALSE;
  }
#else
  (void)result;
#endif

  *out_display = display;
  *out_surface = surface;
  return EGL_TRUE;
}

/** \brief Uninitialize EGL display.
 *
 * \param display EGL display to uninitialize.
 */
static void egl_quit(EGLDisplay display)
{
  EGLBoolean result =  dnload_eglMakeCurrent(display, EGL_NO_CONTEXT, EGL_NO_CONTEXT, EGL_NO_CONTEXT);
#if defined(USE_LD)
  if(!result)
  {
    fprintf(stderr, "eglMakeCurrent(): %i\n", eglGetError());
  }
#else
  (void)result;
#endif
  egl_terminate(display);
}

#if defined(__cplusplus)
}
#endif

#endif
