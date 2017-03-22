/// \file
/// Very small intro stub.

//######################################
// Include #############################
//######################################

#include "dnload.h"

#if defined(USE_LD)
#include "glsl_program.hpp"
#include "image_png.hpp"
#include <cstdio>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <boost/exception/diagnostic_information.hpp>
#include <boost/program_options.hpp>
#include <boost/scoped_array.hpp>
#include <boost/tuple/tuple.hpp>
namespace po = boost::program_options;
#endif

//######################################
// Define ##############################
//######################################

/// Screen mode.
///
/// Negative values windowed.
/// Positive values fullscreen.
#define DISPLAY_MODE -720

/// \cond
#if (0 > (DISPLAY_MODE))
#define SCREEN_F 0
#define SCREEN_H (-(DISPLAY_MODE))
#elif (0 < (DISPLAY_MODE))
#define SCREEN_F 1
#define SCREEN_H (DISPLAY_MODE)
#else
#error "invalid display mode (pre)"
#endif
#if ((800 == SCREEN_H) || (1200 == SCREEN_H))
#define SCREEN_W ((SCREEN_H / 10) * 16)
#else
#define SCREEN_W (((SCREEN_H * 16) / 9) - (((SCREEN_H * 16) / 9) % 4))
#endif
/// \endcond

/// Size of one sample in bytes.
#define AUDIO_SAMPLE_SIZE 1

/// \cond
#if (4 == AUDIO_SAMPLE_SIZE)
#define AUDIO_SAMPLE_TYPE_SDL AUDIO_F32SYS
typedef float sample_t;
#elif (2 == AUDIO_SAMPLE_SIZE)
#define AUDIO_SAMPLE_TYPE_SDL AUDIO_S16SYS
typedef int16_t sample_t;
#elif (1 == AUDIO_SAMPLE_SIZE)
#define AUDIO_SAMPLE_TYPE_SDL AUDIO_U8
typedef uint8_t sample_t;
#else
#error "invalid audio sample size"
#endif
#define AUDIO_POSITION_SHIFT (9 - (4 / sizeof(sample_t)))
/// \endcond

/// Audio channels.
#define AUDIO_CHANNELS 1

/// Audio samplerate.
#define AUDIO_SAMPLERATE 8000

/// Audio byterate.
#define AUDIO_BYTERATE (AUDIO_CHANNELS * AUDIO_SAMPLERATE * sizeof(sample_t))

/// Intro length (in bytes of audio).
#define INTRO_LENGTH (16 * AUDIO_BYTERATE)

/// Intro start position (in seconds).
#define INTRO_START (0 * AUDIO_BYTERATE)

/// \cond
#define STARTING_POS_X 0.0f
#define STARTING_POS_Y 0.0f
#define STARTING_POS_Z 2.0f
#define STARTING_FW_X 0.0f
#define STARTING_FW_Y 0.0f
#define STARTING_FW_Z -1.0f
#define STARTING_UP_X 0.0f
#define STARTING_UP_Y 1.0f
#define STARTING_UP_Z 0.0f
/// \endcond

//######################################
// Global data #########################
//######################################

/// Audio buffer for output.
static uint8_t g_audio_buffer[INTRO_LENGTH * 9 / 8 / sizeof(sample_t)];

/// Current audio position.
static uint8_t *g_audio_position = reinterpret_cast<uint8_t*>(&g_audio_buffer[INTRO_START]);

#if defined(USE_LD)

/// \cond
static float g_pos_x = STARTING_POS_X;
static float g_pos_y = STARTING_POS_Y;
static float g_pos_z = STARTING_POS_Z;
static float g_fw_x = STARTING_FW_X;
static float g_fw_y = STARTING_FW_Y;
static float g_fw_z = STARTING_FW_Z;
static float g_up_x = STARTING_UP_X;
static float g_up_y = STARTING_UP_Y;
static float g_up_z = STARTING_UP_Z;
/// \endcond

/// Developer mode global toggle.
static uint8_t g_flag_developer = 0;

static const char *usage = ""
"Usage: intro <options>\n"
"Main function wrapper for intro stub.\n"
"Release version does not pertain to any size limitations.\n";

#else

/// Developer mode disabled.
#define g_flag_developer 0

#endif

//######################################
// Global functions ####################
//######################################

/// Global SDL window storage.
SDL_Window *g_sdl_window;

