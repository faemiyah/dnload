#ifndef __g_shader_fragment_quad_header__
#define __g_shader_fragment_quad_header__
static const char *g_shader_fragment_quad = ""
#if defined(USE_LD)
"quad_430.frag.glsl"
#else
"#version 430\n"
"layout(location=0)uniform vec3 i[4];"
"in vec2 o;"
"out vec4 r;"
"void main()"
"{"
"vec2 e=o;"
"if(i[3].g>1.)e.r*=i[3].g;"
"else e.g/=i[3].g;"
"vec3 o=normalize(i[1]),g=normalize(cross(o,i[2])),v=normalize(e.r*g+e.g*normalize(cross(g,o))+o);"
"float t=dot(-i[0],v),h=1.+sin(i[3].r/4444.)*.1;"
"vec3 l=t*v+i[0];"
"float c=dot(l,l);"
"if(c<=h)"
"{"
"vec3 o=(t-sqrt(h*h-c*c))*v+i[0];"
"r=vec4(o*dot(o,vec3(1)),1.);"
"}"
"else r=vec4(.0,.0,.0,1.);"
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
#endif
