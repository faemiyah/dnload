static const char *g_shader_vertex_quad = ""
#if defined(USE_LD)
"quad_430.vert.glsl"
#else
"#version 430\n"
"in vec2 o;"
"out vec2 v;"
"out gl_PerVertex"
"{"
"vec4 gl_Position;"
"}"
";"
"void main()"
"{"
"v=o;"
"gl_Position=vec4(o,.0,1.);"
"}"
#endif
"";
