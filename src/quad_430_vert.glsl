#version 430

in vec2 vertex;

out vec2 position;

out gl_PerVertex
{
  vec4 gl_Position;
};

void main()
{
  position = vertex;
  gl_Position=vec4(vertex, 0.0, 1.0);
}
