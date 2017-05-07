#include "glsl_shader.hpp"

#include "glsl_program.hpp"
#include "glsl_wave.hpp"

#include <boost/filesystem.hpp>
#include <boost/throw_exception.hpp>

#include <fstream>
#include <iostream>
#include <sstream>

namespace fs = boost::filesystem;

//######################################
// Local ###############################
//######################################

namespace
{

/// Find a file, try several different default locations.
///
/// \param name Base name to open.
/// \return File to open or an empty string.
fs::path find_file(const std::string &name)
{
  fs::path attempt = name;
  if(fs::exists(attempt))
  {
    return attempt;
  }

  attempt = fs::path("..") / fs::path(name);
  if(fs::exists(attempt))
  {
    return attempt;
  }

  const fs::path SRC_PATH("src");
  attempt = SRC_PATH / fs::path(name);
  if(fs::exists(attempt))
  {
    return attempt;
  }

  attempt = fs::path("..") / SRC_PATH / fs::path(name);
  if(fs::exists(attempt))
  {
    return attempt;
  }

  const fs::path REL_PATH("rel");
  attempt = REL_PATH / fs::path(name);
  if(fs::exists(attempt))
  {
    return attempt;
  }

  attempt = fs::path("..") / REL_PATH / fs::path(name);
  if(fs::exists(attempt))
  {
    return attempt;
  }

  return fs::path();
}

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

/// Read a file.
///
/// \param name File to open.
/// \return Contents of file as a string.
std::string read_file(const fs::path &name)
{
  std::ostringstream ret;
  std::ifstream fd(name.string());

  for(;;)
  {
    char cc;
    fd.get(cc);

    if(fd.eof())
    {
      return ret.str();
    }

    ret << cc;
  }
}

}

//######################################
// Global ##############################
//######################################

GlslShader::GlslShader(GLenum type, const char *src1) :
  m_type(type),
  m_id(0),
  m_pipeline_id(0)
{
  m_files.push_back(std::string(src1));

  compile();
}

GlslShader::GlslShader(GLenum type, const char *src1, const char *src2) :
  m_type(type),
  m_id(0),
  m_pipeline_id(0)
{
  m_files.push_back(std::string(src1));
  m_files.push_back(std::string(src2));

  compile();
}

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

  if(m_pipeline_id)
  {
    glDeleteProgram(m_pipeline_id);
    m_pipeline_id = 0;
  }
}

bool GlslShader::compile(bool pipeline)
{
  cleanup();

  std::vector<std::string> parts;

  for(const std::string &vv : m_files)
  {
    fs::path name = find_file(vv);
    if(name.empty())
    {
      std::ostringstream sstr;
      sstr << "could not find suitable file source for " << fs::path(vv);
      BOOST_THROW_EXCEPTION(std::runtime_error(sstr.str()));
    }

    std::string source = read_file(name);
    std::string processed = glsl_wave_preprocess(source);

    parts.push_back(processed);
  }

  std::vector<const GLchar*> glsl_parts;

  for(const std::string &vv : parts)
  {
    glsl_parts.push_back(vv.c_str());
  }

  if(pipeline)
  {
    m_pipeline_id = glCreateShaderProgramv(m_type, static_cast<GLsizei>(glsl_parts.size()), &(glsl_parts[0]));

    if(!GlslProgram::get_program_link_status(m_pipeline_id))
    {
      std::cout << GlslProgram::get_program_info_log(m_pipeline_id);
      return false;
    }
  }
  else
  {
    m_id = glCreateShader(m_type);
    glShaderSource(m_id, static_cast<GLsizei>(glsl_parts.size()), &(glsl_parts[0]), NULL);
    glCompileShader(m_id);
  
    if(!get_shader_compile_status(m_id))
    {
      std::cout << get_shader_info_log(m_id);
      return false;
    }
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

