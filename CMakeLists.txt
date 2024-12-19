cmake_minimum_required(VERSION 3.13)
set(CMAKE_CONFIGURATION_TYPES "Debug;Release")
project(dnload)

enable_language(C)
enable_language(CXX)

include("defaults.cmake")
find_boost("filesystem" "program_options" "system" "wave")
find_png()
find_sdl2()
find_threads()

option(USE_GLES "Use OpenGL ES as opposed to OpenGL without testing" OFF)
if(USE_GLES)
    set(MALI_FOUND TRUE)
else()
    check_mali()
    check_videocore()
endif()
if(MALI_FOUND)
    add_definitions(-DDNLOAD_USE_GLES)
    set(EGL_LIBRARY "EGL")
    set(OPENGL_gl_LIBRARY "GLESv2")
elseif(VIDEOCORE_FOUND)
    add_definitions(-DDNLOAD_USE_GLES -DDNLOAD_USE_VIDEOCORE)
    set(BCM_HOST_LIBRARY "bcm_host")
    set(EGL_LIBRARY "EGL")
    set(OPENGL_gl_LIBRARY "GLESv2")
else()
    find_opengl()
    find_glew()
endif()

output_flags("DEBUG" on)

add_definitions(-DDNLOAD_USE_LD)
add_definitions(-DDNLOAD_VERSION="r16")

include_directories("${PROJECT_SOURCE_DIR}/src")

set(EXECUTABLE_NAME "intro")
add_executable("${EXECUTABLE_NAME}"
    "src/bsd_rand.c"
    "src/bsd_rand.h"
    "src/fps_counter.cpp"
    "src/fps_counter.hpp"
    "src/glsl_pipeline.cpp"
    "src/glsl_pipeline.hpp"
    "src/glsl_program.cpp"
    "src/glsl_program.hpp"
    "src/glsl_shader.cpp"
    "src/glsl_shader.hpp"
    "src/glsl_shader_program.cpp"
    "src/glsl_shader_program.hpp"
    "src/glsl_shader_source.cpp"
    "src/glsl_shader_source.hpp"
    "src/glsl_wave.cpp"
    "src/glsl_wave.hpp"
    "src/image_png.cpp"
    "src/image_png.hpp"
    "src/intro.cpp")
if(MSVC)
    target_link_libraries("${EXECUTABLE_NAME}" "WINMM")
    target_link_libraries("${EXECUTABLE_NAME}" "${OPENGL_gl_LIBRARY}")
    target_link_libraries("${EXECUTABLE_NAME}" debug "${GLEW_LIBRARY_DEBUG}" optimized "${GLEW_LIBRARY}")
    target_link_libraries("${EXECUTABLE_NAME}" debug "${PNG_LIBRARY_DEBUG}" optimized "${PNG_LIBRARY}")
    target_link_libraries("${EXECUTABLE_NAME}" debug "${SDL2_LIBRARY_DEBUG}" optimized "${SDL2_LIBRARY}")
    target_link_libraries("${EXECUTABLE_NAME}" debug "${ZLIB_LIBRARY_DEBUG}" optimized "${ZLIB_LIBRARY}")
else()
    if(MALI_FOUND)
        target_link_libraries("${EXECUTABLE_NAME}" "${EGL_LIBRARY}")
        target_link_libraries("${EXECUTABLE_NAME}" "${OPENGL_gl_LIBRARY}")
    elseif(VIDEOCORE_FOUND)
        target_link_libraries("${EXECUTABLE_NAME}" "${BCM_HOST_LIBRARY}")
        target_link_libraries("${EXECUTABLE_NAME}" "${EGL_LIBRARY}")
        target_link_libraries("${EXECUTABLE_NAME}" "${OPENGL_gl_LIBRARY}")
    else()
        target_link_libraries("${EXECUTABLE_NAME}" "${GLEW_LIBRARY}")
    endif()
    target_link_libraries("${EXECUTABLE_NAME}" "${BOOST_FILESYSTEM_LIBRARY}")
    target_link_libraries("${EXECUTABLE_NAME}" "${BOOST_PROGRAM_OPTIONS_LIBRARY}")
    target_link_libraries("${EXECUTABLE_NAME}" "${BOOST_SYSTEM_LIBRARY}")
    target_link_libraries("${EXECUTABLE_NAME}" "${BOOST_THREAD_LIBRARY}")
    target_link_libraries("${EXECUTABLE_NAME}" "${BOOST_WAVE_LIBRARY}")
    target_link_libraries("${EXECUTABLE_NAME}" "${PNG_LIBRARY}")
    target_link_libraries("${EXECUTABLE_NAME}" "${SDL2_LIBRARY}")
endif()
target_link_libraries("${EXECUTABLE_NAME}" "${THREADS_LIBRARY}")
