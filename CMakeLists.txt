cmake_minimum_required(VERSION 3.1)
set(CMAKE_CONFIGURATION_TYPES "Debug;Release")
project(dnload)

enable_language(C)
enable_language(CXX)

include("defaults.cmake")

find_boost("filesystem" "program_options" "system" "thread" "wave")
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

add_executable(fcmp
  "src/arithmetic_coder.hpp"
  "src/arithmetic_decoder.cpp"
  "src/arithmetic_decoder.hpp"
  "src/arithmetic_encoder.cpp"
  "src/arithmetic_encoder.hpp"
  "src/bit_file.cpp"
  "src/bit_file.hpp"
  "src/common.cpp"
  "src/common.hpp"
  "src/compressor.cpp"
  "src/compressor.hpp"
  "src/compressor_state.cpp"
  "src/compressor_state.hpp"
  "src/compressor_thread.cpp"
  "src/compressor_thread.hpp"
  "src/data_bits.cpp"
  "src/data_bits.hpp"
  "src/data_bits_reader.cpp"
  "src/data_bits_reader.hpp"
  "src/data_bits_state.cpp"
  "src/data_bits_state.hpp"
  "src/data_compressed.cpp"
  "src/data_compressed.hpp"
  "src/data_compressed_reader.cpp"
  "src/data_compressed_reader.hpp"
  "src/filesystem.hpp"
  "src/main.cpp"
  "src/model.cpp"
  "src/model.hpp"
  "src/prediction.hpp"
  "src/predictor_key.cpp"
  "src/predictor_key.hpp"
  "src/predictor_value.cpp"
  "src/predictor_value.hpp"
  "src/probability.hpp"
  "src/threading.hpp")
if(${MSVC})
  target_link_libraries(fcmp "WINMM")
else()
  target_link_libraries(fcmp "${BOOST_FILESYSTEM_LIBRARY}")
  target_link_libraries(fcmp "${BOOST_PROGRAM_OPTIONS_LIBRARY}")
  target_link_libraries(fcmp "${BOOST_SYSTEM_LIBRARY}")
endif()
target_link_libraries(fcmp "${THREADS_LIBRARY}")

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

# TODO: Remove when Wave works with C++11.
set_property(SOURCE "src/glsl_wave.cpp" APPEND_STRING PROPERTY COMPILE_FLAGS "-std=c++03")
