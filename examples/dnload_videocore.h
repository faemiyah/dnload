#ifndef DNLOAD_VIDEOCORE_H
#define DNLOAD_VIDEOCORE_H

#include "bcm_host.h"
#include "EGL/eglplatform.h"

#if defined(__cplusplus)
extern "C"
{
#endif

/// Window mode enumeration.
enum WindowMode
{
  /// Put window to origin (top left).
  MODE_ORIGO,

  /// Stretch window to fill screen.
  MODE_STRETCH,

  /// Center window in the middle of screen.
  MODE_CENTERED,

  /// Stretch window to fill whole screen area.
  MODE_KEEP_ASPECT
};

/// Global native window storage.
static EGL_DISPMANX_WINDOW_T g_egl_native_window;

/// Open a videocore display.
///
/// \param dst_rect Destination rectangle.
/// \param src_rect Source rectangle.
static void videocore_open_native_window(const VC_RECT_T *dst_rect, const VC_RECT_T *src_rect)
{
  VC_DISPMANX_ALPHA_T alpha =
  {
    DISPMANX_FLAGS_ALPHA_FIXED_ALL_PIXELS, 255, 0
  };
  DISPMANX_DISPLAY_HANDLE_T dispman_display = dnload_vc_dispmanx_display_open(0);
  DISPMANX_UPDATE_HANDLE_T dispman_update = dnload_vc_dispmanx_update_start(0);
  DISPMANX_ELEMENT_HANDLE_T element = dnload_vc_dispmanx_element_add(
      dispman_update, dispman_display, 0/*layer*/, dst_rect, 0/*src*/,
      src_rect, DISPMANX_PROTECTION_NONE, &alpha, 0/*clamp*/,
      (DISPMANX_TRANSFORM_T)0/*transform*/);
  int result;

  g_egl_native_window.element = element;

  result = dnload_vc_dispmanx_update_submit_sync(dispman_update);
#if defined(USE_LD)
  if(result)
  {
    fprintf(stderr, "vc_dispmanx_update_submit_sync() failed: %i", result);
    dnload_bcm_host_deinit();
    return;
  }
#else
  (void)result;
#endif
}

/// Create native videocore window.
///
/// \param screen_width Window width.
/// \param screen_height Window height.
/// \param mode Defines how window is scaled to match the actual screen size.
static void videocore_create_native_window_extended(int screen_width, int screen_height, enum WindowMode mode)
{
  VC_RECT_T src_rect =
  {
    0, 0, screen_width << 16, screen_height << 16
  };
  VC_RECT_T dst_rect =
  {
    0, 0, screen_width, screen_height
  };
  uint32_t native_width;
  uint32_t native_height;
  int32_t result;

  dnload_bcm_host_init();

  result = dnload_graphics_get_display_size(0, &native_width, &native_height);
#if defined(USE_LD)
  if(result)
  {
    fprintf(stderr, "graphics_get_display_size() failed: %i", result);
    dnload_bcm_host_deinit();
    return;
  }
#else
  (void)result;
#endif

  switch(mode)
  {
    case MODE_STRETCH:
      dst_rect.x = dst_rect.y = 0;
      dst_rect.width = native_width;
      dst_rect.height = native_height;
    case MODE_CENTERED:
      dst_rect.x = (native_width - screen_width) / 2;
      dst_rect.y = (native_height - screen_height) / 2;
      // Default size is ok.
      break;

    case MODE_KEEP_ASPECT:
      {
        const float fwidth = (float)screen_width;
        const float fheight = (float)screen_height;
        const float rx = (float)native_width / fwidth;
        const float ry = (float)native_height / fheight;
        if(rx > ry)
        {
          dst_rect.width = static_cast<int32_t>(fwidth * ry);
          dst_rect.height = native_height;
          dst_rect.x = (native_width - dst_rect.width) / 2;
        }
        else
        {
          dst_rect.width = native_width;
          dst_rect.height = static_cast<int32_t>(fheight * rx);
          dst_rect.y = (native_height - dst_rect.height) / 2;
        }
      }
      break;

    case MODE_ORIGO:
    default:
      // Defaults are ok.
      break;
  };

  videocore_open_native_window(&dst_rect, &src_rect);
  g_egl_native_window.width = screen_width;
  g_egl_native_window.height = screen_height;
}

/// Create native videocore window with default settings.
///
/// \param screen_width Window width.
/// \param screen_height Window height.
/// \param out_native_window Native window output.
static void videocore_create_native_window(int screen_width, int screen_height)
{
  videocore_create_native_window_extended(screen_width, screen_height, MODE_KEEP_ASPECT);
}

#if defined(USE_LD)
/// Move videocore window on screen.
///
/// \param px X position.
/// \param py Y position.
/// \param width Widht.
/// \param height Height.
static void videocore_move_native_window(int px, int py, int width, int height)
{
  VC_RECT_T src_rect =
  {
    0, 0, width << 16, height << 16
  };
  VC_RECT_T dst_rect =
  {
    px, py, width, height
  };
  DISPMANX_UPDATE_HANDLE_T dispman_update = dnload_vc_dispmanx_update_start(0);

  vc_dispmanx_element_change_attributes(dispman_update, g_egl_native_window.element,
      (1 << 2) | (1 << 3), 0/*layer*/, 0/*opacity*/, &dst_rect, &src_rect, 0/*mask*/,
      (DISPMANX_TRANSFORM_T)0/*transform*/);

  dnload_vc_dispmanx_update_submit_sync(dispman_update);
}
#endif

#if defined(__cplusplus)
}
#endif

#endif
