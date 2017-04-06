#version 430

layout(location=0) uniform vec3[4] uniform_array;

in vec2 position;

out vec4 output_color;

void main()
{
  vec2 aspect = position;
  if(uniform_array[3].y > 1.0)
  {
    aspect.x *= uniform_array[3].y;
  }
  else
  {
    aspect.y /= uniform_array[3].y;
  }

  vec3 forward = normalize(uniform_array[1]);
  vec3 right = normalize(cross(forward, uniform_array[2]));
  vec3 direction = normalize(aspect.x * right + aspect.y * normalize(cross(right, forward)) + forward);

  float product = dot(-uniform_array[0], direction);
  float radius = 1.0 + sin(uniform_array[3].x / 4444.0) * 0.1;
  vec3 collision = product * direction + uniform_array[0];

  float squared = dot(collision, collision);
  if(squared <= radius)
  {
    vec3 color = (product - sqrt(radius * radius - squared * squared)) * direction + uniform_array[0];
    output_color = vec4(color * dot(color, vec3(1.0)), 1.0);
  }
  else
  {
    output_color = vec4(0.0, 0.0, 0.0, 1.0);
  }
}
