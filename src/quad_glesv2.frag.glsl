uniform mediump vec3 uniform_array[4];

varying mediump vec2 position;

void main()
{
    mediump vec2 aspect = position;
    if(uniform_array[3].y > 1.0)
    {
        aspect.x *= uniform_array[3].y;
    }
    else
    {
        aspect.y /= uniform_array[3].y;
    }

    mediump vec3 forward = normalize(uniform_array[1]);
    mediump vec3 right = normalize(cross(forward, uniform_array[2]));
    mediump vec3 direction = normalize(aspect.x * right + aspect.y * normalize(cross(right, forward)) + forward);

    mediump float product = dot(-uniform_array[0], direction);
    mediump float radius = 1.0 + sin(uniform_array[3].x / 4444.0) * 0.1;
    mediump vec3 collision = product * direction + uniform_array[0];

    mediump float squared = dot(collision, collision);
    if(squared <= radius)
    {
        mediump vec3 color = (product - sqrt(radius * radius - squared * squared)) * direction + uniform_array[0];
        gl_FragColor = vec4(color * dot(color, vec3(1.0)), 1.0);
    }
    else
    {
        gl_FragColor = vec4(0.0, 0.0, 0.0, 1.0);
    }
}
