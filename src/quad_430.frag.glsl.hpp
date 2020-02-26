#ifndef __g_shader_fragment_quad_header__
#define __g_shader_fragment_quad_header__
static const char *g_shader_fragment_quad = ""
#if defined(USE_LD)
"quad_430.frag.glsl"
#else
"#version 430\n"
"layout(location=0)uniform vec3 i[4];"
"in vec2 e;"
"out vec4 g;"
"void main()"
"{"
"vec2 o=e;"
"if(i[3].g>1.)o.r*=i[3].g;"
"else o.g/=i[3].g;"
"vec3 e=normalize(i[1]),l=normalize(cross(e,i[2])),v=normalize(o.r*l+o.g*normalize(cross(l,e))+e);"
"float t=dot(-i[0],v),c=1.+sin(i[3].r/4444.)*.1;"
"vec3 n=t*v+i[0];"
"float r=dot(n,n);"
"if(r<=c)"
"{"
"vec3 e=(t-sqrt(c*c-r*r))*v+i[0];"
"g=vec4(e*dot(e,vec3(1)),1.);"
"}"
"else g=vec4(.0,.0,.0,1.);"
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