#if defined(DNLOAD_GLESV2) && defined(DNLOAD_VIDEOCORE)
#include "dnload_egl.h"
#include "dnload_videocore.h"
#endif

/// Swap buffers.
///
/// Uses global data.
static void swap_buffers()
{
#if defined(DNLOAD_GLESV2) && defined(DNLOAD_VIDEOCORE)
  dnload_eglSwapBuffers(g_egl_display, g_egl_surface);
#else
  dnload_SDL_GL_SwapWindow(g_sdl_window);
#endif
}

/// Tear down initialized systems.
///
/// Uses global data.
static void teardown()
{
#if defined(DNLOAD_GLESV2) && defined(DNLOAD_VIDEOCORE)
  egl_quit(g_egl_display);
  dnload_bcm_host_deinit();
#endif
  dnload_SDL_Quit();
}

//######################################
// Random ##############################
//######################################

#if 0

/// \brief Random float value.
///
/// \param op Given maximum value.
/// \return Random value between 0 and given value.
static float frand(float op)
{
  return static_cast<float>(dnload_rand() & 0xFFFF) * ((1.0f / 65535.0f) * op);
}

#endif

//######################################
// Music ###############################
//######################################

/// \brief Update audio stream.
///
/// \param userdata Not used.
/// \param stream Target stream.
/// \param len Number of bytes to write.
static void audio_callback(void *userdata, Uint8 *stream, int len)
{
  (void)userdata;

#if defined(__GNUC__) && !defined(__clang__) && 0
  __builtin_memcpy(g_audio_position, stream, len);
#else
  for(int ii = 0; (ii < len); ++ii)
  {
    stream[ii] = g_audio_position[ii];
  }
#endif
  g_audio_position += len;
}

/// SDL audio specification struct.
static SDL_AudioSpec audio_spec =
{
  AUDIO_SAMPLERATE,
  AUDIO_SAMPLE_TYPE_SDL,
  AUDIO_CHANNELS,
  0,
#if defined(USE_LD)
  4096,
#else
  256, // ~172.3Hz, lower values seem to cause underruns
#endif
  0,
  0,
  audio_callback,
  NULL
};

//######################################
// Shaders #############################
//######################################

#if defined(DNLOAD_GLESV2)

/// Quad vertex shader.
static const char *g_shader_vertex_quad = ""
"attribute vec2 a;"
"varying mediump vec2 b;"
"precision mediump float;"
"void main()"
"{"
"b=a;"
"gl_Position=vec4(a,0.,1.);"
"}";

/// Quad fragment shader.
static const char *g_shader_fragment_quad = ""
"uniform highp vec3 u[4];"
"varying mediump vec2 b;"
"precision highp float;"
"void main()"
"{"
"vec2 m=b;"
"if(u[3].y>1.)m.x*=u[3].y;"
"else m.y/=u[3].y;"
"vec3 h=normalize(u[1]),r=normalize(cross(h,u[2])),d=normalize(m.x*r+m.y*normalize(cross(r,h))+h),c,e;"
"float D=dot(-u[0],d),R=1.+sin(u[3].x/4444.)*.1,S;"
"c=D*d+u[0];"
"S=dot(c,c);"
"if(S<=R)"
"{"
"e=(D-sqrt(R*R-S*S))*d+u[0];"
"gl_FragColor=vec4(e*dot(e,vec3(1.)),1.);"
"}"
"else"
"{"
"gl_FragColor=vec4(0.,0.,0.,1.);"
"}"
"}";

/// Uniform location.
static GLint g_uniform_u;

#else

#if 1

#include "quad_430.vert.glsl.hpp" // g_shader_vertex_quad
#include "quad_430.frag.glsl.hpp" // g_shader_fragment_quad

#else

/// Quad vertex shader.
static const char *g_shader_vertex_quad = ""
"#version 430\n"
"in vec2 a;"
"out vec2 b;"
"out gl_PerVertex"
"{"
"vec4 gl_Position;"
"};"
"void main()"
"{"
"b=a;"
"gl_Position=vec4(a,0,1);"
"}";

