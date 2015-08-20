/** \file
 * One-quad example.
 */

//######################################
// Define ##############################
//######################################

/** Screen width. */
#define SCREEN_W 1280

/** Screen heigth. */
#define SCREEN_H 720

/** Fullscreen on/off. */
#define FLAG_FULLSCREEN 0

/** Intro length (in milliseconds). */
#define INTRO_LENGTH (16000)

//######################################
// Include #############################
//######################################

#include "dnload.h"

//######################################
// Shaders #############################
//######################################

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
"layout(location=0)uniform float t;"
"in vec2 b;"
"out vec4 o;"
"void main()"
"{"
"o=vec4(b.x,sin(t/777)*.5+.5,b.y,1);"
"}";

/** \cond */
static GLuint g_program_fragment;
/** \endcond */

//######################################
// Draw ################################
//######################################

/** \brief Draw the world.
 *
 * \param ticks Milliseconds.
 * \param aspec Screen aspect.
 */
static void draw(unsigned ticks)
{
  dnload_glProgramUniform1f(g_program_fragment, 0, ticks);

  dnload_glRects(-1, -1, 1, 1);
}

//######################################
// Main ################################
//######################################

#if defined(USE_LD)
int main()
#else
void _start()
#endif
{
  dnload();
  dnload_SDL_Init(SDL_INIT_VIDEO | SDL_INIT_AUDIO);
  SDL_Window *window = dnload_SDL_CreateWindow(NULL, 0, 0, SCREEN_W, SCREEN_H,
      SDL_WINDOW_OPENGL | (FLAG_FULLSCREEN ? SDL_WINDOW_FULLSCREEN : 0));
  dnload_SDL_GL_CreateContext(window);
  dnload_SDL_ShowCursor(0);
#if defined(USE_LD)
  glewInit();
#endif

  // Shader generation inline.
  GLuint pipeline;
  GLuint program_vert = dnload_glCreateShaderProgramv(GL_VERTEX_SHADER, 1, &g_shader_vertex_quad);
  g_program_fragment = dnload_glCreateShaderProgramv(GL_FRAGMENT_SHADER, 1, &g_shader_fragment_quad);

  dnload_glGenProgramPipelines(1, &pipeline);
  dnload_glBindProgramPipeline(pipeline);
  dnload_glUseProgramStages(pipeline, 1, program_vert);
  dnload_glUseProgramStages(pipeline, 2, g_program_fragment);

  unsigned start_ticks = dnload_SDL_GetTicks();

  for(;;)
  {
    SDL_Event event;
    unsigned curr_ticks = dnload_SDL_GetTicks() - start_ticks;

    dnload_SDL_PollEvent(&event);

    if((curr_ticks >= INTRO_LENGTH) || (event.type == SDL_KEYDOWN))
    {
      break;
    }

    draw(curr_ticks);
    dnload_SDL_GL_SwapWindow(window);
  }

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

