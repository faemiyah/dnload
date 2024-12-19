#include "glsl_pipeline.hpp"

#include <boost/throw_exception.hpp>

#include <iostream>
#include <sstream>

#if !defined(DNLOAD_USE_GLES)

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
        GLchar *log = new GLchar[static_cast<unsigned>(len)];
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

GlslPipeline::~GlslPipeline()
{
    cleanup();
}

void GlslPipeline::cleanup()
{
    if(m_id)
    {
        glDeleteProgramPipelines(1, &m_id);
        m_id = 0;
    }
}

std::string GlslPipeline::getName() const
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

GLuint GlslPipeline::getProgramId(GLenum type) const
{
    for(auto& vv : m_shaders)
    {
        if(vv->getType() == type)
        {
            return vv->getId();
        }
    }

    std::ostringstream sstr;
    sstr << "no shader program of type '" << type << "' in pipeline";
    BOOST_THROW_EXCEPTION(std::runtime_error(sstr.str()));
}

bool GlslPipeline::link()
{
    cleanup();

    glGenProgramPipelines(1, &m_id);

    for(auto& vv : m_shaders)
    {
        if(!vv->compile())
        {
            return false;
        }

        glUseProgramStages(m_id, vv->getStage(), vv->getId());
    }

    std::string log = get_pipeline_info_log(m_id);
    if(!log.empty())
    {
        std::cout << log;
        return false;
    }

    return true;
}

#endif