/// Quad fragment shader.
static const char *g_shader_fragment_quad = ""
"#version 430\n"
"layout(location=0)uniform vec3[4] u;"
"in vec2 b;"
"out vec4 o;"
"void main()"
"{"
"vec2 m=b;"
"if(u[3].y>1.)m.x*=u[3].y;"
"else m.y/=u[3].y;"
"vec3 h=normalize(u[1]),r=normalize(cross(h,u[2])),d=normalize(m.x*r+m.y*normalize(cross(r,h))+h),c,e;"
"float D=dot(-u[0],d),R=1.+sin(u[3].x/4444.)*.1,S;"
"c=D*d+u[0];"
"S=dot(c,c);"
"if(S<=R)"
"{"
"e=(D-sqrt(R*R-S*S))*d+u[0];"
"o=vec4(e*dot(e,vec3(1.)),1.);"
"}"
"else"
"{"
"o=vec4(0.0,0.0,0.0,1.0);"
"}"
"}";

#endif

/// Fixed uniform location.
static const GLint g_uniform_u = 0;

#endif

/// Shader program.
GLuint g_program_fragment;

#if defined(DNLOAD_GLESV2)

/// \brief Create shader.
///
/// \param source Source of the shader.
/// \return Shader ID.
GLuint create_shader(const char *source, GLenum type)
{
  GLuint ret = dnload_glCreateShader(type);
  
#if defined(USE_LD)
  GlslShaderSource glsl_source(source);
  std::string pretty_source = glsl_source.str();
  const char *pretty_source_c_str = pretty_source.c_str();
  dnload_glShaderSource(ret, 1, &pretty_source_c_str, NULL);
#else
  dnload_glShaderSource(ret, 1, &source, NULL);
#endif

  dnload_glCompileShader(ret);

#if defined(USE_LD)
  std::string log = GlslShaderSource::get_shader_info_log(ret);

  std::cout << pretty_source << std::endl;
  if(0 < log.length())
  {
    std::cout << log << std::endl;
  }

  if(!GlslShaderSource::get_shader_compile_status(ret))
  {
    teardown();
    exit(1);
  }
#endif

  return ret;
}

/// \brief Create program.
///
/// \param vertex Vertex shader.
/// \param fragment Fragment shader.
/// \return Program ID
GLuint create_program(const char *vertex, const char *fragment)
{
  GLuint ret = dnload_glCreateProgram();

  dnload_glAttachShader(ret, create_shader(vertex, GL_VERTEX_SHADER));
  dnload_glAttachShader(ret, create_shader(fragment, GL_FRAGMENT_SHADER));

  dnload_glLinkProgram(ret);

#if defined(USE_LD)
  std::string log = GlslShaderSource::get_program_info_log(ret);

  if(0 < log.length())
  {
    std::cout << log << std::endl;
  }

  if(!GlslShaderSource::get_program_link_status(ret))
  {
    teardown();
    exit(1);
  }
  std::cout << "GLSL program id: " << ret << std::endl;
#endif

  return ret;
}

#elif defined(USE_LD) && 0

/// \brief Create a shader.
///
/// \param type Shader type.
/// \param source Shader content.
/// \return Shader program ID.
static GLuint program_attach(GLenum type, const char *source, GLuint pipeline, GLbitfield mask)
{
  GlslShaderSource glsl_source(source);
  std::string pretty_source = glsl_source.str();
  const GLchar *pretty_source_c_str = pretty_source.c_str();
  GLuint ret = dnload_glCreateShaderProgramv(type, 1, &pretty_source_c_str);

  dnload_glUseProgramStages(pipeline, mask, ret);

  std::string log = GlslShaderSource::get_program_info_log(ret);

  std::cout << pretty_source << std::endl;
  if(0 < log.length())
  {
    std::cout << log << std::endl;
  }

  if(!GlslShaderSource::get_program_link_status(ret))
  {
    SDL_Quit();
    exit(1);
  }
  std::cout << "GLSL separable program id: " << ret << std::endl;

  return ret;
}

/// \brief Create a program pipeline.
///
/// \return Program pipeline (already bound).
static GLuint pipeline_create()
{
  GLuint ret;

  dnload_glGenProgramPipelines(1, &ret);
  dnload_glBindProgramPipeline(ret);

  return ret;
}

#endif

//######################################
// Uniform data ########################
//######################################

