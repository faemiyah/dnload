#include "glsl_program.hpp"

#include <iostream>

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

/// Get program info log.
///
/// \param op Program ID.
/// \return Info string.
std::string GlslProgram::get_program_info_log(GLuint op)
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

//######################################
// Global ##############################
//######################################

/// Get link status for a program.
///
/// \param op Program ID.
/// \return True if link successful, false otherwise.
bool GlslProgram::get_program_link_status(GLuint op)
{
  GLint ret;

  glGetProgramiv(op, GL_LINK_STATUS, &ret);

  return (GL_FALSE != ret);
}

GlslProgram::GlslProgram() :
  m_id(0),
  m_pipeline_id(0)
{
}

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

  if(m_pipeline_id)
  {
    glDeleteProgramPipelines(1, &m_pipeline_id);
    m_pipeline_id = 0;
  }
}

GLuint GlslProgram::getPipelineId(GLenum op) const
{
  for(const GlslShaderUptr &vv : m_shaders)
  {
    if(vv->getType() == op)
    {
      return vv->getPipelineId();
    }
  }

  return 0;
}

bool GlslProgram::link(bool pipeline)
{
  cleanup();

  if(pipeline)
  {
    glGenProgramPipelines(1, &m_pipeline_id);
  }
  else
  {
    m_id = glCreateProgram();
  }

  for(GlslShaderUptr &vv : m_shaders)
  {
    if(!vv->compile(pipeline))
    {
      return false;
    }

    if(pipeline)
    {
      glUseProgramStages(m_pipeline_id, vv->getStage(), vv->getPipelineId());
    }
    else
    {
      glAttachShader(m_id, vv->getId());
    }
  }

  if(pipeline)
  {
    std::string log = get_pipeline_info_log(m_pipeline_id);
    if(!log.empty())
    {
      std::cout << log;
      return false;
    }
  }
  else
  {
    glLinkProgram(m_id);

    if(!get_program_link_status(m_id))
    {
      std::cout << get_program_info_log(m_id);
      return false;
    }
  }

  return true;
}

