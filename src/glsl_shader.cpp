#include "glsl_shader.hpp"

#include <boost/throw_exception.hpp>

#include <iostream>

//######################################
// Local ###############################
//######################################

namespace
{

/// Get shader info log.
///
/// \param op Shader ID.
/// \return Info string.
std::string get_shader_info_log(GLuint op)
{
    std::string ret;
    GLint len;

    glGetShaderiv(op, GL_INFO_LOG_LENGTH, &len);
    if(len)
    {
        GLchar *log = new GLchar[len];
        GLsizei acquired;

        glGetShaderInfoLog(op, len, &acquired, log);

        ret.assign(log);
        delete[] log;
    }

    return ret;
}

/// Get compile status for a shader.
///
/// \param op Shader ID.
/// \return True if compilation was successful, false otherwise.
bool get_shader_compile_status(GLuint op)
{
    GLint ret;

    glGetShaderiv(op, GL_COMPILE_STATUS, &ret);

    return (GL_FALSE != ret);
}

}

//######################################
// Class ###############################
//######################################

GlslShader::~GlslShader()
{
    cleanup();
}

void GlslShader::cleanup()
{
    if(m_id)
    {
        glDeleteShader(m_id);
        m_id = 0;
    }
}

bool GlslShader::compile()
{
    cleanup();

    std::string source = read();
    const GLchar* glsl_parts[1] = { source.c_str() };

    m_id = glCreateShader(m_type);
    glShaderSource(m_id, static_cast<GLsizei>(1), &(glsl_parts[0]), NULL);
    glCompileShader(m_id);

    if(!get_shader_compile_status(m_id))
    {
        std::cout << get_shader_info_log(m_id);
        return false;
    }

    return true;
}