/// \brief Uniforms.
///
/// 0: X position.
/// 1: Y position.
/// 2: Z position.
/// 3: X forward.
/// 4: Y forward.
/// 5: Z forward.
/// 6: X up.
/// 7: Y up.
/// 8: Z up.
/// 9: Time.
/// 10: Screen aspect ratio x/y.
/// 11: Unused.
static float g_uniform_array[12] =
{
  STARTING_POS_X, STARTING_POS_Y, STARTING_POS_Z,
  STARTING_FW_X, STARTING_FW_Y, STARTING_FW_Z,
  STARTING_UP_X, STARTING_UP_Y, STARTING_UP_Z,
  0.0f, 0.0f, 0.0f,
};

/// \brief Draw the world.
///
/// \param ticks Tick count.
/// \param aspec Screen aspect.
static void draw(unsigned ticks)
{
  //dnload_glDisable(GL_DEPTH_TEST);

#if defined(USE_LD)
  if(g_flag_developer)
  {
    g_uniform_array[0] = g_pos_x;
    g_uniform_array[1] = g_pos_y;
    g_uniform_array[2] = g_pos_z;
    g_uniform_array[3] = g_fw_x;
    g_uniform_array[4] = g_fw_y;
    g_uniform_array[5] = g_fw_z;
    g_uniform_array[6] = g_up_x;
    g_uniform_array[7] = g_up_y;
    g_uniform_array[8] = g_up_z;
  }
#endif
  g_uniform_array[9] = static_cast<float>(ticks);

#if defined(DNLOAD_GLESV2)
  dnload_glUniform3fv(g_uniform_u, 4, g_uniform_array);
  {
    int8_t array[] =
    {
      -3, 1,
      1, -3,
      1, 1,
    };

    dnload_glVertexAttribPointer(0, 2, GL_BYTE, GL_FALSE, 0, array);
    dnload_glEnableVertexAttribArray(0);
    dnload_glDrawArrays(GL_TRIANGLES, 0, 3);
  }
#else
  dnload_glProgramUniform3fv(g_program_fragment, g_uniform_u, 4, g_uniform_array);
  dnload_glRects(-1, -1, 1, 1);
#endif
}

//######################################
// Utility #############################
//######################################

#if defined(USE_LD)

/// Parse resolution from string input.
///
/// \param op Resolution string.
/// \return Tuple of width and height.
boost::tuple<unsigned, unsigned> parse_resolution(const std::string &op)
{
  size_t cx = op.find("x");
  
  if(std::string::npos == cx)
  {
    cx = op.rfind("p");

    if((std::string::npos == cx) || (0 >= cx))
    {
      std::ostringstream sstr;
      sstr << "invalid resolution string '" << op << '\'';
      BOOST_THROW_EXCEPTION(std::runtime_error(sstr.str()));
    }

    std::string sh = op.substr(0, cx);

    unsigned rh = boost::lexical_cast<unsigned>(sh);
    unsigned rw = (rh * 16) / 9;
    unsigned rem4 = rw % 4;

    return boost::make_tuple(rw - rem4, rh);
  }

  std::string sw = op.substr(0, cx);
  std::string sh = op.substr(cx + 1);

  return boost::make_tuple(boost::lexical_cast<int>(sw), boost::lexical_cast<int>(sh));
}

/// \brief Audio writing callback.
///
/// \param data Raw audio data.
/// \param size Audio data size (in samples).
void write_audio(void *data, size_t size)
{
  FILE *fd = fopen("intro.raw", "wb");

  if(fd != NULL)
  {
    fwrite(data, size, 1, fd);
  }

  fclose(fd);
  return;
}

/// \brief Image writing callback.
///
/// \param screen_w Screen width.
/// \param screen_h Screen height.
/// \param idx Frame index to write.
void write_frame(unsigned screen_w, unsigned screen_h, unsigned idx)
{
  boost::scoped_array<uint8_t> image(new uint8_t[screen_w * screen_h * 3]);
  std::ostringstream sstr;

  glReadPixels(0, 0, static_cast<GLsizei>(screen_w), static_cast<GLsizei>(screen_h), GL_RGB, GL_UNSIGNED_BYTE,
      image.get());

  sstr << "intro_" << std::setfill('0') << std::setw(4) << idx << ".png";

  gfx::image_png_save(sstr.str(), screen_w, screen_h, 24, image.get());
  return;
}

