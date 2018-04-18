cmake_minimum_required(VERSION 3.1)
set(CMAKE_CONFIGURATION_TYPES "Debug;Release")
project(dnload)

enable_language(C)
enable_language(CXX)

include("defaults.cmake")

find_boost("filesystem" "program_options" "system" "wave")
find_png()
find_sdl2()
find_threads()

check_mali()
check_videocore()
if(MALI_FOUND)
  add_definitions(-DDNLOAD_MALI -DDNLOAD_GLESV2)
  set(EGL_LIBRARY "EGL")
  set(OPENGL_gl_LIBRARY "GLESv2")
elseif(VIDEOCORE_FOUND)
  add_definitions(-DDNLOAD_VIDEOCORE -DDNLOAD_GLESV2)
  set(BCM_HOST_LIBRARY "bcm_host")
  set(EGL_LIBRARY "EGL")
  set(OPENGL_gl_LIBRARY "GLESv2")
else()
  find_opengl()
  find_glew()
endif()

output_flags("DEBUG" on)

add_definitions(-DUSE_LD)
add_definitions(-DVERSION="r14")

include_directories("${PROJECT_SOURCE_DIR}/src")

add_executable(intro
  "src/bsd_rand.c"
  "src/bsd_rand.h"
  "src/glsl_program.cpp"
  "src/glsl_program.hpp"
  "src/glsl_shader.cpp"
  "src/glsl_shader.hpp"
  "src/glsl_wave.cpp"
  "src/glsl_wave.hpp"
  "src/image_png.cpp"
  "src/image_png.hpp"
  "src/intro.cpp")
if(MSVC)
  target_link_libraries(intro "WINMM")
  target_link_libraries(intro "${OPENGL_gl_LIBRARY}")
  target_link_libraries(intro debug "${GLEW_LIBRARY_DEBUG}" optimized "${GLEW_LIBRARY}")
  target_link_libraries(intro debug "${PNG_LIBRARY_DEBUG}" optimized "${PNG_LIBRARY}")
  target_link_libraries(intro debug "${SDL2_LIBRARY_DEBUG}" optimized "${SDL2_LIBRARY}")
  target_link_libraries(intro debug "${ZLIB_LIBRARY_DEBUG}" optimized "${ZLIB_LIBRARY}")
else()
  if(MALI_FOUND)
    target_link_libraries(intro "${EGL_LIBRARY}")
    target_link_libraries(intro "${OPENGL_gl_LIBRARY}")
  elseif(VIDEOCORE_FOUND)
    target_link_libraries(intro "${BCM_HOST_LIBRARY}")
    target_link_libraries(intro "${EGL_LIBRARY}")
    target_link_libraries(intro "${OPENGL_gl_LIBRARY}")
  else()
    target_link_libraries(intro "${GLEW_LIBRARY}")
  endif()
  target_link_libraries(intro "${BOOST_FILESYSTEM_LIBRARY}")
  target_link_libraries(intro "${BOOST_PROGRAM_OPTIONS_LIBRARY}")
  target_link_libraries(intro "${BOOST_SYSTEM_LIBRARY}")
  target_link_libraries(intro "${BOOST_THREAD_LIBRARY}")
  target_link_libraries(intro "${BOOST_WAVE_LIBRARY}")
  target_link_libraries(intro "${PNG_LIBRARY}")
  target_link_libraries(intro "${SDL2_LIBRARY}")
endif()
target_link_libraries(intro "${THREADS_LIBRARY}")
