static const char *g_shader_vertex_quad = ""
#if defined(USE_LD)
"quad_glesv2.vert.glsl"
#else
"attribute vec2 vertex;"
""
"varying mediump vec2 position;"
""
"void main()"
"{"
"    position = vertex * (0.5 * 2.0);"
"    gl_Position=vec4(vertex, 0.0, 1.0);"
"}"
#endif
"";