/// Update window position.
///
/// May be NOP depending on platform.
void update_window_position()
{
  static int window_x = INT_MIN;
  static int window_y = INT_MIN;
  static int window_width = INT_MIN;
  static int window_height = INT_MIN;
  int current_window_x;
  int current_window_y;
  int current_window_width;
  int current_window_height;
  
  SDL_GetWindowPosition(g_sdl_window, &current_window_x, &current_window_y);
  SDL_GetWindowSize(g_sdl_window, &current_window_width, &current_window_height);
  if((current_window_x != window_x) || (current_window_y != window_y) ||
      (current_window_width != window_width) || (current_window_height != window_height))
  {
    window_x = current_window_x;
    window_y = current_window_y;
    window_width = current_window_width;
    window_height = current_window_height;
#if defined(DNLOAD_VIDEOCORE)
    videocore_move_native_window(window_x, window_y, window_width, window_height);
#endif
  }
}

#endif

//######################################
// intro / _start ######################
//######################################

/// \cond
#if defined(DNLOAD_VIDEOCORE)
#define DEFAULT_SDL_WINDOW_FLAGS SDL_WINDOW_BORDERLESS
#else
#define DEFAULT_SDL_WINDOW_FLAGS SDL_WINDOW_OPENGL
#endif
/// \endcond

