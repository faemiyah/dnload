#ifndef __g_shader_vertex_quad_header__
#define __g_shader_vertex_quad_header__
static const char *g_shader_vertex_quad = ""
#if defined(USE_LD)
"quad_430.vert.glsl"
#else
"#version 430\n"
"in vec2 i;"
"out vec2 e;"
"out gl_PerVertex"
"{"
"vec4 gl_Position;"
"}"
";"
"void main()"
"{"
"e=i,gl_Position=vec4(i,0,1);"
"}"
#endif
"";
#if !defined(DNLOAD_RENAME_UNUSED)
#if defined(__GNUC__)
#define DNLOAD_RENAME_UNUSED __attribute__((unused))
#else
#define DNLOAD_RENAME_UNUSED
#endif
#endif
static const char* g_shader_vertex_quad_attribute_vertex DNLOAD_RENAME_UNUSED = ""
#if defined(USE_LD)
"vertex"
#else
"i"
#endif
"";
#endif
