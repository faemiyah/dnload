#ifndef __g_shader_fragment_quad_header__
#define __g_shader_fragment_quad_header__
static const char *g_shader_fragment_quad = ""
#if defined(USE_LD)
"quad_glesv2.frag.glsl"
#else
"uniform vec3 i[4];"
"varying vec2 o;"
"void main()"
"{"
"vec2 e=o;"
"if(i[3].g>1.)e.r*=i[3].g;"
"else e.g/=i[3].g;"
"vec3 o=normalize(i[1]),r=normalize(cross(o,i[2])),v=normalize(e.r*r+e.g*normalize(cross(r,o))+o);"
"float g=dot(-i[0],v),h=1.+sin(i[3].r/4444.)*.1;"
"vec3 t=g*v+i[0];"
"float c=dot(t,t);"
"if(c<=h)"
"{"
"vec3 o=(g-sqrt(h*h-c*c))*v+i[0];"
"gl_FragColor=vec4(o*dot(o,vec3(1)),1.);"
"}"
"else gl_FragColor=vec4(.0,.0,.0,1.);"
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
static const char* g_shader_fragment_quad_uniform_uniform_array DNLOAD_RENAME_UNUSED = ""
#if defined(USE_LD)
"uniform_array"
#else
"i"
#endif
"";
#endif
