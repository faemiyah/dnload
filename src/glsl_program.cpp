#include "glsl_program.hpp"

#include <iostream>
#include <sstream>

//######################################
// Class ###############################
//######################################

GlslProgram::~GlslProgram()
{
    cleanup();
}

void GlslProgram::cleanup()
{
    if(m_id)
    {
        glDeleteProgram(m_id);
        m_id = 0;
    }
}

std::string GlslProgram::getName() const
{
    std::ostringstream sstr;
    sstr << "'";

    for(size_t ii = 0; (ii < m_shaders.size()); ++ii)
    {
        if(ii)
        {
            sstr << ";";
        }
        sstr << m_shaders[ii]->getName();
    }

    sstr << "'";
    return sstr.str();
}

bool GlslProgram::link()
{
    cleanup();

    m_id = glCreateProgram();

    for(auto& vv : m_shaders)
    {
        if(!vv->compile())
        {
            return false;
        }

        glAttachShader(m_id, vv->getId());
    }

    glLinkProgram(m_id);

    if(!get_program_link_status(m_id))
    {
        std::cout << get_program_info_log(m_id);
        return false;
    }

    return true;
}

//######################################
// Global ##############################
//######################################

/// Get program info log.
///
/// \param op Program ID.
/// \return Info string.
std::string get_program_info_log(GLuint op)
{
    std::string ret;
    GLint len;

    glGetProgramiv(op, GL_INFO_LOG_LENGTH, &len);
    if(len)
    {
        GLchar *log = new GLchar[len];
        GLsizei acquired;

        glGetProgramInfoLog(op, len, &acquired, log);

        ret.assign(log);
        delete[] log;
    }

    return ret;
}

/// Get link status for a program.
///
/// \param op Program ID.
/// \return True if link successful, false otherwise.
bool get_program_link_status(GLuint op)
{
    GLint ret;

    glGetProgramiv(op, GL_LINK_STATUS, &ret);

    return (GL_FALSE != ret);
}

