/** \file
 * Very small intro stub.
 */

//######################################
// Define ##############################
//######################################

/** Screen width. */
#define SCREEN_W 1280

/** Screen heigth. */
#define SCREEN_H 720

/** Audio channels. */
#define AUDIO_CHANNELS 2

/** Audio samplerate. */
#define AUDIO_SAMPLERATE 8000

/** Audio byterate. */
#define AUDIO_BYTERATE (AUDIO_CHANNELS * AUDIO_SAMPLERATE * sizeof(uint8_t))

/** Intro length (in bytes of audio). */
#define INTRO_LENGTH (16 * AUDIO_BYTERATE)

/** Intro start position (in seconds). */
#define INTRO_START (0 * AUDIO_BYTERATE)

/** \cond */
#define STARTING_POS_X 0.0f
#define STARTING_POS_Y 0.0f
#define STARTING_POS_Z 2.0f
#define STARTING_FW_X 0.0f
#define STARTING_FW_Y 0.0f
#define STARTING_FW_Z -1.0f
#define STARTING_UP_X 0.0f
#define STARTING_UP_Y 1.0f
#define STARTING_UP_Z 0.0f
/** \endcond */

//######################################
// Include #############################
//######################################

#include "dnload.h"
#include "intro.hpp"

#if defined(DNLOAD_GLESV2)
#include "dnload_videocore.h"
#include "dnload_egl.h"
#endif

#if defined(USE_LD)
#include "glsl_shader_source.hpp"
#include <iostream>
#endif

//######################################
// Global data #########################
//######################################

/** Audio buffer for output. */
static int16_t g_audio_buffer[INTRO_LENGTH * 9 / 8 / sizeof(uint8_t)];

/** Current audio position. */
static uint8_t *g_audio_position = reinterpret_cast<uint8_t*>(&g_audio_buffer[INTRO_START]);

#if defined(USE_LD)

/** \cond */
static float g_pos_x = STARTING_POS_X;
static float g_pos_y = STARTING_POS_Y;
static float g_pos_z = STARTING_POS_Z;
static float g_fw_x = STARTING_FW_X;
static float g_fw_y = STARTING_FW_Y;
static float g_fw_z = STARTING_FW_Z;
static float g_up_x = STARTING_UP_X;
static float g_up_y = STARTING_UP_Y;
static float g_up_z = STARTING_UP_Z;
/** \endcond */

/** Developer mode global toggle. */
static uint8_t g_flag_developer = 0;

#endif

//######################################
// Random ##############################
//######################################

#if 0

/** \brief Random float value.
 *
 * \param op Given maximum value.
 * \return Random value between 0 and given value.
 */
static float frand(float op)
{
  return static_cast<float>(dnload_rand() & 0xFFFF) * ((1.0f / 65535.0f) * op);
}

#endif

//######################################
// Music ###############################
//######################################

/** \brief Update audio stream.
 *
 * \param userdata Not used.
 * \param stream Target stream.
 * \param len Number of bytes to write.
 */
static void audio_callback(void *userdata, Uint8 *stream, int len)
{
  (void)userdata;

  while(len--)
  {
    *stream++ = *g_audio_position++;
  }
}

/** SDL audio specification struct. */
static SDL_AudioSpec audio_spec =
{
  AUDIO_SAMPLERATE,
  AUDIO_U8,
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

/** Quad vertex shader. */
static const char *g_shader_vertex_quad = ""
"attribute vec2 a;"
"varying mediump vec2 b;"
"precision mediump float;"
"void main()"
"{"
"b=a;"
"gl_Position=vec4(a,0.,1.);"
"}";

/** Quad fragment shader. */
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

/** Uniform location. */
static GLint g_uniform_u;

#else

/** Quad vertex shader. */
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

/** Quad fragment shader. */
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

/** Fixed uniform location. */
static const GLint g_uniform_u = 0;

#endif

/** \cond */
GLuint g_program_fragment;
/** \endcond */

#if defined(DNLOAD_GLESV2)

/** \brief Create shader.
 *
 * \param source Source of the shader.
 * \return Shader ID.
 */
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
    SDL_Quit();
    exit(1);
  }
#endif

  return ret;
}

/** \brief Create program.
 *
 * \param vertex Vertex shader.
 * \param fragment Fragment shader.
 * \return Program ID
 */
GLuint create_program(const char *vertex, const char *fragment)
{
  GLuint ret = dnload_glCreateProgram();

  dnload_glAttachShader(ret, create_shader(vertex, GL_VERTEX_SHADER));
  dnload_glAttachShader(ret, create_shader(fragment, GL_FRAGMENT_SHADER));

  dnload_glLinkProgram(ret);

#if defined(USE_LD)
  std::cout << "Getting info log. " << std::endl;
  //std::string log = GlslShaderSource::get_program_info_log(ret);

  //if(0 < log.length())
  //{
  //  std::cout << log << std::endl;
  //}

  std::cout << "Getting link status. " << std::endl;
  if(!GlslShaderSource::get_program_link_status(ret))
  {
    std::cout << "Link status bad. " << ret << std::endl;
    SDL_Quit();
    exit(1);
  }
  std::cout << "GLSL program id: " << ret << std::endl;
#endif

  return ret;
}

#elif defined(USE_LD)

