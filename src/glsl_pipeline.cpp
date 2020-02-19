#include "glsl_pipeline.hpp"

#if !defined(DNLOAD_GLESV2)

//######################################
// Local ###############################
//######################################

namespace
{

/// Get pipeline info log.
///
/// \param op Pipeline ID.
/// \return Info string.
std::string get_pipeline_info_log(GLuint op)
{
    std::string ret;
    GLint len;

    glGetProgramPipelineiv(op, GL_INFO_LOG_LENGTH, &len);
    if(len)
    {
        GLchar *log = new GLchar[len];
        GLsizei acquired;

        glGetProgramPipelineInfoLog(op, len, &acquired, log);

        ret.assign(log);
        delete[] log;
    }

    return ret;
}

}

//######################################
// Global ##############################
//######################################

GlslProgram::~GlslProgram()
{
    cleanup();
}

void GlslProgram::cleanup()
{
    if(m_id)
    {
        glDeleteProgramPipelines(1, &m_id);
        m_pipeline_id = 0;
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

    glGenProgramPipelines(1, &m_pipeline_id);

    for(GlslShaderProgramUptr &vv : m_shader_programs)
    {
        if(!vv->link())
        {
            return false;
        }

        glUseProgramStages(m_pipeline_id, vv->getStage(), vv->getPipelineId());
    }

    std::string log = get_pipeline_info_log(m_pipeline_id);
    if(!log.empty())
    {
        std::cout << log;
        return false;
    }

    return true;
}

#endif

