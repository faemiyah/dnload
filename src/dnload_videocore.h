#ifndef DNLOAD_VIDEOCORE_H
#define DNLOAD_VIDEOCORE_H

#include "bcm_host.h"
#include "EGL/eglplatform.h"

#if defined(__cplusplus)
extern "C"
{
#endif

enum WindowMode
{
  MODE_ORIGO,
  MODE_STRETCH,
  MODE_CENTERED,
  MODE_KEEP_ASPECT
};

/** \brief Create native videocore window.
 *
 * \param screen_width Window width.
 * \param screen_height Window height.
 * \param mode Defines how window is scaled to match the actual screen size.
 * \param out_native_window Native window output.
 */
static void videocore_create_native_window_extended(int screen_width, int screen_height, enum WindowMode mode,
    EGL_DISPMANX_WINDOW_T *out_native_window)
{
  dnload_bcm_host_init();

  // The actual screen resolution. Initialized as if it was the same as
  // window size. Thiw way we have some sane values in case
  // graphics_get_display_size fails.
  uint32_t native_width = screen_width;
  uint32_t native_height = screen_height;

  dnload_graphics_get_display_size(0, &native_width, &native_height);

  static VC_DISPMANX_ALPHA_T alpha =
  {
    DISPMANX_FLAGS_ALPHA_FIXED_ALL_PIXELS, 255, 0
  };
  
  VC_RECT_T dst_rect;
  switch(mode)
  {
    default:
    case MODE_ORIGO:
      dst_rect.x = dst_rect.y = 0;
      dst_rect.width = screen_width;
      dst_rect.height = screen_height;
      break;
    case MODE_STRETCH:
      dst_rect.x = dst_rect.y = 0;
      dst_rect.width = native_width;
      dst_rect.height = native_height;
    case MODE_CENTERED:
      dst_rect.x = (native_width - screen_width) / 2;
      dst_rect.y = (native_height - screen_height) / 2;
      dst_rect.width = screen_width;
      dst_rect.height = screen_height;
      break;
    case MODE_KEEP_ASPECT:
      {
        const float fwidth = (float)screen_width;
        const float fheight = (float)screen_height;
        const float rx = (float)native_width / fwidth;
        const float ry = (float)native_height / fheight;
        const float r = (rx > ry) ? ry : rx;
        dst_rect.width = static_cast<int>(fwidth * r + 0.5f);
        dst_rect.height = static_cast<int>(fheight * r + 0.5f);
        dst_rect.x = (native_width - dst_rect.width) / 2;
        dst_rect.y = (native_height - dst_rect.height) / 2;
      }
      break;
  };

  VC_RECT_T src_rect =
  {
    0, 0, screen_width << 16, screen_height << 16
  };

  DISPMANX_DISPLAY_HANDLE_T dispman_display;
  DISPMANX_UPDATE_HANDLE_T dispman_update;
  DISPMANX_ELEMENT_HANDLE_T dispman_element;

  dispman_display = dnload_vc_dispmanx_display_open(0);
  dispman_update = dnload_vc_dispmanx_update_start(0);

  dispman_element = dnload_vc_dispmanx_element_add(
      dispman_update, dispman_display, 0/*layer*/, &dst_rect, 0/*src*/,
      &src_rect, DISPMANX_PROTECTION_NONE, &alpha, 0/*clamp*/,
      (DISPMANX_TRANSFORM_T)0/*transform*/);

  out_native_window->element = dispman_element;
  out_native_window->width = screen_width;
  out_native_window->height = screen_height;

  dnload_vc_dispmanx_update_submit_sync(dispman_update);
}

/** \brief Create native videocore window with default settings.
 *
 * \param screen_width Window width.
 * \param screen_height Window height.
 * \param out_native_window Native window output.
 */
static void videocore_create_native_window(int screen_width, int screen_height,
    EGL_DISPMANX_WINDOW_T *out_native_window)
{
  videocore_create_native_window_extended(screen_width, screen_height, MODE_KEEP_ASPECT, out_native_window);
}

#if defined(__cplusplus)
}
#endif

#endif