/** \brief Create a shader.
 *
 * \param type Shader type.
 * \param source Shader content.
 * \return Shader program ID.
 */
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

/** \brief Create a program pipeline.
 *
 * \return Program pipeline (already bound).
 */
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

/** \brief Uniforms.
 *
 * 0: X position.
 * 1: Y position.
 * 2: Z position.
 * 3: X forward.
 * 4: Y forward.
 * 5: Z forward.
 * 6: X up.
 * 7: Y up.
 * 8: Z up.
 * 9: Time.
 * 10: Screen aspect ratio x/y.
 * 11: Unused.
 */
static float g_uniform_array[12] =
{
  STARTING_POS_X, STARTING_POS_Y, STARTING_POS_Z,
  STARTING_FW_X, STARTING_FW_Y, STARTING_FW_Z,
  STARTING_UP_X, STARTING_UP_Y, STARTING_UP_Z,
  0.0f, 0.0f, 0.0f,
};

/** \brief Draw the world.
 *
 * \param ticks Tick count.
 * \param aspec Screen aspect.
 */
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
// Main ################################
//######################################

#if defined(USE_LD)
int intro(unsigned screen_w, unsigned screen_h, uint8_t flag_developer, uint8_t flag_fullscreen,
    uint8_t flag_record)
{
#else
/** \cond */
#define screen_w SCREEN_W
#define screen_h SCREEN_H
#define flag_developer 0
#define flag_fullscreen 0
/** \endcond */
void _start()
{
#endif
  dnload();
#if defined(DNLOAD_GLESV2)
  dnload_SDL_Init(SDL_INIT_VIDEO | SDL_INIT_AUDIO);
  dnload_SDL_SetVideoMode(static_cast<int>(screen_w), static_cast<int>(screen_h), 0,
      (flag_fullscreen ? SDL_FULLSCREEN : 0));
  dnload_SDL_ShowCursor(flag_developer);
  EGL_DISPMANX_WINDOW_T native_window;
  videocore_create_native_window(screen_w, screen_h, &native_window);
  EGLDisplay egl_display;
  EGLSurface egl_surface;
  bool egl_result = egl_init(reinterpret_cast<NativeWindowType>(&native_window), &egl_display, &egl_surface);
#if defined(USE_LD)
  if(!egl_result)
  {
    SDL_Quit();
    exit(1);
  }
#else
  (void)egl_result;
#endif
#else
  dnload_SDL_Init(SDL_INIT_VIDEO | SDL_INIT_AUDIO);
  dnload_SDL_SetVideoMode(static_cast<int>(screen_w), static_cast<int>(screen_h), 0,
      SDL_OPENGL | (flag_fullscreen ? SDL_FULLSCREEN : 0));
  dnload_SDL_ShowCursor(flag_developer);
#if defined(USE_LD)
  {
    GLenum err = glewInit();
    if(GLEW_OK != err)
    {
      SDL_Quit();
      std::cerr  << "glewInit(): " << glewGetErrorString(err) << std::endl;
      exit(1);
    }
  }
#endif
#endif

#if defined(DNLOAD_GLESV2)
  g_program_fragment = create_program(g_shader_vertex_quad, g_shader_fragment_quad);
  dnload_glUseProgram(g_program_fragment);
  g_uniform_u = dnload_glGetUniformLocation(g_program_fragment, "u");
#elif defined(USE_LD)
  GLuint pipeline = pipeline_create();
  program_attach(GL_VERTEX_SHADER, g_shader_vertex_quad, pipeline, 1);
  g_program_fragment = program_attach(GL_FRAGMENT_SHADER, g_shader_fragment_quad, pipeline, 2);
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

  g_uniform_array[10] = static_cast<float>(screen_w) / static_cast<float>(screen_h);

  {
    unsigned ii;

    // Example by "bst", taken from "Music from very short programs - the 3rd iteration" by viznut.
    for(ii = 0; (INTRO_LENGTH / sizeof(uint8_t) > ii); ++ii)
    {
      g_audio_buffer[ii] = static_cast<int>(ii / 70000000 * ii * ii + ii) % 127 | ii >> 4 | ii >> 5 | (ii % 127 + (ii >> 17)) | ii;
    }
  }

#if defined(USE_LD)
  if(flag_record)
  {
    SDL_Event event;
    unsigned frame_idx = 0;

    // audio
    SDL_PauseAudio(1);

    write_audio_callback(g_audio_buffer, static_cast<unsigned>(INTRO_LENGTH * sizeof(uint16_t) * AUDIO_CHANNELS));

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
      write_frame_callback(screen_w, screen_h, frame_idx);
      SDL_GL_SwapBuffers();
      ++frame_idx;
    }

    SDL_Quit();
    return 0;
  }

  if(!flag_developer)
  {
    SDL_OpenAudio(&audio_spec, NULL);
    SDL_PauseAudio(0);
  }
  g_flag_developer = flag_developer;
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
#if defined(DNLOAD_GLESV2)
    dnload_eglSwapBuffers(egl_display, egl_surface);
#else
    dnload_SDL_GL_SwapBuffers();
#endif
  }

#if defined(DNLOAD_GLESV2)
  egl_quit(egl_display);
#endif
  dnload_SDL_Quit();

#if defined(USE_LD)
  return 0;
#else
  asm_exit();
#endif
}

//######################################
// End #################################
//######################################

