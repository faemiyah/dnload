cmake_minimum_required(VERSION 2.6)

project(stub)

enable_language(C)
enable_language(CXX)

include("defaults.cmake")

find_boost_program_options(TRUE)
find_png(TRUE)
find_sdl(TRUE)

check_raspberry_pi()
if(RASPBERRY_PI_FOUND)
  add_definitions(-DDNLOAD_VIDEOCORE -DDNLOAD_GLESV2)
  set(BCM_HOST_LIBRARY "bcm_host")
  set(EGL_LIBRARY "EGL")
  set(OPENGL_gl_LIBRARY "GLESv2")
else()
  find_opengl(TRUE)
  find_glew(TRUE STATIC)
endif()

add_definitions(-DUSE_LD)

output_flags("DEBUG" on)

add_subdirectory(src)
