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
"vec3 e=normalize(i[1]),c=normalize(cross(e,i[2])),v=normalize(o.r*c+o.g*normalize(cross(c,e))+e);"
"float g=dot(-i[0],v),r=1.+sin(i[3].r/4444.)*.1;"
"vec3 t=g*v+i[0];"
"float h=dot(t,t);"
"if(h<=r)"
"{"
"vec3 e=(g-sqrt(r*r-h*h))*v+i[0];"
"gl_FragColor=vec4(e*dot(e,vec3(1)),1);"
"}"
"else gl_FragColor=vec4(0,0,0,1);"
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