#if defined(USE_LD)
/// \brief Intro body function.
///
/// \param screen_w Screen width.
/// \param screen_h Screen height.
/// \param flag_fullscreen Fullscreen toggle.
/// \param flag_record Record toggle.
void intro(unsigned screen_w, unsigned screen_h, bool flag_fullscreen, bool flag_record)
#else
#define screen_w static_cast<unsigned>(SCREEN_W)
#define screen_h static_cast<unsigned>(SCREEN_H)
#define flag_fullscreen static_cast<bool>(SCREEN_F)
void _start()
#endif
{
  dnload();
  dnload_SDL_Init(SDL_INIT_VIDEO | SDL_INIT_AUDIO);
#if defined(DNLOAD_GLESV2) && !defined(DNLOAD_VIDEOCORE)
  dnload_SDL_GL_SetAttribute(SDL_GL_CONTEXT_PROFILE_MASK, SDL_GL_CONTEXT_PROFILE_ES);
  dnload_SDL_GL_SetAttribute(SDL_GL_CONTEXT_MAJOR_VERSION, 2);
  dnload_SDL_GL_SetAttribute(SDL_GL_CONTEXT_MINOR_VERSION, 0);
#endif
  g_sdl_window = dnload_SDL_CreateWindow(NULL, SDL_WINDOWPOS_UNDEFINED, SDL_WINDOWPOS_UNDEFINED,
      static_cast<int>(screen_w), static_cast<int>(screen_h),
      DEFAULT_SDL_WINDOW_FLAGS | (flag_fullscreen ? SDL_WINDOW_FULLSCREEN : 0));
#if defined(DNLOAD_GLESV2) && defined(DNLOAD_VIDEOCORE)
  videocore_create_native_window(screen_w, screen_h);
  bool egl_result = egl_init(reinterpret_cast<NativeWindowType>(&g_egl_native_window), &g_egl_display,
      &g_egl_surface);
#if defined(USE_LD)
  if(!egl_result)
  {
    teardown();
    exit(1);
  }
#else
  (void)egl_result;
#endif
#else
  dnload_SDL_GL_CreateContext(g_sdl_window);
#endif
  dnload_SDL_ShowCursor(g_flag_developer);

#if defined(USE_LD)
#if !defined(DNLOAD_GLESV2)
  {
    GLenum err = glewInit();
    if(GLEW_OK != err)
    {
      std::cerr  << "glewInit(): " << glewGetErrorString(err) << std::endl;
      teardown();
      exit(1);
    }
  }
#endif
  if(!flag_fullscreen)
  {
    update_window_position();
  }
#endif

#if defined(DNLOAD_GLESV2)
#if defined(USE_LD)
  GlslProgram program;
  program.addShader(GL_VERTEX_SHADER, g_shader_vertex_quad);
  program.addShader(GL_FRAGMENT_SHADER, g_shader_fragment_quad);
  if(!program.link())
  {
    BOOST_THROW_EXCEPTION(std::runtime_error("program creation failure"));
  }
  g_program_fragment = program.getId();
  glUseProgram(g_program_fragment);
  g_uniform_u = glGetUniformLocation(g_program_fragment, "u");
#else
  g_program_fragment = create_program(g_shader_vertex_quad, g_shader_fragment_quad);
  dnload_glUseProgram(g_program_fragment);
  g_uniform_u = dnload_glGetUniformLocation(g_program_fragment, "u");
#endif
#else
#if defined(USE_LD)
  GlslProgram program;
  program.addShader(GL_VERTEX_SHADER, g_shader_vertex_quad);
  program.addShader(GL_FRAGMENT_SHADER, g_shader_fragment_quad);
  if(!program.link(true))
  {
    BOOST_THROW_EXCEPTION(std::runtime_error("pipeline creation failure"));
  }
  glBindProgramPipeline(program.getPipelineId());
  g_program_fragment = program.getPipelineId(GL_FRAGMENT_SHADER);
#else
  // Shader generation inline.
  GLuint pipeline;
  GLuint program_vert = dnload_glCreateShaderProgramv(GL_VERTEX_SHADER, 1, &g_shader_vertex_quad);
  g_program_fragment = dnload_glCreateShaderProgramv(GL_FRAGMENT_SHADER, 1, &g_shader_fragment_quad);

  dnload_glGenProgramPipelines(1, &pipeline);
  dnload_glBindProgramPipeline(pipeline);
  dnload_glUseProgramStages(pipeline, 1, program_vert);
  dnload_glUseProgramStages(pipeline, 2, g_program_fragment);
#endif
#endif

  g_uniform_array[10] = static_cast<float>(screen_w) / static_cast<float>(screen_h);

  {
    unsigned ii;

    // Example by "bst", taken from "Music from very short programs - the 3rd iteration" by viznut.
    for(ii = 0; (INTRO_LENGTH / sizeof(sample_t) > ii); ++ii)
    {
      g_audio_buffer[ii] =
        static_cast<uint8_t>(
            static_cast<int>(ii / 70000000 * ii * ii + ii) % 127 |
            ii >> 4 | ii >> 5 | (ii % 127 + (ii >> 17)) | ii
          );
    }
  }

#if defined(USE_LD)
  if(flag_record)
  {
    SDL_Event event;
    unsigned frame_idx = 0;

    // audio
    SDL_PauseAudio(1);

    write_audio(g_audio_buffer, INTRO_LENGTH);

    // video
    for(;;)
    {
      unsigned ticks = static_cast<unsigned>(static_cast<float>(frame_idx) / 60.0f *
          static_cast<float>(AUDIO_BYTERATE));

      if(ticks > INTRO_LENGTH)
      {
        break;
      }

      if(SDL_PollEvent(&event) && (event.type == SDL_KEYDOWN) && (event.key.keysym.sym == SDLK_ESCAPE))
      {
        break;
      }

      draw(ticks);
      write_frame(screen_w, screen_h, frame_idx);
      swap_buffers();
      ++frame_idx;
    }

    teardown();
    return;
  }

  if(!g_flag_developer)
  {
    SDL_OpenAudio(&audio_spec, NULL);
    SDL_PauseAudio(0);
  }
#else
  dnload_SDL_OpenAudio(&audio_spec, NULL);
  dnload_SDL_PauseAudio(0);
#endif

#if defined(USE_LD)
  uint32_t start_ticks = SDL_GetTicks();	
#endif

  for(;;)
  {
#if defined(USE_LD)
    static float move_speed = 1.0f / 60.0f;
    static float current_time = 0.0f;
    static uint8_t mouse_look = 0;
    static int8_t move_backward = 0;
    static int8_t move_down = 0;
    static int8_t move_forward = 0;
    static int8_t move_left = 0;
    static int8_t move_right = 0;
    static int8_t move_up = 0;
    static int8_t time_delta = 0;
    int mouse_look_x = 0;
    int mouse_look_y = 0;
    bool quit = false;
#endif
    SDL_Event event;
    unsigned curr_ticks;

#if defined(USE_LD)
    while(SDL_PollEvent(&event))
    {
      if(SDL_QUIT == event.type)
      {
        quit = true;
      }
      else if(SDL_KEYDOWN == event.type)
      {
        switch(event.key.keysym.sym)
        {
          case SDLK_a:
            move_left = 1;
            break;

          case SDLK_d:
            move_right = 1;
            break;

          case SDLK_e:
            move_up = 1;
            break;

          case SDLK_q:
            move_down = 1;
            break;

          case SDLK_s:
            move_backward = 1;
            break;

          case SDLK_w:
            move_forward = 1;
            break;

          case SDLK_LSHIFT:
          case SDLK_RSHIFT:
            move_speed = 1.0f / 5.0f;
            break;            

          case SDLK_LALT:
            time_delta = -1;
            break;

          case SDLK_MODE:
          case SDLK_RALT:
            time_delta = 1;
            break;

          case SDLK_F5:
#if defined(DNLOAD_GLESV2)
            if(!program.link())
            {
              BOOST_THROW_EXCEPTION(std::runtime_error("program recreation failure"));
            }
            g_program_fragment = program.getId();
            glUseProgram(g_program_fragment);
            g_uniform_u = glGetUniformLocation(g_program_fragment, "u");
#else
            if(!program.link(true))
            {
              BOOST_THROW_EXCEPTION(std::runtime_error("pipeline recreation failure"));
            }
            glBindProgramPipeline(program.getPipelineId());
            g_program_fragment = program.getPipelineId(GL_FRAGMENT_SHADER);
#endif
            break;

          case SDLK_ESCAPE:
            quit = true;
            break;

          default:
            break;
        }
      }
      else if(SDL_KEYUP == event.type)
      {
        switch(event.key.keysym.sym)
        {
          case SDLK_a:
            move_left = 0;
            break;

          case SDLK_d:
            move_right = 0;
            break;

          case SDLK_e:
            move_up = 0;
            break;

          case SDLK_q:
            move_down = 0;
            break;

          case SDLK_s:
            move_backward = 0;
            break;

          case SDLK_w:
            move_forward = 0;
            break;

          case SDLK_LSHIFT:
          case SDLK_RSHIFT:
            move_speed = 1.0f / 60.0f;
            break;            

          case SDLK_MODE:
          case SDLK_LALT:
          case SDLK_RALT:
            time_delta = 0;
            break;

          default:
            break;
        }
      }
      else if(SDL_MOUSEBUTTONDOWN == event.type)
      {
        if(1 == event.button.button)
        {
          mouse_look = 1;
        }
      }
      else if(SDL_MOUSEBUTTONUP == event.type)
      {
        if(1 == event.button.button)
        {
          mouse_look = 0;
        }
      }
      else if(SDL_MOUSEMOTION == event.type)
      {
        if(0 != mouse_look)
        {
          mouse_look_x += event.motion.xrel;
          mouse_look_y += event.motion.yrel;
        }
      }
      else if(SDL_WINDOWEVENT == event.type)
      {
        if(!flag_fullscreen)
        {
          update_window_position();
        }
      }
    }

    if(g_flag_developer)
    {
      float uplen = sqrtf(g_up_x * g_up_x + g_up_y * g_up_y + g_up_z * g_up_z);
      float fwlen = sqrtf(g_fw_x * g_fw_x + g_fw_y * g_fw_y + g_fw_z * g_fw_z);
      float rt_x;
      float rt_y;
      float rt_z;
      float movement_rt = static_cast<float>(move_right - move_left) * move_speed;
      float movement_up = static_cast<float>(move_up - move_down) * move_speed;
      float movement_fw = static_cast<float>(move_forward - move_backward) * move_speed;

      g_up_x /= uplen;
      g_up_y /= uplen;
      g_up_z /= uplen;

      g_fw_x /= fwlen;
      g_fw_y /= fwlen;
      g_fw_z /= fwlen;

      rt_x = g_fw_y * g_up_z - g_fw_z * g_up_y;
      rt_y = g_fw_z * g_up_x - g_fw_x * g_up_z;
      rt_z = g_fw_x * g_up_y - g_fw_y * g_up_x;

      if(0 != mouse_look_x)
      {
        float angle = static_cast<float>(mouse_look_x) / static_cast<float>(screen_h / 4) * 0.25f;
        float ca = cosf(angle);
        float sa = sinf(angle);
        float new_rt_x = ca * rt_x + sa * g_fw_x;
        float new_rt_y = ca * rt_y + sa * g_fw_y;
        float new_rt_z = ca * rt_z + sa * g_fw_z;
        float new_fw_x = ca * g_fw_x - sa * rt_x;
        float new_fw_y = ca * g_fw_y - sa * rt_y;
        float new_fw_z = ca * g_fw_z - sa * rt_z;

        rt_x = new_rt_x;          
        rt_y = new_rt_y;
        rt_z = new_rt_z;
        g_fw_x = new_fw_x;
        g_fw_y = new_fw_y;
        g_fw_z = new_fw_z;
      }
      if(0 != mouse_look_y)
      {
        float angle = static_cast<float>(mouse_look_y) / static_cast<float>(screen_h / 4) * 0.25f;
        float ca = cosf(angle);
        float sa = sinf(angle);
        float new_fw_x = ca * g_fw_x + sa * g_up_x;
        float new_fw_y = ca * g_fw_y + sa * g_up_y;
        float new_fw_z = ca * g_fw_z + sa * g_up_z;
        float new_up_x = ca * g_up_x - sa * g_fw_x;
        float new_up_y = ca * g_up_y - sa * g_fw_y;
        float new_up_z = ca * g_up_z - sa * g_fw_z;

        g_fw_x = new_fw_x;
        g_fw_y = new_fw_y;
        g_fw_z = new_fw_z;
        g_up_x = new_up_x;
        g_up_y = new_up_y;
        g_up_z = new_up_z;
      }

      g_pos_x += movement_rt * rt_x + movement_up * g_up_x + movement_fw * g_fw_x;
      g_pos_y += movement_rt * rt_y + movement_up * g_up_y + movement_fw * g_fw_y;
      g_pos_z += movement_rt * rt_z + movement_up * g_up_z + movement_fw * g_fw_z;
    }

    if(g_flag_developer)
    {
      current_time += static_cast<float>(AUDIO_BYTERATE) / 60.0f * static_cast<float>(time_delta);

      curr_ticks = static_cast<unsigned>(current_time);
    }
    else
    {
      float seconds_elapsed = static_cast<float>(SDL_GetTicks() - start_ticks) / 1000.0f;

      curr_ticks = static_cast<unsigned>(seconds_elapsed * static_cast<float>(AUDIO_BYTERATE)) + INTRO_START;
    }

    if((curr_ticks >= INTRO_LENGTH) || quit)
    {
      break;
    }
#else
    curr_ticks = g_audio_position - reinterpret_cast<uint8_t*>(g_audio_buffer);

    dnload_SDL_PollEvent(&event);
    
    if((curr_ticks >= INTRO_LENGTH) || (event.type == SDL_KEYDOWN))
    {
      break;
    }
#endif

    draw(curr_ticks);
    swap_buffers();
  }

  teardown();
  asm_exit();
}

