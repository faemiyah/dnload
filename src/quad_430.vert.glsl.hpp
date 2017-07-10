static const char *g_shader_vertex_quad = ""
#if defined(USE_LD)
"quad_430.vert.glsl"
#else
"#version 430\n"
"in vec2 e;"
"out vec2 i;"
"out gl_PerVertex"
"{"
"vec4 gl_Position;"
"}"
";"
"void main()"
"{"
"i=e;"
"gl_Position=vec4(e,.0,1.);"
"}"
#endif
"";
