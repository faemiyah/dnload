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

include_directories("${PROJECT_SOURCE_DIR}")
include_directories("${PROJECT_SOURCE_DIR}/src")

add_executable(intro "src/bsd_rand.c" "src/glsl_shader_source.cpp" "src/image_png.cpp" "src/intro.cpp" "src/main.cpp")
if(${MSVC})
  target_link_libraries(intro "WINMM")
else()
  target_link_libraries(intro ${BOOST_PROGRAM_OPTIONS_LIBRARY})
endif()
target_link_libraries(intro debug ${PNG_LIBRARY_DEBUG})
target_link_libraries(intro optimized ${PNG_LIBRARY_RELEASE})
target_link_libraries(intro debug ${SDL_LIBRARY_DEBUG})
target_link_libraries(intro optimized ${SDL_LIBRARY_RELEASE})
if(RASPBERRY_PI_FOUND)
  target_link_libraries(intro ${BCM_HOST_LIBRARY})
  target_link_libraries(intro ${EGL_LIBRARY})
  target_link_libraries(intro ${OPENGL_gl_LIBRARY})
else()
  target_link_libraries(intro debug ${GLEW_LIBRARY_DEBUG})
  target_link_libraries(intro optimized ${GLEW_LIBRARY_RELEASE})
endif()