//######################################
// Main ################################
//######################################

#if defined(USE_LD)
/// Main function.
///
/// \param argc Argument count.
/// \param argv Arguments.
/// \return Program return code.
int DNLOAD_MAIN(int argc, char **argv)
{
  unsigned screen_w = SCREEN_W;
  unsigned screen_h = SCREEN_H;
  bool fullscreen = true;
  bool record = false;

  try
  {
    if(argc > 0)
    {
      po::options_description desc("Options");
      desc.add_options()
        ("developer,d", "Developer mode.")
        ("help,h", "Print help text.")
        ("record,R", "Do not play intro normally, instead save audio as .wav and frames as .png -files.")
        ("resolution,r", po::value<std::string>(), "Resolution to use, specify as 'WIDTHxHEIGHT' or 'HEIGHTp'.")
        ("window,w", "Start in window instead of full-screen.");

      po::variables_map vmap;
      po::store(po::command_line_parser(argc, argv).options(desc).run(), vmap);
      po::notify(vmap);

      if(vmap.count("developer"))
      {
        g_flag_developer = true;
      }
      if(vmap.count("help"))
      {
        std::cout << usage << desc << std::endl;
        return 0;
      }
      if(vmap.count("record"))
      {
        record = true;
      }
      if(vmap.count("resolution"))
      {
        boost::tie(screen_w, screen_h) = parse_resolution(vmap["resolution"].as<std::string>());
      }
      if(vmap.count("window"))
      {
        fullscreen = false;
      }
    }

    intro(screen_w, screen_h, fullscreen, record);
  }
  catch(const boost::exception &err)
  {
    std::cerr << boost::diagnostic_information(err);
    return 1;
  }
  catch(const std::exception &err)
  {
    std::cerr << err.what() << std::endl;
    return 1;
  }
  catch(...)
  {
    std::cerr << __FILE__ << ": unknown exception caught\n";
    return -1;
  }
  return 0;
}
#endif

//######################################
// End #################################
//######################################

