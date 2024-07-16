#ifndef __g_shader_fragment_quad_header__
#define __g_shader_fragment_quad_header__
static const char *g_shader_fragment_quad = ""
#if defined(USE_LD)
"quad_glesv2.frag.glsl"
#else
"uniform vec3 i[4];"
"varying vec2 e;"
"void main()"
"{"
"vec2 o=e;"
"if(i[3].g>1.)o.r*=i[3].g;"
"else o.g/=i[3].g;"
"vec3 e=normalize(i[1]),t=normalize(cross(e,i[2])),v=normalize(o.r*t+o.g*normalize(cross(t,e))+e);"
"float r=dot(-i[0],v),h=1.+sin(i[3].r/4444.)*.1;"
"vec3 g=r*v+i[0];"
"float c=dot(g,g);"
"if(c<=h)"
"{"
"vec3 e=(r-sqrt(h*h-c*c))*v+i[0];"
"gl_FragColor=vec4(e*dot(e,vec3(1)),1.);"
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
