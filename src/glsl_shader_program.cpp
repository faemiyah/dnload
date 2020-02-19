#include "glsl_shader_program.hpp"

#include "glsl_program.hpp"

#if !defined(DNLOAD_GLESV2)

//######################################
// Global ##############################
//######################################

GlslShaderProgram::GlslShaderProgram(GLenum type) :
    GlslShaderSource(type)
{
}

GlslShader::~GlslShader()
{
    cleanup();
}

void GlslShader::cleanup()
{
    if(m_id)
    {
        glDeleteProgram(m_pipeline_id);
        m_id = 0u;
    }
}

bool GlslShader::compile(bool pipeline)
{
    cleanup();

    std::string source = read();
    const GLchar* glsl_parts[1] = { source.c_str() };

    m_id = glCreateShaderProgramv(m_type, static_cast<GLsizei>(glsl_parts.size()), &(glsl_parts[0]));
    if(!GlslProgram::get_program_link_status(m_id))
    {
        std::cout << GlslProgram::get_program_info_log(m_id);
        return false;
    }

    return true;
}

GLuint GlslShader::getStage() const
{
    switch(m_type)
    {
    case GL_VERTEX_SHADER:
        return 1;

    case GL_FRAGMENT_SHADER:
        return 2;

    default:
        break;
    }

    std::ostringstream sstr;
    sstr << "no stage known for shader of type '" << m_type << "'";
    BOOST_THROW_EXCEPTION(std::runtime_error(sstr.str()));
}

#endif
