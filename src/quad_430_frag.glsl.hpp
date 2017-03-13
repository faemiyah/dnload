static const char *g_shader_fragment_quad = ""
#if defined(USE_LD)
"quad_430_frag.glsl"
#else
"#version 430\n"
"layout(location=0)uniform vec3[4] uniform_array;"
"in vec2 position;"
"out vec4 gl_FragColor;"
"void main(){vec2 aspect=position;if(uniform_array[3].y>1.){aspect.x*=uniform_array[3].y;}else{aspect.y/=uniform_array[3].y;}vec3 forward=normalize(uniform_array[1]);vec3 right=normalize(cross(forward,uniform_array[2]));vec3 direction=normalize(aspect.x*right+aspect.y*normalize(cross(right,forward))+forward);float product=dot(-uniform_array[0],direction);float radius=1.+sin(uniform_array[3].x/4444.)*0.1;vec3 collision=product*direction+uniform_array[0];float squared=dot(collision,collision);if(squared<=radius){vec3 e=(product-sqrt(radius*radius-squared*squared))*direction+uniform_array[0];gl_FragColor=vec4(e*dot(e,vec3(1.)),1.);}else{gl_FragColor=vec4(0.,0.,0.,1.);}}"
#endif
"";
